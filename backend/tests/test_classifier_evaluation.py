from decimal import Decimal

from django.test import SimpleTestCase

from apps.classify.evaluation import evaluate_classifier
from tests.test_tfidf import TfidfTests


class ClassifierEvaluationTests(SimpleTestCase):
    def test_abstention_is_not_counted_as_a_correct_classification(self):
        report = evaluate_classifier(
            TfidfTests().examples(),
            [
                ("LICENCIA DIGITAL NUEVA", "Software"),
                ("BUS PASAJE LOCAL", "Software"),
                ("DESCONOCIDO", "Transporte"),
            ],
        )
        self.assertEqual(report["suggested"], 2)
        self.assertEqual(report["abstained"], 1)
        self.assertEqual(report["accuracy_when_suggested"], "0.5")
        self.assertEqual(Decimal(report["coverage"]), Decimal(2) / 3)
        transit = next(row for row in report["per_category"] if row["category"] == "Transporte")
        self.assertEqual((transit["tp"], transit["fp"], transit["fn"]), (0, 1, 1))

    def test_no_accepted_predictions_is_undefined_accuracy_not_perfect(self):
        report = evaluate_classifier(TfidfTests().examples(), [("DESCONOCIDO", "Software")])
        self.assertEqual(report["coverage"], "0")
        self.assertIsNone(report["accuracy_when_suggested"])

    def test_normalized_overlap_and_repeated_test_rows_are_rejected(self):
        for test in (
            [("pago licencia digital alfa", "Software")],
            [("NUEVO", "Software"), ("nuevo", "Software")],
            [],
        ):
            with self.assertRaises(ValueError):
                evaluate_classifier(TfidfTests().examples(), test)
