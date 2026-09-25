import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.banking.models import BankAccount, Transaction
from apps.forecast.models import Obligation, Settlement


class ObligationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="finance")
        self.company = Company.objects.create(name="Finance", nit="finance")
        self.other = Company.objects.create(name="Other", nit="other")
        self.member = CompanyMember.objects.create(
            user=self.user, company=self.company, role="owner"
        )
        self.account = BankAccount.objects.create(
            company=self.company, name="Account", balance=500, balance_date=date(2026, 9, 23)
        )
        self.movement = Transaction.objects.create(
            account=self.account,
            external_id="payment",
            date=date(2026, 9, 20),
            amount=100,
            description="Customer payment",
        )
        self.obligation = Obligation.objects.create(
            company=self.company,
            reference="invoice",
            description="Sale",
            direction="in",
            due_date=date(2026, 10, 1),
            outstanding_amount=150,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.base = f"/api/companies/{self.company.id}/obligations/"
        self.url = f"{self.base}{self.obligation.id}/settlements/"

    def pay(self, amount="50.00", request_id=None, movement=None, url=None):
        return self.client.post(
            url or self.url,
            {
                "amount": amount,
                "transaction_id": (movement or self.movement).id,
                "request_id": str(request_id or uuid.uuid4()),
            },
            format="json",
        )

    def test_partial_idempotent_and_reversible(self):
        attempt = uuid.uuid4()
        first = self.pay(request_id=attempt)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.pay(request_id=attempt).status_code, 200)
        self.obligation.refresh_from_db()
        self.assertEqual(self.obligation.outstanding_amount, Decimal("100"))
        self.assertEqual(Settlement.objects.count(), 1)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("500"))
        reverse = f"{self.url}{first.json()['id']}/reverse/"
        self.assertEqual(self.client.post(reverse).status_code, 200)
        self.assertEqual(self.client.post(reverse).status_code, 200)
        self.obligation.refresh_from_db()
        self.assertEqual(self.obligation.outstanding_amount, Decimal("150"))
        self.assertEqual(AuditLog.objects.count(), 2)

    def test_overallocation_across_obligations_rejected(self):
        self.assertEqual(self.pay("70").status_code, 201)
        other = Obligation.objects.create(
            company=self.company,
            reference="second",
            description="Second sale",
            direction="in",
            due_date=date(2026, 10, 2),
            outstanding_amount=100,
        )
        self.assertEqual(self.pay("31", url=f"{self.base}{other.id}/settlements/").status_code, 400)
        self.assertEqual(self.pay("30", url=f"{self.base}{other.id}/settlements/").status_code, 201)
        candidates = self.client.get(f"{self.base}{other.id}/candidates/").json()
        self.assertEqual(candidates["count"], 0)

    def test_direction_tenant_and_role(self):
        self.movement.amount = -100
        self.movement.save()
        self.assertEqual(self.pay().status_code, 400)
        foreign_account = BankAccount.objects.create(
            company=self.other, name="Other", balance=0, balance_date=date(2026, 9, 23)
        )
        foreign = Transaction.objects.create(
            account=foreign_account,
            external_id="foreign",
            date=date(2026, 9, 1),
            amount=100,
            description="Foreign",
        )
        self.assertEqual(self.pay(movement=foreign).status_code, 404)
        self.assertEqual(
            self.client.get(f"/api/companies/{self.other.id}/obligations/").status_code, 404
        )
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.pay().status_code, 403)
        self.assertEqual(
            self.client.patch(
                f"{self.base}{self.obligation.id}/", {"cancelled": True}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(Settlement.objects.count(), 0)

    def test_cancelled_excluded_from_dashboard_and_reactivation(self):
        url = f"{self.base}{self.obligation.id}/"
        self.assertEqual(
            self.client.patch(url, {"cancelled": True}, format="json").status_code, 200
        )
        self.assertEqual(self.pay().status_code, 400)
        dashboard = self.client.get(f"/api/companies/{self.company.id}/dashboard/").json()
        self.assertEqual(Decimal(dashboard["receivable"]), 0)
        self.client.patch(url, {"cancelled": False}, format="json")
        dashboard = self.client.get(f"/api/companies/{self.company.id}/dashboard/").json()
        self.assertEqual(Decimal(dashboard["receivable"]), 150)

    def test_create_validate_audit_and_duplicate_reference(self):
        payload = {
            "reference": "manual",
            "description": "Invoice",
            "counterparty": "Client",
            "direction": "out",
            "due_date": "2026-10-01",
            "outstanding_amount": "12.30",
        }
        self.assertEqual(self.client.post(self.base, payload, format="json").status_code, 201)
        self.assertEqual(self.client.post(self.base, payload, format="json").status_code, 400)
        payload["reference"] = "bad"
        payload["outstanding_amount"] = "-1"
        self.assertEqual(self.client.post(self.base, payload, format="json").status_code, 400)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_pending_not_directly_editable(self):
        self.assertEqual(
            self.client.patch(
                f"{self.base}{self.obligation.id}/", {"outstanding_amount": "0"}, format="json"
            ).status_code,
            400,
        )

    def test_attempt_conflict(self):
        attempt = uuid.uuid4()
        self.pay(request_id=attempt)
        self.assertEqual(self.pay("40", request_id=attempt).status_code, 400)

    def test_future_movement_rejected(self):
        self.movement.date = date(2026, 10, 1)
        self.movement.save()
        self.assertEqual(self.pay().status_code, 400)
