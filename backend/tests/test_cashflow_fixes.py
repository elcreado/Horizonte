from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings

from apps.banking.models import ImportJob, Transaction
from apps.forecast.models import MonthlyOccurrence, MonthlySchedule, Obligation
from apps.forecast.monthly import materialize_monthly
from tests.test_imports import ImportTests


class CashflowFixTests(TestCase):
    setUp = ImportTests.setUp

    def test_manual_entry_changes_summary_without_adding_history_to_balance(self):
        url = f"/api/companies/{self.company.pk}/dashboard/"
        before = self.client.get(url).json()
        response = self.client.post(
            f"/api/companies/{self.company.pk}/movements/",
            {
                "request_id": str(uuid4()),
                "account_id": self.account.pk,
                "date": str(self.account.balance_date),
                "amount": "70",
                "direction": "out",
                "description": "Compra",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        after = self.client.get(url).json()
        self.assertEqual(after["balance"], "500.00")
        self.assertNotEqual(before["points"], after["points"])
        self.assertEqual(after["points"][-1]["balance"], "200.00")
        # A new operation after the declared cut updates available cash exactly once.
        Transaction.objects.create(
            account=self.account,
            external_id="later",
            date=self.account.balance_date + timedelta(days=1),
            amount="50",
            description="Venta",
        )
        after = self.client.get(url).json()
        self.assertEqual(after["balance"], "550.00")
        evaluation = self.client.post(
            f"/api/companies/{self.company.pk}/alert-history/", {"horizon": 30}, format="json"
        )
        self.assertEqual(evaluation.data["result"], after["liquidity_alert"])

    def test_monthly_schedule_idempotent_calendar_forecast_and_cancellation(self):
        base = f"/api/companies/{self.company.pk}/monthly-schedules/"
        payload = {
            "request_id": str(uuid4()),
            "description": "Sueldos",
            "direction": "out",
            "amount": "100",
            "day": 1,
            "start_date": "2026-10-01",
        }
        with patch("apps.forecast.monthly.timezone.localdate", return_value=date(2026, 9, 23)):
            result = self.client.post(base, payload, format="json")
            self.assertEqual(result.status_code, 201, result.data)
            self.assertEqual(self.client.post(base, payload, format="json").status_code, 200)
            self.assertEqual(MonthlySchedule.objects.count(), 1)
            count = MonthlyOccurrence.objects.count()
            materialize_monthly(self.company.pk, date(2026, 12, 31))
            self.assertEqual(MonthlyOccurrence.objects.count(), count)
            calendar = self.client.get(
                f"/api/companies/{self.company.pk}/obligation-calendar/?month=2026-10"
            ).json()
            self.assertEqual(calendar["days"][0]["payable"], "100")
            dashboard = self.client.get(
                f"/api/companies/{self.company.pk}/dashboard/?horizon=90"
            ).json()
            self.assertEqual(Decimal(dashboard["payable"]), Decimal("300"))
            self.assertEqual(Decimal(dashboard["points"][-1]["balance"]), Decimal("200"))
            identifier = result.data["id"]
            response = self.client.post(f"{base}{identifier}/cancel/", {}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.data["active"])
            materialize_monthly(self.company.pk, date(2027, 12, 31))
            self.assertEqual(MonthlyOccurrence.objects.count(), count)
            self.assertFalse(Obligation.objects.filter(cancelled=False).exists())

    def test_month_end_leap_year_and_permissions(self):
        base = f"/api/companies/{self.company.pk}/monthly-schedules/"
        payload = {
            "request_id": str(uuid4()),
            "description": "Arriendo",
            "amount": "10",
            "day": 31,
            "start_date": "2028-01-01",
            "end_date": "2028-03-31",
        }
        with patch("apps.forecast.monthly.timezone.localdate", return_value=date(2028, 1, 1)):
            result = self.client.post(base, payload, format="json")
            self.assertEqual(result.status_code, 201)
            self.assertEqual(
                list(MonthlyOccurrence.objects.order_by("date").values_list("date", flat=True)),
                [date(2028, 1, 31), date(2028, 2, 29), date(2028, 3, 31)],
            )
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.client.post(base, payload, format="json").status_code, 403)
        self.assertEqual(
            self.client.post(f"{base}{result.data['id']}/cancel/", {}, format="json").status_code,
            403,
        )

    def test_schedule_continues_all_months_after_a_long_gap(self):
        base = f"/api/companies/{self.company.pk}/monthly-schedules/"
        payload = {
            "request_id": str(uuid4()),
            "description": "Nómina",
            "amount": "10",
            "day": 1,
            "start_date": "2026-10-01",
        }
        with patch("apps.forecast.monthly.timezone.localdate", return_value=date(2026, 10, 1)):
            result = self.client.post(base, payload, format="json")
            self.assertEqual(result.status_code, 201)
        with patch("apps.forecast.monthly.timezone.localdate", return_value=date(2030, 1, 1)):
            materialize_monthly(self.company.pk, date(2030, 3, 1))
        dates = list(MonthlyOccurrence.objects.order_by("date").values_list("date", flat=True))
        self.assertIn(date(2028, 1, 1), dates)
        self.assertIn(date(2029, 1, 1), dates)
        self.assertEqual(dates[-1], date(2030, 3, 1))
        self.assertEqual(len(dates), 42)

    def test_monthly_validation_and_foreign_company_access(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import Company

        url = f"/api/companies/{self.company.pk}/monthly-schedules/"
        base = {
            "request_id": str(uuid4()),
            "description": "Sueldo",
            "amount": "10",
            "day": 1,
            "start_date": "2026-10-01",
        }
        for changes in [
            {"day": 0},
            {"day": 32},
            {"amount": "0"},
            {"amount": "NaN"},
            {"end_date": "2026-09-01"},
        ]:
            self.assertEqual(
                self.client.post(url, {**base, **changes}, format="json").status_code, 400
            )
        other = Company.objects.create(name="Other", nit="monthly-other")
        self.assertEqual(
            self.client.post(
                f"/api/companies/{other.pk}/monthly-schedules/", base, format="json"
            ).status_code,
            404,
        )
        secure = APIClient(enforce_csrf_checks=True)
        secure.force_login(self.user)
        self.assertEqual(secure.post(url, base, format="json").status_code, 403)
        self.assertFalse(MonthlySchedule.objects.exists())

    @override_settings(BACKGROUND_MODE="database")
    def test_downloaded_example_processes_through_real_queue(self):
        from pathlib import Path

        from config.background import run_one

        raw = Path("frontend/public/movimientos-ejemplo.csv").read_bytes()
        response = self.client.post(
            self.url,
            {"account_id": self.account.pk, "file": SimpleUploadedFile("ejemplo.csv", raw)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 202)
        self.assertTrue(run_one())
        job = ImportJob.objects.get(pk=response.data["id"])
        self.assertEqual(job.status, "completed", job.error)
        self.assertEqual(job.created_count, 2)
        self.assertEqual(Transaction.objects.count(), 2)
        self.client.post(
            self.url,
            {"account_id": self.account.pk, "file": SimpleUploadedFile("ejemplo.csv", raw)},
            format="multipart",
        )
        run_one()
        self.assertEqual(Transaction.objects.count(), 2)


class LocalWorkerTests(SimpleTestCase):
    @override_settings(DEBUG=True, BACKGROUND_MODE="database")
    def test_runserver_starts_and_stops_worker(self):
        from apps.accounts.management.commands.runserver import Command

        with (
            patch("apps.accounts.management.commands.runserver.subprocess.Popen") as process,
            patch("django.core.management.commands.runserver.Command.inner_run"),
        ):
            Command().inner_run()
            self.assertEqual(process.call_count, 1)
            self.assertIn("run_background", process.call_args.args[0])
            process.return_value.terminate.assert_called_once()
            process.return_value.wait.assert_called_once()
