from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, Transaction
from apps.forecast.services import project_obligations


class ApplicationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner", password="a-long-test-password"
        )
        self.company = Company.objects.create(name="A", nit="1")
        self.other = Company.objects.create(name="B", nit="2")
        CompanyMember.objects.create(company=self.company, user=self.user, role="owner")
        self.account = BankAccount.objects.create(
            company=self.company,
            name="A",
            balance="100.00",
            balance_date=date(2026, 1, 1),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_company_isolation(self):
        self.assertEqual(
            self.client.get(f"/api/companies/{self.other.id}/dashboard/").status_code,
            404,
        )
        self.assertEqual(len(self.client.get("/api/companies/").json()), 1)

    def test_authentication_required(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/companies/").status_code, 403)

    def test_invalid_horizon(self):
        for value in ("0", "31", "abc", "90.5"):
            self.assertEqual(
                self.client.get(
                    f"/api/companies/{self.company.id}/dashboard/?horizon={value}"
                ).status_code,
                400,
            )

    def test_transaction_uniqueness(self):
        values = dict(
            account=self.account,
            external_id="1",
            date=date(2026, 1, 1),
            amount="10.00",
            description="Sale",
        )
        Transaction.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transaction.objects.create(**values)

    def test_exact_money_and_overdue_exclusion(self):
        as_of = date(2026, 1, 1)
        obligations = [
            SimpleNamespace(
                due_date=as_of + timedelta(days=1),
                direction="out",
                outstanding_amount=Decimal("100.10"),
            ),
            SimpleNamespace(due_date=as_of, direction="in", outstanding_amount=Decimal("500")),
        ]
        points = project_obligations(Decimal("100.00"), as_of, 30, obligations)
        self.assertEqual(len(points), 30)
        self.assertEqual(points[0]["balance"], "-0.10")
        self.assertEqual(points[-1]["balance"], "-0.10")

    def test_empty_company(self):
        self.account.delete()
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.id}/dashboard/").status_code,
            409,
        )

    def test_real_login_csrf_and_logout(self):
        client = APIClient(enforce_csrf_checks=True)
        payload = {"username": "owner", "password": "a-long-test-password"}
        self.assertEqual(client.post("/api/auth/login/", payload).status_code, 403)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(
            client.post("/api/auth/login/", payload, HTTP_X_CSRFTOKEN=token).status_code,
            200,
        )
        self.assertEqual(client.get("/api/auth/me/").status_code, 200)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token).status_code, 204)
        self.assertEqual(client.get("/api/auth/me/").status_code, 403)

    def test_mismatched_balance_dates(self):
        BankAccount.objects.create(
            company=self.company, name="Other", balance="50.00", balance_date=date(2026, 1, 2)
        )
        self.assertEqual(
            self.client.get(f"/api/companies/{self.company.id}/dashboard/").status_code, 409
        )

    def test_seed_is_idempotent_and_dashboard_matches_obligations(self):
        from io import StringIO
        from unittest.mock import patch

        from django.core.management import call_command
        from django.test import override_settings

        from apps.forecast.models import Obligation

        with (
            override_settings(DEBUG=True),
            patch.dict("os.environ", {"DEMO_PASSWORD": "test-demo-password"}),
        ):
            call_command("seed_demo", stdout=StringIO())
            call_command("seed_demo", stdout=StringIO())
        company = Company.objects.get(nit="SYNTHETIC-001")
        user = get_user_model().objects.get(username="demo")
        self.client.force_authenticate(user)
        self.assertEqual(Transaction.objects.filter(account__company=company).count(), 60)
        self.assertEqual(Obligation.objects.filter(company=company).count(), 5)
        for horizon in (30, 60, 90):
            response = self.client.get(f"/api/companies/{company.id}/dashboard/?horizon={horizon}")
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertEqual(Decimal(result["balance"]), Decimal("8500000"))
            self.assertEqual(Decimal(result["receivable"]), Decimal("5500000"))
            self.assertEqual(Decimal(result["payable"]), Decimal("12800000"))
            self.assertEqual(Decimal(result["minimum_balance"]), Decimal("-1200000"))
            self.assertEqual(len(result["points"]), horizon)
            self.assertEqual(Decimal(result["points"][-1]["balance"]), Decimal("1200000"))
            self.assertEqual(
                result["first_deficit"],
                (date.fromisoformat(result["as_of"]) + timedelta(days=23)).isoformat(),
            )

    def test_browser_origin_login(self):
        from django.test import override_settings

        client = APIClient(enforce_csrf_checks=True)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        payload = {"username": "owner", "password": "a-long-test-password"}
        with override_settings(CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:5173"]):
            self.assertEqual(
                client.post(
                    "/api/auth/login/",
                    payload,
                    HTTP_X_CSRFTOKEN=token,
                    HTTP_ORIGIN="https://untrusted.example",
                ).status_code,
                403,
            )
            self.assertEqual(
                client.post(
                    "/api/auth/login/", payload, HTTP_ORIGIN="http://127.0.0.1:5173"
                ).status_code,
                403,
            )
            self.assertEqual(
                client.post(
                    "/api/auth/login/",
                    payload,
                    HTTP_X_CSRFTOKEN=token,
                    HTTP_ORIGIN="http://127.0.0.1:5173",
                ).status_code,
                200,
            )
