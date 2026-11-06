from decimal import Decimal as D

from django.test import SimpleTestCase

from apps.forecast.empirical_quantiles import empirical_quantile, weekly_cash_quantiles


class EmpiricalQuantileTests(SimpleTestCase):
    def test_order_statistic_interpolation(self):
        self.assertEqual(empirical_quantile([D("10"), D("0")], D("0.1")), D("1"))
        self.assertEqual(empirical_quantile([D("10"), D("0")], D("0.9")), D("9"))

    def test_exact_weekly_history_has_zero_error_and_known_flow_added_once(self):
        history = [D(i % 7) for i in range(250)]
        flows = [D("0")] * 30
        flows[0] = D("-100")
        points, evidence = weekly_cash_quantiles(history, D("500"), flows)
        self.assertEqual(points[0], {"p10": D("405"), "p50": D("405"), "p90": D("405")})
        self.assertTrue(all(point["p10"] == point["p90"] for point in points))
        self.assertLess(evidence["last_calibration_end_index"], len(history))

    def test_shifted_history_creates_ordered_nontrivial_intervals(self):
        history = [D((i // 7) ** 2) for i in range(250)]
        points, evidence = weekly_cash_quantiles(history, D("0"), [D("0")] * 90)
        self.assertTrue(all(point["p10"] <= point["p50"] <= point["p90"] for point in points))
        self.assertGreater(points[-1]["p90"], points[-1]["p10"])
        self.assertGreaterEqual(evidence["historical_origins"], 20)

    def test_insufficient_history_and_nonfinite_input_are_unavailable(self):
        with self.assertRaises(ValueError):
            weekly_cash_quantiles([D("1")] * 90, D("0"), [D("0")] * 90)
        with self.assertRaises(ValueError):
            weekly_cash_quantiles([D("NaN")] * 250, D("0"), [D("0")] * 30)
