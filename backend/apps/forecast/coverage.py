from datetime import timedelta

from django.db.models import Count, Max, Min, Q

from apps.banking.models import Transaction


def history_coverage(accounts, as_of):
    """Describe evidencia observada, no confianza predictiva ni completitud bancaria."""
    start = as_of - timedelta(days=364)
    stats = (
        Transaction.objects.filter(
            account_id__in=[account.pk for account in accounts], date__gte=start, date__lte=as_of
        )
        .values("account_id")
        .annotate(
            count=Count("id"),
            first=Min("date"),
            last=Max("date"),
            active_days=Count("date", distinct=True),
            unclassified=Count("id", filter=Q(category="Otros")),
        )
    )
    by_account = {row["account_id"]: row for row in stats}
    result = []
    for account in accounts:
        row = by_account.get(account.pk, {})
        first, last = row.get("first"), row.get("last")
        span = (last - first).days + 1 if first else 0
        count = row.get("count", 0)
        state = "empty" if not count else "limited" if span < 90 else "extended"
        result.append(
            {
                "account_id": account.pk,
                "name": account.name,
                "state": state,
                "count": count,
                "first": first,
                "last": last,
                "span_days": span,
                "active_days": row.get("active_days", 0),
                "days_since_last": (as_of - last).days if last else None,
                "other_category_count": row.get("unclassified", 0),
            }
        )
    return {
        "start": start,
        "as_of": as_of,
        "accounts": result,
        "method": "obligations_only",
        "notice": "La proyección actual utiliza únicamente obligaciones. La amplitud del historial no mide confianza ni garantiza que se hayan importado todos los movimientos. Un día sin registros puede ser inactividad o falta de datos.",
    }
