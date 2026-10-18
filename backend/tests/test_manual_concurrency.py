"""Exercise cross-user idempotency with real PostgreSQL row locks."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.banking.models import BankAccount, ManualEntry, Transaction


@skipUnless(
    connection.vendor == "postgresql",
    "Requiere bloqueos de PostgreSQL; SQLite no acredita concurrencia.",
)
class ConcurrentManualEntryTests(TransactionTestCase):
    def test_same_request_from_two_members_creates_one_transaction(self):
        company = Company.objects.create(name="Concurrent demo", nit="concurrent-manual")
        users = [
            get_user_model().objects.create_user(username=name)
            for name in ("owner-concurrent", "accountant-concurrent")
        ]
        for user, role in zip(users, ("owner", "accountant"), strict=True):
            CompanyMember.objects.create(company=company, user=user, role=role)
        account = BankAccount.objects.create(
            company=company, name="Caja", balance=500, balance_date=timezone.localdate()
        )
        body = {
            "request_id": str(uuid4()),
            "account_id": account.pk,
            "date": str(account.balance_date),
            "direction": "out",
            "amount": "10.00",
            "description": "Operación concurrente",
        }
        barrier = Barrier(2)

        def submit(user_id):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(get_user_model().objects.get(pk=user_id))
                barrier.wait(timeout=10)
                response = client.post(
                    f"/api/companies/{company.pk}/movements/", body, format="json"
                )
                return response.status_code, response.json()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(submit, user.pk) for user in users]
            results = [future.result(timeout=20) for future in futures]
        self.assertEqual(sorted(status for status, _ in results), [200, 201])
        self.assertEqual(len({body["id"] for _, body in results}), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(ManualEntry.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="transaction.manual_created").count(), 1)
        self.assertEqual(Transaction.objects.get().amount, Decimal("-10.00"))
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal("500.00"))
