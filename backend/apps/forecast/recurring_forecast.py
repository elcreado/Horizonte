"""Flujos estimados de patrones vigentes, separados de obligaciones reales."""

from datetime import date
from decimal import Decimal

from .recurrences import expand_dates, occurrence_key


class RecurrenceConflict(ValueError):
    pass


def estimate_recurrences(candidates, rows, cutoff, horizon, obligations, linked):
    """Un vínculo o referencia gestionada prevalece, incluso cancelado o saldado.

    Una obligación ambigua de la misma fecha/sentido necesita conciliación explícita;
    jamás se suman ambos flujos ni se decide silenciosamente que son el mismo pago.
    """
    flows, evidence = {}, []
    by_reference = {row.reference: row for row in obligations}
    ambiguous = {
        (row.due_date, row.direction)
        for row in obligations
        if not row.cancelled and row.outstanding_amount > 0
    }
    for candidate in candidates:
        for day_string in expand_dates(candidate, rows, cutoff, horizon):
            key = occurrence_key({**candidate, "next_date": day_string})
            day = date.fromisoformat(day_string)
            managed = linked.get(key) or by_reference.get("REC-" + key)
            if managed is not None:
                evidence.append(
                    {
                        "key": key,
                        "date": day_string,
                        "state": "managed",
                        "obligation_id": managed.pk,
                        "actual_due_date": managed.due_date.isoformat(),
                        "cancelled": managed.cancelled,
                        "outstanding_amount": str(managed.outstanding_amount),
                    }
                )
                continue
            if (day, candidate["direction"]) in ambiguous:
                raise RecurrenceConflict(
                    f"Revisa y vincula la recurrencia {candidate['description']} del {day_string}: "
                    "ya hay una obligación del mismo sentido y fecha."
                )
            amount = Decimal(candidate["amount"]) * (1 if candidate["direction"] == "in" else -1)
            flows[day] = flows.get(day, Decimal("0")) + amount
            evidence.append(
                {
                    "key": key,
                    "date": day_string,
                    "state": "estimated",
                    "amount": str(amount),
                    "account_id": candidate["account_id"],
                    "description": candidate["description"],
                }
            )
    return flows, evidence
