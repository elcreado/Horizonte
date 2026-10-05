from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.db import DatabaseError
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import BackgroundTask
from apps.accounts.tasks import send_password_recovery


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"],
)
class RecoveryTests(TransactionTestCase):
    # Incluye el comando worker, que renueva conexiones fuera de transacciones activas.
    @override_settings(BACKGROUND_MODE="database")
    def test_database_queue_failure_returns_generic_503_without_message(self):
        with patch(
            "apps.accounts.models.BackgroundTask.objects.create",
            side_effect=DatabaseError("private-db-password"),
        ):
            for username, email in (
                (self.user.username, self.user.email),
                ("missing", "missing@example.com"),
            ):
                response = self.post("recover-password", {"username": username, "email": email})
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private-db-password", response.content.decode())
        self.assertFalse(BackgroundTask.objects.exists())
        self.assertFalse(mail.outbox)

    @override_settings(BACKGROUND_MODE="database")
    def test_recovery_flows_through_database_worker_and_reset(self):
        response = self.post(
            "recover-password", {"username": self.user.username, "email": self.user.email}
        )
        self.assertEqual(response.status_code, 202)
        self.assertFalse(mail.outbox)
        call_command("run_background", once=True)
        queued = BackgroundTask.objects.get()
        self.assertEqual(queued.status, "completed")
        self.assertEqual(queued.kwargs, {})
        self.assertEqual(len(mail.outbox), 1)
        link = next(line for line in mail.outbox[0].body.splitlines() if line.startswith("http"))
        query = parse_qs(urlsplit(link).fragment.split("?", 1)[1])
        password = "Recovered-through-worker-592!"
        payload = {
            "uid": query["uid"][0],
            "token": query["token"][0],
            "password": password,
            "password_confirm": password,
        }
        self.assertEqual(self.post("reset-password", payload).status_code, 200)
        self.assertEqual(self.post("reset-password", payload).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(password))

    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username="recover", email="recover@example.com", password="Previous-test-password!"
        )
        self.client = APIClient(enforce_csrf_checks=True)

    def post(self, endpoint, body):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        return self.client.post(
            "/api/auth/" + endpoint + "/",
            body,
            format="json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN="http://127.0.0.1:5173",
        )

    def reset_body(self):
        send_password_recovery(self.user.username, self.user.email)
        link = next(line for line in mail.outbox[-1].body.splitlines() if line.startswith("http"))
        query = parse_qs(urlsplit(link).fragment.split("?", 1)[1])
        return {
            "uid": query["uid"][0],
            "token": query["token"][0],
            "password": "Updated-test-password-592!",
            "password_confirm": "Updated-test-password-592!",
        }

    def test_request_is_generic_and_queued(self):
        with patch("apps.accounts.recovery.send_password_recovery.apply_async") as dispatch:
            existing = self.post(
                "recover-password", {"username": self.user.username, "email": self.user.email}
            )
            missing = self.post(
                "recover-password", {"username": "missing", "email": "missing@example.com"}
            )
        self.assertEqual(existing.status_code, 202)
        self.assertEqual(existing.json(), missing.json())
        self.assertEqual(dispatch.call_count, 2)

    def test_token_one_use_and_old_session_invalidated(self):
        session = APIClient()
        session.login(username=self.user.username, password="Previous-test-password!")
        payload = self.reset_body()
        self.assertEqual(self.post("reset-password", payload).status_code, 200)
        self.assertEqual(self.post("reset-password", payload).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(session.get("/api/auth/me/").status_code, 403)

    def test_expired_token(self):
        now = datetime(2026, 9, 23, 12, 0)
        with patch.object(default_token_generator, "_now", return_value=now):
            payload = self.reset_body()
        with patch.object(default_token_generator, "_now", return_value=now + timedelta(hours=2)):
            self.assertEqual(self.post("reset-password", payload).status_code, 400)

    def test_wrong_email_sends_nothing_and_csrf_required(self):
        send_password_recovery(self.user.username, "other@example.com")
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.client.post("/api/auth/recover-password/", {}).status_code, 403)

    def test_weak_password_rejected(self):
        payload = self.reset_body()
        payload["password"] = payload["password_confirm"] = "123456789012"
        self.assertEqual(self.post("reset-password", payload).status_code, 400)

    def test_inactive_user_and_malformed_token_rejected(self):
        payload = self.reset_body()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.post("reset-password", payload).status_code, 400)
        payload["uid"] = "invalid"
        self.assertEqual(self.post("reset-password", payload).status_code, 400)
