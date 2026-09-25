from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AuditLog, CompanyMember


class ProfileInput(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False)
    email = serializers.EmailField(max_length=254, required=False)
    password = serializers.CharField(
        min_length=10, max_length=128, trim_whitespace=False, required=False
    )
    password_confirm = serializers.CharField(max_length=128, trim_whitespace=False, required=False)


@api_view(["GET", "PATCH"])
def profile(request):
    if request.method == "GET":
        return Response({"username": request.user.username, "email": request.user.email})
    serializer = ProfileInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    if not ("email" in values or "password" in values):
        return Response({"detail": "Indica un correo o una nueva contraseña."}, status=400)
    with transaction.atomic():
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if not user.check_password(values["current_password"]):
            return Response({"detail": "La contraseña actual no es correcta."}, status=400)
        if "password" in values and values["password"] != values.get("password_confirm"):
            return Response({"detail": "Las contraseñas nuevas no coinciden."}, status=400)
        if "email" in values:
            user.email = values["email"]
        if "password" in values:
            try:
                validate_password(values["password"], user=user)
            except DjangoValidationError as error:
                return Response({"detail": " ".join(error.messages)}, status=400)
            user.set_password(values["password"])
        user.save(update_fields=["email", "password"])
        for member in CompanyMember.objects.filter(user=user):
            AuditLog.objects.create(
                company=member.company,
                user=user,
                action="account.updated",
                entity="user",
                entity_id=str(user.pk),
                after={
                    "email_changed": "email" in values,
                    "password_changed": "password" in values,
                },
            )
    if "password" in values:
        update_session_auth_hash(request, user)
    return Response({"username": user.username, "email": user.email})
