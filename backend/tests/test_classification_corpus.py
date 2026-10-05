import csv
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from apps.classify.corpus import evaluate_corpus


class ClassificationCorpusTests(SimpleTestCase):
    def rows(self):
        rows = []
        for category, text in (("Software", "LICENCIA DIGITAL"), ("Transporte", "BUS PASAJE")):
            for suffix in ("ALFA", "BETA", "GAMA"):
                rows.append(
                    {
                        "company_id": "one",
                        "direction": "out",
                        "date": "2026-01-01",
                        "reviewed_on": "2026-01-02",
                        "description": f"{text} {suffix}",
                        "category": category,
                        "group_id": f"{text}-{suffix}",
                    }
                )
        rows.append(
            {
                **rows[0],
                "date": "2026-03-01",
                "reviewed_on": "2026-03-02",
                "description": "LICENCIA DIGITAL NUEVA",
                "group_id": "new-group",
            }
        )
        rows.append(
            {
                **rows[0],
                "reviewed_on": "2026-04-01",
                "description": "ETIQUETA TARDIA",
                "group_id": "late",
            }
        )
        return rows

    def evaluate(self, rows):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.csv"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            return evaluate_corpus(path, "one", "out", date(2026, 2, 1))

    def test_labels_created_after_cutoff_never_enter_training(self):
        result = self.evaluate(self.rows())
        self.assertEqual(result["training_descriptions"], 6)
        self.assertEqual(result["testing_descriptions"], 1)
        self.assertEqual(result["corpus"]["excluded_late_labels"], 1)
        self.assertEqual(len(result["corpus"]["sha256"]), 64)

    def test_group_leakage_and_mixed_tenants_are_rejected(self):
        rows = self.rows()
        rows[6]["group_id"] = rows[0]["group_id"]
        with self.assertRaisesRegex(ValueError, "grupos"):
            self.evaluate(rows)
        rows = self.rows()
        rows[6]["company_id"] = "other"
        with self.assertRaisesRegex(ValueError, "empresa"):
            self.evaluate(rows)
