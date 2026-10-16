import hashlib
import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from apps.banking.models import BankAccount

from .models import AlertEvaluation, Obligation
from .views import build_dashboard


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
        try:
            summary = build_dashboard(company, horizon)
        except ValueError as error:
            return Response({"detail": str(error)}, status=409)
        obligations = list(
            Obligation.objects.filter(
                company_id=company_id, cancelled=False, outstanding_amount__gt=0
            ).order_by("pk")
        )
        evidence = {
            "method": "summary_v2",
            "as_of": summary["as_of"],
            "horizon": horizon,
            "threshold": str(company.liquidity_threshold),
            "balance": summary["balance"],
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
        evidence["summary_points"] = summary["points"]
        result = summary["liquidity_alert"]
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
