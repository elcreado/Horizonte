import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.forecast.arima_candidate import ArimaFitError
from apps.forecast.research import evaluate_dataset, research_recurrences
from apps.forecast.synthetic import generate_dataset


class ResearchTests(SimpleTestCase):
    def test_arima_policy_does_not_hide_invalid_data_or_missing_dependencies(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate_dataset(root, companies=1, seed=7)
            for error in (ValueError("Datos inválidos"), ImportError("Dependencia ausente")):
                with self.subTest(error=type(error).__name__):
                    with patch("apps.forecast.research.predict_arima", side_effect=error):
                        with self.assertRaises(type(error)):
                            evaluate_dataset(
                                root, step=180, include_arima=True, arima_ses_fallback=True
                            )

    def test_arima_failure_uses_same_windows_and_records_ses_policy(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate_dataset(root, companies=1, seed=7)
            with patch(
                "apps.forecast.research.predict_arima", side_effect=ArimaFitError("No convergió")
            ):
                report = evaluate_dataset(
                    root, step=180, include_arima=True, arima_ses_fallback=True
                )
            for horizon in (30, 60, 90):
                rows = {
                    row["method"]: row for row in report["metrics"] if row["horizon"] == horizon
                }
                candidate = rows["arima_100_ses_fallback"]
                self.assertEqual(candidate["windows"], rows["ses"]["windows"])
                self.assertEqual(candidate["fallback_windows"], candidate["windows"])
                self.assertEqual(candidate["balance_mae"], rows["ses"]["balance_mae"])
            self.assertEqual(len(report["arima_fallbacks"]), 9)

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
