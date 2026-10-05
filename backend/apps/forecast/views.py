from datetime import timedelta
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Company
from apps.banking.models import BankAccount, Transaction

from .alerts import threshold_alert
from .coverage import history_coverage
from .models import Obligation
from .services import project_obligations


@api_view(["GET"])
def dashboard(request, company_id):
    company = get_object_or_404(Company, pk=company_id, members__user=request.user)
    try:
        horizon = int(request.query_params.get("horizon", "30"))
        if horizon not in (30, 60, 90):
            raise ValueError
    except (TypeError, ValueError):
        return Response({"detail": "El horizonte debe ser 30, 60 o 90."}, status=400)
    accounts = list(BankAccount.objects.filter(company=company))
    if not accounts:
        return Response({"detail": "La empresa no tiene saldos disponibles."}, status=409)
    dates = {account.balance_date for account in accounts}
    if len(dates) != 1 or any(account.currency != "COP" for account in accounts):
        return Response(
            {"detail": "Se requieren saldos COP con la misma fecha de corte."},
            status=409,
        )
    as_of = dates.pop()
    balance = sum((account.balance for account in accounts), Decimal("0"))
    pending = Obligation.objects.filter(company=company, outstanding_amount__gt=0, cancelled=False)
    overdue_count = pending.filter(due_date__lte=as_of).count()
    upcoming = list(
        pending.filter(due_date__gt=as_of, due_date__lte=as_of + timedelta(days=horizon)).order_by(
            "due_date"
        )
    )
    points = project_obligations(balance, as_of, horizon, upcoming)
    negative = [point for point in points if Decimal(point["balance"]) < 0]
    transactions = Transaction.objects.filter(account__company=company).order_by("-date", "-id")[
        :20
    ]
    return Response(
        {
            "company": company.name,
            "liquidity_alert": threshold_alert(points, company.liquidity_threshold, balance, as_of),
            "coverage": history_coverage(accounts, as_of),
            "currency": "COP",
            "as_of": as_of.isoformat(),
            "balance": str(balance),
            "horizon": horizon,
            "method": "Escenario de obligaciones · sin modelo estadístico",
            "notice": "Escenario basado en saldos declarados y obligaciones pendientes. Se asume cobro y pago puntual. No incluye flujos variables ni probabilidades.",
            "receivable": str(
                sum(
                    (o.outstanding_amount for o in upcoming if o.direction == "in"),
                    Decimal("0"),
                )
            ),
            "payable": str(
                sum(
                    (o.outstanding_amount for o in upcoming if o.direction == "out"),
                    Decimal("0"),
                )
            ),
            "overdue_count": overdue_count,
            "first_deficit": negative[0]["date"] if negative else None,
            "minimum_balance": str(min(Decimal(p["balance"]) for p in points)),
            "points": points,
            "obligations": [
                {
                    "id": o.id,
                    "description": o.description,
                    "due_date": o.due_date.isoformat(),
                    "direction": o.direction,
                    "amount": str(o.outstanding_amount),
                }
                for o in upcoming
            ],
            "transactions": [
                {
                    "id": t.id,
                    "date": t.date.isoformat(),
                    "description": t.description,
                    "category": t.category,
                    "amount": str(t.amount),
                }
                for t in transactions
            ],
        }
    )
