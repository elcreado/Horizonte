from datetime import timedelta
from unittest import skipUnless

from django.db import connection
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import AuditLog
from apps.banking.models import Transaction
from tests.test_imports import ImportTests


class AccountBalanceTests(TestCase):
    setUp = ImportTests.setUp

    def test_account_list_serializes_money_as_decimal_text(self):
        self.account.balance = "123.45"
        self.account.save(update_fields=["balance"])
        response = self.client.get(f"/api/companies/{self.company.pk}/accounts/")
        self.assertEqual(response.json()["accounts"][0]["balance"], "123.45")

    @skipUnless(connection.vendor == "postgresql", "Importe máximo requiere NUMERIC de PostgreSQL.")
    def test_account_list_preserves_cents_above_float_precision(self):
        self.account.balance = "9999999999999999.99"
        self.account.save(update_fields=["balance"])
        response = self.client.get(f"/api/companies/{self.company.pk}/accounts/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["accounts"][0]["balance"], "9999999999999999.99")

    def test_update_audits_and_changes_dashboard(self):
        url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/balance/"
        payload = {"balance": "123.45", "balance_date": "2026-09-23"}
        self.assertEqual(self.client.patch(url, payload, format="json").status_code, 200)
        self.assertEqual(self.client.patch(url, payload, format="json").status_code, 200)
        self.assertEqual(AuditLog.objects.filter(action="account.balance_updated").count(), 1)
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.pk}/dashboard/").data["balance"],
            "123.45",
        )

    def test_future_date_history_and_viewer_guards(self):
        url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/balance/"
        payload = {
            "balance": "0",
            "balance_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
        }
        self.assertEqual(self.client.patch(url, payload, format="json").status_code, 400)
        Transaction.objects.create(
            account=self.account,
            external_id="latest",
            date="2026-09-23",
            amount="10",
            description="Test",
        )
        payload["balance_date"] = "2026-09-22"
        self.assertEqual(self.client.patch(url, payload, format="json").status_code, 409)
        self.member.role = "viewer"
        self.member.save()
        payload["balance_date"] = "2026-09-23"
        self.assertEqual(self.client.patch(url, payload, format="json").status_code, 403)
        self.account.refresh_from_db()
        self.assertEqual(str(self.account.balance), "500.00")
