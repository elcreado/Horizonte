"""End-of-day balances anchored to a declared cut, never inferred across unknown history."""

from collections.abc import Sequence
from datetime import date, timedelta
from decimal import Decimal

from apps.banking.models import BankAccount


def build_balance_history(
    accounts: Sequence[BankAccount],
    start: date,
    cutoff: date,
    daily_flows: dict[date, Decimal],
) -> dict:
    declared = sum((account.balance for account in accounts), Decimal("0"))
    sources = []
    for account in accounts:
        valid = bool(
            account.history_complete_from
            and account.history_complete_through
            and account.history_complete_from <= cutoff <= account.history_complete_through
        )
        sources.append(
            {
                "account_id": account.pk,
                "name": account.name,
                "declared_balance": format(account.balance, ".2f"),
                "balance_date": account.balance_date,
                "complete_from": account.history_complete_from,
                "complete_through": account.history_complete_through,
                "coverage_valid": valid,
                "coverage_source": "source" if account.connection_id else "manual_confirmation",
            }
        )
    complete_from = (
        max(start, max(account.history_complete_from for account in accounts))
        if sources and all(source["coverage_valid"] for source in sources)
        else None
    )
    points = []
    balance = declared
    day = cutoff
    while day >= start:
        known = day == cutoff or (complete_from is not None and day >= complete_from)
        points.append(
            {
                "date": day,
                "balance": format(balance, ".2f") if known else None,
                "status": "declared" if day == cutoff else "reconstructed" if known else "unknown",
            }
        )
        # The declared balance already includes movements on the cut day. Undo that
        # day's net only when stepping back to the preceding day's closing balance.
        balance -= daily_flows.get(day, Decimal("0"))
        day -= timedelta(days=1)
    points.reverse()
    return {
        "currency": "COP",
        "cutoff": cutoff,
        "declared_balance": format(declared, ".2f"),
        "complete_from": complete_from,
        "accounts": sources,
        "points": points,
        "notice": (
            "Saldos al cierre del día reconstruidos desde el saldo declarado al corte, "
            "restando los movimientos posteriores a cada día. Solo se reconstruye donde "
            "todas las cuentas tienen historial completo confirmado o cobertura de su fuente. "
            "Los días sin cobertura se dejan sin saldo; no representan cero. La declaración "
            "del saldo y la cobertura no equivalen a una verificación bancaria independiente. "
            "No incluye obligaciones futuras ni vuelve a descontar pagos conciliados."
        ),
    }
