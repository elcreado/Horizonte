"""Preparación de cuantiles actuales con cobertura explícita por cuenta."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum

from apps.banking.models import Transaction

from .baselines import daily_residual
from .empirical_quantiles import weekly_cash_quantiles
from .models import Settlement


def build_quantiles(company_id, accounts, cutoff, balance, points, recurring_ids):
    start = cutoff - timedelta(days=269)
    if any(
        not account.history_complete_from
        or account.history_complete_from > start
        or account.history_complete_through != cutoff
        for account in accounts
    ):
        return {
            "status": "unavailable",
            "notice": "Los cuantiles requieren 270 días completos hasta el corte en cada cuenta.",
        }, {}
    rows = list(
        Transaction.objects.filter(
            account__company_id=company_id, date__range=(start, cutoff)
        ).order_by("date", "pk")
    )
    settled = dict(
        Settlement.objects.filter(
            transaction_id__in=[row.pk for row in rows], reversed_at__isnull=True
        )
        .values("transaction_id")
        .annotate(total=Sum("amount"))
        .values_list("transaction_id", "total")
    )
    residual = daily_residual(rows, start, cutoff, settled, recurring_ids, coverage_confirmed=True)
    flows = [Decimal(point["known_flow"]) + Decimal(point["recurring_flow"]) for point in points]
    quantiles, evidence = weekly_cash_quantiles(residual, balance, flows)
    for point, quantile in zip(points, quantiles, strict=True):
        point.update({key: str(value) for key, value in quantile.items()})
    inputs = {
        "training_start": start.isoformat(),
        "training_series": [str(value) for value in residual],
        "future_flows": [str(value) for value in flows],
        "model": evidence,
    }
    return {"status": "experimental", **evidence}, inputs
