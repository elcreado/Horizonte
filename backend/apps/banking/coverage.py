from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember

from .models import BankAccount


class CoverageInput(serializers.Serializer):
    start = serializers.DateField()
    confirmed = serializers.BooleanField()


@api_view(["POST"])
def confirm_coverage(request, company_id, account_id):
    serializer = CoverageInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        account = get_object_or_404(
            BankAccount.objects.select_for_update(), pk=account_id, company_id=company_id
        )
        if account.connection_id:
            return Response(
                {"detail": "La cobertura de esta cuenta proviene de su fuente."}, status=409
            )
        if values["start"] > account.balance_date or values[
            "start"
        ] < account.balance_date - timedelta(days=3650):
            return Response(
                {"detail": "El inicio debe ser anterior al corte y como máximo diez años atrás."},
                status=400,
            )
        before = {
            "start": account.history_complete_from.isoformat()
            if account.history_complete_from
            else None,
            "through": account.history_complete_through.isoformat()
            if account.history_complete_through
            else None,
        }
        if values["confirmed"]:
            account.history_complete_from = values["start"]
            account.history_complete_through = account.balance_date
            account.history_confirmed_at = timezone.now()
            account.history_confirmed_by = request.user
        else:
            account.history_complete_from = None
            account.history_complete_through = None
            account.history_confirmed_at = None
            account.history_confirmed_by = None
        account.save(
            update_fields=[
                "history_complete_from",
                "history_complete_through",
                "history_confirmed_at",
                "history_confirmed_by",
            ]
        )
        after = {
            "start": account.history_complete_from.isoformat()
            if account.history_complete_from
            else None,
            "through": account.history_complete_through.isoformat()
            if account.history_complete_through
            else None,
        }
        if before != after:
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="account.coverage_updated",
                entity="BankAccount",
                entity_id=str(account.pk),
                before=before,
                after=after,
            )
    return Response(
        {"history_complete_from": after["start"], "history_complete_through": after["through"]}
    )
