from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from apps.accounts.models import Company
from apps.banking.models import Transaction
from apps.forecast.models import Obligation
from apps.forecast.recurrences import detect_recurrences
from config.api_inventory import build_inventory
from tests.test_imports import ImportTests


def rows(dates, amounts=None):
    return [
        SimpleNamespace(
            pk=i + 1,
            account_id=1,
            date=date.fromisoformat(day),
            amount=Decimal(str(amounts[i] if amounts else -100)),
            normalized_description="ARRIENDO",
            description="Arriendo",
        )
        for i, day in enumerate(dates)
    ]


class RecurrenceTests(SimpleTestCase):
    def test_month_end_and_year_boundary(self):
        result = detect_recurrences(
            rows(["2026-10-31", "2026-11-30", "2026-12-31"]), date(2026, 12, 31)
        )
        self.assertEqual(result[0]["next_date"], "2027-01-31")
        self.assertEqual(result[0]["cadence"], "monthly")

    def test_weekly_and_future_leakage(self):
        data = rows(["2026-09-01", "2026-09-08", "2026-09-15", "2026-09-22"])
        result = detect_recurrences(data, date(2026, 9, 15))
        self.assertEqual(result[0]["observations"], 3)
        self.assertEqual(result[0]["next_date"], "2026-09-22")

    def test_rejects_stale_variable_and_insufficient_history(self):
        dates = ["2026-09-01", "2026-09-08", "2026-09-15"]
        self.assertEqual(detect_recurrences(rows(dates), date(2026, 9, 23)), [])
        self.assertEqual(detect_recurrences(rows(dates, [-100, -100, -150]), date(2026, 9, 15)), [])
        self.assertEqual(detect_recurrences(rows(dates[:2]), date(2026, 9, 8)), [])

    def test_no_merging_accounts_or_directions(self):
        data = rows(["2026-09-01", "2026-09-08", "2026-09-15"])
        data[-1].account_id = 2
        self.assertEqual(detect_recurrences(data, date(2026, 9, 15)), [])
        data[-1].account_id = 1
        data[-1].amount = Decimal("100")
        self.assertEqual(detect_recurrences(data, date(2026, 9, 15)), [])


