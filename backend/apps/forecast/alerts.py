from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, Company, CompanyMember


class ThresholdInput(serializers.Serializer):
    threshold = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0"))


@api_view(["GET", "PATCH"])
def threshold(request, company_id):
    with transaction.atomic():
        company = get_object_or_404(
            Company.objects.select_for_update(), pk=company_id, members__user=request.user
        )
        member = CompanyMember.objects.get(company=company, user=request.user)
        can_edit = member.role == "owner"
        if request.method == "PATCH":
            if not can_edit:
                return Response(
                    {"detail": "Solo el propietario puede configurar el umbral."}, status=403
                )
            serializer = ThresholdInput(data=request.data)
            serializer.is_valid(raise_exception=True)
            before = str(company.liquidity_threshold)
            company.liquidity_threshold = serializer.validated_data["threshold"]
            company.save(update_fields=["liquidity_threshold"])
            if before != str(company.liquidity_threshold):
                AuditLog.objects.create(
                    company=company,
                    user=request.user,
                    action="liquidity.threshold_updated",
                    entity="company",
                    entity_id=str(company.pk),
                    before={"threshold": before},
                    after={"threshold": str(company.liquidity_threshold)},
                )
    return Response({"threshold": str(company.liquidity_threshold), "can_edit": can_edit})


def threshold_alert(points: list[dict], threshold: Decimal, balance: Decimal, as_of) -> dict:
    below = [point for point in points if Decimal(point["balance"]) < threshold]
    current_breach = balance < threshold
    return {
        "threshold": str(threshold),
        "currently_below": current_breach,
        "first_below": as_of.isoformat() if current_breach else below[0]["date"] if below else None,
        "projected_days_below": len(below),
        "shortfall_at_minimum": str(
            max(
                Decimal("0"),
                threshold - min([balance] + [Decimal(point["balance"]) for point in points]),
            )
        ),
    }
