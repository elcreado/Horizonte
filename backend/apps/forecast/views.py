from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Company
from apps.banking.models import BankAccount, Transaction

from .alerts import threshold_alert
from .baselines import hybrid_points
from .coverage import history_coverage
from .models import Obligation, Settlement
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
    try:
        return Response(build_dashboard(company, horizon))
    except ValueError as error:
        return Response({"detail": str(error)}, status=409)


def build_dashboard(company, horizon):
    accounts = list(BankAccount.objects.filter(company=company))
    if not accounts:
        raise ValueError("La empresa no tiene saldos disponibles.")
    dates = {account.balance_date for account in accounts}
    if len(dates) != 1 or any(account.currency != "COP" for account in accounts):
        raise ValueError("Se requieren saldos COP con la misma fecha de corte.")
    cutoff = dates.pop()
    rows = list(
        Transaction.objects.filter(
            account__company=company, date__lte=timezone.localdate()
        ).order_by("date", "pk")
    )
    as_of = max([cutoff] + [row.date for row in rows])
    from .monthly import materialize_monthly

    materialize_monthly(company.pk, as_of + timedelta(days=horizon))
    balance = sum((account.balance for account in accounts), Decimal("0"))
    # Declared balances already include history through the cut. Add only subsequent actual flows.
    balance += sum((row.amount for row in rows if row.date > cutoff), Decimal("0"))
    pending = Obligation.objects.filter(company=company, outstanding_amount__gt=0, cancelled=False)
    overdue_count = pending.filter(due_date__lte=as_of).count()
    upcoming = list(
        pending.filter(due_date__gt=as_of, due_date__lte=as_of + timedelta(days=horizon)).order_by(
            "due_date"
        )
    )
    points = project_obligations(balance, as_of, horizon, upcoming)
    if rows:
        start = min(rows[0].date, as_of - timedelta(days=6))
        settlements = dict(
            Settlement.objects.filter(
                transaction_id__in=[row.pk for row in rows], reversed_at__isnull=True
            )
            .values("transaction_id")
            .annotate(total=Sum("amount"))
            .values_list("transaction_id", "total")
        )
        residual = sum(
            (
                row.amount
                - (
                    settlements.get(row.pk, Decimal("0"))
                    if row.amount > 0
                    else -settlements.get(row.pk, Decimal("0"))
                )
                for row in rows
            ),
            Decimal("0"),
        )
        average = (residual / Decimal((as_of - start).days + 1)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        known = {}
        for item in upcoming:
            known[item.due_date] = known.get(item.due_date, Decimal("0")) + (
                item.outstanding_amount if item.direction == "in" else -item.outstanding_amount
            )
        points = hybrid_points(balance, as_of, [average] * horizon, known)
        points = [{"date": point["date"], "balance": point["balance"]} for point in points]
    negative = [point for point in points if Decimal(point["balance"]) < 0]
    transactions = Transaction.objects.filter(account__company=company).order_by("-date", "-id")[
        :20
    ]
    return {
        "company": company.name,
        "liquidity_alert": threshold_alert(points, company.liquidity_threshold, balance, as_of),
        "coverage": history_coverage(accounts, as_of),
        "currency": "COP",
        "as_of": as_of.isoformat(),
        "balance": str(balance),
        "horizon": horizon,
        "method": "Estimación con movimientos registrados y compromisos"
        if rows
        else "Escenario de obligaciones · sin movimientos",
        "notice": (
            f"Estimación orientativa: promedio neto diario {average} COP desde {start.isoformat()} hasta {as_of.isoformat()}, más compromisos pendientes. Incluye todos los movimientos registrados; los posteriores al saldo declarado actualizan la caja disponible sin volver a sumar los anteriores. Los días sin registros se tratan como cero; si faltan operaciones, completa el historial. No es una predicción validada ni una probabilidad."
            if rows
            else "Escenario basado en el saldo declarado y compromisos pendientes. Registra movimientos para estimar el flujo variable."
        ),
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
