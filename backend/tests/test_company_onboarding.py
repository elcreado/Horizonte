from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.banking.models import BankAccount
from tests.test_imports import ImportTests


class AdditionalCompanyTests(TestCase):
    setUp = ImportTests.setUp

    def payload(self):
        return {
            "company_name": "Additional",
            "nit": "new-123",
            "account_name": "Manual",
            "opening_balance": "-12.34",
            "balance_date": timezone.localdate().isoformat(),
            "role": "viewer",
        }

    def test_create_assigns_owner_and_preserves_existing_company(self):
        response = self.client.post("/api/companies/create/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        company = Company.objects.get(pk=response.data["id"])
        self.assertEqual(company.nit, "NEW-123")
        self.assertEqual(CompanyMember.objects.get(company=company).role, "owner")
        self.assertEqual(str(BankAccount.objects.get(company=company).balance), "-12.34")
        self.assertTrue(AuditLog.objects.filter(company=company, action="company.created").exists())
        self.assertEqual(len(self.client.get("/api/companies/").data), 2)
        self.account.refresh_from_db()
        self.assertEqual(str(self.account.balance), "500.00")

    def test_duplicate_and_future_date_are_atomic(self):
        payload = self.payload()
        payload["nit"] = self.company.nit
        self.assertEqual(
            self.client.post("/api/companies/create/", payload, format="json").status_code, 400
        )
        payload = self.payload()
        payload["balance_date"] = (timezone.localdate() + timedelta(days=1)).isoformat()
        self.assertEqual(
            self.client.post("/api/companies/create/", payload, format="json").status_code, 400
        )
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(BankAccount.objects.count(), 1)
        self.client.force_authenticate(None)
        self.assertIn(
            self.client.post("/api/companies/create/", self.payload(), format="json").status_code,
            [401, 403],
        )
