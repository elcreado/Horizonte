from decimal import Decimal as D

from django.test import SimpleTestCase

from apps.forecast.calibrated_intervals import temporal_cash_intervals


class TemporalIntervalTests(SimpleTestCase):
    def test_reserved_block_detects_trend_without_contaminating_training(self):
        history = [D("0")] * 400
        baseline, evidence = temporal_cash_intervals(history, D("100"), [D("0")] * 30)
        start = evidence["calibration_start_index"]
        shifted = history[:start] + [D(index - start) for index in range(start, len(history))]
        points, revised = temporal_cash_intervals(shifted, D("100"), [D("0")] * 30)
        self.assertEqual(evidence["training_days"], revised["training_days"])
        self.assertEqual(revised["training_origins"], evidence["training_origins"])
        self.assertGreater(D(revised["corrections"][-1]), D("0"))
        self.assertEqual(baseline[-1]["lower"], D("100"))
        self.assertTrue(all(p["lower"] <= p["median"] <= p["upper"] for p in points))
        self.assertEqual(revised["calibration_end_index"], len(history) - 1)

    def test_known_commitment_translates_interval_once(self):
        history = [D(i % 7) for i in range(550)]
        for horizon in (30, 60, 90):
            with self.subTest(horizon=horizon):
                flows = [D("0")] * horizon
                original, _ = temporal_cash_intervals(history, D("0"), flows)
                flows[0] = D("-100")
                revised, _ = temporal_cash_intervals(history, D("0"), flows)
                for before, after in zip(original, revised, strict=True):
                    for key in ("lower", "median", "upper"):
                        self.assertEqual(after[key], before[key] - D("100"))

    def test_short_or_nonfinite_history_is_rejected(self):
        for history in ([D("1")] * 100, [D("NaN")] * 550):
            with self.assertRaises(ValueError):
                temporal_cash_intervals(history, D("0"), [D("0")] * 90)
