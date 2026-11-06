"""Ejecuciones persistidas de la referencia experimental."""

import hashlib
import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember

from .live_baseline import ForecastUnavailable, build_forecast, validate_forecast_parameters
from .models import ForecastRun


def serialize(row):
    return {
        "id": row.pk,
        "created_at": row.created_at,
        "method": row.method,
        "horizon": row.horizon,
        "as_of": row.as_of,
        "evidence": row.evidence,
        "result": row.result,
    }


@api_view(["GET", "POST"])
def forecast_runs(request, company_id):
    member = get_object_or_404(
        CompanyMember.objects.select_related("company"), company_id=company_id, user=request.user
    )
    if request.method == "GET":
        pagination = PageNumberPagination()
        pagination.page_size = 10
        rows = ForecastRun.objects.filter(company_id=company_id).order_by("-created_at", "-pk")
        response = pagination.get_paginated_response(
            [serialize(row) for row in pagination.paginate_queryset(rows, request)]
        )
        response.data["can_save"] = member.role in ("owner", "accountant")
        return response
    if member.role not in ("owner", "accountant"):
        return Response({"detail": "Tu rol solo permite consultar."}, status=403)
    try:
        horizon, method = validate_forecast_parameters(request.data)
    except ForecastUnavailable as error:
        return Response({"detail": error.detail}, status=400)
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update().select_related("company"),
            company_id=company_id,
            user=request.user,
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        try:
            result, evidence = build_forecast(member, horizon, method, lock=True)
        except ForecastUnavailable as error:
            return Response(
                {
                    "detail": error.detail,
                    **({"accounts": error.accounts} if error.accounts is not None else {}),
                },
                status=409,
            )
        fingerprint = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        row, created = ForecastRun.objects.get_or_create(
            company_id=company_id,
            fingerprint=fingerprint,
            defaults={
                "user": request.user,
                "method": method,
                "horizon": horizon,
                "as_of": result["as_of"],
                "evidence": evidence,
                "result": result,
            },
        )
        if created:
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="forecast.run_saved",
                entity="ForecastRun",
                entity_id=str(row.pk),
                after={"fingerprint": fingerprint, "method": method, "horizon": horizon},
            )
    return Response(serialize(row), status=201 if created else 200)
