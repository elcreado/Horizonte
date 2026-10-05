from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import BankAccount, BankConnection, BankSyncJob, Transaction
from apps.banking.sync import sync_bank
from tests.test_imports import ImportTests


class BankConnectionTests(TestCase):
    setUp = ImportTests.setUp

    def connect(self):
        with patch("apps.banking.connections.sync_bank.apply_async"):
            response = self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/",
                {"provider": "mock", "consent": True},
                format="json",
            )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_connect_sync_idempotent_and_revoke(self):
        created = self.connect()
        connection_id = created["connection"]["id"]
        account = BankAccount.objects.get(connection_id=connection_id)
        account_data = self.client.get(f"/api/companies/{self.company.pk}/accounts/").data
        self.assertIn(connection_id, [row["connection_id"] for row in account_data["accounts"]])
        self.assertEqual(account.balance_date, self.account.balance_date)
        sync_bank(created["job"]["id"])
        account.refresh_from_db()
        self.assertEqual(Transaction.objects.filter(account=account).count(), 120)
        self.assertEqual(str(account.balance), "5000000.00")
        self.assertEqual(
            (account.history_complete_through - account.history_complete_from).days, 119
        )
        self.assertIsNone(account.history_confirmed_by)
        sync_bank(created["job"]["id"])
        self.assertEqual(Transaction.objects.filter(account=account).count(), 120)
        with patch("apps.banking.connections.sync_bank.apply_async"):
            second = self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/{connection_id}/sync/",
                {},
                format="json",
            )
        self.assertEqual(second.status_code, 202)
        sync_bank(second.data["id"])
        job = BankSyncJob.objects.get(pk=second.data["id"])
        self.assertEqual((job.created_count, job.duplicate_count), (0, 120))
        self.assertEqual(
            self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/",
                {"provider": "mock", "consent": True},
                format="json",
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/companies/{self.company.pk}/accounts/{account.pk}/balance/",
                {"balance": "1.00", "balance_date": str(account.balance_date)},
                format="json",
            ).status_code,
            409,
        )
        revoked = self.client.post(
            f"/api/companies/{self.company.pk}/bank-connections/{connection_id}/revoke/",
            {},
            format="json",
        )
        self.assertEqual(revoked.status_code, 200)
        self.assertEqual(revoked.data["status"], "revoked")
        self.assertEqual(
            self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/{connection_id}/sync/",
                {},
                format="json",
            ).status_code,
            409,
        )
        with patch("apps.banking.connections.sync_bank.apply_async"):
            reconnected = self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/",
                {"provider": "mock", "consent": True},
                format="json",
            )
        self.assertEqual(reconnected.status_code, 201, reconnected.data)
        self.assertEqual(reconnected.data["connection"]["id"], connection_id)
        self.assertEqual(reconnected.data["connection"]["account_id"], account.pk)
        self.assertNotEqual(
            reconnected.data["connection"]["consent"]["id"],
            created["connection"]["consent"]["id"],
        )
        sync_bank(reconnected.data["job"]["id"])
        self.assertEqual(Transaction.objects.filter(account=account).count(), 120)
        self.assertEqual(
            BankSyncJob.objects.get(pk=reconnected.data["job"]["id"]).duplicate_count, 120
        )
        self.assertEqual(AuditLog.objects.filter(action="bank.synced").count(), 3)
        self.assertEqual(AuditLog.objects.filter(action="bank.reconnected").count(), 1)

    def test_consent_roles_and_tenant(self):
        url = f"/api/companies/{self.company.pk}/bank-connections/"
        self.assertEqual(
            self.client.post(url, {"provider": "mock"}, format="json").status_code, 400
        )
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.post(url, {"provider": "mock", "consent": True}, format="json").status_code,
            403,
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        other = Company.objects.create(name="Other", nit="bank-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/bank-connections/").status_code, 404
        )
        self.assertFalse(BankConnection.objects.exists())

    def test_revocation_cancels_queued_job_before_reauthorization(self):
        created = self.connect()
        old_job = created["job"]["id"]
        connection_id = created["connection"]["id"]
        response = self.client.post(
            f"/api/companies/{self.company.pk}/bank-connections/{connection_id}/revoke/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BankSyncJob.objects.get(pk=old_job).status, "failed")
        with patch("apps.banking.connections.sync_bank.apply_async"):
            again = self.client.post(
                f"/api/companies/{self.company.pk}/bank-connections/",
                {"provider": "mock", "consent": True},
                format="json",
            )
        self.assertEqual(again.status_code, 201)
        sync_bank(old_job)
        self.assertEqual(Transaction.objects.count(), 0)
        sync_bank(again.data["job"]["id"])
        self.assertEqual(Transaction.objects.count(), 120)
