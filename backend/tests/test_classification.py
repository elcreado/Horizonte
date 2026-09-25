from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, ImportJob, Transaction
from apps.banking.tasks import import_csv
from apps.classify.models import ClassificationChange
from apps.classify.services import classify


class ClassificationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="classifier")
        self.company = Company.objects.create(name="A", nit="A")
        self.other = Company.objects.create(name="B", nit="B")
        self.member = CompanyMember.objects.create(
            company=self.company, user=self.user, role="owner"
        )
        self.account = BankAccount.objects.create(
            company=self.company, name="A", balance=100, balance_date=date(2026, 9, 23)
        )
        self.movement = Transaction.objects.create(
            account=self.account,
            external_id="one",
            date=date(2026, 9, 1),
            amount=-10,
            description="Adobe",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/companies/{self.company.id}/movements/{self.movement.id}/category/"

    def test_rules_conservative_and_directional(self):
        self.assertEqual(
            classify(self.company.id, "PAGO NÓMINA", Decimal("-5")), ("Nómina", "rule")
        )
        self.assertEqual(classify(self.company.id, "NOMINA ADOBE", Decimal("-5"))[0], "Otros")
        self.assertEqual(classify(self.company.id, "NOMINAL", Decimal("-5"))[0], "Otros")
        self.assertEqual(classify(self.company.id, "ADOBE", Decimal("5"))[0], "Otros")

    def test_remembered_rule_scoped_and_audited(self):
        response = self.client.patch(
            self.url, {"category": "Marketing", "remember": True}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            classify(self.company.id, "  adobe ", Decimal("-5")), ("Marketing", "company_rule")
        )
        self.assertEqual(classify(self.other.id, "Adobe", Decimal("-5")), ("Software", "rule"))
        self.assertEqual(classify(self.company.id, "Adobe", Decimal("5"))[0], "Otros")
        self.assertEqual(ClassificationChange.objects.get().user, self.user)

    def test_manual_only_does_not_create_rule(self):
        self.client.patch(self.url, {"category": "Marketing", "remember": False}, format="json")
        self.assertEqual(classify(self.company.id, "Adobe", Decimal("-5")), ("Software", "rule"))

    def test_invalid_category_and_cross_tenant(self):
        self.assertEqual(
            self.client.patch(self.url, {"category": "Ventas"}, format="json").status_code, 400
        )
        url = f"/api/companies/{self.other.id}/movements/{self.movement.id}/category/"
        self.assertEqual(
            self.client.patch(url, {"category": "Software"}, format="json").status_code, 404
        )
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.patch(self.url, {"category": "Software"}, format="json").status_code, 403
        )
        self.assertEqual(ClassificationChange.objects.count(), 0)

    def test_import_classifies_and_duplicate_preserves_manual(self):
        content = "external_id,date,amount,description\nnew,2026-09-01,-5.00,Adobe\n"
        job = ImportJob.objects.create(account=self.account, user=self.user, content=content)
        import_csv(job.id)
        movement = Transaction.objects.get(external_id="new")
        self.assertEqual(movement.category, "Software")
        url = f"/api/companies/{self.company.id}/movements/{movement.id}/category/"
        self.client.patch(url, {"category": "Marketing"}, format="json")
        job = ImportJob.objects.create(account=self.account, user=self.user, content=content)
        import_csv(job.id)
        movement.refresh_from_db()
        self.assertEqual(movement.category, "Marketing")
        self.assertEqual(movement.classification_source, "manual")

    def test_list_requires_membership(self):
        self.assertEqual(
            self.client.get(f"/api/companies/{self.other.id}/movements/").status_code, 404
        )
        result = self.client.get(f"/api/companies/{self.company.id}/movements/").json()
        self.assertEqual(result["count"], 1)
        self.assertTrue(result["can_edit"])
