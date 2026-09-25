from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount


class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.payload = {
            "username": "new-owner",
            "email": "owner@example.com",
            "password": "A-unique-test-pass-582!",
            "password_confirm": "A-unique-test-pass-582!",
            "company_name": "Test Company",
            "nit": "TEST-REG-01",
            "account_name": "Manual",
            "opening_balance": "1000.25",
            "balance_date": "2026-01-01",
        }

    def register(self):
        token = self.client.get("/api/auth/csrf/").json()["csrfToken"]
        return self.client.post(
            "/api/auth/register/",
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
            HTTP_ORIGIN="http://127.0.0.1:5173",
        )

    @override_settings(CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"])
    def test_register_creates_isolated_owner_and_session(self):
        self.assertEqual(self.register().status_code, 201)
        user = get_user_model().objects.get(username="new-owner")
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(CompanyMember.objects.get(user=user).role, "owner")
        self.assertEqual(str(BankAccount.objects.get().balance), "1000.25")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(len(self.client.get("/api/companies/").json()), 1)

    def test_csrf_required(self):
        self.assertEqual(
            self.client.post("/api/auth/register/", self.payload, format="json").status_code, 403
        )
        self.assertEqual(get_user_model().objects.count(), 0)

    @override_settings(CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"])
    def test_duplicate_company_rolls_back_user(self):
        Company.objects.create(name="Existing", nit=self.payload["nit"])
        self.assertEqual(self.register().status_code, 400)
        self.assertFalse(get_user_model().objects.filter(username="new-owner").exists())
        self.assertEqual(BankAccount.objects.count(), 0)

    @override_settings(CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"])
    def test_weak_mismatched_and_future_inputs(self):
        self.payload["password_confirm"] = "Different-test-pass"
        self.assertEqual(self.register().status_code, 400)
        self.payload["password"] = self.payload["password_confirm"] = "123456789012"
        self.assertEqual(self.register().status_code, 400)
        self.payload["password"] = self.payload["password_confirm"] = "A-unique-test-pass-582!"
        self.payload["balance_date"] = "2999-01-01"
        self.assertEqual(self.register().status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)
