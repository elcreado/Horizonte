from django.test import SimpleTestCase, TestCase

from apps.accounts.models import Company
from apps.banking.merchants import resolve_merchants
from apps.banking.models import Merchant, MerchantAlias, Transaction
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
        self.assertEqual(row.merchant.display_name, "CAFE 24")
        self.assertEqual(MerchantAlias.objects.get().provider, "manual_upload")
        self.assertEqual(str(row.amount), "-10.00")
        response = self.client.get(f"/api/companies/{self.company.id}/movements/")
        self.assertEqual(response.data["results"][0]["merchant_name"], "CAFE 24")
        self.assertEqual(response.data["results"][0]["merchant_id"], row.merchant_id)
        merchants = self.client.get(f"/api/companies/{self.company.id}/merchants/")
        self.assertEqual(merchants.data["results"][0]["movement_count"], 1)
        import_csv(self.job(content).id)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Merchant.objects.count(), 1)

    def test_alias_is_company_and_provider_scoped(self):
        company_other = Company.objects.create(name="Other", nit="merchant-other")
        first = resolve_merchants(self.company.pk, "manual_upload", ["Café 24"])["Café 24"]
        other = resolve_merchants(company_other.pk, "manual_upload", ["Cafe 24"])["Cafe 24"]
        self.assertNotEqual(first, other)
        target = Merchant.objects.create(
            company=self.company, normalized_name="CAFE CENTRAL", display_name="Café Central"
        )
        MerchantAlias.objects.create(
            company=self.company,
            merchant=target,
            provider="mock",
            normalized_name="CAFE 24",
        )
        self.assertEqual(
            resolve_merchants(self.company.pk, "mock", ["Café 24"])["Café 24"], target.pk
        )
        self.assertEqual(Merchant.objects.filter(company=self.company).count(), 2)
        self.assertEqual(
            self.client.get(f"/api/companies/{company_other.pk}/merchants/").status_code, 404
        )
