from django.test import SimpleTestCase, TestCase

from apps.banking.models import Transaction
from apps.banking.normalization import normalize_movement
from apps.banking.tasks import import_csv
from tests.test_imports import ImportTests


class NormalizationTests(SimpleTestCase):
    def test_explicit_merchant_and_reference(self):
        result = normalize_movement("Pago; Comercio: Tienda 24; REF: AB123")
        self.assertEqual(result["merchant_name"], "TIENDA 24")
        self.assertEqual(result["normalized_description"], "PAGO COMERCIO TIENDA 24")

    def test_ambiguous_text_preserves_numbers(self):
        result = normalize_movement("  Café 24   pedido 123  ")
        self.assertEqual(result["normalized_description"], "CAFE 24 PEDIDO 123")
        self.assertEqual(result["merchant_name"], "")
        self.assertEqual(
            normalize_movement("REFORMAS 123")["normalized_description"], "REFORMAS 123"
        )


class NormalizationImportTests(TestCase):
    setUp = ImportTests.setUp
    job = ImportTests.job

    def test_import_preserves_original_and_api_exposes_normalization(self):
        content = "external_id,date,amount,description\nid,2026-09-01,-10.00,Pago; Comercio: Café 24; REF: 123\n"
        import_csv(self.job(content).id)
        row = Transaction.objects.get()
        self.assertEqual(row.description, "Pago; Comercio: Café 24; REF: 123")
        self.assertEqual(row.merchant_name, "CAFE 24")
        self.assertEqual(str(row.amount), "-10.00")
        response = self.client.get(f"/api/companies/{self.company.id}/movements/")
        self.assertEqual(response.data["results"][0]["merchant_name"], "CAFE 24")
        import_csv(self.job(content).id)
        self.assertEqual(Transaction.objects.count(), 1)
