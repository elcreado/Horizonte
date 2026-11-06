from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.forecast.research_intervals import evaluate_intervals, interval_metrics
from apps.forecast.synthetic import generate_dataset


class IntervalResearchTests(SimpleTestCase):
    def test_interval_score_penalizes_misses_and_unnecessary_width(self):
        result = interval_metrics(
            [D("-1"), D("5"), D("11")], [{"lower": D("0"), "upper": D("10")}] * 3
        )
        self.assertEqual(D(result["coverage"]), D("1") / 3)
        self.assertEqual(D(result["mean_interval_score"]), D("50") / 3)
        with self.assertRaises(ValueError):
            interval_metrics([D("1")], [{"lower": D("2"), "upper": D("0")}])

    def test_methods_share_windows_after_calibration_and_validate_dataset(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate_dataset(root, companies=1, seed=7)
            report = evaluate_intervals(root, step=180)
            for horizon in (30, 60, 90):
                rows = {
                    row["method"]: row
                    for row in report["metrics"]
                    if row["horizon"] == horizon and row["profile"] == "all"
                }
                self.assertEqual(rows["empirical"]["windows"], rows["corrected"]["windows"])
                self.assertEqual(
                    rows["corrected"]["predictions"], rows["corrected"]["windows"] * horizon
                )
            (root / "daily.csv").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_intervals(root)
