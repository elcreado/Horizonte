from datetime import date
from decimal import Decimal

from django.db.models import Count, Min, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import CompanyMember
from apps.banking.models import BankAccount, Transaction


@api_view(["GET"])
def history(request, company_id):
    get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    accounts = list(BankAccount.objects.filter(company_id=company_id))
    dates = {account.balance_date for account in accounts}
    if len(dates) != 1 or any(account.currency != "COP" for account in accounts):
        return Response({"detail": "Se requieren cuentas COP con el mismo corte."}, status=409)
    cutoff = dates.pop()
    first_month = cutoff.year * 12 + cutoff.month - 12
    start = date(first_month // 12, first_month % 12 + 1, 1)
    rows = Transaction.objects.filter(
        account__company_id=company_id, date__gte=start, date__lte=cutoff
    )
    totals = rows.aggregate(count=Count("id"), first=Min("date"))
    aggregated = (
        rows.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(
            income=Sum("amount", filter=Q(amount__gt=0)),
            expense=Sum("amount", filter=Q(amount__lt=0)),
            count=Count("id"),
        )
    )
    by_month = {item["month"]: item for item in aggregated}
    months = []
    for offset in range(12):
        number = first_month + offset
        month = date(number // 12, number % 12 + 1, 1)
        values = by_month.get(month, {})
        income = values.get("income") or Decimal("0")
        expense = -(values.get("expense") or Decimal("0"))
        months.append(
            {
                "month": month.isoformat()[:7],
                "income": str(income),
                "expense": str(expense),
                "net": str(income - expense),
                "count": values.get("count", 0),
            }
        )
    categories = []
    for item in (
        rows.values("category")
        .annotate(
            income=Sum("amount", filter=Q(amount__gt=0)),
            expense=Sum("amount", filter=Q(amount__lt=0)),
        )
        .order_by("category")
    ):
        categories.append(
            {
                "category": item["category"],
                "income": str(item["income"] or Decimal("0")),
                "expense": str(-(item["expense"] or Decimal("0"))),
            }
        )
    return Response(
        {
            "start": start,
            "as_of": cutoff,
            "first_transaction": totals["first"],
            "count": totals["count"],
            "months": months,
            "categories": categories,
            "notice": "Solo movimientos registrados: un mes sin datos no demuestra ausencia de actividad. El mes del corte puede estar incompleto. Los flujos netos no equivalen al saldo bancario.",
        }
    )
