from datetime import timedelta

from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import Transaction
from apps.forecast.models import ForecastRun, Obligation
from config.api_inventory import build_inventory
from tests.test_imports import ImportTests


class ForecastRunTests(TestCase):
    setUp = ImportTests.setUp

    def populate(self):
        cutoff = self.account.balance_date
        start = cutoff - timedelta(days=89)
        Transaction.objects.bulk_create(
            [
                Transaction(
                    account=self.account,
                    external_id=f"run-day-{offset}",
                    date=start + timedelta(days=offset),
                    amount="1.00",
                    description="Variable",
                )
                for offset in range(90)
            ]
        )
        response = self.client.post(
            f"/api/companies/{self.company.pk}/accounts/{self.account.pk}/coverage/",
            {"start": start.isoformat(), "confirmed": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_saved_run_is_idempotent_and_old_result_is_immutable(self):
        self.populate()
        url = f"/api/companies/{self.company.pk}/forecast-runs/"
        params = {"horizon": 30, "method": "naive"}
        first = self.client.post(url, params, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        contract = build_inventory()["paths"]["/api/companies/{company_id}/forecast-runs/"]
        schema = contract["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertEqual(set(first.json()), set(schema["properties"]))
        self.assertIn("snapshots-pending", contract["post"]["x-contract-status"])
        repeat = self.client.post(url, params, format="json")
        self.assertEqual(repeat.status_code, 200, repeat.data)
        self.assertEqual(repeat.data["id"], first.data["id"])
        original = first.data["result"]["points"][0]["balance"]
        Obligation.objects.create(
            company=self.company,
            reference="future",
            description="Pago",
            direction="out",
            due_date=self.account.balance_date + timedelta(days=1),
            outstanding_amount="100.00",
        )
        changed = self.client.post(url, params, format="json")
        self.assertEqual(changed.status_code, 201, changed.data)
        self.assertNotEqual(changed.data["id"], first.data["id"])
        self.assertNotEqual(changed.data["result"]["points"][0]["balance"], original)
        history = self.client.get(url)
        self.assertEqual(history.status_code, 200)
        page_schema = contract["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(set(history.json()), set(page_schema["properties"]))
        self.assertEqual(history.data["count"], 2)
        self.assertEqual(
            ForecastRun.objects.get(pk=first.data["id"]).result["points"][0]["balance"], original
        )
        self.assertEqual(AuditLog.objects.filter(action="forecast.run_saved").count(), 2)
        smoothed = self.client.post(url, {"horizon": 30, "method": "ses"}, format="json")
        self.assertEqual(smoothed.status_code, 201, smoothed.data)
        self.assertEqual(smoothed.data["method"], "ses")

    def test_coverage_role_and_tenant(self):
        url = f"/api/companies/{self.company.pk}/forecast-runs/"
        self.assertEqual(self.client.post(url, {"horizon": 30}, format="json").status_code, 409)
        self.populate()
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.client.post(url, {"horizon": 30}, format="json").status_code, 403)
        self.assertEqual(self.client.get(url).status_code, 200)
        other = Company.objects.create(name="Other", nit="forecast-run-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/forecast-runs/").status_code, 404
        )
        self.assertEqual(
            self.client.post(
                f"/api/companies/{other.pk}/forecast-runs/", {}, format="json"
            ).status_code,
            404,
        )
