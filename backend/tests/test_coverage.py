from datetime import date

from django.test import TestCase

from apps.banking.models import BankAccount, Transaction
from apps.forecast.coverage import history_coverage
from tests.test_imports import ImportTests


class CoverageTests(TestCase):
    setUp = ImportTests.setUp

    def test_sparse_history_and_empty_account_are_not_hidden(self):
        empty = BankAccount.objects.create(
            company=self.company, name="Empty", balance="0", balance_date=self.account.balance_date
        )
        for identifier, day in [
            ("first", "2026-01-01"),
            ("last", "2026-09-01"),
            ("future", "2026-09-24"),
            ("old", "2020-01-01"),
        ]:
            Transaction.objects.create(
                account=self.account,
                external_id=identifier,
                date=day,
                amount="10",
                description=identifier,
            )
        result = history_coverage([self.account, empty], date(2026, 9, 23))
        observed, missing = result["accounts"]
        self.assertEqual(observed["count"], 2)
        self.assertEqual(observed["active_days"], 2)
        self.assertEqual(observed["state"], "extended")
        self.assertEqual(observed["days_since_last"], 22)
        self.assertEqual(missing["state"], "empty")
        self.assertIsNone(missing["days_since_last"])
        self.assertEqual(result["method"], "obligations_only")

    def test_limited_history_and_dashboard_contract(self):
        Transaction.objects.create(
            account=self.account,
            external_id="one",
            date=self.account.balance_date,
            amount="-10",
            description="One",
            category="Software",
        )
        response = self.client.get(f"/api/companies/{self.company.pk}/dashboard/")
        self.assertEqual(response.status_code, 200)
        row = response.data["coverage"]["accounts"][0]
        self.assertEqual(row["state"], "limited")
        self.assertEqual(row["span_days"], 1)
        self.assertEqual(row["other_category_count"], 0)
        self.assertEqual(response.data["balance"], "500.00")
