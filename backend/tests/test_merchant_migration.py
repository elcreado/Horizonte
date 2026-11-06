from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MerchantBackfillTests(TransactionTestCase):
    def test_existing_explicit_label_is_linked_without_changing_original(self):
        before = [("banking", "0008_bankconnection_bankaccount_connection_bankconsent_and_more")]
        after = [("banking", "0010_backfill_merchants")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            company = old.get_model("accounts", "Company").objects.create(
                name="Migration", nit="migration-merchant"
            )
            account = old.get_model("banking", "BankAccount").objects.create(
                company_id=company.pk,
                name="Cuenta",
                balance="100.00",
                balance_date=date(2026, 9, 23),
            )
            row = old.get_model("banking", "Transaction").objects.create(
                account_id=account.pk,
                external_id="historic-merchant",
                date=date(2026, 9, 1),
                amount="-10.00",
                description="Pago; Comercio: Café 24",
                merchant_name="CAFE 24",
            )
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            current = executor.loader.project_state(after).apps
            migrated = current.get_model("banking", "Transaction").objects.get(pk=row.pk)
            self.assertEqual(migrated.description, "Pago; Comercio: Café 24")
            self.assertEqual(migrated.merchant.normalized_name, "CAFE 24")
            self.assertEqual(
                current.get_model("banking", "MerchantAlias").objects.get().provider,
                "manual_upload",
            )
        finally:
            MigrationExecutor(connection).migrate(after)
