from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from apps.forecast.models import Obligation


class ObligationCalendarTests(TestCase):
    def test_month_totals_exclude_other_tenants_cancelled_and_settled(self):
        user = get_user_model().objects.create_user("calendar")
        company = Company.objects.create(name="Calendar", nit="calendar")
        other = Company.objects.create(name="Other", nit="calendar-other")
        CompanyMember.objects.create(company=company, user=user, role="viewer")
        for index, (tenant, amount, cancelled, direction) in enumerate(
            [
                (company, "10.25", False, "in"),
                (company, "20.10", False, "out"),
                (company, "100", True, "out"),
                (company, "0", False, "out"),
                (other, "999", False, "in"),
            ]
        ):
            Obligation.objects.create(
                company=tenant,
                reference=str(index),
                description="test",
                due_date="2024-02-29",
                outstanding_amount=amount,
                cancelled=cancelled,
                direction=direction,
            )
        client = APIClient()
        client.force_authenticate(user)
        url = f"/api/companies/{company.pk}/obligation-calendar/"
        response = client.get(url, {"month": "2024-02"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["days"]), 29)
        last = response.data["days"][-1]
        self.assertEqual(Decimal(last["receivable"]), Decimal("10.25"))
        self.assertEqual(Decimal(last["payable"]), Decimal("20.10"))
        self.assertEqual(last["receivable_count"], 1)
        self.assertEqual(last["payable_count"], 1)
        self.assertEqual(client.get(url, {"month": "2024-13"}).status_code, 400)
        self.assertEqual(
            client.get(f"/api/companies/{other.pk}/obligation-calendar/").status_code, 404
        )
