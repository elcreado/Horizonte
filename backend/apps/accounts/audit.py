from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import AuditLog, CompanyMember


@api_view(["GET"])
def audit_history(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    if member.role not in ("owner", "accountant"):
        return Response(
            {"detail": "La auditoría está disponible para propietario y contador."}, status=403
        )
    rows = (
        AuditLog.objects.filter(company_id=company_id)
        .select_related("user")
        .order_by("-created_at", "-id")
    )
    action = request.query_params.get("action", "").strip()
    if len(action) > 80:
        return Response({"detail": "Filtro de acción inválido."}, status=400)
    if action:
        rows = rows.filter(action=action)
    pagination = PageNumberPagination()
    pagination.page_size = 20
    return pagination.get_paginated_response(
        [
            {
                "id": row.pk,
                "created_at": row.created_at,
                "username": row.user.username,
                "action": row.action,
                "entity": row.entity,
                "entity_id": row.entity_id,
                "before": row.before,
                "after": row.after,
            }
            for row in pagination.paginate_queryset(rows, request)
        ]
    )
