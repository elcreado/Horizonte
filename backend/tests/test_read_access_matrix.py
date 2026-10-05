"""Las operaciones de empresa deben rechazar sesiones ajenas o ausentes."""

import re
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, Merchant, Transaction
from apps.forecast.models import Obligation, Settlement
from config.api_inventory import build_inventory


class ReadAccessMatrixTests(TestCase):
    def test_foreign_financial_objects_and_nested_settlements_are_isolated(self):
        own = Company.objects.create(name="Own", nit="financial-own")
        foreign = Company.objects.create(name="Foreign", nit="financial-foreign")
        user = get_user_model().objects.create_user("financial-owner")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        account = BankAccount.objects.create(
            company=foreign, name="Foreign", balance="100", balance_date="2026-01-01"
        )
        movement = Transaction.objects.create(
            account=account,
            external_id="foreign",
            date="2026-01-01",
            amount="100",
            description="Foreign payment",
        )
        fields = dict(direction="in", due_date="2026-01-01", outstanding_amount="50")
        foreign_obligation = Obligation.objects.create(
            company=foreign, reference="private", description="Private", **fields
        )
        own_obligation = Obligation.objects.create(
            company=own, reference="own", description="Own", **fields
        )
        payment = Settlement.objects.create(
            obligation=foreign_obligation,
            transaction=movement,
            user=user,
            amount="50",
            request_id=uuid.uuid4(),
        )
        client = APIClient()
        client.force_authenticate(user)
        root = f"/api/companies/{own.pk}/obligations/"
        for suffix in ("candidates/", "settlements/", "history/"):
            with self.subTest(read=suffix):
                self.assertEqual(
                    client.get(f"{root}{foreign_obligation.pk}/{suffix}").status_code, 404
                )
        self.assertEqual(
            client.patch(
                f"{root}{foreign_obligation.pk}/", {"description": "Changed"}, format="json"
            ).status_code,
            404,
        )
        payload = {"transaction_id": movement.pk, "amount": "10", "request_id": str(uuid.uuid4())}
        for obligation in (foreign_obligation, own_obligation):
            with self.subTest(settle=obligation.pk):
                self.assertEqual(
                    client.post(
                        f"{root}{obligation.pk}/settlements/", payload, format="json"
                    ).status_code,
                    404,
                )
            with self.subTest(reverse=obligation.pk):
                self.assertEqual(
                    client.post(
                        f"{root}{obligation.pk}/settlements/{payment.pk}/reverse/",
                        {},
                        format="json",
                    ).status_code,
                    404,
                )
        foreign_obligation.refresh_from_db()
        own_obligation.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(foreign_obligation.description, "Private")
        self.assertEqual(foreign_obligation.outstanding_amount, 50)
        self.assertEqual(own_obligation.outstanding_amount, 50)
        self.assertIsNone(payment.reversed_at)
        self.assertEqual(Settlement.objects.count(), 1)

    def test_session_cookie_cannot_mutate_any_company_route_without_csrf(self):
        company = Company.objects.create(name="CSRF", nit="csrf-matrix")
        user = get_user_model().objects.create_user("csrf-matrix", password="synthetic-test-pass")
        CompanyMember.objects.create(company=company, user=user, role="owner")
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=user.username, password="synthetic-test-pass"))
        checked = 0
        for path, operations in build_inventory()["paths"].items():
            if "{company_id}" not in path:
                continue
            url = re.sub(r"\{[^}]+\}", "1", path.replace("{company_id}", str(company.pk)))
            for method in ("post", "patch", "put", "delete"):
                if method not in operations:
                    continue
                with self.subTest(path=path, method=method):
                    response = getattr(client, method)(url, {}, format="json")
                    self.assertEqual(response.status_code, 403)
                    self.assertIn("CSRF", response.json()["detail"])
                checked += 1
        self.assertGreaterEqual(checked, 20)

    def test_existing_foreign_objects_cannot_be_written_through_own_company(self):
        own = Company.objects.create(name="Own", nit="object-matrix-own")
        foreign = Company.objects.create(name="Foreign", nit="object-matrix-foreign")
        user = get_user_model().objects.create_user("object-matrix-user")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        account = BankAccount.objects.create(
            company=foreign, name="Foreign account", balance="123.45", balance_date="2026-01-01"
        )
        merchant = Merchant.objects.create(
            company=foreign, normalized_name="foreign", display_name="Foreign merchant"
        )
        movement = Transaction.objects.create(
            account=account,
            external_id="foreign",
            date="2026-01-01",
            amount="10",
            description="Foreign movement",
            category="Otros",
        )
        client = APIClient()
        client.force_authenticate(user)
        cases = [
            (
                "patch",
                f"accounts/{account.pk}/balance/",
                {"balance": "999", "balance_date": "2026-01-01"},
            ),
            (
                "post",
                f"accounts/{account.pk}/coverage/",
                {"start": "2025-01-01", "confirmed": True},
            ),
            ("patch", f"merchants/{merchant.pk}/name/", {"display_name": "Changed"}),
            ("patch", f"movements/{movement.pk}/category/", {"category": "Software"}),
        ]
        for method, suffix, payload in cases:
            with self.subTest(endpoint=suffix):
                response = getattr(client, method)(
                    f"/api/companies/{own.pk}/{suffix}", payload, format="json"
                )
                self.assertEqual(response.status_code, 404)
        account.refresh_from_db()
        merchant.refresh_from_db()
        movement.refresh_from_db()
        self.assertEqual(str(account.balance), "123.45")
        self.assertIsNone(account.history_complete_from)
        self.assertEqual(merchant.display_name, "Foreign merchant")
        self.assertEqual(movement.category, "Otros")

    def test_every_company_get_rejects_another_tenant_and_anonymous_session(self):
        own = Company.objects.create(name="Own", nit="read-matrix-own")
        foreign = Company.objects.create(name="Foreign", nit="read-matrix-foreign")
        user = get_user_model().objects.create_user("read-matrix-user")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        client = APIClient()
        checked = []
        for path, operations in build_inventory()["paths"].items():
            if "{company_id}" not in path or "get" not in operations:
                continue
            url = re.sub(r"\{[^}]+\}", "1", path.replace("{company_id}", str(foreign.pk)))
            with self.subTest(path=path, session="foreign"):
                client.force_authenticate(user)
                self.assertEqual(client.get(url).status_code, 404)
            with self.subTest(path=path, session="anonymous"):
                client.force_authenticate(None)
                self.assertEqual(client.get(url).status_code, 403)
            checked.append(path)
        self.assertGreaterEqual(len(checked), 20)

    def test_company_mutations_reject_foreign_and_anonymous_sessions(self):
        own = Company.objects.create(name="Own", nit="write-matrix-own")
        foreign = Company.objects.create(name="Foreign", nit="write-matrix-foreign")
        user = get_user_model().objects.create_user("write-matrix-user")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        client = APIClient()
        checked = []
        for path, operations in build_inventory()["paths"].items():
            if "{company_id}" not in path:
                continue
            url = re.sub(r"\{[^}]+\}", "1", path.replace("{company_id}", str(foreign.pk)))
            for method in ("post", "patch", "put", "delete"):
                if method not in operations:
                    continue
                with self.subTest(path=path, method=method, session="foreign"):
                    client.force_authenticate(user)
                    response = getattr(client, method)(url, {}, format="json")
                    self.assertIn(response.status_code, (403, 404))
                with self.subTest(path=path, method=method, session="anonymous"):
                    client.force_authenticate(None)
                    self.assertEqual(
                        getattr(client, method)(url, {}, format="json").status_code, 403
                    )
                checked.append((path, method))
        self.assertGreaterEqual(len(checked), 20)
