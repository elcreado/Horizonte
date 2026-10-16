"""Atomic manual capture with immutable request receipts and declared balances."""

from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response

from apps.accounts.models import AuditLog, Company, CompanyMember
from apps.classify.services import categories, classify

from .models import BankAccount, ManualEntry, Transaction
from .normalization import normalize_movement


class ManualEntryInput(serializers.Serializer):
    request_id = serializers.UUIDField()
    account_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    direction = serializers.ChoiceField(choices=["in", "out"])
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    description = serializers.CharField(max_length=250)
    category = serializers.CharField(max_length=80, required=False, allow_blank=True)


def create_manual_entry(request, company_id: int) -> Response:
    with transaction.atomic():
        # Company lock serializes the same key even when requests target different accounts.
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        Company.objects.select_for_update().get(pk=company_id)
        serializer = ManualEntryInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        payload = dict(serializer.data)
        payload.setdefault("category", "")
        previous = ManualEntry.objects.filter(
            company_id=company_id, request_id=values["request_id"]
        ).first()
        if previous:
            if previous.payload != payload:
                return Response({"detail": "La solicitud ya se usó con otros datos."}, status=409)
            return Response({"id": previous.transaction_id, "created": False}, status=200)
        account = get_object_or_404(
            BankAccount.objects.select_for_update(), pk=values["account_id"], company_id=company_id
        )
        if account.connection_id:
            return Response({"detail": "Selecciona una cuenta manual."}, status=409)
        if values["date"] > min(account.balance_date, timezone.localdate()):
            return Response(
                {
                    "detail": "La fecha no puede superar hoy ni el corte de la cuenta. Registra compromisos futuros en Obligaciones."
                },
                status=400,
            )
        amount = values["amount"] * (1 if values["direction"] == "in" else -1)
        category = values.get("category", "")
        if category and category not in categories(amount):
            return Response(
                {"detail": "La categoría no corresponde al ingreso o egreso."}, status=400
            )
        automatic, source = classify(company_id, values["description"], amount)
        if Transaction.objects.filter(
            account=account, external_id=f"manual:{values['request_id']}"
        ).exists():
            return Response(
                {
                    "detail": "El identificador ya existe en el historial. Inicia una solicitud nueva."
                },
                status=409,
            )
        movement = Transaction.objects.create(
            account=account,
            external_id=f"manual:{values['request_id']}",
            date=values["date"],
            amount=amount,
            description=values["description"],
            category=category or automatic,
            classification_source="manual" if category else source,
            **normalize_movement(values["description"]),
        )
        ManualEntry.objects.create(
            company_id=company_id,
            request_id=values["request_id"],
            transaction=movement,
            payload=payload,
            user=request.user,
        )
        revoked = bool(
            account.history_complete_from
            and account.history_complete_through
            and account.history_complete_from <= movement.date <= account.history_complete_through
        )
        if revoked:
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
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            action="transaction.manual_created",
            entity="Transaction",
            entity_id=str(movement.pk),
            after={**payload, "entry_source": "manual", "coverage_revoked": revoked},
        )
    return Response({"id": movement.pk, "created": True}, status=201)
