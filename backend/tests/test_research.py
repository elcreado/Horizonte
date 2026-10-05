import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.forecast.research import evaluate_dataset, research_recurrences
from apps.forecast.synthetic import generate_dataset


class ResearchTests(SimpleTestCase):
    def test_future_commitments_do_not_leak_into_recurrence_estimation(self):
        commitments = [
            {
                "id": str(month),
                "kind": "rent",
                "due": date(2026, month, 1),
                "announced": date(2026, month - 1, 1),
                "amount": Decimal(-20),
            }
            for month in (6, 7, 8)
        ]
        cutoff = date(2026, 8, 20)
        baseline = research_recurrences(commitments, cutoff, 90)
        future = {
            "id": "unknown-future",
            "kind": "rent",
            "due": date(2026, 9, 1),
            "announced": date(2026, 8, 25),
            "amount": Decimal(-9999),
        }
        self.assertEqual(baseline, research_recurrences(commitments + [future], cutoff, 90))
        visible = {**future, "announced": date(2026, 8, 19)}
        revised = research_recurrences(commitments + [visible], cutoff, 90)
        self.assertNotIn(date(2026, 9, 1), revised)
        self.assertEqual(revised[date(2026, 10, 1)], Decimal(-20))

    def test_dataset_reproducible_and_cash_conserves_decimal_flows(self):
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            manifest = generate_dataset(Path(first), companies=5, seed=7)
            repeated = generate_dataset(Path(second), companies=5, seed=7)
            self.assertEqual(manifest, repeated)
            self.assertEqual(manifest["daily_rows"], 5 * 731)
            self.assertGreater(manifest["companies_with_negative_balance"], 0)
            previous = {}
            with (Path(first) / "daily.csv").open(encoding="utf-8", newline="") as file:
                for row in csv.DictReader(file):
                    company = row["company_id"]
                    balance = Decimal(row["balance"])
                    if company in previous:
                        self.assertEqual(
                            balance,
                            previous[company]
                            + Decimal(row["known_flow"])
                            + Decimal(row["variable_flow"]),
                        )
                    previous[company] = balance
            with (Path(first) / "obligations.csv").open(encoding="utf-8", newline="") as file:
                for row in csv.DictReader(file):
                    self.assertLess(
                        date.fromisoformat(row["announced_on"]), date.fromisoformat(row["due_date"])
                    )

    def test_rolling_evaluation_and_dataset_integrity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate_dataset(root, companies=1, seed=3)
            report = evaluate_dataset(root, step=90)
            self.assertEqual(len(report["metrics"]), 12)
            for row in report["metrics"]:
                self.assertEqual(row["predictions"], row["windows"] * row["horizon"])
                self.assertEqual(
                    row["windows"],
                    row["tp"] + row["fp"] + row["fn"] + row["tn"] + row["ongoing_deficit_windows"],
                )
                self.assertGreaterEqual(Decimal(row["balance_mae"]), 0)
            manifest = json.loads((root / "manifest.json").read_text())
            manifest["sha256"]["daily.csv"] = "tampered"
            (root / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                evaluate_dataset(root)
