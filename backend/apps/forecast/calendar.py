"""Calendario mensual agregado de compromisos pendientes de una empresa."""

import calendar
import re
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import CompanyMember

from .models import Obligation


@api_view(["GET"])
def obligation_calendar(request, company_id):
    get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    month = request.query_params.get("month", timezone.localdate().strftime("%Y-%m"))
    try:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", month):
            raise ValueError
        year, number = map(int, month.split("-"))
        start = date(year, number, 1)
        length = calendar.monthrange(year, number)[1]
        end = date(year, number, length)
    except ValueError:
        return Response({"detail": "Mes requerido en formato YYYY-MM válido."}, status=400)
    rows = (
        Obligation.objects.filter(
            company_id=company_id,
            cancelled=False,
            outstanding_amount__gt=0,
            due_date__gte=start,
            due_date__lte=end,
        )
        .values("due_date", "direction")
        .annotate(amount=Sum("outstanding_amount"), count=Count("pk"))
    )
    grouped = {(row["due_date"], row["direction"]): row for row in rows}
    days = []
    for day in range(1, length + 1):
        current = date(year, number, day)
        income, expense = grouped.get((current, "in"), {}), grouped.get((current, "out"), {})
        days.append(
            {
                "date": current.isoformat(),
                "receivable": str(income.get("amount", Decimal("0"))),
                "payable": str(expense.get("amount", Decimal("0"))),
                "receivable_count": income.get("count", 0),
                "payable_count": expense.get("count", 0),
            }
        )
    return Response(
        {
            "month": month,
            "currency": "COP",
            "days": days,
            "notice": "Obligaciones pendientes por vencimiento; excluye canceladas y saldadas. "
            "No representa cobros o pagos realizados ni probabilidad de cumplimiento.",
        }
    )
