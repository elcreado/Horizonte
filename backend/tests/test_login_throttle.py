from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import RateLimitBucket


class LoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    @patch("apps.accounts.views.authenticate", return_value=None)
    def test_existing_session_cannot_bypass_login_limit(self, authenticate):
        user = get_user_model().objects.create_user(username="signed-in")
        client = APIClient()
        client.force_authenticate(user)
        for _ in range(10):
            self.assertEqual(
                client.post(
                    "/api/auth/login/", {"username": "target", "password": "wrong"}
                ).status_code,
                400,
            )
        cache.clear()
        client = APIClient()
        client.force_authenticate(user)
        limited = client.post("/api/auth/login/", {"username": "target", "password": "wrong"})
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(authenticate.call_count, 10)
        bucket = RateLimitBucket.objects.get()
        self.assertEqual(bucket.requests, 10)
        self.assertNotIn("signed-in", bucket.key)
        bucket.expires_at = timezone.now() - timedelta(seconds=1)
        bucket.save()
        self.assertEqual(
            client.post(
                "/api/auth/login/", {"username": "target", "password": "wrong"}
            ).status_code,
            400,
        )
        bucket.refresh_from_db()
        self.assertEqual(bucket.requests, 1)

    @patch("apps.accounts.views.authenticate", return_value=None)
    def test_anonymous_limit_still_applies(self, authenticate):
        client = APIClient()
        for _ in range(10):
            client.post("/api/auth/login/", {"username": "target", "password": "wrong"})
        self.assertEqual(
            client.post(
                "/api/auth/login/", {"username": "target", "password": "wrong"}
            ).status_code,
            429,
        )
        self.assertEqual(authenticate.call_count, 10)
