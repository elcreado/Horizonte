from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from apps.forecast.alerts import threshold_alert
from tests.test_imports import ImportTests


class ThresholdCalculationTests(SimpleTestCase):
    def test_equality_and_current_shortfall(self):
        points = [{"date": "2026-09-24", "balance": "100"}, {"date": "2026-09-25", "balance": "50"}]
        result = threshold_alert(points, Decimal("100"), Decimal("100"), date(2026, 9, 23))
        self.assertEqual(result["first_below"], "2026-09-25")
        self.assertEqual(result["projected_days_below"], 1)
        result = threshold_alert(points, Decimal("100"), Decimal("-10"), date(2026, 9, 23))
        self.assertTrue(result["currently_below"])
        self.assertEqual(result["first_below"], "2026-09-23")
        self.assertEqual(result["shortfall_at_minimum"], "110")


class ThresholdApiTests(TestCase):
    setUp = ImportTests.setUp

    def test_permissions_validation_and_dashboard(self):
        url = f"/api/companies/{self.company.pk}/liquidity-threshold/"
        self.assertEqual(
            self.client.patch(url, {"threshold": "-1"}, format="json").status_code, 400
        )
        self.assertEqual(
            self.client.patch(url, {"threshold": "600.00"}, format="json").status_code, 200
        )
        result = self.client.get(f"/api/companies/{self.company.pk}/dashboard/").data[
            "liquidity_alert"
        ]
        self.assertTrue(result["currently_below"])
        self.assertEqual(result["projected_days_below"], 30)
        self.member.role = "accountant"
        self.member.save()
        self.assertFalse(self.client.get(url).data["can_edit"])
        self.assertEqual(self.client.patch(url, {"threshold": "0"}, format="json").status_code, 403)
