from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import Company
from apps.banking.models import BankAccount, Transaction
from tests.test_imports import ImportTests


class HistoryTests(TestCase):
    setUp = ImportTests.setUp

    def test_window_signed_totals_and_tenant(self):
        for identifier, day, amount, category in [
            ("income", "2026-09-23", "120.25", "Ventas"),
            ("expense", "2026-09-01", "-20.10", "Software"),
            ("start", "2025-10-01", "10.00", "Ventas"),
            ("old", "2025-09-30", "9999", "Ventas"),
            ("future", "2026-09-24", "9999", "Ventas"),
        ]:
            Transaction.objects.create(
                account=self.account,
                external_id=identifier,
                date=day,
                amount=amount,
                description=identifier,
                category=category,
            )
        other = Company.objects.create(name="Other", nit="history-other")
        account = BankAccount.objects.create(
            company=other, name="Other", balance="0", balance_date=date(2026, 9, 23)
        )
        Transaction.objects.create(
            account=account,
            external_id="foreign",
            date="2026-09-01",
            amount="9999",
            description="Other",
        )
        response = self.client.get(f"/api/companies/{self.company.id}/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(str(response.data["start"]), "2025-10-01")
        self.assertEqual(len(response.data["months"]), 12)
        last = response.data["months"][-1]
        self.assertEqual(Decimal(last["net"]), Decimal("100.15"))
        self.assertEqual(Decimal(last["expense"]), Decimal("20.10"))
        categories = {row["category"]: row for row in response.data["categories"]}
        self.assertEqual(Decimal(categories["Ventas"]["income"]), Decimal("130.25"))
        self.assertEqual(self.client.get(f"/api/companies/{other.id}/history/").status_code, 404)

    def test_empty_and_incompatible_cuts(self):
        url = f"/api/companies/{self.company.id}/history/"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 0)
        self.assertIsNone(response.data["first_transaction"])
        self.assertTrue(all(row["count"] == 0 for row in response.data["months"]))
        BankAccount.objects.create(
            company=self.company, name="Different", balance="0", balance_date=date(2026, 9, 22)
        )
        self.assertEqual(self.client.get(url).status_code, 409)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(url).status_code, [401, 403])
