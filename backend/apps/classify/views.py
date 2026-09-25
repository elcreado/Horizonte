from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from apps.banking.models import Transaction

from .models import ClassificationChange, ClassificationRule
from .services import categories, normalize


@api_view(["GET"])
def movements(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    queryset = Transaction.objects.filter(account__company_id=company_id).order_by("-date", "-id")
    pagination = PageNumberPagination()
    pagination.page_size = 20
    rows = pagination.paginate_queryset(queryset, request)
    response = pagination.get_paginated_response(
        [
            {
                "id": row.id,
                "date": row.date,
                "description": row.description,
                "normalized_description": row.normalized_description,
                "merchant_name": row.merchant_name,
                "amount": str(row.amount),
                "category": row.category,
                "source": row.classification_source,
                "categories": categories(row.amount),
            }
            for row in rows
        ]
    )
    response.data["can_edit"] = member.role in ("owner", "accountant")
    return response


@api_view(["PATCH"])
def correct(request, company_id, transaction_id):
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        movement = get_object_or_404(
            Transaction.objects.select_for_update(),
            pk=transaction_id,
            account__company_id=company_id,
        )
        category = request.data.get("category")
        remember = request.data.get("remember", False)
        if (
            not isinstance(category, str)
            or category not in categories(movement.amount)
            or not isinstance(remember, bool)
        ):
            return Response(
                {"detail": "Categoría o preferencia inválida para este movimiento."}, status=400
            )
        if remember and not movement.amount:
            return Response(
                {"detail": "No se crean reglas para movimientos de valor cero."}, status=400
            )
        ClassificationChange.objects.create(
            transaction=movement,
            user=request.user,
            previous_category=movement.category,
            category=category,
            remembered=remember,
        )
        movement.category = category
        movement.classification_source = "manual"
        movement.save(update_fields=["category", "classification_source"])
        if remember:
            ClassificationRule.objects.update_or_create(
                company_id=company_id,
                normalized_description=normalize(movement.description),
                direction="in" if movement.amount > 0 else "out",
                defaults={"category": category},
            )
    return Response({"category": category, "source": "manual"})


@api_view(["GET"])
def rules(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    pagination = PageNumberPagination()
    pagination.page_size = 20
    rows = ClassificationRule.objects.filter(company_id=company_id).order_by(
        "normalized_description", "id"
    )
    response = pagination.get_paginated_response(
        list(
            pagination.paginate_queryset(
                rows.values("id", "normalized_description", "direction", "category", "updated_at"),
                request,
            )
        )
    )
    response.data["can_edit"] = member.role in ("owner", "accountant")
    return response


@api_view(["DELETE"])
def delete_rule(request, company_id, rule_id):
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        rule = get_object_or_404(
            ClassificationRule.objects.select_for_update(), pk=rule_id, company_id=company_id
        )
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            action="classification.rule_deleted",
            entity="ClassificationRule",
            entity_id=str(rule.pk),
            before={
                "description": rule.normalized_description,
                "direction": rule.direction,
                "category": rule.category,
            },
            after={},
        )
        rule.delete()
    return Response(status=204)
