from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import AuditLog, Company, CompanyMember


class RoleInput(serializers.Serializer):
    role = serializers.ChoiceField(choices=CompanyMember.Role.choices)


class AddMember(RoleInput):
    username = serializers.CharField(max_length=150)


def owner(request, company_id: int) -> CompanyMember:
    # Un lock común serializa las bajas/promociones, incluso con propietarios distintos.
    get_object_or_404(Company.objects.select_for_update(), pk=company_id)
    member = get_object_or_404(
        CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
    )
    if member.role != CompanyMember.Role.OWNER:
        raise PermissionDenied("Solo un propietario puede administrar el equipo.")
    return member


def record(
    request, company_id: int, member_id: int, action: str, before: dict, after: dict
) -> None:
    AuditLog.objects.create(
        company_id=company_id,
        user=request.user,
        entity="membership",
        entity_id=str(member_id),
        action=action,
        before=before,
        after=after,
    )


@api_view(["GET", "POST"])
def team(request, company_id):
    if request.method == "GET":
        member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
        rows = (
            CompanyMember.objects.filter(company_id=company_id)
            .select_related("user")
            .order_by("id")
        )
        pagination = PageNumberPagination()
        pagination.page_size = 20
        response = pagination.get_paginated_response(
            [
                {
                    "id": row.id,
                    "username": row.user.username,
                    "role": row.role,
                    "active": row.user.is_active,
                }
                for row in pagination.paginate_queryset(rows, request)
            ]
        )
        response.data["can_manage"] = member.role == "owner"
        response.data["my_membership_id"] = member.id
        return response
    with transaction.atomic():
        owner(request, company_id)
        serializer = AddMember(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        user = get_user_model().objects.filter(username=values["username"], is_active=True).first()
        if not user:
            raise ValidationError("El usuario debe tener una cuenta activa registrada.")
        if CompanyMember.objects.filter(company_id=company_id, user=user).exists():
            raise ValidationError(
                "Este usuario ya pertenece a la empresa. Edita su rol en la lista."
            )
        member = CompanyMember.objects.create(company_id=company_id, user=user, role=values["role"])
        record(
            request,
            company_id,
            member.id,
            "membership.added",
            {},
            {"username": user.username, "role": member.role},
        )
    return Response({"id": member.id, "role": member.role}, status=201)


@api_view(["PATCH", "DELETE"])
def change_member(request, company_id, member_id):
    with transaction.atomic():
        owner(request, company_id)
        target = get_object_or_404(
            CompanyMember.objects.select_for_update(), pk=member_id, company_id=company_id
        )
        role = None
        if request.method == "PATCH":
            serializer = RoleInput(data=request.data)
            serializer.is_valid(raise_exception=True)
            role = serializer.validated_data["role"]
        if target.role == "owner" and role != "owner":
            if (
                not CompanyMember.objects.filter(
                    company_id=company_id, role="owner", user__is_active=True
                )
                .exclude(pk=target.pk)
                .exists()
            ):
                raise ValidationError(
                    "Debe quedar al menos un propietario activo. Asigna otro antes de retirar este acceso."
                )
        before = {"username": target.user.username, "role": target.role}
        if request.method == "DELETE":
            record(request, company_id, target.id, "membership.removed", before, {})
            target.delete()
        else:
            target.role = role
            target.save(update_fields=["role"])
            record(
                request, company_id, target.id, "membership.role_changed", before, {"role": role}
            )
    return Response(status=204)


class CompanyName(serializers.Serializer):
    name = serializers.CharField(max_length=200)


@api_view(["PATCH"])
def rename_company(request, company_id):
    with transaction.atomic():
        owner(request, company_id)
        serializer = CompanyName(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = Company.objects.get(pk=company_id)
        old_name = company.name
        company.name = serializer.validated_data["name"]
        company.save(update_fields=["name"])
        AuditLog.objects.create(
            company=company,
            user=request.user,
            entity="company",
            entity_id=str(company.id),
            action="company.renamed",
            before={"name": old_name},
            after={"name": company.name},
        )
    return Response({"id": company.id, "name": company.name})
