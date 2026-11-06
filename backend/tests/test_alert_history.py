from django.test import TestCase

from apps.accounts.models import Company
from apps.forecast.models import AlertEvaluation
from tests.test_imports import ImportTests


class AlertHistoryTests(TestCase):
    setUp = ImportTests.setUp

    def test_snapshot_is_idempotent_and_preserved(self):
        url = f"/api/companies/{self.company.pk}/alert-history/"
        response = self.client.post(url, {"horizon": 30}, format="json")
        self.assertEqual(response.status_code, 201)
        original = response.data["id"]
        self.assertEqual(self.client.post(url, {"horizon": 30}, format="json").status_code, 200)
        self.company.liquidity_threshold = "600"
        self.company.save()
        changed = self.client.post(url, {"horizon": 30}, format="json")
        self.assertEqual(changed.status_code, 201)
        self.assertTrue(changed.data["result"]["currently_below"])
        self.assertFalse(AlertEvaluation.objects.get(pk=original).result["currently_below"])
        self.assertEqual(self.client.get(url).data["count"], 2)

    def test_permissions_and_horizon(self):
        url = f"/api/companies/{self.company.pk}/alert-history/"
        self.assertEqual(self.client.post(url, {"horizon": 999}, format="json").status_code, 400)
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.client.post(url, {"horizon": 30}, format="json").status_code, 403)
        other = Company.objects.create(name="Other", nit="alert-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/alert-history/").status_code, 404
        )
