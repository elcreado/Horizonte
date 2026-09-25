from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from apps.banking.models import Transaction

from .models import Obligation, Settlement
from .serializers import ObligationEdit, ObligationInput, ObligationOutput, SettlementInput


def membership(request, company_id: int, write: bool = False) -> CompanyMember:
    query = CompanyMember.objects.select_for_update() if write else CompanyMember.objects
    member = get_object_or_404(query, company_id=company_id, user=request.user)
    if write and member.role not in ("owner", "accountant"):
        raise PermissionDenied("Tu rol solo permite consultar.")
    return member


def audit(request, obligation: Obligation, action: str, before: dict, after: dict) -> None:
    AuditLog.objects.create(
        company_id=obligation.company_id,
        user=request.user,
        action=action,
        entity="obligation",
        entity_id=str(obligation.id),
        before=before,
        after=after,
    )


@api_view(["GET", "POST"])
def obligations(request, company_id):
    if request.method == "GET":
        member = membership(request, company_id)
        rows = Obligation.objects.filter(company_id=company_id).order_by(
            "cancelled", "due_date", "id"
        )
        pagination = PageNumberPagination()
        pagination.page_size = 20
        response = pagination.get_paginated_response(
            ObligationOutput(pagination.paginate_queryset(rows, request), many=True).data
        )
        response.data["can_edit"] = member.role in ("owner", "accountant")
        return response
    with transaction.atomic():
        membership(request, company_id, write=True)
        serializer = ObligationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                row = Obligation.objects.create(company_id=company_id, **serializer.validated_data)
        except IntegrityError:
            raise ValidationError(
                {"reference": "Ya existe una obligación con esta referencia."}
            ) from None
        result = ObligationOutput(row).data
        audit(request, row, "obligation.created", {}, dict(result))
    return Response(result, status=201)


@api_view(["PATCH"])
def edit_obligation(request, company_id, obligation_id):
    with transaction.atomic():
        membership(request, company_id, write=True)
        row = get_object_or_404(
            Obligation.objects.select_for_update(), pk=obligation_id, company_id=company_id
        )
        serializer = ObligationEdit(data=request.data)
        serializer.is_valid(raise_exception=True)
        if set(request.data) - set(serializer.fields):
            raise ValidationError(
                "Solo se pueden editar descripción, contraparte, vencimiento y cancelación."
            )
        before = dict(ObligationOutput(row).data)
        for key, value in serializer.validated_data.items():
            setattr(row, key, value)
        row.save()
        result = ObligationOutput(row).data
        audit(request, row, "obligation.updated", before, dict(result))
    return Response(result)


def settlement_data(row: Settlement) -> dict:
    return {
        "id": row.id,
        "transaction_id": row.transaction_id,
        "amount": str(row.amount),
        "request_id": str(row.request_id),
        "created_at": row.created_at,
        "reversed_at": row.reversed_at,
    }