class RecurrenceApiTests(TestCase):
    setUp = ImportTests.setUp

    def test_access_and_evidence(self):
        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        response = self.client.get(f"/api/companies/{self.company.id}/recurrences/")
        self.assertEqual(response.status_code, 200)
        schema = build_inventory()["paths"]["/api/companies/{company_id}/recurrences/"]["get"][
            "responses"
        ]["200"]["content"]["application/json"]["schema"]
        body = response.json()
        self.assertEqual(set(body), set(schema["properties"]))
        candidate_schema = schema["properties"]["results"]["items"]
        candidate = body["results"][0]
        self.assertEqual(set(candidate), set(candidate_schema["properties"]))
        occurrence = candidate["occurrences"][0]
        self.assertEqual(
            set(occurrence),
            set(candidate_schema["properties"]["occurrences"]["items"]["properties"]),
        )
        Obligation.objects.create(
            company=self.company,
            reference="precision-test",
            description="Pending",
            direction="out",
            due_date=occurrence["date"],
            outstanding_amount="1234.56",
        )
        matching = self.client.get(f"/api/companies/{self.company.pk}/recurrences/").json()[
            "results"
        ][0]["occurrences"][0]["matching_obligations"]
        self.assertEqual(matching[0]["outstanding_amount"], "1234.56")
        self.assertEqual(response.data["results"][0]["observations"], 4)
        other = Company.objects.create(name="Other", nit="recurrence-other")
        self.assertEqual(
            self.client.get(f"/api/companies/{other.id}/recurrences/").status_code, 404
        )
        self.client.force_authenticate(None)
        self.assertIn(
            self.client.get(f"/api/companies/{self.company.id}/recurrences/").status_code,
            [401, 403],
        )

    def test_reviews_persist_are_idempotent_and_require_current_evidence(self):
        from apps.accounts.models import AuditLog
        from apps.forecast.models import RecurrenceReview

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url).data["results"][0]
        payload = {"fingerprint": candidate["fingerprint"], "status": "confirmed"}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 200)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 200)
        self.assertEqual(RecurrenceReview.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action="recurrence.review").count(), 1)
        self.assertEqual(self.client.get(url).data["results"][0]["status"], "confirmed")
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(
            self.client.post(url, {**payload, "status": "rejected"}, format="json").status_code, 403
        )
        self.member.role = "owner"
        self.member.save()
        self.assertEqual(
            self.client.post(url, {**payload, "status": "rejected"}, format="json").status_code, 200
        )
        self.assertEqual(
            self.client.post(url, {**payload, "status": "pending"}, format="json").status_code, 200
        )
        Transaction.objects.filter(account=self.account).update(amount="-105")
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 409)
        self.assertEqual(self.client.get(url).data["results"][0]["status"], "pending")

    def test_occurrence_creates_one_obligation_and_changes_projection(self):
        from apps.forecast.models import Obligation

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url).data["results"][0]
        payload = {"fingerprint": candidate["fingerprint"], "status": "create"}
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 409)
        self.client.post(url, {**payload, "status": "confirmed"}, format="json")
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 201)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 200)
        self.assertEqual(Obligation.objects.count(), 1)
        dashboard = self.client.get(f"/api/companies/{self.company.id}/dashboard/")
        self.assertEqual(Decimal(dashboard.data["payable"]), Decimal("100"))
        self.assertEqual(Decimal(dashboard.data["balance"]), Decimal("500"))

    def test_link_existing_without_double_counting(self):
        from apps.forecast.models import Obligation

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        obligation = Obligation.objects.create(
            company=self.company,
            reference="existing",
            description="Arriendo",
            direction="out",
            due_date=date(2026, 9, 29),
            outstanding_amount="80",
        )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url).data["results"][0]
        payload = {"fingerprint": candidate["fingerprint"], "status": "confirmed"}
        self.client.post(url, payload, format="json")
        self.assertEqual(
            self.client.post(url, {**payload, "status": "create"}, format="json").status_code, 409
        )
        self.assertEqual(
            self.client.post(
                url, {**payload, "status": "link", "obligation_id": obligation.pk}, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(Obligation.objects.count(), 1)
        self.assertEqual(
            Decimal(
                self.client.get(f"/api/companies/{self.company.id}/dashboard/").data["payable"]
            ),
            Decimal("80"),
        )

    def test_full_horizon_and_repeated_creation_across_horizons(self):
        from apps.forecast.models import Obligation

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url + "?horizon=90").data["results"][0]
        self.assertEqual(len(candidate["occurrences"]), 13)
        payload = {"fingerprint": candidate["fingerprint"], "status": "confirmed"}
        self.client.post(url, payload, format="json")
        for occurrence in candidate["occurrences"]:
            response = self.client.post(
                url + "?horizon=90",
                {**payload, "status": "create", "occurrence_date": occurrence["date"]},
                format="json",
            )
            self.assertEqual(response.status_code, 201)
        first = candidate["occurrences"][0]["date"]
        self.assertEqual(
            self.client.post(
                url, {**payload, "status": "create", "occurrence_date": first}, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(Obligation.objects.count(), 13)
        for horizon, expected in [(30, 400), (60, 800), (90, 1300)]:
            response = self.client.get(
                f"/api/companies/{self.company.id}/dashboard/?horizon={horizon}"
            )
            self.assertEqual(Decimal(response.data["payable"]), Decimal(expected))
        self.assertEqual(
            self.client.post(
                url,
                {
                    **payload,
                    "status": "create",
                    "occurrence_date": candidate["occurrences"][-1]["date"],
                },
                format="json",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                url, {**payload, "status": "create", "occurrence_date": "2026-09-30"}, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get(url + "?horizon=999").status_code, 400)


class RecurrenceCalendarTests(SimpleTestCase):
    def test_month_end_crosses_february_without_drift(self):
        from apps.forecast.recurrences import expand_dates

        data = rows(["2026-10-31", "2026-11-30", "2026-12-31"])
        cutoff = date(2026, 12, 31)
        candidate = detect_recurrences(data, cutoff)[0]
        self.assertEqual(
            expand_dates(candidate, data, cutoff, 90), ["2027-01-31", "2027-02-28", "2027-03-31"]
        )

    def test_fixed_monthly_day(self):
        from apps.forecast.recurrences import expand_dates

        data = rows(["2026-10-17", "2026-11-17", "2026-12-17"])
        cutoff = date(2026, 12, 17)
        candidate = detect_recurrences(data, cutoff)[0]
        self.assertEqual(
            expand_dates(candidate, data, cutoff, 90), ["2027-01-17", "2027-02-17", "2027-03-17"]
        )


class UnlinkRecurrenceTests(TestCase):
    setUp = ImportTests.setUp

    def test_unlink_preserves_finances_and_checks_permissions(self):
        import uuid

        from apps.accounts.models import AuditLog
        from apps.forecast.models import Obligation, RecurrenceOccurrence, Settlement

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url).data["results"][0]
        payload = {"fingerprint": candidate["fingerprint"], "status": "confirmed"}
        self.client.post(url, payload, format="json")
        self.client.post(url, {**payload, "status": "create"}, format="json")
        obligation = Obligation.objects.get()
        obligation.outstanding_amount = Decimal("80")
        obligation.save()
        Settlement.objects.create(
            obligation=obligation,
            transaction=Transaction.objects.first(),
            user=self.user,
            amount="20",
            request_id=uuid.uuid4(),
        )
        link = RecurrenceOccurrence.objects.get()
        unlink_url = f"/api/companies/{self.company.id}/recurrence-occurrences/{link.pk}/unlink/"
        other = Company.objects.create(name="Other", nit="unlink-other")
        self.assertEqual(
            self.client.post(
                f"/api/companies/{other.pk}/recurrence-occurrences/{link.pk}/unlink/"
            ).status_code,
            404,
        )
        self.member.role = "viewer"
        self.member.save()
        self.assertEqual(self.client.post(unlink_url).status_code, 403)
        self.member.role = "owner"
        self.member.save()
        self.assertEqual(self.client.post(unlink_url).status_code, 200)
        self.assertEqual(RecurrenceOccurrence.objects.count(), 0)
        self.assertEqual(Settlement.objects.count(), 1)
        obligation.refresh_from_db()
        self.assertEqual(obligation.outstanding_amount, Decimal("80"))
        self.assertFalse(obligation.cancelled)
        self.assertEqual(AuditLog.objects.filter(action="recurrence.unlinked").count(), 1)
        self.assertEqual(
            Decimal(
                self.client.get(f"/api/companies/{self.company.id}/dashboard/").data["payable"]
            ),
            Decimal("80"),
        )
        self.assertEqual(
            self.client.post(
                url, {**payload, "status": "link", "obligation_id": obligation.pk}, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(self.client.post(unlink_url).status_code, 404)
        self.assertEqual(RecurrenceOccurrence.objects.count(), 1)

    def test_cancelled_unlinked_obligation_cannot_be_recreated(self):
        from apps.forecast.models import Obligation, RecurrenceOccurrence

        for i, day in enumerate([1, 8, 15, 22]):
            Transaction.objects.create(
                account=self.account,
                external_id=str(i),
                date=date(2026, 9, day),
                amount="-100",
                description="Arriendo",
                normalized_description="ARRIENDO",
            )
        url = f"/api/companies/{self.company.id}/recurrences/"
        candidate = self.client.get(url).data["results"][0]
        payload = {"fingerprint": candidate["fingerprint"], "status": "confirmed"}
        self.client.post(url, payload, format="json")
        self.client.post(url, {**payload, "status": "create"}, format="json")
        link = RecurrenceOccurrence.objects.get()
        self.client.post(
            f"/api/companies/{self.company.id}/recurrence-occurrences/{link.pk}/unlink/"
        )
        Obligation.objects.update(cancelled=True)
        self.assertEqual(
            self.client.post(url, {**payload, "status": "create"}, format="json").status_code, 409
        )
        self.assertEqual(Obligation.objects.count(), 1)
