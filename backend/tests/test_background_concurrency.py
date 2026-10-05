from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings

from apps.accounts.models import BackgroundTask
from apps.accounts.tasks import send_password_recovery
from config.background import enqueue, run_one


@skipUnless(connection.vendor == "postgresql", "Locks concurrentes requieren PostgreSQL.")
@override_settings(BACKGROUND_MODE="database")
class BackgroundConcurrencyTests(TransactionTestCase):
    def test_concurrent_workers_claim_each_message_once(self):
        messages = [enqueue(send_password_recovery, args=[index]) for index in range(12)]
        seen = []
        lock = Lock()

        def consume(index):
            with lock:
                seen.append(index)

        def worker(_):
            close_old_connections()
            try:
                return run_one()
            finally:
                close_old_connections()

        registry = {send_password_recovery.name: SimpleNamespace(run=consume)}
        with patch("config.background.task_registry", return_value=registry):
            with ThreadPoolExecutor(max_workers=4) as pool:
                claimed = list(pool.map(worker, range(12)))
        self.assertTrue(all(claimed))
        self.assertEqual(sorted(seen), list(range(12)))
        self.assertEqual(BackgroundTask.objects.filter(status="completed").count(), len(messages))
        self.assertTrue(
            all(row.attempts == 1 and row.args == [] for row in BackgroundTask.objects.all())
        )
