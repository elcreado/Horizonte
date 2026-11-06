from datetime import date
from decimal import Decimal
from unittest import skipUnless
from uuid import uuid4

from django.db import connection
from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import BankAccount, BankConnection, BankConsent, ImportJob, Transaction
from apps.banking.tasks import import_csv
from apps.forecast.balance_history import build_balance_history
from apps.forecast.models import Obligation, Settlement
from tests import test_imports


class BalanceHistoryTests(TestCase):
    setUp = test_imports.ImportTests.setUp

    def confirm(self, account=None, start=date(2026, 9, 21), through=date(2026, 9, 23)):
        account = account or self.account
        account.history_complete_from = start
        account.history_complete_through = through
        account.save(update_fields=["history_complete_from", "history_complete_through"])

    def movement(self, identifier, day, amount, account=None):
        return Transaction.objects.create(
            account=account or self.account,
            external_id=identifier,
            date=day,
            amount=amount,
            description=identifier,
        )

    def series(self):
        response = self.client.get(f"/api/companies/{self.company.pk}/history/")
        self.assertEqual(response.status_code, 200, response.data)
        return response.json()["balance_history"]

    def test_exact_closing_balances_and_no_double_counting_at_cut(self):
        self.confirm()
        self.movement("sale", "2026-09-22", "100.10")
        self.movement("cost", "2026-09-23", "-20.05")
        self.movement("old", "2025-09-30", "90000")
        self.movement("after-cut", "2026-09-24", "90000")
        Obligation.objects.create(
            company=self.company,
            reference="unpaid",
            description="Unpaid future commitment",
            direction="out",
            outstanding_amount="9999",
            due_date=date(2026, 9, 24),
        )
        result = self.series()
        points = {row["date"]: row for row in result["points"]}
        self.assertEqual(result["declared_balance"], "500.00")
        self.assertEqual(result["complete_from"], "2026-09-21")
        self.assertEqual(points["2026-09-21"]["balance"], "419.95")
        self.assertEqual(points["2026-09-22"]["balance"], "520.05")
        self.assertEqual(
            points["2026-09-23"], {"date": "2026-09-23", "balance": "500.00", "status": "declared"}
        )
        self.assertEqual(points["2026-09-20"]["status"], "unknown")
        self.assertIsNone(points["2026-09-20"]["balance"])
        self.assertNotIn("2026-09-24", points)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500.00"))
        self.assertFalse(AuditLog.objects.exists())

    def test_missing_or_stale_coverage_never_invents_zeros(self):
        self.movement("income", "2026-09-22", "100.10")
        for through in (None, date(2026, 9, 22)):
            if through:
                self.confirm(through=through)
            result = self.series()
            self.assertIsNone(result["complete_from"])
            self.assertFalse(result["accounts"][0]["coverage_valid"])
            self.assertTrue(all(p["balance"] is None for p in result["points"][:-1]))
            self.assertEqual(result["points"][-1]["balance"], "500.00")

    def test_all_accounts_must_cover_the_same_interval(self):
        second = BankAccount.objects.create(
            company=self.company,
            name="Other cash",
            balance="50.01",
            balance_date=self.account.balance_date,
        )
        self.confirm(start=date(2026, 9, 19))
        self.movement("first", "2026-09-23", "10.01")
        self.movement("second", "2026-09-23", "-2.02", second)
        self.assertIsNone(self.series()["complete_from"])
        self.confirm(second, start=date(2026, 9, 22))
        result = self.series()
        self.assertEqual(result["complete_from"], "2026-09-22")
        self.assertEqual(result["points"][-2]["balance"], "542.02")
        self.assertEqual(result["points"][-1]["balance"], "550.01")
        self.assertIsNone(result["points"][-3]["balance"])

    def test_days_without_activity_zero_and_negative_balances_are_distinct(self):
        self.account.balance = Decimal("-0.01")
        self.account.save(update_fields=["balance"])
        self.confirm(start=date(2026, 9, 19))
        self.movement("same-day-a", "2026-09-22", "-0.02")
        self.movement("same-day-b", "2026-09-22", "0.01")
        points = self.series()["points"]
        self.assertEqual(
            [p["balance"] for p in points[-5:]], ["0.00", "0.00", "0.00", "-0.01", "-0.01"]
        )
        self.assertIsNone(points[-6]["balance"])

    def test_period_starts_at_twelve_month_window_even_with_older_coverage(self):
        self.confirm(start=date(2024, 1, 1))
        result = self.series()
        self.assertEqual(result["complete_from"], "2025-10-01")
        self.assertEqual(result["points"][0]["date"], "2025-10-01")
        self.assertLessEqual(len(result["points"]), 366)
        self.assertEqual(result["points"][0]["balance"], "500.00")

    def test_read_roles_isolation_and_incompatible_accounts(self):
        self.member.role = "viewer"
        self.member.save(update_fields=["role"])
        self.assertEqual(self.series()["declared_balance"], "500.00")
        other = Company.objects.create(name="Foreign", nit="foreign-balance-history")
        foreign_account = BankAccount.objects.create(
            company=other,
            name="Foreign cash",
            balance="99999",
            balance_date=self.account.balance_date,
        )
        self.movement("foreign", "2026-09-22", "99999", foreign_account)
        self.assertEqual(self.series()["declared_balance"], "500.00")
        self.assertEqual(self.client.get(f"/api/companies/{other.pk}/history/").status_code, 404)
        second = BankAccount.objects.create(
            company=self.company, name="Incompatible", balance="10", balance_date=date(2026, 9, 22)
        )
        url = f"/api/companies/{self.company.pk}/history/"
        self.assertEqual(self.client.get(url).status_code, 409)
        second.balance_date = self.account.balance_date
        second.currency = "USD"
        second.save(update_fields=["balance_date", "currency"])
        self.assertEqual(self.client.get(url).status_code, 409)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(url).status_code, (401, 403))

    def test_new_manual_movement_revokes_series_until_reconfirmed(self):
        self.confirm()
        self.assertIsNotNone(self.series()["complete_from"])
        response = self.client.post(
            f"/api/companies/{self.company.pk}/movements/",
            {
                "request_id": str(uuid4()),
                "account_id": self.account.pk,
                "date": "2026-09-22",
                "direction": "in",
                "amount": "5.01",
                "description": "Late record",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(self.series()["complete_from"])
        response = self.client.post(
            f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/",
            {"start": "2026-09-21", "confirmed": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.series()["points"][-3]["balance"], "494.99")

    def test_import_revokes_series_and_balance_update_uses_new_anchor(self):
        self.confirm()
        job = ImportJob.objects.create(
            account=self.account,
            user=self.user,
            content="external_id,date,amount,description\nlate,2026-09-22,2.01,Late record\n",
        )
        import_csv(job.pk)
        job.refresh_from_db()
        self.assertEqual(job.status, "completed", job.error)
        self.assertIsNone(self.series()["complete_from"])
        response = self.client.patch(
            f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/balance/",
            {"balance": "600.01", "balance_date": "2026-09-23"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.series()["points"][-1]["balance"], "600.01")

    def test_source_coverage_is_distinguished_from_manual_confirmation(self):
        consent = BankConsent.objects.create(company=self.company, user=self.user, scopes=["read"])
        connection = BankConnection.objects.create(
            company=self.company, consent=consent, provider="mock"
        )
        self.account.connection = connection
        self.account.save(update_fields=["connection"])
        self.confirm()
        source = self.series()["accounts"][0]
        self.assertTrue(source["coverage_valid"])
        self.assertEqual(source["coverage_source"], "source")

    @skipUnless(
        connection.vendor == "postgresql", "SQLite no conserva DECIMAL extremo sin pérdida."
    )
    def test_large_amounts_preserve_cents_in_api_and_reconstruction(self):
        self.account.balance = Decimal("9999999999999999.99")
        self.account.save(update_fields=["balance"])
        self.confirm()
        self.movement("cents", "2026-09-23", "0.01")
        result = self.series()
        self.assertEqual(result["declared_balance"], "9999999999999999.99")
        self.assertEqual(result["points"][-2]["balance"], "9999999999999999.98")

    def test_decimal_reconstruction_preserves_extreme_cents_without_float_conversion(self):
        self.account.balance = Decimal("9999999999999999.99")
        self.account.history_complete_from = date(2026, 9, 21)
        self.account.history_complete_through = self.account.balance_date
        result = build_balance_history(
            [self.account],
            date(2026, 9, 21),
            self.account.balance_date,
            {self.account.balance_date: Decimal("0.01")},
        )
        self.assertEqual(result["points"][-2]["balance"], "9999999999999999.98")
        self.assertEqual(result["points"][-1]["balance"], "9999999999999999.99")

    def test_settled_payment_is_not_subtracted_twice(self):
        self.confirm()
        self.movement("income", "2026-09-22", "100.10")
        payment = self.movement("payment", "2026-09-23", "-20.05")
        obligation = Obligation.objects.create(
            company=self.company,
            reference="paid",
            description="Already paid",
            direction="out",
            outstanding_amount="0",
            due_date=self.account.balance_date,
        )
        Settlement.objects.create(
            obligation=obligation,
            transaction=payment,
            user=self.user,
            amount="20.05",
            request_id=uuid4(),
        )
        points = self.series()["points"]
        self.assertEqual(points[-3]["balance"], "419.95")
        self.assertEqual(points[-2]["balance"], "520.05")
        self.assertEqual(points[-1]["balance"], "500.00")
