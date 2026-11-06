from django.test import SimpleTestCase

from apps.classify.tfidf import fit_tfidf


class TfidfTests(SimpleTestCase):
    def examples(self):
        return [
            (f"PAGO LICENCIA DIGITAL {item}", "Software") for item in ("ALFA", "BETA", "GAMA")
        ] + [(f"PAGO BUS PASAJE {item}", "Transporte") for item in ("NORTE", "SUR", "CENTRO")]

    def test_known_language_suggests_and_unknown_language_abstains(self):
        model = fit_tfidf(self.examples())
        self.assertEqual(model.suggest("LICENCIA DIGITAL NUEVA")["category"], "Software")
        self.assertEqual(model.suggest("BUS PASAJE LOCAL")["category"], "Transporte")
        self.assertEqual(model.suggest("DESCONOCIDO")["status"], "abstained")
        self.assertEqual(model.suggest("PAGO")["status"], "abstained")

    def test_repeated_rows_do_not_inflate_training_support(self):
        with self.assertRaises(ValueError):
            fit_tfidf([("LICENCIA", "Software")] * 20 + [("BUS", "Transporte")] * 20)
        model = fit_tfidf(self.examples() * 2)
        self.assertEqual(model.examples, 6)

    def test_conflicting_labels_and_single_class_are_rejected(self):
        with self.assertRaises(ValueError):
            fit_tfidf(self.examples() + [("PAGO LICENCIA DIGITAL ALFA", "Transporte")])
        with self.assertRaises(ValueError):
            fit_tfidf(self.examples()[:3])
