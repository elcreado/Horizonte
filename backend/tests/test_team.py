from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, Company, CompanyMember


class TeamTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner")
        self.teammate = get_user_model().objects.create_user(username="teammate")
        self.company = Company.objects.create(name="Team", nit="team")
        self.other = Company.objects.create(name="Other", nit="other")
        self.owner = CompanyMember.objects.create(
            company=self.company, user=self.user, role="owner"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.base = f"/api/companies/{self.company.id}/"

    def add(self, role="viewer"):
        return self.client.post(
            self.base + "team/", {"username": self.teammate.username, "role": role}, format="json"
        )

    def test_add_change_remove_access_and_audit(self):
        result = self.add()
        self.assertEqual(result.status_code, 201)
        member_id = result.json()["id"]
        self.assertEqual(
            self.client.patch(
                f"{self.base}team/{member_id}/", {"role": "accountant"}, format="json"
            ).status_code,
            204,
        )
        self.assertEqual(self.client.delete(f"{self.base}team/{member_id}/").status_code, 204)
        self.assertEqual(AuditLog.objects.count(), 3)
        self.client.force_authenticate(self.teammate)
        self.assertEqual(self.client.get(self.base + "team/").status_code, 404)
        self.assertEqual(self.client.get("/api/companies/").json(), [])

    def test_last_owner_cannot_be_removed_or_demoted(self):
        url = f"{self.base}team/{self.owner.id}/"
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertEqual(self.client.patch(url, {"role": "viewer"}, format="json").status_code, 400)
        self.add("owner")
        self.assertEqual(self.client.patch(url, {"role": "viewer"}, format="json").status_code, 204)

    def test_inactive_owner_does_not_satisfy_last_owner_rule(self):
        self.add("owner")
        self.teammate.is_active = False
        self.teammate.save()
        self.assertEqual(self.client.delete(f"{self.base}team/{self.owner.id}/").status_code, 400)

    def test_accountant_and_foreign_company_cannot_manage(self):
        self.add("accountant")
        self.client.force_authenticate(self.teammate)
        self.assertFalse(self.client.get(self.base + "team/").json()["can_manage"])
        self.assertEqual(
            self.client.patch(
                f"{self.base}team/{self.owner.id}/", {"role": "viewer"}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(self.base + "name/", {"name": "Renamed"}, format="json").status_code,
            403,
        )
        self.assertEqual(self.client.get(f"/api/companies/{self.other.id}/team/").status_code, 404)

    def test_duplicate_member_invalid_role_and_company_rename(self):
        self.assertEqual(self.add("administrator").status_code, 400)
        self.assertEqual(self.add().status_code, 201)
        self.assertEqual(self.add().status_code, 400)
        self.assertEqual(
            self.client.patch(self.base + "name/", {"name": "New Team"}, format="json").status_code,
            200,
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "New Team")
