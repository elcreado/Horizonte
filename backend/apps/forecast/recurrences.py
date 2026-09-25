import hashlib
import json
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import median

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.banking.models import BankAccount, Transaction
from apps.banking.normalization import normalize_movement

from .models import Obligation, RecurrenceOccurrence, RecurrenceReview


def detect_recurrences(rows, as_of):
    """Candidatos conservadores: al menos tres fechas y montos dentro del 10%.

    Agrupa por cuenta, descripción y signo; nunca usa movimientos posteriores al corte.
    Las sugerencias no se suman al escenario hasta su revisión y conciliación.
    """
    groups = defaultdict(list)
    for row in rows:
        if not row.amount or row.date > as_of or row.date < as_of - timedelta(days=370):
            continue
        label = (
            row.normalized_description
            or normalize_movement(row.description)["normalized_description"]
        )
        if label:
            groups[(row.account_id, label, row.amount > 0)].append(row)
    result = []
    for (account_id, label, income), items in groups.items():
        items.sort(key=lambda row: (row.date, row.pk))
        dates = [row.date for row in items]
        if len(dates) < 3 or len(set(dates)) != len(dates):
            continue
        amount = median([abs(row.amount) for row in items])
        if any(abs(abs(row.amount) - amount) > amount * Decimal("0.10") for row in items):
            continue
        gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
        month_steps = [(b.year - a.year) * 12 + b.month - a.month for a, b in zip(dates, dates[1:])]
        month_end = all(d.day >= monthrange(d.year, d.month)[1] - 2 for d in dates)
        monthly = all(step == 1 for step in month_steps) and (
            month_end or max(d.day for d in dates) - min(d.day for d in dates) <= 3
        )
        if monthly:
            cadence = "monthly"
            year, month = dates[-1].year, dates[-1].month + 1
            if month == 13:
                year, month = year + 1, 1
            day = (
                monthrange(year, month)[1]
                if month_end
                else min(int(median([d.day for d in dates])), monthrange(year, month)[1])
            )
            next_date = dates[-1].replace(year=year, month=month, day=day)
        elif all(6 <= gap <= 8 for gap in gaps):
            cadence = "weekly"
            next_date = dates[-1] + timedelta(days=7)
        else:
            continue
        if next_date <= as_of:
            continue
        result.append(
            {
                "account_id": account_id,
                "description": label,
                "direction": "in" if income else "out",
                "cadence": cadence,
                "amount": str(amount.quantize(Decimal("0.01"))),
                "next_date": next_date.isoformat(),
                "observations": len(items),
                "transaction_ids": [row.pk for row in items],
            }
        )
    return sorted(
        result, key=lambda item: (item["next_date"], item["account_id"], item["description"])
    )


