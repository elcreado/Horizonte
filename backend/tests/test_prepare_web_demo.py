from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, Company
from apps.banking.models import ManualEntry, Transaction


@override_settings(DEBUG=True)
class PrepareWebDemoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="presenter", password="synthetic-test-password"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def invoke(self, **options):
        output = StringIO()
        call_command(
            "prepare_web_demo",
            username=self.user.username,
            as_of=date(2026, 9, 23),
            stdout=output,
            **options,
        )
        return output.getvalue()

    def test_dry_run_does_not_write_and_checks_environment(self):
        if connection.vendor != "sqlite":
            with self.assertRaises(CommandError):
                self.invoke(dry_run=True)
            return
        output = self.invoke(dry_run=True)
        self.assertIn("Simulación", output)
        self.assertFalse(Company.objects.exists())
        self.assertFalse(AuditLog.objects.exists())
        with override_settings(DEBUG=False), self.assertRaises(CommandError):
            self.invoke()
        with self.assertRaises(CommandError):
            call_command("prepare_web_demo", username="unknown", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command(
                "prepare_web_demo",
                username=self.user.username,
                as_of=date(9999, 1, 1),
                stdout=StringIO(),
            )
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.assertRaises(CommandError):
            self.invoke(dry_run=True)
        self.assertFalse(Company.objects.exists())

    def test_repeated_preparation_preserves_existing_data_and_matches_demo(self):
        if connection.vendor != "sqlite":
            self.skipTest("El preparador de demo solo admite SQLite local.")
        previous = Company.objects.create(name="Existing company", nit="existing-demo")
        old_password = self.user.password
        self.invoke()
        obligations = Company.objects.filter(name__startswith="Demo V1 Obligaciones").get()
        manual = Company.objects.filter(name__startswith="Demo V1 Historial manual").get()
        result = self.client.get(f"/api/companies/{obligations.pk}/dashboard/?horizon=30").json()
        self.assertEqual(Decimal(result["points"][-1]["balance"]), Decimal("-81000"))
        self.assertEqual(result["first_deficit"], "2026-10-08")
        self.assertEqual(result["liquidity_alert"]["shortfall_at_minimum"], "181000.00")
        for horizon, expected in [(30, "200000"), (60, "-100000"), (90, "-400000")]:
            result = self.client.get(
                f"/api/companies/{manual.pk}/experimental-forecast/?method=manual_average&horizon={horizon}"
            )
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(Decimal(result.data["points"][-1]["balance"]), Decimal(expected))
        before = list(Transaction.objects.values())
        self.assertEqual(ManualEntry.objects.count(), 2)
        self.invoke()
        self.assertEqual(Company.objects.count(), 5)
        self.assertTrue(Company.objects.filter(pk=previous.pk, name="Existing company").exists())
        self.assertEqual(
            list(Transaction.objects.filter(pk__in=[row["id"] for row in before]).values()), before
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, old_password)
        self.assertEqual(AuditLog.objects.filter(action="demo.prepared").count(), 4)

    def test_preparation_rolls_back_whole_batch_on_failure(self):
        if connection.vendor != "sqlite":
            self.skipTest("El preparador de demo solo admite SQLite local.")
        with patch(
            "apps.accounts.management.commands.prepare_web_demo.ManualEntry.objects.create",
            side_effect=RuntimeError("interrupted"),
        ):
            with self.assertRaises(RuntimeError):
                self.invoke()
        self.assertFalse(Company.objects.exists())
        self.assertFalse(Transaction.objects.exists())
        self.assertFalse(AuditLog.objects.exists())
