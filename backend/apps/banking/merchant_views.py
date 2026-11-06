from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from apps.classify.services import normalize

from .models import Merchant, MerchantAlias


class MerchantAliasInput(serializers.Serializer):
    merchant_id = serializers.IntegerField(min_value=1)
    provider = serializers.ChoiceField(choices=["manual_upload", "mock"])
    name = serializers.CharField(max_length=250)

    def validate_name(self, value):
        key = normalize(value)
        if not key or len(key) > 250:
            raise serializers.ValidationError(
                "La etiqueta normalizada debe tener entre 1 y 250 caracteres."
            )
        return key


@api_view(["GET", "POST"])
def merchant_aliases(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    if request.method == "POST":
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        serializer = MerchantAliasInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            member = get_object_or_404(
                CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
            )
            if member.role not in ("owner", "accountant"):
                return Response({"detail": "Tu rol solo permite consultar."}, status=403)
            merchant = get_object_or_404(Merchant, company_id=company_id, pk=data["merchant_id"])
            alias, created = MerchantAlias.objects.select_for_update().get_or_create(
                company_id=company_id,
                provider=data["provider"],
                normalized_name=data["name"],
                defaults={"merchant": merchant},
            )
            before = None if created else alias.merchant_id
            if created or before != merchant.pk:
                alias.merchant = merchant
                alias.save(update_fields=["merchant"])
                AuditLog.objects.create(
                    company_id=company_id,
                    user=request.user,
                    action="merchant.alias_assigned",
                    entity="MerchantAlias",
                    entity_id=str(alias.pk),
                    before={"merchant_id": before},
                    after={
                        "merchant_id": merchant.pk,
                        "provider": alias.provider,
                        "normalized_name": alias.normalized_name,
                    },
                )
        return Response(
            {"id": alias.pk, "merchant_id": merchant.pk}, status=201 if created else 200
        )
    rows = (
        MerchantAlias.objects.filter(company_id=company_id)
        .select_related("merchant")
        .order_by("provider", "normalized_name", "pk")
    )
    pagination = PageNumberPagination()
    pagination.page_size = 20
    response = pagination.get_paginated_response(
        [
            {
                "id": row.pk,
                "provider": row.provider,
                "normalized_name": row.normalized_name,
                "merchant_id": row.merchant_id,
                "merchant_display_name": row.merchant.display_name,
            }
            for row in pagination.paginate_queryset(rows, request)
        ]
    )
    response.data["can_edit"] = member.role in ("owner", "accountant")
    return response


class MerchantNameInput(serializers.Serializer):
    display_name = serializers.CharField(max_length=250)


@api_view(["PATCH"])
def rename_merchant(request, company_id, merchant_id):
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        serializer = MerchantNameInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = get_object_or_404(
            Merchant.objects.select_for_update(), company_id=company_id, pk=merchant_id
        )
        before = merchant.display_name
        merchant.display_name = serializer.validated_data["display_name"]
        if before != merchant.display_name:
            merchant.save(update_fields=["display_name"])
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="merchant.renamed",
                entity="Merchant",
                entity_id=str(merchant.pk),
                before={"display_name": before},
                after={"display_name": merchant.display_name},
            )
    return Response({"id": merchant.pk, "display_name": merchant.display_name})


@api_view(["GET"])
def merchants(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    rows = (
        Merchant.objects.filter(company_id=company_id)
        .annotate(movement_count=Count("transaction"))
        .order_by("display_name", "pk")
    )
    pagination = PageNumberPagination()
    pagination.page_size = 20
    response = pagination.get_paginated_response(
        [
            {
                "id": row.pk,
                "display_name": row.display_name,
                "normalized_name": row.normalized_name,
                "movement_count": row.movement_count,
            }
            for row in pagination.paginate_queryset(rows, request)
        ]
    )
    response.data["can_edit"] = member.role in ("owner", "accountant")
    return response
