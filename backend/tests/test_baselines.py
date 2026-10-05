from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.forecast.baselines import (
    daily_residual,
    evaluate_baselines,
    hybrid_points,
    predict_baseline,
)


class BaselineTests(SimpleTestCase):
    def test_partial_settlement_and_recurrence_are_not_double_subtracted(self):
        rows = [
            SimpleNamespace(pk=1, date=date(2026, 9, 1), amount=Decimal("-100")),
            SimpleNamespace(pk=2, date=date(2026, 9, 2), amount=Decimal("200")),
            SimpleNamespace(pk=3, date=date(2026, 9, 4), amount=Decimal("999")),
        ]
        result = daily_residual(
            rows,
            date(2026, 9, 1),
            date(2026, 9, 3),
            {1: Decimal("30"), 2: Decimal("50")},
            {2},
            coverage_confirmed=True,
        )
        self.assertEqual(result, [Decimal("-70"), Decimal("0"), Decimal("0")])
        with self.assertRaises(ValueError):
            daily_residual(
                rows, date(2026, 9, 1), date(2026, 9, 3), {}, set(), coverage_confirmed=False
            )

    def test_baseline_periods_and_hybrid_balance(self):
        history = [Decimal(i) for i in range(1, 8)]
        self.assertEqual(predict_baseline(history, 30, "naive"), [Decimal("7")] * 30)
        seasonal = predict_baseline(history, 30, "seasonal_naive")
        self.assertEqual(seasonal[:14], history * 2)
        points = hybrid_points(
            Decimal("100"),
            date(2026, 9, 1),
            [Decimal("-10"), Decimal("20")],
            {date(2026, 9, 1): Decimal("999"), date(2026, 9, 2): Decimal("-30")},
        )
        self.assertEqual([row["balance"] for row in points], ["60", "80"])

    def test_simple_exponential_smoothing_uses_past_only(self):
        history = [Decimal("10"), Decimal("20"), Decimal("30")]
        self.assertEqual(predict_baseline(history, 30, "ses"), [Decimal("18.10")] * 30)
        self.assertEqual(
            predict_baseline(history + [Decimal("100")], 30, "ses")[0], Decimal("42.67")
        )

    def test_rolling_origin_has_no_future_leakage(self):
        constant = [Decimal("5")] * 100
        result = evaluate_baselines(constant, 30)
        self.assertEqual(Decimal(result["naive"]["mae"]), 0)
        self.assertEqual(Decimal(result["ses"]["mae"]), 0)
        seasonal = [Decimal(i % 7) for i in range(100)]
        result = evaluate_baselines(seasonal, 30)
        self.assertEqual(Decimal(result["seasonal_naive"]["mae"]), 0)
        self.assertGreater(Decimal(result["naive"]["mae"]), 0)
        jump = [Decimal("0")] * 28 + [Decimal("100")] * 30
        result = evaluate_baselines(jump, 30)
        self.assertEqual(result["naive"]["origins"], 1)
        self.assertEqual(Decimal(result["naive"]["mae"]), 100)
        with self.assertRaises(ValueError):
            evaluate_baselines([Decimal("1")] * 10, 90)
