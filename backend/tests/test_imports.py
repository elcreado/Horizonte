from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.banking.imports import parse_csv
from apps.banking.models import BankAccount, ImportJob, Transaction
from apps.banking.tasks import import_csv

HEADER = "external_id,date,amount,description\n"
CSV = HEADER + "csv-1,2026-09-01,100.10,Venta\n"


class ImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="importer")
        self.company = Company.objects.create(name="Import", nit="csv")
        self.member = CompanyMember.objects.create(
            company=self.company, user=self.user, role="owner"
        )
        self.account = BankAccount.objects.create(
            company=self.company, name="CSV", balance="500", balance_date=date(2026, 9, 23)
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/companies/{self.company.id}/imports/"

    def job(self, content=CSV):
        return ImportJob.objects.create(account=self.account, user=self.user, content=content)

    def test_repeat_import_and_redelivery(self):
        first = self.job()
        import_csv(first.id)
        import_csv(first.id)
        second = self.job()
        import_csv(second.id)
        second.refresh_from_db()
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(second.duplicate_count, 1)
        self.account.refresh_from_db()
        self.assertEqual(str(self.account.balance), "500.00")

    def test_conflict_rolls_back_entire_import(self):
        import_csv(self.job().id)
        job = self.job(HEADER + "new,2026-09-01,20.00,Other\ncsv-1,2026-09-01,200.00,Venta\n")
        import_csv(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(job.content, "")

    def test_invalid_csv_and_dates(self):
        for content in (
            HEADER,
            HEADER + "id,2026-02-30,1,Sale\n",
            HEADER + "id,2026-01-01,NaN,Sale\n",
            HEADER + "id,2026-01-01,1.123,Sale\n",
        ):
            with self.assertRaises(ValueError):
                parse_csv(content)
        job = self.job(HEADER + "future,2027-01-01,1,Sale\n")
        import_csv(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_authorization_checked_again_by_worker(self):
        job = self.job()
        self.member.role = "viewer"
        self.member.save()
        import_csv(job.id)
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertEqual(self.client.post(self.url, {}).status_code, 403)

    def test_upload_is_queued_and_tenant_scoped(self):
        with patch("apps.banking.views.import_csv.apply_async") as dispatch:
            response = self.client.post(
                self.url,
                {
                    "account_id": self.account.id,
                    "file": SimpleUploadedFile("demo.csv", CSV.encode()),
                },
                format="multipart",
            )
        self.assertEqual(response.status_code, 202)
        dispatch.assert_called_once()
        self.assertEqual(Transaction.objects.count(), 0)
        other = Company.objects.create(name="Other", nit="other")
        self.assertEqual(self.client.get(f"/api/companies/{other.id}/imports/").status_code, 404)
        foreign = BankAccount.objects.create(
            company=other, name="Other", balance="0", balance_date=date(2026, 9, 23)
        )
        self.assertEqual(
            self.client.post(
                self.url,
                {"account_id": foreign.id, "file": SimpleUploadedFile("demo.csv", CSV.encode())},
                format="multipart",
            ).status_code,
            404,
        )

    def test_broker_failure_visible(self):
        with patch("apps.banking.views.import_csv.apply_async", side_effect=ConnectionError):
            response = self.client.post(
                self.url,
                {
                    "account_id": self.account.id,
                    "file": SimpleUploadedFile("demo.csv", CSV.encode()),
                },
                format="multipart",
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(ImportJob.objects.get().status, "failed")
