from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.banking.models import BankAccount, Transaction
from apps.forecast.models import ForecastRun, Obligation, RecurrenceReview
from tests.test_imports import ImportTests


class HybridRecurrenceTests(TestCase):
    setUp = ImportTests.setUp

    def prepare(self):
        cutoff = self.account.balance_date
        start = cutoff - timedelta(days=89)
        for offset in range(90):
            Transaction.objects.create(
                account=self.account,
                external_id=f"variable-{offset}",
                date=start + timedelta(days=offset),
                amount="1",
                description="Variable",
            )
        for day in (date(2026, 6, 30), date(2026, 7, 31), date(2026, 8, 31)):
            Transaction.objects.create(
                account=self.account,
                external_id=f"rent-{day}",
                date=day,
                amount="-20",
                description="Arriendo",
            )
        self.account.history_complete_from = start
        self.account.history_complete_through = cutoff
        self.account.save()
        self.rec_url = f"/api/companies/{self.company.pk}/recurrences/?horizon=90"
        candidate = self.client.get(self.rec_url).data["results"][0]
        response = self.client.post(
            self.rec_url,
            {"fingerprint": candidate["fingerprint"], "status": "confirmed"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.candidate = candidate
        self.url = f"/api/companies/{self.company.pk}/experimental-forecast/?horizon=90&method=hybrid_weekly"

    def test_unlinked_confirmed_pattern_projects_without_creating_obligations(self):
        self.prepare()
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["estimated_recurrence_occurrences"], 3)
        self.assertEqual(result.data["excluded_recurring_movements"], 3)
        estimated = [
            (row["date"], Decimal(row["recurring_flow"]))
            for row in result.data["points"]
            if Decimal(row["recurring_flow"])
        ]
        self.assertEqual(
            estimated,
            [
                ("2026-09-30", Decimal(-20)),
                ("2026-10-31", Decimal(-20)),
                ("2026-11-30", Decimal(-20)),
            ],
        )
        self.assertEqual(Decimal(result.data["points"][-1]["balance"]), Decimal(530))
        self.assertFalse(Obligation.objects.exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal(500))
        save = self.client.post(
            f"/api/companies/{self.company.pk}/forecast-runs/",
            {"horizon": 90, "method": "hybrid_weekly"},
            format="json",
        )
        self.assertEqual(save.status_code, 201)
        self.assertEqual(ForecastRun.objects.get().evidence["version"], "hybrid_weekly_v2")

    def test_quantiles_require_long_coverage_and_saved_runs_preserve_inputs(self):
        self.prepare()
        short = self.client.get(self.url)
        self.assertEqual(short.data["quantiles"]["status"], "unavailable")
        self.assertNotIn("p10", short.data["points"][0])
        cutoff = self.account.balance_date
        self.account.history_complete_from = cutoff - timedelta(days=269)
        self.account.save()
        Transaction.objects.bulk_create(
            [
                Transaction(
                    account=self.account,
                    external_id=f"older-{offset}",
                    date=cutoff - timedelta(days=offset),
                    amount="1",
                    description="Variable",
                )
                for offset in range(90, 270)
            ]
        )
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["quantiles"]["status"], "experimental")
        for point in result.data["points"]:
            self.assertLessEqual(Decimal(point["p10"]), Decimal(point["p50"]))
            self.assertLessEqual(Decimal(point["p50"]), Decimal(point["p90"]))
        saved = self.client.post(
            f"/api/companies/{self.company.pk}/forecast-runs/",
            {"horizon": 90, "method": "hybrid_weekly"},
            format="json",
        )
        self.assertEqual(saved.status_code, 201)
        run = ForecastRun.objects.get()
        self.assertEqual(len(run.evidence["quantile_inputs"]["training_series"]), 270)
        self.assertEqual(run.result["points"], result.data["points"])
        repeat = self.client.post(
            f"/api/companies/{self.company.pk}/forecast-runs/",
            {"horizon": 90, "method": "hybrid_weekly"},
            format="json",
        )
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(ForecastRun.objects.count(), 1)
        Transaction.objects.filter(account=self.account, external_id="older-200").update(
            amount="999"
        )
        changed = self.client.post(
            f"/api/companies/{self.company.pk}/forecast-runs/",
            {"horizon": 90, "method": "hybrid_weekly"},
            format="json",
        )
        self.assertEqual(changed.status_code, 201)
        run.refresh_from_db()
        self.assertEqual(run.result["points"], result.data["points"])
        self.assertNotEqual(
            changed.data["evidence"]["source_digest"], run.evidence["source_digest"]
        )
        self.assertNotEqual(
            changed.data["evidence"]["quantile_inputs"], run.evidence["quantile_inputs"]
        )
        BankAccount.objects.create(
            company=self.company,
            name="Cobertura corta",
            balance=0,
            balance_date=cutoff,
            history_complete_from=cutoff - timedelta(days=89),
            history_complete_through=cutoff,
        )
        limited = self.client.get(self.url)
        self.assertEqual(limited.status_code, 200)
        self.assertEqual(limited.data["quantiles"]["status"], "unavailable")
        self.assertNotIn("p10", limited.data["points"][0])

    def test_ambiguous_obligation_blocks_then_linked_partial_and_cancelled_are_not_duplicated(self):
        self.prepare()
        obligation = Obligation.objects.create(
            company=self.company,
            reference="manual-partial",
            description="Arriendo",
            direction="out",
            due_date=date(2026, 9, 30),
            outstanding_amount=5,
        )
        self.assertEqual(self.client.get(self.url).status_code, 409)
        linked = self.client.post(
            self.rec_url,
            {
                "fingerprint": self.candidate["fingerprint"],
                "status": "link",
                "occurrence_date": "2026-09-30",
                "obligation_id": obligation.pk,
            },
            format="json",
        )
        self.assertEqual(linked.status_code, 201)
        result = self.client.get(self.url).data
        self.assertEqual(result["estimated_recurrence_occurrences"], 2)
        self.assertEqual(Decimal(result["points"][-1]["balance"]), Decimal(545))
        obligation.cancelled = True
        obligation.save()
        result = self.client.get(self.url).data
        self.assertEqual(Decimal(result["points"][-1]["balance"]), Decimal(550))
        obligation.cancelled = False
        obligation.outstanding_amount = 0
        obligation.save()
        self.assertEqual(
            Decimal(self.client.get(self.url).data["points"][-1]["balance"]), Decimal(550)
        )

    def test_rejected_or_stale_pattern_stops_recurring_estimates(self):
        self.prepare()
        RecurrenceReview.objects.update(status="rejected")
        result = self.client.get(self.url).data
        self.assertEqual(result["estimated_recurrence_occurrences"], 0)
        self.assertEqual(result["excluded_recurring_movements"], 0)
        RecurrenceReview.objects.update(status="confirmed")
        Transaction.objects.filter(external_id="rent-2026-08-31").update(amount=-40)
        result = self.client.get(self.url).data
        self.assertEqual(result["estimated_recurrence_occurrences"], 0)
