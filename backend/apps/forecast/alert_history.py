import hashlib
import json
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from apps.banking.models import BankAccount

from .alerts import threshold_alert
from .models import AlertEvaluation, Obligation
from .services import project_obligations


def serialize(row):
    return {
        "id": row.pk,
        "created_at": row.created_at,
        "evidence": row.evidence,
        "result": row.result,
    }


@api_view(["GET", "POST"])
def alert_history(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    if request.method == "GET":
        pagination = PageNumberPagination()
        pagination.page_size = 10
        rows = AlertEvaluation.objects.filter(company_id=company_id).order_by("-created_at", "-pk")
        response = pagination.get_paginated_response(
            [serialize(row) for row in pagination.paginate_queryset(rows, request)]
        )
        response.data["can_save"] = member.role in ("owner", "accountant")
        return response
    try:
        horizon = int(request.data.get("horizon", 30))
        if horizon not in (30, 60, 90):
            raise ValueError
    except (TypeError, ValueError):
        return Response({"detail": "El horizonte debe ser 30, 60 o 90."}, status=400)
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        company = member.company
        accounts = list(BankAccount.objects.filter(company_id=company_id).order_by("pk"))
        dates = {account.balance_date for account in accounts}
        if len(dates) != 1 or any(account.currency != "COP" for account in accounts):
            return Response({"detail": "Se requieren cuentas COP con el mismo corte."}, status=409)
        cutoff = dates.pop()
        balance = sum((account.balance for account in accounts), Decimal("0"))
        obligations = list(
            Obligation.objects.filter(
                company_id=company_id, cancelled=False, outstanding_amount__gt=0
            ).order_by("pk")
        )
        evidence = {
            "method": "obligations_v1",
            "as_of": cutoff.isoformat(),
            "horizon": horizon,
            "threshold": str(company.liquidity_threshold),
            "balance": str(balance),
            "accounts": [{"id": row.pk, "balance": str(row.balance)} for row in accounts],
            "obligations": [
                {
                    "id": row.pk,
                    "description": row.description,
                    "date": row.due_date.isoformat(),
                    "direction": row.direction,
                    "amount": str(row.outstanding_amount),
                }
                for row in obligations
            ],
        }
        points = project_obligations(balance, cutoff, horizon, obligations)
        result = threshold_alert(points, company.liquidity_threshold, balance, cutoff)
        fingerprint = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        row, created = AlertEvaluation.objects.get_or_create(
            company_id=company_id,
            fingerprint=fingerprint,
            defaults={"user": request.user, "evidence": evidence, "result": result},
        )
        if created:
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="liquidity.evaluated",
                entity="AlertEvaluation",
                entity_id=str(row.pk),
                after={"fingerprint": fingerprint},
            )
    return Response(serialize(row), status=201 if created else 200)
