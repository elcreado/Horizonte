from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember


class PlatformTests(TestCase):
    def test_only_active_staff_superuser_can_inspect_users(self):
        user = get_user_model().objects.create_user(
            username="owner", password="test-platform-password"
        )
        company = Company.objects.create(name="Company", nit="platform-test")
        CompanyMember.objects.create(user=user, company=company, role="owner")
        client = APIClient()
        self.assertEqual(client.get("/api/platform/users/").status_code, 403)
        client.force_authenticate(user)
        self.assertFalse(client.get("/api/auth/me/").json()["platform_admin"])
        self.assertEqual(client.get("/api/platform/users/").status_code, 403)
        user.is_staff = True
        user.save()
        self.assertEqual(client.get("/api/platform/users/").status_code, 403)
        user.is_superuser = True
        user.save()
        response = client.get("/api/platform/users/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(client.get("/api/auth/me/").json()["platform_admin"])
        row = response.json()["results"][0]
        self.assertEqual(row["company_count"], 1)
        self.assertNotIn("password", row)
        self.assertNotIn("last_login", row)
        user.is_active = False
        user.save()
        self.assertEqual(client.get("/api/platform/users/").status_code, 403)
