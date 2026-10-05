from datetime import timedelta

from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import Transaction
from apps.forecast.models import ForecastRun, Obligation
from config.api_inventory import build_inventory
from tests.test_imports import ImportTests


class ForecastRunTests(TestCase):
    setUp = ImportTests.setUp

    def test_quantile_result_matches_documented_experimental_variant(self):
        start = self.account.balance_date - timedelta(days=269)
        Transaction.objects.bulk_create(
            [
                Transaction(
                    account=self.account,
                    external_id=f"quantile-{offset}",
                    date=start + timedelta(days=offset),
                    amount="1.00",
                    description="Variable",
                )
                for offset in range(270)
            ]
        )
        self.account.history_complete_from = start
        self.account.history_complete_through = self.account.balance_date
        self.account.save()
        response = self.client.post(
            f"/api/companies/{self.company.pk}/forecast-runs/",
            {"horizon": 90, "method": "hybrid_weekly"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        result = response.json()["result"]
        operation = build_inventory()["paths"]["/api/companies/{company_id}/forecast-runs/"]["post"]
        schema = operation["responses"]["201"]["content"]["application/json"]["schema"][
            "properties"
        ]["result"]
        self.assertEqual(set(result), set(schema["properties"]))
        quantiles = result["quantiles"]
        self.assertEqual(quantiles["status"], "experimental")
        variant = schema["properties"]["quantiles"]["oneOf"][1]
        self.assertEqual(set(quantiles), set(variant["properties"]))
        self.assertEqual(len(result["points"]), 90)
        point_fields = schema["properties"]["points"]["items"]["properties"]
        for point in result["points"]:
            self.assertEqual(set(point), set(point_fields))
            for key in ("p10", "p50", "p90"):
                self.assertIsInstance(point[key], str)

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
        result_schema = schema["properties"]["result"]
        self.assertEqual(set(first.json()["result"]), set(result_schema["properties"]))
        quantiles = first.json()["result"]["quantiles"]
        self.assertEqual(quantiles["status"], "unavailable")
        self.assertEqual(
            set(quantiles), set(result_schema["properties"]["quantiles"]["oneOf"][0]["properties"])
        )
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
