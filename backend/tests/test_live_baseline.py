from datetime import timedelta

from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import Transaction
from apps.banking.tasks import import_csv
from apps.forecast.models import Obligation, RecurrenceOccurrence, RecurrenceReview
from config.api_inventory import build_inventory
from tests.test_imports import ImportTests


class LiveBaselineTests(TestCase):
    setUp = ImportTests.setUp
    job = ImportTests.job

    def test_requires_coverage_then_adds_known_and_estimated_once(self):
        cutoff = self.account.balance_date
        url = f"/api/companies/{self.company.pk}/experimental-forecast/?horizon=30&method=naive"
        self.assertEqual(self.client.get(url).status_code, 409)
        start = cutoff - timedelta(days=89)
        for offset in range(90):
            Transaction.objects.create(
                account=self.account,
                external_id=f"day-{offset}",
                date=start + timedelta(days=offset),
                amount="1.00",
                description="Variable",
            )
        coverage_url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/"
        self.assertEqual(
            self.client.post(
                coverage_url, {"start": start.isoformat(), "confirmed": True}, format="json"
            ).status_code,
            200,
        )
        obligation = Obligation.objects.create(
            company=self.company,
            reference="due",
            description="Pago",
            direction="out",
            due_date=cutoff + timedelta(days=1),
            outstanding_amount="100.00",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        operation = build_inventory()["paths"][
            "/api/companies/{company_id}/experimental-forecast/"
        ]["get"]
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(set(response.json()), set(schema["properties"]))
        self.assertEqual(set(schema["required"]), set(response.json()))
        self.assertIn("recurring_flow", schema["properties"]["points"]["items"]["required"])
        self.assertEqual(
            operation["responses"]["409"]["content"]["application/json"]["schema"]["required"],
            ["detail"],
        )
        self.assertEqual(response.data["status"], "experimental")
        self.assertEqual(response.data["points"][0]["known_flow"], "-100.00")
        self.assertEqual(response.data["points"][0]["estimated_flow"], "1.00")
        self.assertEqual(response.data["points"][0]["balance"], "401.00")
        self.assertEqual(response.data["points"][1]["balance"], "402.00")
        self.assertEqual(response.data["first_deficit"], None)
        smoothed = self.client.get(url.replace("method=naive", "method=ses"))
        self.assertEqual(smoothed.status_code, 200, smoothed.data)
        self.assertEqual(smoothed.data["points"][0]["estimated_flow"], "1.00")
        self.assertTrue(AuditLog.objects.filter(action="account.coverage_updated").exists())
        self.assertEqual(Obligation.objects.filter(pk=obligation.pk).count(), 1)
        other = Company.objects.create(name="Other", nit="baseline-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/experimental-forecast/").status_code, 404
        )

    def test_import_and_cut_change_revoke_coverage(self):
        cutoff = self.account.balance_date
        start = cutoff - timedelta(days=89)
        coverage_url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/"
        self.client.post(
            coverage_url, {"start": start.isoformat(), "confirmed": True}, format="json"
        )
        job = self.job("external_id,date,amount,description\nnew,2026-09-01,10.00,Venta\n")
        import_csv(job.pk)
        self.account.refresh_from_db()
        self.assertIsNone(self.account.history_complete_from)
        self.client.post(
            coverage_url, {"start": start.isoformat(), "confirmed": True}, format="json"
        )
        balance_url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/balance/"
        self.assertEqual(
            self.client.patch(
                balance_url, {"balance": "500.00", "balance_date": "2026-09-24"}, format="json"
            ).status_code,
            200,
        )
        self.account.refresh_from_db()
        self.assertIsNone(self.account.history_complete_from)

    def test_linked_recurrence_is_excluded_and_viewer_cannot_attest(self):
        cutoff = self.account.balance_date
        start = cutoff - timedelta(days=89)
        for offset in range(90):
            Transaction.objects.create(
                account=self.account,
                external_id=f"day-{offset}",
                date=start + timedelta(days=offset),
                amount="1.00",
                description="Variable",
            )
        first = Transaction.objects.filter(account=self.account).order_by("pk").first()
        review = RecurrenceReview.objects.create(
            company=self.company,
            fingerprint="test",
            status="confirmed",
            evidence={"transaction_ids": [first.pk]},
            user=self.user,
        )
        obligation = Obligation.objects.create(
            company=self.company,
            reference="known",
            description="Conocido",
            direction="out",
            due_date=cutoff + timedelta(days=1),
            outstanding_amount="80.00",
        )
        RecurrenceOccurrence.objects.create(
            company=self.company, key="test", review=review, obligation=obligation
        )
        coverage_url = f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/"
        self.client.post(
            coverage_url, {"start": start.isoformat(), "confirmed": True}, format="json"
        )
        result = self.client.get(
            f"/api/companies/{self.company.pk}/experimental-forecast/?method=seasonal_naive"
        ).data
        self.assertEqual(result["excluded_recurring_movements"], 1)
        self.assertEqual(result["points"][0]["known_flow"], "-80.00")
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.post(
                coverage_url, {"start": start.isoformat(), "confirmed": False}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.pk}/experimental-forecast/").status_code,
            200,
        )
