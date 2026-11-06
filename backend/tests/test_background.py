from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import BackgroundTask, Company, CompanyMember
from apps.accounts.tasks import send_password_recovery
from apps.banking.models import BankAccount, ImportJob, Transaction
from apps.banking.tasks import import_csv
from apps.invoices.models import InvoiceImport
from config.background import QueueUnavailable, create_job, enqueue, run_one


@override_settings(BACKGROUND_MODE="database")
class BackgroundTests(TransactionTestCase):
    # El comando limpia conexiones: debe ejecutarse fuera de la transacción
    # envolvente de TestCase, como ocurre en el proceso worker real.
    def test_expired_worker_cannot_overwrite_recovered_attempt(self):
        for recovered_fails in (False, True):
            with self.subTest(recovered_fails=recovered_fails):
                task = enqueue(
                    send_password_recovery, kwargs={"username": "missing", "email": "a@b.co"}
                )
                calls = 0
                leases = []

                def competing_attempt(**kwargs):
                    nonlocal calls
                    calls += 1
                    active = BackgroundTask.objects.get(pk=task.pk)
                    leases.append(active.lease)
                    if calls == 1:
                        BackgroundTask.objects.filter(pk=task.pk).update(
                            available_at=timezone.now() - timedelta(seconds=1)
                        )
                        self.assertTrue(run_one())
                        if not recovered_fails:
                            raise OSError("old attempt failed after recovery")
                    elif recovered_fails:
                        raise OSError("new attempt needs retry")

                with patch(
                    "apps.accounts.tasks.send_password_recovery.run", side_effect=competing_attempt
                ):
                    self.assertTrue(run_one())
                task.refresh_from_db()
                self.assertEqual(calls, 2)
                self.assertNotEqual(leases[0], leases[1])
                self.assertEqual(task.lease, leases[1])
                self.assertEqual(task.attempts, 2)
                self.assertEqual(task.status, "queued" if recovered_fails else "completed")
                if recovered_fails:
                    self.assertEqual(task.kwargs["username"], "missing")
                    self.assertIsNone(task.finished_at)
                    self.assertFalse(run_one())
                    # Retirar el reintento de esta variante antes de probar la siguiente.
                    task.delete()
                else:
                    self.assertEqual(task.kwargs, {})
                    self.assertIsNotNone(task.finished_at)

    def test_worker_command_processes_one_real_import_without_broker(self):
        fields = self.fixture_fields()
        CompanyMember.objects.create(
            company=fields["account"].company, user=fields["user"], role="owner"
        )
        fields["content"] = "external_id,date,amount,description\ncli,2026-09-01,12.34,Venta\n"
        first = create_job(import_csv, ImportJob, **fields)
        second = create_job(import_csv, ImportJob, **{**fields, "checksum": "other"})
        call_command("run_background", once=True)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, "completed")
        self.assertEqual(second.status, "queued")
        self.assertEqual(Transaction.objects.get().external_id, "cli")
        call_command("run_background", once=True)
        second.refresh_from_db()
        self.assertEqual(second.status, "completed")
        self.assertEqual(Transaction.objects.count(), 1)
        call_command("run_background", once=True)

    @override_settings(BACKGROUND_MODE="celery")
    def test_worker_command_rejects_wrong_queue_configuration(self):
        with self.assertRaisesMessage(CommandError, "BACKGROUND_MODE=database"):
            call_command("run_background", once=True)

    def fixture_fields(self):
        user = get_user_model().objects.create_user(username="atomic")
        company = Company.objects.create(name="Atomic", nit="atomic")
        account = BankAccount.objects.create(
            company=company, name="Manual", balance=0, balance_date=date(2026, 9, 23)
        )
        return {"account": account, "user": user, "content": "private", "checksum": "abc"}

    def test_queue_failure_rolls_back_domain_job(self):
        fields = self.fixture_fields()
        with patch("apps.accounts.models.BackgroundTask.objects.create", side_effect=OSError):
            with self.assertRaises(QueueUnavailable):
                create_job(import_csv, ImportJob, **fields)
        self.assertEqual(ImportJob.objects.count(), 0)
        self.assertEqual(BackgroundTask.objects.count(), 0)

    def test_http_queue_failure_is_sanitized_and_leaves_no_import_or_message(self):
        fields = self.fixture_fields()
        CompanyMember.objects.create(
            company=fields["account"].company, user=fields["user"], role="owner"
        )
        client = APIClient()
        client.force_authenticate(fields["user"])
        company = fields["account"].company_id
        uploads = [
            (
                f"/api/companies/{company}/imports/",
                {
                    "account_id": fields["account"].pk,
                    "file": SimpleUploadedFile(
                        "test.csv", b"external_id,date,amount,description\nx,2026-09-01,1,Test\n"
                    ),
                },
            ),
            (
                f"/api/companies/{company}/invoices/imports/",
                {"file": SimpleUploadedFile("test.xml", b"<Invoice/>")},
            ),
        ]
        with patch(
            "apps.accounts.models.BackgroundTask.objects.create",
            side_effect=DatabaseError("private-db-secret"),
        ):
            for url, payload in uploads:
                response = client.post(url, payload, format="multipart")
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private-db-secret", str(response.data))
        self.assertEqual(ImportJob.objects.count(), 0)
        self.assertEqual(InvoiceImport.objects.count(), 0)
        self.assertEqual(BackgroundTask.objects.count(), 0)

    def test_exhausted_interruption_finishes_domain_job_and_erases_payload(self):
        domain = create_job(import_csv, ImportJob, **self.fixture_fields())
        queued = BackgroundTask.objects.get()
        queued.status = "running"
        queued.attempts = 3
        queued.available_at = timezone.now() - timedelta(seconds=1)
        queued.save()
        self.assertTrue(run_one())
        domain.refresh_from_db()
        queued.refresh_from_db()
        self.assertEqual(domain.status, "failed")
        self.assertEqual(domain.content, "")
        self.assertIsNotNone(domain.finished_at)
        self.assertEqual(queued.status, "failed")
        self.assertEqual(queued.args, [])
        self.assertFalse(run_one())

    def test_http_upload_survives_without_broker_and_worker_checks_revoked_role(self):
        user = get_user_model().objects.create_user(username="queued")
        company = Company.objects.create(name="Queued", nit="queued")
        member = CompanyMember.objects.create(company=company, user=user, role="owner")
        account = BankAccount.objects.create(
            company=company, name="Manual", balance=500, balance_date=date(2026, 9, 23)
        )
        client = APIClient()
        client.force_authenticate(user)
        for identifier in ["one", "two"]:
            upload = SimpleUploadedFile(
                "sample.csv",
                (
                    "external_id,date,amount,description\n"
                    + identifier
                    + ",2026-09-01,10.10,Venta\n"
                ).encode(),
            )
            response = client.post(
                f"/api/companies/{company.pk}/imports/",
                {"account_id": account.pk, "file": upload},
                format="multipart",
            )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(Transaction.objects.count(), 0 if identifier == "one" else 1)
            if identifier == "two":
                member.role = "viewer"
                member.save()
            self.assertTrue(run_one())
            job = ImportJob.objects.get(pk=response.data["id"])
            self.assertEqual(job.status, "completed" if identifier == "one" else "failed")
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertFalse(run_one())
        self.assertTrue(all(row.args == [] for row in BackgroundTask.objects.all()))

    def test_interrupted_lease_is_recovered_and_failures_are_bounded(self):
        task = enqueue(send_password_recovery, kwargs={"username": "missing", "email": "a@b.co"})
        task.status = "running"
        task.available_at = timezone.now() - timedelta(seconds=1)
        task.save()
        with patch("apps.accounts.tasks.send_password_recovery.run", side_effect=OSError):
            for attempt in range(1, 4):
                self.assertTrue(run_one())
                task.refresh_from_db()
                self.assertEqual(task.attempts, attempt)
                task.available_at = timezone.now() - timedelta(seconds=1)
                task.save()
        self.assertEqual(task.status, "failed")
        self.assertEqual(task.kwargs, {})
        self.assertFalse(run_one())
