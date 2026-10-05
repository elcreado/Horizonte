from django.test import TestCase

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.banking.merchants import resolve_merchants
from apps.banking.models import Merchant, MerchantAlias, Transaction
from apps.banking.tasks import import_csv
from tests.test_imports import ImportTests


class MerchantEditTests(TestCase):
    setUp = ImportTests.setUp
    job = ImportTests.job

    def test_aliases_are_scoped_to_tenant_and_source(self):
        other = Company.objects.create(name="Other", nit="other-alias")
        foreign = Merchant.objects.create(
            company=other, normalized_name="TARGET", display_name="Otro"
        )
        target = Merchant.objects.create(
            company=self.company, normalized_name="TARGET", display_name="Propio"
        )
        url = f"/api/companies/{self.company.pk}/merchant-aliases/"
        payload = {"merchant_id": foreign.pk, "provider": "manual_upload", "name": "Café 24"}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 404)
        self.assertFalse(MerchantAlias.objects.exists())
        payload["merchant_id"] = target.pk
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 201)
        self.assertEqual(
            resolve_merchants(self.company.pk, "manual_upload", ["CAFE 24"])["CAFE 24"], target.pk
        )
        mock_id = resolve_merchants(self.company.pk, "mock", ["CAFE 24"])["CAFE 24"]
        other_id = resolve_merchants(other.pk, "manual_upload", ["CAFE 24"])["CAFE 24"]
        self.assertNotEqual(mock_id, target.pk)
        self.assertNotEqual(other_id, target.pk)
        rows = self.client.get(url).json()["results"]
        self.assertEqual({row["merchant_id"] for row in rows}, {target.pk, mock_id})
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/merchant-aliases/").status_code, 404
        )
        self.assertEqual(AuditLog.objects.filter(action="merchant.alias_assigned").count(), 1)

    def test_alias_assignment_only_changes_future_imports_and_is_audited(self):
        header = "external_id,date,amount,description\n"
        description = "Pago; Comercio: Cafe 24; REF: 123"
        import_csv(self.job(header + f"one,2026-09-01,-10.00,{description}\n").pk)
        first = Transaction.objects.get()
        target = Merchant.objects.create(
            company=self.company, normalized_name="TARGET", display_name="Destino"
        )
        url = f"/api/companies/{self.company.pk}/merchant-aliases/"
        data = {"merchant_id": target.pk, "provider": "manual_upload", "name": "Café 24"}
        for _ in range(2):
            self.assertEqual(self.client.post(url, data, format="json").status_code, 200)
        self.assertEqual(AuditLog.objects.filter(action="merchant.alias_assigned").count(), 1)
        import_csv(self.job(header + f"two,2026-09-02,-20.00,{description}\n").pk)
        first.refresh_from_db()
        self.assertNotEqual(first.merchant_id, target.pk)
        self.assertEqual(first.description, description)
        self.assertEqual(Transaction.objects.get(external_id="two").merchant_id, target.pk)
        self.assertEqual(self.client.get(url).json()["results"][0]["merchant_id"], target.pk)
        data["provider"] = "unsupported"
        self.assertEqual(self.client.post(url, data, format="json").status_code, 400)
        data["provider"] = "manual_upload"
        data["merchant_id"] = target.pk + 1000
        self.assertEqual(self.client.post(url, data, format="json").status_code, 404)
        CompanyMember.objects.filter(company=self.company).update(role="viewer")
        self.assertEqual(self.client.post(url, data, format="json").status_code, 403)

    def test_future_import_preserves_reviewed_name_and_original_descriptions(self):
        header = "external_id,date,amount,description\n"
        original = "Pago; Comercio: Café 24; REF: 123"
        import_csv(self.job(header + f"one,2026-09-01,-10.00,{original}\n").pk)
        first = Transaction.objects.get()
        merchant = first.merchant
        response = self.client.patch(
            f"/api/companies/{self.company.pk}/merchants/{merchant.pk}/name/",
            {"display_name": "Café del barrio"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        newer = "Pago; Comercio: Cafe 24; REF: 456"
        import_csv(self.job(header + f"two,2026-09-02,-20.00,{newer}\n").pk)
        self.assertEqual(Merchant.objects.count(), 1)
        self.assertEqual(Transaction.objects.filter(merchant=merchant).count(), 2)
        first.refresh_from_db()
        self.assertEqual(first.description, original)
        self.assertEqual(Transaction.objects.get(external_id="two").description, newer)
        rows = self.client.get(f"/api/companies/{self.company.pk}/movements/").json()["results"]
        self.assertEqual({row["merchant_display_name"] for row in rows}, {"Café del barrio"})
        self.assertEqual({row["merchant_name"] for row in rows}, {"CAFE 24"})

    def test_rename_is_audited_without_changing_resolution(self):
        mapping = resolve_merchants(self.company.pk, "manual_upload", ["SHOP ORIGINAL"])
        merchant = Merchant.objects.get(pk=mapping["SHOP ORIGINAL"])
        url = f"/api/companies/{self.company.pk}/merchants/{merchant.pk}/name/"
        self.assertTrue(
            self.client.get(f"/api/companies/{self.company.pk}/merchants/").data["can_edit"]
        )
        for _ in range(2):
            self.assertEqual(
                self.client.patch(url, {"display_name": "Mi proveedor"}, format="json").status_code,
                200,
            )
        self.assertEqual(AuditLog.objects.filter(action="merchant.renamed").count(), 1)
        self.assertEqual(
            resolve_merchants(self.company.pk, "manual_upload", ["SHOP ORIGINAL"]), mapping
        )
        merchant.refresh_from_db()
        self.assertEqual(merchant.display_name, "Mi proveedor")

    def test_viewer_other_tenant_and_blank_name_rejected(self):
        merchant = Merchant.objects.create(
            company=self.company, display_name="A", normalized_name="a"
        )
        url = f"/api/companies/{self.company.pk}/merchants/{merchant.pk}/name/"
        self.assertEqual(
            self.client.patch(url, {"display_name": " "}, format="json").status_code, 400
        )
        other_url = f"/api/companies/{self.company.pk + 100}/merchants/{merchant.pk}/name/"
        self.assertEqual(
            self.client.patch(other_url, {"display_name": "B"}, format="json").status_code, 404
        )
        CompanyMember.objects.filter(company=self.company).update(role="viewer")
        self.assertFalse(
            self.client.get(f"/api/companies/{self.company.pk}/merchants/").data["can_edit"]
        )
        self.assertEqual(
            self.client.patch(url, {"display_name": "B"}, format="json").status_code, 403
        )
        merchant.refresh_from_db()
        self.assertEqual(merchant.display_name, "A")
