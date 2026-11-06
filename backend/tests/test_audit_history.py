from django.test import TestCase

from apps.accounts.models import AuditLog, Company
from tests.test_imports import ImportTests


class AuditHistoryTests(TestCase):
    setUp = ImportTests.setUp

    def test_scope_filter_pagination_and_read_only(self):
        for i in range(21):
            AuditLog.objects.create(
                company=self.company,
                user=self.user,
                action="account.balance_updated",
                entity="BankAccount",
                entity_id=str(self.account.pk),
                before={"balance": str(i)},
                after={"balance": str(i + 1)},
            )
        other = Company.objects.create(name="Other", nit="audit-other")
        AuditLog.objects.create(
            company=other,
            user=self.user,
            action="private",
            entity="company",
            entity_id=str(other.pk),
        )
        url = f"/api/companies/{self.company.pk}/audit/"
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 21)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertEqual(response.data["results"][0]["username"], self.user.username)
        self.assertEqual(len(self.client.get(url + "?page=2").data["results"]), 1)
        self.assertEqual(self.client.get(url + "?action=private").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/companies/{other.pk}/audit/").status_code, 404)
        self.assertEqual(self.client.post(url, {}).status_code, 405)

    def test_viewer_cannot_read_audit(self):
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.pk}/audit/").status_code, 403
        )