@api_view(["GET", "POST"])
def settlements(request, company_id, obligation_id):
    if request.method == "GET":
        membership(request, company_id)
        row = get_object_or_404(Obligation, pk=obligation_id, company_id=company_id)
        return Response([settlement_data(item) for item in row.settlements.order_by("-id")])
    with transaction.atomic():
        membership(request, company_id, write=True)
        row = get_object_or_404(
            Obligation.objects.select_for_update(), pk=obligation_id, company_id=company_id
        )
        serializer = SettlementInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        previous = row.settlements.filter(request_id=values["request_id"]).first()
        if previous:
            if (
                previous.amount != values["amount"]
                or previous.transaction_id != values["transaction_id"]
            ):
                raise ValidationError(
                    "El identificador del intento ya corresponde a otra conciliación."
                )
            return Response(settlement_data(previous))
        movement = get_object_or_404(
            Transaction.objects.select_for_update(),
            pk=values["transaction_id"],
            account__company_id=company_id,
        )
        amount = values["amount"]
        if row.cancelled:
            raise ValidationError("No se puede conciliar una obligación cancelada.")
        if (row.direction == "in" and movement.amount <= 0) or (
            row.direction == "out" and movement.amount >= 0
        ):
            raise ValidationError("El movimiento debe tener el mismo sentido que la obligación.")
        if movement.date > movement.account.balance_date:
            raise ValidationError(
                "El movimiento debe estar incluido en el corte del saldo bancario."
            )
        used = movement.settlements.filter(reversed_at__isnull=True).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal(0)
        if amount > row.outstanding_amount or used + amount > abs(movement.amount):
            raise ValidationError(
                "El valor supera el pendiente o el importe disponible del movimiento."
            )
        before = dict(ObligationOutput(row).data)
        payment = Settlement.objects.create(
            obligation=row,
            transaction=movement,
            user=request.user,
            amount=amount,
            request_id=values["request_id"],
        )
        row.outstanding_amount -= amount
        row.save(update_fields=["outstanding_amount"])
        audit(
            request,
            row,
            "obligation.reconciled",
            before,
            {
                **dict(ObligationOutput(row).data),
                "settlement_id": payment.id,
                "transaction_id": movement.id,
            },
        )
    return Response(settlement_data(payment), status=201)


@api_view(["POST"])
def reverse_settlement(request, company_id, obligation_id, settlement_id):
    with transaction.atomic():
        membership(request, company_id, write=True)
        row = get_object_or_404(
            Obligation.objects.select_for_update(), pk=obligation_id, company_id=company_id
        )
        payment = get_object_or_404(Settlement, pk=settlement_id, obligation=row)
        if payment.reversed_at:
            return Response(settlement_data(payment))
        # Mismo orden de locks que al conciliar: obligación, después movimiento.
        Transaction.objects.select_for_update().get(pk=payment.transaction_id)
        before = dict(ObligationOutput(row).data)
        row.outstanding_amount += payment.amount
        row.save(update_fields=["outstanding_amount"])
        payment.reversed_at = timezone.now()
        payment.save(update_fields=["reversed_at"])
        audit(
            request,
            row,
            "obligation.reconciliation_reversed",
            before,
            {**dict(ObligationOutput(row).data), "settlement_id": payment.id},
        )
    return Response(settlement_data(payment))


@api_view(["GET"])
def obligation_history(request, company_id, obligation_id):
    membership(request, company_id)
    get_object_or_404(Obligation, pk=obligation_id, company_id=company_id)
    rows = AuditLog.objects.filter(
        company_id=company_id, entity="obligation", entity_id=str(obligation_id)
    ).order_by("-id")
    pagination = PageNumberPagination()
    pagination.page_size = 20
    return pagination.get_paginated_response(
        list(
            pagination.paginate_queryset(
                rows.values("id", "user__username", "action", "before", "after", "created_at"),
                request,
            )
        )
    )


@api_view(["GET"])
def settlement_candidates(request, company_id, obligation_id):
    from django.db.models import DecimalField, F, Q, Value
    from django.db.models.functions import Abs, Coalesce

    membership(request, company_id)
    obligation = get_object_or_404(Obligation, pk=obligation_id, company_id=company_id)
    rows = Transaction.objects.filter(
        account__company_id=company_id, date__lte=F("account__balance_date")
    )
    rows = rows.filter(amount__gt=0) if obligation.direction == "in" else rows.filter(amount__lt=0)
    rows = rows.annotate(
        allocated=Coalesce(
            Sum("settlements__amount", filter=Q(settlements__reversed_at__isnull=True)),
            Value(Decimal(0)),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
    )
    rows = (
        rows.annotate(available=Abs(F("amount")) - F("allocated"))
        .filter(available__gt=0)
        .order_by("-date", "-id")
    )
    pagination = PageNumberPagination()
    pagination.page_size = 20
    return pagination.get_paginated_response(
        [
            {
                "id": row.id,
                "date": row.date,
                "description": row.description,
                "amount": str(row.amount),
                "available": str(row.available),
            }
            for row in pagination.paginate_queryset(rows, request)
        ]
    )