@api_view(["GET", "POST"])
def recurrences(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    try:
        horizon = int(request.query_params.get("horizon", "30"))
        if horizon not in (30, 60, 90):
            raise ValueError
    except (TypeError, ValueError):
        return Response({"detail": "El horizonte debe ser 30, 60 o 90."}, status=400)
    accounts = list(BankAccount.objects.filter(company_id=company_id))
    dates = {account.balance_date for account in accounts}
    if len(dates) != 1 or any(account.currency != "COP" for account in accounts):
        return Response({"detail": "Se requieren cuentas COP con el mismo corte."}, status=409)
    as_of = dates.pop()
    rows = Transaction.objects.filter(
        account__company_id=company_id, date__lte=as_of, date__gte=as_of - timedelta(days=370)
    ).order_by("date", "id")
    rows = list(rows)
    candidates = detect_recurrences(rows, as_of)
    for candidate in candidates:
        candidate["fingerprint"] = hashlib.sha256(
            json.dumps(candidate, sort_keys=True).encode()
        ).hexdigest()
    if request.method == "POST":
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        status = request.data.get("status")
        if status not in ("confirmed", "rejected", "pending", "create", "link"):
            return Response({"detail": "Estado de revisión inválido."}, status=400)
        candidate = next(
            (item for item in candidates if item["fingerprint"] == request.data.get("fingerprint")),
            None,
        )
        if candidate is None:
            return Response(
                {"detail": "El patrón cambió o ya no está vigente. Actualiza la lista."}, status=409
            )
        with transaction.atomic():
            Company.objects.select_for_update().get(pk=company_id)
            current_member = get_object_or_404(
                CompanyMember, company_id=company_id, user=request.user
            )
            if current_member.role not in ("owner", "accountant"):
                return Response({"detail": "Tu rol solo permite consultar."}, status=403)
            review = RecurrenceReview.objects.filter(
                company_id=company_id, fingerprint=candidate["fingerprint"]
            ).first()
            if status in ("create", "link"):
                occurrence_date = request.data.get("occurrence_date", candidate["next_date"])
                if occurrence_date not in expand_dates(candidate, rows, as_of, horizon):
                    return Response(
                        {"detail": "Fecha fuera del patrón o del horizonte seleccionado."},
                        status=400,
                    )
                return materialize(
                    request, company_id, {**candidate, "next_date": occurrence_date}, review
                )
            previous = review.status if review else "pending"
            review, _ = RecurrenceReview.objects.update_or_create(
                company_id=company_id,
                fingerprint=candidate["fingerprint"],
                defaults={"status": status, "evidence": candidate, "user": request.user},
            )
            if previous != status:
                AuditLog.objects.create(
                    company_id=company_id,
                    user=request.user,
                    action="recurrence.review",
                    entity="RecurrenceReview",
                    entity_id=str(review.pk),
                    before={"status": previous},
                    after={"status": status, "fingerprint": candidate["fingerprint"]},
                )
        return Response({"status": status})
    reviews = dict(
        RecurrenceReview.objects.filter(company_id=company_id).values_list("fingerprint", "status")
    )
    for candidate in candidates:
        candidate["status"] = reviews.get(candidate["fingerprint"], "pending")
        candidate["occurrences"] = []
        for occurrence_date in expand_dates(candidate, rows, as_of, horizon):
            occurrence = (
                RecurrenceOccurrence.objects.filter(
                    company_id=company_id,
                    key=occurrence_key({**candidate, "next_date": occurrence_date}),
                )
                .select_related("obligation")
                .first()
            )
            candidate["occurrences"].append(
                {
                    "date": occurrence_date,
                    "link_id": occurrence.pk if occurrence else None,
                    "obligation_id": occurrence.obligation_id if occurrence else None,
                    "cancelled": occurrence.obligation.cancelled if occurrence else False,
                    "matching_obligations": list(
                        Obligation.objects.filter(
                            company_id=company_id,
                            due_date=occurrence_date,
                            direction=candidate["direction"],
                            cancelled=False,
                            outstanding_amount__gt=0,
                            recurrenceoccurrence__isnull=True,
                        ).values("id", "reference", "description", "outstanding_amount")
                    ),
                }
            )
    return Response(
        {
            "as_of": as_of,
            "horizon": horizon,
            "can_edit": member.role in ("owner", "accountant"),
            "results": candidates,
            "notice": "Patrones sugeridos a partir del historial. Confirma y vincula cada ocurrencia a una obligación para incluirla una sola vez en la proyección. Revisar el patrón no cancela obligaciones ya creadas.",
        }
    )


def occurrence_key(candidate):
    identity = {
        key: candidate[key] for key in ("account_id", "description", "direction", "next_date")
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def materialize(request, company_id, candidate, review):
    """Se ejecuta con lock de empresa; la obligación es la única fuente de proyección."""
    if review is None or review.status != "confirmed":
        return Response({"detail": "Confirma primero el patrón vigente."}, status=409)
    key = occurrence_key(candidate)
    existing = RecurrenceOccurrence.objects.filter(company_id=company_id, key=key).first()
    if existing:
        return Response({"obligation_id": existing.obligation_id})
    if request.data["status"] == "link":
        identifier = request.data.get("obligation_id")
        if (
            not isinstance(identifier, int)
            or isinstance(identifier, bool)
            or not 0 < identifier < 2**63
        ):
            return Response({"detail": "Selecciona una obligación."}, status=400)
        obligation = get_object_or_404(
            Obligation.objects.select_for_update(), pk=identifier, company_id=company_id
        )
        if (
            obligation.cancelled
            or obligation.outstanding_amount <= 0
            or obligation.direction != candidate["direction"]
            or obligation.due_date.isoformat() != candidate["next_date"]
            or RecurrenceOccurrence.objects.filter(obligation=obligation).exists()
        ):
            return Response(
                {"detail": "La obligación no es compatible o ya está vinculada."}, status=409
            )
    else:
        if Obligation.objects.filter(company_id=company_id, reference="REC-" + key).exists():
            return Response(
                {
                    "detail": "La obligación de esta fecha ya fue creada. Revísala en Obligaciones y vuelve a vincularla si corresponde."
                },
                status=409,
            )
        if Obligation.objects.filter(
            company_id=company_id,
            direction=candidate["direction"],
            due_date=candidate["next_date"],
            cancelled=False,
            outstanding_amount__gt=0,
        ).exists():
            return Response(
                {
                    "detail": "Ya hay obligaciones del mismo sentido y fecha. Revisa y vincula una existente para evitar duplicados."
                },
                status=409,
            )
        obligation = Obligation.objects.create(
            company_id=company_id,
            reference="REC-" + key,
            description=candidate["description"][:200],
            direction=candidate["direction"],
            due_date=candidate["next_date"],
            outstanding_amount=candidate["amount"],
        )
    RecurrenceOccurrence.objects.create(
        company_id=company_id, key=key, obligation=obligation, review=review
    )
    AuditLog.objects.create(
        company_id=company_id,
        user=request.user,
        action="recurrence." + request.data["status"],
        entity="obligation",
        entity_id=str(obligation.pk),
        after={"fingerprint": candidate["fingerprint"], "occurrence_key": key},
    )
    return Response({"obligation_id": obligation.pk}, status=201)


def expand_dates(candidate: dict, rows: list, as_of: date, horizon: int) -> list[str]:
    """Ancla mensual estable: febrero no desplaza las fechas de marzo."""
    evidence_ids = set(candidate["transaction_ids"])
    evidence_dates = [row.date for row in rows if row.pk in evidence_ids]
    month_end = all(day.day >= monthrange(day.year, day.month)[1] - 2 for day in evidence_dates)
    anchor = int(median([day.day for day in evidence_dates]))
    current = date.fromisoformat(candidate["next_date"])
    end = as_of + timedelta(days=horizon)
    result = []
    while current <= end:
        result.append(current.isoformat())
        if candidate["cadence"] == "weekly":
            current += timedelta(days=7)
        else:
            year, month = current.year, current.month + 1
            if month == 13:
                year, month = year + 1, 1
            last_day = monthrange(year, month)[1]
            current = date(year, month, last_day if month_end else min(anchor, last_day))
    return result


@api_view(["POST"])
def unlink_occurrence(request, company_id, occurrence_id):
    with transaction.atomic():
        get_object_or_404(Company, pk=company_id, members__user=request.user)
        Company.objects.select_for_update().get(pk=company_id)
        member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        occurrence = get_object_or_404(
            RecurrenceOccurrence, pk=occurrence_id, company_id=company_id
        )
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            action="recurrence.unlinked",
            entity="obligation",
            entity_id=str(occurrence.obligation_id),
            before={"occurrence_key": occurrence.key, "review_id": occurrence.review_id},
            after={"linked": False},
        )
        occurrence.delete()
    return Response(
        {
            "detail": "Vínculo eliminado. La obligación, sus pagos y su efecto en la proyección se conservan."
        }
    )
