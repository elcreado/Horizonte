from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.forecast.models import Obligation
from apps.invoices.models import Invoice, InvoiceImport
from apps.invoices.parser import parse_invoice
from apps.invoices.tasks import import_invoice

XML = (Path(__file__).resolve().parents[2] / "frontend/public/factura-ejemplo.xml").read_text(
    encoding="utf-8"
)


class InvoiceTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Demo", nit="SYNTHETIC-001")
        self.other = Company.objects.create(name="Other", nit="OTHER")
        self.user = get_user_model().objects.create_user(username="invoice")
        self.member = CompanyMember.objects.create(
            company=self.company, user=self.user, role="owner"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.base = f"/api/companies/{self.company.id}/invoices/"

    def run_import(self, content=XML):
        job = InvoiceImport.objects.create(company=self.company, user=self.user, content=content)
        import_invoice(job.id)
        job.refresh_from_db()
        return job

    def test_parse_parties_amounts_dates(self):
        data = parse_invoice(XML, self.company.nit)
        self.assertEqual(data["direction"], "in")
        self.assertEqual(data["tax"], "19000.00")
        self.assertEqual(data["total"], "119000.00")
        self.assertEqual(parse_invoice(XML, "SYNTHETIC-CLIENT")["direction"], "out")
        with self.assertRaises(ValueError):
            parse_invoice(XML, self.other.nit)

    def test_reject_entities_wrong_currency_and_dates(self):
        unsafe = '<!DOCTYPE Invoice [<!ENTITY x "secret">]><Invoice>&x;</Invoice>'
        for content in (unsafe, XML.replace("COP", "USD"), XML.replace("2026-09-23", "2026-02-30")):
            with self.assertRaises(ValueError):
                parse_invoice(content, self.company.nit)

    def test_attached_document(self):
        content = (
            '<AttachedDocument xmlns="urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"><cac:Attachment><cac:ExternalReference><cbc:Description><![CDATA['
            + XML
            + "]]></cbc:Description></cac:ExternalReference></cac:Attachment></AttachedDocument>"
        )
        self.assertEqual(parse_invoice(content, self.company.nit)["number"], "DEMO-XML-001")

    def test_duplicate_conflict_and_no_automatic_cashflow(self):
        first = self.run_import()
        self.assertEqual(first.status, "completed")
        self.assertEqual(Obligation.objects.count(), 0)
        duplicate = self.run_import()
        self.assertTrue(duplicate.duplicate)
        conflict = self.run_import(XML.replace("119000.00", "120000.00"))
        self.assertEqual(conflict.status, "failed")
        self.assertEqual(conflict.content, "")
        self.assertEqual(Invoice.objects.count(), 1)

    def test_confirmation_creates_one_obligation_with_explicit_pending(self):
        job = self.run_import()
        url = f"{self.base}{job.invoice_id}/confirm/"
        payload = {"due_date": "2026-10-20", "outstanding_amount": "50000.00"}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 201)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 200)
        self.assertEqual(Obligation.objects.count(), 1)
        self.assertEqual(str(Obligation.objects.get().outstanding_amount), "50000.00")

    def test_missing_due_date_requires_confirmation(self):
        job = self.run_import(XML.replace("<cbc:DueDate>2026-10-15</cbc:DueDate>", ""))
        self.assertEqual(job.status, "completed")
        self.assertIsNone(job.invoice.data["due_date"])
        url = f"{self.base}{job.invoice_id}/confirm/"
        self.assertEqual(
            self.client.post(url, {"outstanding_amount": "1"}, format="json").status_code, 400
        )
        self.assertEqual(
            self.client.post(
                url, {"due_date": "2026-10-01", "outstanding_amount": "999999"}, format="json"
            ).status_code,
            400,
        )

    def test_permissions_on_upload_review_and_worker(self):
        self.assertEqual(
            self.client.get(f"/api/companies/{self.other.id}/invoices/").status_code, 404
        )
        job = self.run_import()
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.post(
                f"{self.base}{job.invoice_id}/confirm/", {}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(f"{self.base}imports/", {}, format="multipart").status_code, 403
        )
        self.assertEqual(self.run_import().status, "failed")

    def test_upload_queues_without_parsing_in_http(self):
        with patch("apps.invoices.views.import_invoice.apply_async") as dispatch:
            response = self.client.post(
                f"{self.base}imports/",
                {"file": SimpleUploadedFile("invoice.xml", XML.encode())},
                format="multipart",
            )
        self.assertEqual(response.status_code, 202)
        dispatch.assert_called_once()
        self.assertEqual(Invoice.objects.count(), 0)

    def test_link_existing_obligation_preserves_pending_and_date(self):
        from datetime import date

        job = self.run_import()
        obligation = Obligation.objects.create(
            company=self.company,
            reference="manual-existing",
            description="Existing invoice",
            direction="in",
            due_date=date(2026, 10, 22),
            outstanding_amount="50000.00",
        )
        url = f"{self.base}{job.invoice_id}/obligation-link/"
        self.assertEqual(self.client.get(url).json()["count"], 1)
        self.assertEqual(
            self.client.post(url, {"obligation_id": obligation.id}, format="json").status_code, 200
        )
        self.assertEqual(
            self.client.post(url, {"obligation_id": obligation.id}, format="json").status_code, 200
        )
        self.assertEqual(Obligation.objects.count(), 1)
        obligation.refresh_from_db()
        self.assertEqual(str(obligation.outstanding_amount), "50000.00")
        self.assertEqual(obligation.due_date, date(2026, 10, 22))
        self.assertEqual(self.client.get(url).json()["count"], 0)

    def test_link_rejects_foreign_wrong_direction_and_reused_obligation(self):
        from datetime import date

        first = self.run_import()
        second = self.run_import(XML.replace("00000001</cbc:UUID>", "00000003</cbc:UUID>"))
        obligation = Obligation.objects.create(
            company=self.other,
            reference="foreign",
            description="Other",
            direction="in",
            due_date=date(2026, 10, 22),
            outstanding_amount=10,
        )
        url = f"{self.base}{first.invoice_id}/obligation-link/"
        self.assertEqual(
            self.client.post(url, {"obligation_id": obligation.id}, format="json").status_code, 404
        )
        obligation.company = self.company
        obligation.direction = "out"
        obligation.save()
        self.assertEqual(
            self.client.post(url, {"obligation_id": obligation.id}, format="json").status_code, 400
        )
        obligation.direction = "in"
        obligation.save()
        self.assertEqual(
            self.client.post(url, {"obligation_id": obligation.id}, format="json").status_code, 200
        )
        self.assertEqual(
            self.client.post(
                f"{self.base}{second.invoice_id}/obligation-link/",
                {"obligation_id": obligation.id},
                format="json",
            ).status_code,
            400,
        )

    def test_link_disallows_viewer(self):
        job = self.run_import()
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.post(
                f"{self.base}{job.invoice_id}/obligation-link/", {"obligation_id": 1}, format="json"
            ).status_code,
            403,
        )
