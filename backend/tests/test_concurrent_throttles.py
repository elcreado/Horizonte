from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest import skipUnless

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase

from apps.accounts.models import RateLimitBucket
from apps.accounts.views import LoginThrottle


@skipUnless(connection.vendor == "postgresql", "Requiere locks PostgreSQL")
class ConcurrentThrottleTests(TransactionTestCase):
    def test_first_bucket_creation_and_increments_enforce_exact_limit(self):
        barrier = Barrier(16)

        def attempt():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET statement_timeout = '20s'")
                request = SimpleNamespace(
                    user=SimpleNamespace(is_authenticated=False),
                    META={"REMOTE_ADDR": "192.0.2.10"},
                )
                barrier.wait(timeout=10)
                return LoginThrottle().allow_request(request, None)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=16) as executor:
            attempts = [executor.submit(attempt) for _ in range(16)]
            results = [future.result(timeout=30) for future in attempts]
        self.assertEqual(sum(results), 10)
        self.assertEqual(RateLimitBucket.objects.count(), 1)
        self.assertEqual(RateLimitBucket.objects.get().requests, 10)
