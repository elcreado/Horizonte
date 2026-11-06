from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from config.background import enqueue

from .models import AuditLog, CompanyMember
from .tasks import send_password_recovery
from .throttles import PersistentUserThrottle


class RecoveryThrottle(PersistentUserThrottle):
    scope = "password_recovery"
    rate = "5/hour"


class RecoveryInput(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)


class ResetInput(serializers.Serializer):
    uid = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=150)
    password = serializers.CharField(min_length=10, max_length=128, trim_whitespace=False)
    password_confirm = serializers.CharField(max_length=128, trim_whitespace=False)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecoveryThrottle])
@csrf_protect
def recover_password(request):
    serializer = RecoveryInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        enqueue(send_password_recovery, kwargs=serializer.validated_data, retry=False)
    except Exception:
        return Response(
            {"detail": "El servicio de recuperación no está disponible. Intenta más tarde."},
            status=503,
        )
    return Response(
        {
            "detail": "Si el usuario y el correo corresponden a una cuenta activa, recibirás un enlace de recuperación."
        },
        status=202,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecoveryThrottle])
@csrf_protect
def reset_password(request):
    serializer = ResetInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    if values["password"] != values["password_confirm"]:
        return Response({"detail": "Las contraseñas no coinciden."}, status=400)
    try:
        user_id = int(urlsafe_base64_decode(values["uid"]).decode())
        if not 0 < user_id <= 9223372036854775807:
            raise ValueError("Invalid identifier")
    except (ValueError, TypeError, UnicodeError, OverflowError):
        return Response({"detail": "Enlace inválido o vencido."}, status=400)
    with transaction.atomic():
        user = (
            get_user_model().objects.select_for_update().filter(pk=user_id, is_active=True).first()
        )
        if not user or not default_token_generator.check_token(user, values["token"]):
            return Response({"detail": "Enlace inválido o vencido."}, status=400)
        try:
            validate_password(values["password"], user=user)
        except DjangoValidationError as error:
            return Response({"detail": " ".join(error.messages)}, status=400)
        user.set_password(values["password"])
        user.save(update_fields=["password"])
        for company_id in CompanyMember.objects.filter(user=user).values_list(
            "company_id", flat=True
        ):
            AuditLog.objects.create(
                company_id=company_id,
                user=user,
                entity="user",
                entity_id=str(user.pk),
                action="password.reset",
            )
    return Response({"detail": "Contraseña actualizada. Inicia sesión con la nueva contraseña."})
