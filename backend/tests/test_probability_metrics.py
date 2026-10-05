from decimal import Decimal as D

from django.test import SimpleTestCase

from apps.forecast.probability_metrics import evaluate_quantiles, pinball


class ProbabilityMetricTests(SimpleTestCase):
    def test_asymmetric_penalty_and_median_half_absolute_error(self):
        self.assertEqual(pinball(D("10"), D("0"), D("0.1")), D("1"))
        self.assertEqual(pinball(D("0"), D("10"), D("0.1")), D("9"))
        self.assertEqual(pinball(D("-10"), D("0"), D("0.5")), D("5"))

    def test_coverage_width_and_all_three_losses(self):
        points = [{"p10": D("0"), "p50": D("5"), "p90": D("10")}] * 4
        result = evaluate_quantiles([D("-1"), D("0"), D("10"), D("11")], points)
        self.assertEqual(result["pointwise_coverage"], "0.5")
        self.assertEqual(result["mean_interval_width"], "10")
        self.assertEqual(
            {key: D(value) for key, value in result["pinball"].items()},
            {"p10": D("0.75"), "p50": D("2.75"), "p90": D("0.75")},
        )
        self.assertEqual(result["empirical_cdf"]["p50"], "0.5")

    def test_invalid_or_crossed_quantiles_never_return_plausible_metrics(self):
        for point in (
            {"p10": D("2"), "p50": D("1"), "p90": D("3")},
            {"p10": D("0"), "p50": D("NaN"), "p90": D("3")},
            {"p10": D("0"), "p50": D("1")},
        ):
            with self.subTest(point=point), self.assertRaises(ValueError):
                evaluate_quantiles([D("1")], [point])
        with self.assertRaises(ValueError):
            evaluate_quantiles([], [])
        with self.assertRaises(ValueError):
            evaluate_quantiles([D("1")], [])

    def test_nonfinite_actual_and_invalid_levels_are_rejected(self):
        for actual, level in ((D("Infinity"), D("0.1")), (D("1"), D("0")), (D("1"), D("1"))):
            with self.assertRaises(ValueError):
                pinball(actual, D("1"), level)
