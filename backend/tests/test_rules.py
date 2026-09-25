from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from apps.banking.models import Transaction
from apps.classify.models import ClassificationRule
from apps.classify.services import classify
from tests.test_imports import ImportTests


class RuleManagementTests(TestCase):
    setUp = ImportTests.setUp

    def test_delete_changes_future_classification_only(self):
        rule = ClassificationRule.objects.create(
            company=self.company,
            normalized_description="ADOBE",
            direction="out",
            category="Marketing",
        )
        movement = Transaction.objects.create(
            account=self.account,
            external_id="previous",
            date="2026-09-01",
            amount="-10",
            description="Adobe",
            category="Marketing",
            classification_source="manual",
        )
        url = f"/api/companies/{self.company.pk}/classification-rules/"
        self.assertEqual(self.client.get(url).data["results"][0]["id"], rule.pk)
        self.assertEqual(
            classify(self.company.pk, "Adobe", Decimal("-10")), ("Marketing", "company_rule")
        )
        self.assertEqual(self.client.delete(f"{url}{rule.pk}/").status_code, 204)
        self.assertEqual(classify(self.company.pk, "Adobe", Decimal("-10")), ("Software", "rule"))
        movement.refresh_from_db()
        self.assertEqual(movement.category, "Marketing")
        self.assertEqual(movement.classification_source, "manual")
        self.assertEqual(
            AuditLog.objects.get(action="classification.rule_deleted").before["category"],
            "Marketing",
        )

    def test_viewer_and_other_company(self):
        rule = ClassificationRule.objects.create(
            company=self.company,
            normalized_description="ADOBE",
            direction="out",
            category="Marketing",
        )
        self.member.role = "viewer"
        self.member.save()
        url = f"/api/companies/{self.company.pk}/classification-rules/"
        self.assertFalse(self.client.get(url).data["can_edit"])
        self.assertEqual(self.client.delete(f"{url}{rule.pk}/").status_code, 403)
        other = Company.objects.create(name="Other", nit="rules-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.pk}/classification-rules/").status_code, 404
        )
        self.assertTrue(ClassificationRule.objects.filter(pk=rule.pk).exists())
