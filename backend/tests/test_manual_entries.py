from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog
from apps.banking.models import BankAccount, ManualEntry, Transaction
from tests.test_imports import ImportTests


class ManualEntryTests(TestCase):
    setUp = ImportTests.setUp

    def submit(self, **changes):
        payload = {
            "request_id": str(uuid4()),
            "account_id": self.account.pk,
            "date": self.account.balance_date.isoformat(),
            "direction": "in",
            "amount": "100.25",
            "description": "Venta",
        }
        payload.update(changes)
        return self.client.post(
            f"/api/companies/{self.company.pk}/movements/", payload, format="json"
        )

    def test_creation_classification_receipt_and_unchanged_balance(self):
        self.assertEqual(self.submit().status_code, 201)
        self.assertEqual(self.submit(direction="out", description="Adobe").status_code, 201)
        self.assertEqual(
            list(Transaction.objects.order_by("pk").values_list("amount", "category")),
            [(Decimal("100.25"), "Ventas"), (Decimal("-100.25"), "Software")],
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500"))
        self.assertEqual(ManualEntry.objects.count(), 2)
        self.assertEqual(
            AuditLog.objects.filter(action="transaction.manual_created", user=self.user).count(), 2
        )
        row = self.client.get(f"/api/companies/{self.company.pk}/movements/").json()["results"][0]
        self.assertEqual(row["entry_source"], "manual")
        self.assertEqual(row["account_name"], self.account.name)
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.pk}/movements/").status_code, 403
        )
        self.client.force_authenticate(self.user)
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.pk}/movements/").json()["count"], 2
        )

    def test_idempotency_survives_category_correction_and_coverage(self):
        key = str(uuid4())
        first = self.submit(request_id=key)
        identifier = first.json()["id"]
        self.client.patch(
            f"/api/companies/{self.company.pk}/movements/{identifier}/category/",
            {"category": "Servicios"},
            format="json",
        )
        self.assertEqual(self.submit(request_id=key).json(), {"id": identifier, "created": False})
        self.assertEqual(self.submit(request_id=key, amount="101").status_code, 409)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="transaction.manual_created").count(), 1)
        self.assertEqual(Transaction.objects.get().category, "Servicios")

    def test_invalid_values_dates_and_category_are_atomic(self):
        for amount in ["0", "-1", "NaN", "Infinity", "1.001", "10000000000000000"]:
            with self.subTest(amount=amount):
                self.assertEqual(self.submit(amount=amount).status_code, 400)
        for fields in [
            {"description": " "},
            {"description": "x" * 251},
            {"request_id": "bad"},
            {"direction": "bad"},
            {"category": "Nómina"},
            {"date": (timezone.localdate() + timedelta(days=1)).isoformat()},
        ]:
            self.assertEqual(self.submit(**fields).status_code, 400)
        self.assertFalse(Transaction.objects.exists())
        self.assertFalse(ManualEntry.objects.exists())
        self.assertFalse(AuditLog.objects.exists())

    def test_roles_tenant_and_csrf(self):
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.submit().status_code, 403)
        self.member.role = "accountant"
        self.member.save()
        self.assertEqual(self.submit(category="Servicios").status_code, 201)
        from apps.accounts.models import Company

        other = Company.objects.create(name="Other", nit="manual-other")
        account = BankAccount.objects.create(
            company=other, name="Other", balance=0, balance_date=self.account.balance_date
        )
        self.assertEqual(self.submit(account_id=account.pk).status_code, 404)
        secure = APIClient(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(
            secure.post(
                f"/api/companies/{self.company.pk}/movements/", {}, format="json"
            ).status_code,
            403,
        )

    def test_new_history_revokes_coverage_and_average_uses_manual_data(self):
        cutoff = self.account.balance_date
        start = cutoff - timedelta(days=6)
        coverage = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/"
        forecast = f"/api/companies/{self.company.pk}/experimental-forecast/?method=manual_average&horizon=30"
        self.assertEqual(self.client.get(forecast).status_code, 409)
        self.client.post(coverage, {"start": start.isoformat(), "confirmed": True}, format="json")
        self.assertEqual(self.submit(amount="70").status_code, 201)
        self.account.refresh_from_db()
        self.assertIsNone(self.account.history_complete_from)
        self.assertEqual(self.client.get(forecast).status_code, 409)
        self.client.post(coverage, {"start": start.isoformat(), "confirmed": True}, format="json")
        result = self.client.get(forecast)
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.json()["training_days"], 7)
        self.assertEqual(result.json()["points"][0]["estimated_flow"], "10.00")
        self.assertEqual(result.json()["points"][-1]["balance"], "800.00")
        self.assertEqual(self.submit(direction="out", amount="140").status_code, 201)
        self.client.post(coverage, {"start": start.isoformat(), "confirmed": True}, format="json")
        result = self.client.get(forecast).json()
        self.assertEqual(result["points"][-1]["balance"], "200.00")
        self.assertEqual(
            self.client.get(forecast.replace("manual_average", "hybrid_weekly")).status_code, 409
        )
        for horizon in [30, 60, 90]:
            response = self.client.post(
                f"/api/companies/{self.company.pk}/forecast-runs/",
                {"horizon": horizon, "method": "manual_average"},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(len(response.json()["result"]["points"]), horizon)

    def test_connected_account_and_existing_external_identifier_rejected(self):
        from apps.banking.models import BankConnection, BankConsent

        consent = BankConsent.objects.create(company=self.company, user=self.user)
        connection = BankConnection.objects.create(
            company=self.company, consent=consent, provider="mock"
        )
        self.account.connection = connection
        self.account.save()
        self.assertEqual(self.submit().status_code, 409)
        self.account.connection = None
        self.account.save()
        key = str(uuid4())
        Transaction.objects.create(
            account=self.account,
            external_id=f"manual:{key}",
            date=self.account.balance_date,
            amount=1,
            description="Imported",
        )
        self.assertEqual(self.submit(request_id=key).status_code, 409)
        self.assertFalse(ManualEntry.objects.exists())

    def test_average_includes_pending_obligations_once(self):
        from apps.forecast.models import Obligation

        cutoff = self.account.balance_date
        self.submit(amount="70")
        self.client.post(
            f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/",
            {"start": (cutoff - timedelta(days=6)).isoformat(), "confirmed": True},
            format="json",
        )
        Obligation.objects.create(
            company=self.company,
            reference="pay",
            description="Pago",
            direction="out",
            due_date=cutoff + timedelta(days=2),
            outstanding_amount="100",
        )
        for horizon in [30, 60, 90]:
            result = self.client.get(
                f"/api/companies/{self.company.pk}/experimental-forecast/?method=manual_average&horizon={horizon}"
            ).json()
            self.assertEqual(result["points"][0]["balance"], "510.00")
            self.assertEqual(result["points"][1]["balance"], "420.00")
            self.assertEqual(
                Decimal(result["points"][-1]["balance"]), Decimal(500 + horizon * 10 - 100)
            )

    def test_today_default_and_multiple_identical_operations_on_the_same_day(self):
        # A stale balance cut must not prevent daily manual bookkeeping.
        payload = {
            "request_id": str(uuid4()),
            "account_id": self.account.pk,
            "amount": "10",
            "direction": "in",
            "description": "Venta del día",
        }
        url = f"/api/companies/{self.company.pk}/movements/"
        first = self.client.post(url, payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        payload["request_id"] = str(uuid4())
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 201)
        self.assertEqual(Transaction.objects.filter(date=timezone.localdate()).count(), 2)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500"))
        self.assertEqual(self.account.balance_date.isoformat(), "2026-09-23")

    def test_average_uses_older_history_and_excludes_after_cut(self):
        cutoff = self.account.balance_date
        self.submit(date=(cutoff - timedelta(days=13)).isoformat(), amount="140")
        self.submit(amount="70", direction="out")
        self.submit(date=timezone.localdate().isoformat(), amount="999999")
        coverage = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/"
        forecast = f"/api/companies/{self.company.pk}/experimental-forecast/?method=manual_average&horizon=30"
        self.client.post(
            coverage,
            {"start": (cutoff - timedelta(days=6)).isoformat(), "confirmed": True},
            format="json",
        )
        self.assertEqual(self.client.get(forecast).status_code, 409)
        self.client.post(
            coverage,
            {"start": (cutoff - timedelta(days=13)).isoformat(), "confirmed": True},
            format="json",
        )
        result = self.client.get(forecast)
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["training_days"], 14)
        self.assertEqual(result.data["observed_movements"], 2)
        self.assertEqual(result.data["points"][0]["estimated_flow"], "5.00")
        self.assertEqual(result.data["points"][-1]["balance"], "650.00")
