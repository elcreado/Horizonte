from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.forecast.research_probability import evaluate_probability, render_probability_report
from apps.forecast.synthetic import generate_dataset


class ProbabilityResearchTests(SimpleTestCase):
    def test_all_horizons_report_insufficient_origins_and_valid_metrics(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate_dataset(root, companies=5, seed=7)
            result = evaluate_probability(root, step=180)
            self.assertEqual([row["horizon"] for row in result["metrics"]], [30, 60, 90])
            for row in result["metrics"]:
                self.assertGreater(row["windows"], 0)
                self.assertEqual(row["predictions"], row["windows"] * row["horizon"])
                self.assertTrue(0 <= Decimal(row["pointwise_coverage"]) <= 1)
                self.assertGreaterEqual(Decimal(row["mean_interval_width"]), 0)
            self.assertEqual(result["metrics"][-1]["unavailable_windows"], 5)
            self.assertEqual(len(result["profile_metrics"]), 15)
            for total in result["metrics"]:
                groups = [
                    row for row in result["profile_metrics"] if row["horizon"] == total["horizon"]
                ]
                self.assertEqual(sum(row["predictions"] for row in groups), total["predictions"])
                self.assertEqual(sum(row["windows"] for row in groups), total["windows"])
                weighted = sum(
                    Decimal(row["pointwise_coverage"]) * row["predictions"] for row in groups
                )
                self.assertLess(
                    abs(weighted / total["predictions"] - Decimal(total["pointwise_coverage"])),
                    Decimal("1e-25"),
                )
            self.assertIn("No disponibles", render_probability_report(result))
            (root / "daily.csv").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifiesto"):
                evaluate_probability(root)
