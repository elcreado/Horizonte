from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase

from apps.banking.models import ImportJob, Transaction
from apps.banking.tasks import import_csv
from tests.test_imports import HEADER, ImportTests


@skipUnless(connection.vendor == "postgresql", "Requiere locks PostgreSQL")
class ConcurrentImportTests(TransactionTestCase):
    setUp = ImportTests.setUp
    job = ImportTests.job

    def run_jobs(self, identifiers):
        barrier = Barrier(len(identifiers))

        def execute(identifier):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET statement_timeout = '20s'")
                barrier.wait(timeout=10)
                import_csv(identifier)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(identifiers)) as executor:
            futures = [executor.submit(execute, identifier) for identifier in identifiers]
            for future in futures:
                future.result(timeout=30)

    def test_overlapping_jobs_and_same_job_redelivery(self):
        content = HEADER + "".join(f"same-{i},2026-09-01,1.00,Venta\n" for i in range(200))
        first, second = self.job(content), self.job(content)
        self.run_jobs([first.pk, second.pk, first.pk])
        jobs = list(ImportJob.objects.order_by("pk"))
        self.assertTrue(all(job.status == "completed" for job in jobs))
        self.assertEqual(sum(job.created_count for job in jobs), 200)
        self.assertEqual(sum(job.duplicate_count for job in jobs), 200)
        self.assertEqual(Transaction.objects.count(), 200)
        self.account.refresh_from_db()
        self.assertEqual(str(self.account.balance), "500.00")

    def test_conflicting_jobs_leave_only_winner_data(self):
        first = self.job(
            HEADER + "shared,2026-09-01,1.00,Venta\nonly-first,2026-09-01,1.00,Venta\n"
        )
        second = self.job(
            HEADER + "shared,2026-09-01,2.00,Venta\nonly-second,2026-09-01,2.00,Venta\n"
        )
        self.run_jobs([first.pk, second.pk])
        self.assertEqual(ImportJob.objects.filter(status="completed").count(), 1)
        self.assertEqual(ImportJob.objects.filter(status="failed").count(), 1)
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertEqual(len(set(Transaction.objects.values_list("amount", flat=True))), 1)
