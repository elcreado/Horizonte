"""Consulta administrativa transversal, reservada a superusuarios de plataforma."""

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission


class PlatformAdministrator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated and user.is_active and user.is_staff and user.is_superuser
        )


@api_view(["GET"])
@permission_classes([PlatformAdministrator])
def platform_users(request):
    rows = get_user_model().objects.annotate(company_count=Count("companymember")).order_by("pk")
    pagination = PageNumberPagination()
    pagination.page_size = 20
    return pagination.get_paginated_response(
        [
            {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "company_count": user.company_count,
            }
            for user in pagination.paginate_queryset(rows, request)
        ]
    )
