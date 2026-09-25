from django.contrib.auth import get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .onboarding import CompanyInput, create_company
from .views import LoginThrottle


class Registration(CompanyInput):
    username = serializers.RegexField(r"^[\w.@+-]+$", max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(min_length=10, max_length=128, trim_whitespace=False)
    password_confirm = serializers.CharField(max_length=128, trim_whitespace=False)

    def validate(self, values: dict) -> dict:
        if values["password"] != values["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        candidate = get_user_model()(username=values["username"], email=values["email"])
        try:
            validate_password(values["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from None
        return values


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
@csrf_protect
def register(request):
    if request.user.is_authenticated:
        return Response(
            {"detail": "Cierra la sesión actual para registrar otra cuenta."}, status=400
        )
    serializer = Registration(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    try:
        with transaction.atomic():
            user = get_user_model().objects.create_user(
                username=values["username"], email=values["email"], password=values["password"]
            )
            company = create_company(user, values)
    except IntegrityError:
        return Response(
            {"detail": "El usuario o NIT ya está registrado. Inicia sesión o utiliza otros datos."},
            status=400,
        )
    login(request, user)
    return Response({"username": user.username, "company_id": company.id}, status=201)
