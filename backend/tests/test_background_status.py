import json
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import BackgroundTask


class BackgroundStatusTests(TestCase):
    @override_settings(BACKGROUND_MODE="database")
    def test_pending_leases_are_distinguished_without_disclosing_arguments(self):
        now = timezone.now()
        for state, available in (
            ("queued", now),
            ("queued", now + timedelta(hours=1)),
            ("running", now - timedelta(minutes=1)),
            ("running", now + timedelta(minutes=1)),
        ):
            BackgroundTask.objects.create(
                name="private", args=["private-link"], status=state, available_at=available
            )
        output = StringIO()
        call_command("background_status", stdout=output)
        report = json.loads(output.getvalue())
        self.assertEqual(report["queued"], 2)
        self.assertEqual(report["ready"], 1)
        self.assertEqual(report["running"], 2)
        self.assertEqual(report["expired_leases"], 1)
        self.assertNotIn("private", output.getvalue())
        self.assertFalse(BackgroundTask.objects.filter(status="completed").exists())
