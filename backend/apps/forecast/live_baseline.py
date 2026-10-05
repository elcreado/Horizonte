"""Referencia experimental de caja: obligaciones y flujo diario residual."""

import hashlib
import json
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, Transaction

from .alerts import threshold_alert
from .baselines import daily_residual, hybrid_points, predict_baseline
from .live_quantiles import build_quantiles
from .models import Obligation, RecurrenceOccurrence, RecurrenceReview, Settlement
from .recurrences import detect_recurrences
from .recurring_forecast import RecurrenceConflict, estimate_recurrences


class ForecastUnavailable(Exception):
    def __init__(self, detail: str, *, accounts: list[str] | None = None):
        self.detail = detail
        self.accounts = accounts


def validate_forecast_parameters(params) -> tuple[int, str]:
    try:
        horizon = int(params.get("horizon", "30"))
        if horizon not in (30, 60, 90):
            raise ValueError
    except (TypeError, ValueError):
        raise ForecastUnavailable("El horizonte debe ser 30, 60 o 90.") from None
    method = params.get("method", "seasonal_naive")
    if method not in ("naive", "seasonal_naive", "ses", "hybrid_weekly"):
        raise ForecastUnavailable("Método de referencia inválido.")
    return horizon, method


def build_forecast(
    member: CompanyMember, horizon: int, method: str, *, lock: bool = False
) -> tuple[dict, dict]:
    """Recoge entradas y resultado de una única lectura lógica del estado actual.

    Para guardar, el llamador usa una transacción y bloquea cuentas/obligaciones.
    La serie de 90 días y los flujos conocidos hacen reproducible el cálculo.
    """
    company_id = member.company_id
    if lock:
        Company.objects.select_for_update().get(pk=company_id)
    account_query = BankAccount.objects.filter(company_id=company_id).order_by("pk")
    if lock:
        account_query = account_query.select_for_update()
    accounts = list(account_query)
    cuts = {account.balance_date for account in accounts}
    if len(cuts) != 1 or any(account.currency != "COP" for account in accounts):
        raise ForecastUnavailable("Se requieren cuentas COP con el mismo corte.")
    cutoff = cuts.pop()
    start = cutoff - timedelta(days=89)
    missing = [
        account.name
        for account in accounts
        if not account.history_complete_from
        or account.history_complete_from > start
        or account.history_complete_through != cutoff
    ]
    if missing:
        raise ForecastUnavailable(
            "Confirma al menos 90 días completos hasta el corte para cada cuenta.", accounts=missing
        )
    rows = list(
        Transaction.objects.filter(
            account__company_id=company_id, date__range=(start, cutoff)
        ).order_by("date", "pk")
    )
    if not rows:
        raise ForecastUnavailable("No hay movimientos importados en el periodo confirmado.")
    settled = dict(
        Settlement.objects.filter(
            transaction_id__in=[row.pk for row in rows], reversed_at__isnull=True
        )
        .values("transaction_id")
        .annotate(total=Sum("amount"))
        .values_list("transaction_id", "total")
    )
    end = cutoff + timedelta(days=horizon)
    recurring_links = list(
        RecurrenceOccurrence.objects.filter(
            company_id=company_id,
            review__status="confirmed",
            obligation__cancelled=False,
            obligation__due_date__gt=cutoff,
            obligation__due_date__lte=end,
        ).select_related("review")
    )
    recurring_ids = {
        identifier
        for link in recurring_links
        for identifier in link.review.evidence.get("transaction_ids", [])
    }
    recurring_flows, recurrence_evidence, active_candidates = {}, [], []
    if method == "hybrid_weekly":
        detection_rows = list(
            Transaction.objects.filter(
                account__company_id=company_id, date__range=(cutoff - timedelta(days=370), cutoff)
            ).order_by("date", "pk")
        )
        confirmed = set(
            RecurrenceReview.objects.filter(company_id=company_id, status="confirmed").values_list(
                "fingerprint", flat=True
            )
        )
        for candidate in detect_recurrences(detection_rows, cutoff):
            fingerprint = hashlib.sha256(json.dumps(candidate, sort_keys=True).encode()).hexdigest()
            if fingerprint in confirmed:
                active_candidates.append(candidate)
        managed_obligations = list(Obligation.objects.filter(company_id=company_id).order_by("pk"))
        all_links = {
            row.key: row.obligation
            for row in RecurrenceOccurrence.objects.filter(company_id=company_id).select_related(
                "obligation"
            )
        }
        try:
            recurring_flows, recurrence_evidence = estimate_recurrences(
                active_candidates, detection_rows, cutoff, horizon, managed_obligations, all_links
            )
        except RecurrenceConflict as error:
            raise ForecastUnavailable(str(error)) from error
        recurring_ids = {
            identifier
            for candidate in active_candidates
            for identifier in candidate["transaction_ids"]
        }
    try:
        residual = daily_residual(
            rows, start, cutoff, settled, recurring_ids, coverage_confirmed=True
        )
        if sum(value != 0 for value in residual) < 4 and not (
            method == "hybrid_weekly" and active_candidates and not any(residual)
        ):
            raise ForecastUnavailable(
                "Hay menos de cuatro días con flujo variable; la referencia estadística no es útil todavía."
            )
        estimated = predict_baseline(
            residual, horizon, "seasonal_naive" if method == "hybrid_weekly" else method
        )
    except ValueError as error:
        raise ForecastUnavailable(str(error)) from error
    known = {}
    obligation_query = Obligation.objects.filter(
        company_id=company_id,
        cancelled=False,
        outstanding_amount__gt=0,
        due_date__gt=cutoff,
        due_date__lte=end,
    ).order_by("pk")
    if lock:
        obligation_query = obligation_query.select_for_update()
    obligations = list(obligation_query)
    for obligation in obligations:
        sign = 1 if obligation.direction == "in" else -1
        known[obligation.due_date] = (
            known.get(obligation.due_date, Decimal("0")) + sign * obligation.outstanding_amount
        )
    balance = sum((account.balance for account in accounts), Decimal("0"))
    points = hybrid_points(balance, cutoff, estimated, known)
    accumulated_recurring = Decimal("0")
    for point in points:
        day = cutoff.fromisoformat(point["date"])
        recurring = recurring_flows.get(day, Decimal("0"))
        accumulated_recurring += recurring
        point["recurring_flow"] = str(recurring)
        point["balance"] = str(Decimal(point["balance"]) + accumulated_recurring)
    below_zero = [point for point in points if Decimal(point["balance"]) < 0]
    quantile_status, quantile_inputs = (
        {"status": "unavailable", "notice": "Cuantiles disponibles solo para el híbrido semanal."},
        {},
    )
    if method == "hybrid_weekly":
        quantile_status, quantile_inputs = build_quantiles(
            company_id, accounts, cutoff, balance, points, recurring_ids
        )
    source = {
        "accounts": [
            {
                "id": row.pk,
                "balance": str(row.balance),
                "cutoff": row.balance_date.isoformat(),
                "coverage_from": row.history_complete_from.isoformat(),
                "confirmed_at": row.history_confirmed_at.isoformat()
                if row.history_confirmed_at
                else None,
            }
            for row in accounts
        ],
        "movements": [
            [row.pk, row.account_id, row.date.isoformat(), str(row.amount)] for row in rows
        ],
        "settlements": [[identifier, str(value)] for identifier, value in sorted(settled.items())],
        "recurring_ids": sorted(recurring_ids),
        "obligations": [
            [row.pk, row.due_date.isoformat(), row.direction, str(row.outstanding_amount)]
            for row in obligations
        ],
        "threshold": str(member.company.liquidity_threshold),
        "recurrence_estimates": recurrence_evidence,
        "quantile_inputs": quantile_inputs,
    }
    source_digest = hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()
    evidence = {
        "version": "hybrid_weekly_v2" if method == "hybrid_weekly" else "baseline_v1",
        "quantile_inputs": quantile_inputs,
        "method": method,
        "horizon": horizon,
        "as_of": cutoff.isoformat(),
        "training_start": start.isoformat(),
        "balance": str(balance),
        "threshold": str(member.company.liquidity_threshold),
        "source_digest": source_digest,
        "accounts": len(accounts),
        "movements": len(rows),
        "settlement_allocations": len(settled),
        "excluded_recurring_movements": len(recurring_ids & {row.pk for row in rows}),
        "known_future_obligations": len(obligations),
        "training_series": [str(value) for value in residual],
        "known_flows": {day.isoformat(): str(value) for day, value in sorted(known.items())},
        "recurrence_estimates": recurrence_evidence,
    }
    payload = {
        "status": "experimental",
        "method": method,
        "horizon": horizon,
        "as_of": cutoff.isoformat(),
        "training_start": start.isoformat(),
        "training_days": len(residual),
        "observed_movements": len(rows),
        "excluded_recurring_movements": evidence["excluded_recurring_movements"],
        "balance": str(balance),
        "known_future_obligations": len(obligations),
        "estimated_recurrence_occurrences": sum(
            row["state"] == "estimated" for row in recurrence_evidence
        ),
        "points": points,
        "quantiles": quantile_status,
        "first_deficit": below_zero[0]["date"] if below_zero else None,
        "minimum_balance": str(min(Decimal(point["balance"]) for point in points)),
        "liquidity_alert": threshold_alert(
            points, member.company.liquidity_threshold, balance, cutoff
        ),
        "notice": (
            "Híbrido experimental: suma obligaciones pendientes, flujo variable y fechas estimadas de recurrencias confirmadas vigentes. "
            "Una fecha ya vinculada, cancelada o saldada no se estima otra vez. No crea obligaciones ni modifica saldos. "
            if method == "hybrid_weekly"
            else "Referencia experimental de flujo variable diario. "
        )
        + "No está validado con datos reales. Los cuantiles, si están disponibles, son experimentales no calibrados; no ofrece probabilidad de déficit. Los datos actuales sirven para estimar desde este corte, no para evaluar cortes históricos.",
    }
    return payload, evidence


@api_view(["GET"])
def baseline_forecast(request, company_id):
    member = get_object_or_404(
        CompanyMember.objects.select_related("company"), company_id=company_id, user=request.user
    )
    try:
        horizon, method = validate_forecast_parameters(request.query_params)
        payload, _ = build_forecast(member, horizon, method)
    except ForecastUnavailable as error:
        return Response(
            {
                "detail": error.detail,
                **({"accounts": error.accounts} if error.accounts is not None else {}),
            },
            status=400
            if error.detail
            in ("El horizonte debe ser 30, 60 o 90.", "Método de referencia inválido.")
            else 409,
        )
    return Response(payload)
