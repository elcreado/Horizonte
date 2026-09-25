from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.banking.models import BankAccount

from .models import AuditLog, Company, CompanyMember


class CompanyInput(serializers.Serializer):
    company_name = serializers.CharField(max_length=200)
    nit = serializers.RegexField(r"^[A-Za-z0-9-]+$", max_length=30)
    account_name = serializers.CharField(max_length=120)
    opening_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance_date = serializers.DateField()

    def validate_balance_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("El corte no puede estar en el futuro.")
        return value


def create_company(user, values):
    """El llamador proporciona una transacción atómica para todo el alta."""
    if Company.objects.filter(nit__iexact=values["nit"]).exists():
        raise IntegrityError("NIT already exists")
    company = Company.objects.create(name=values["company_name"], nit=values["nit"].upper())
    CompanyMember.objects.create(company=company, user=user, role=CompanyMember.Role.OWNER)
    account = BankAccount.objects.create(
        company=company,
        name=values["account_name"],
        balance=values["opening_balance"],
        balance_date=values["balance_date"],
    )
    AuditLog.objects.create(
        company=company,
        user=user,
        action="company.created",
        entity="company",
        entity_id=str(company.pk),
        after={"name": company.name, "account_id": account.pk, "source": "manual_onboarding"},
    )
    return company


@api_view(["POST"])
def add_company(request):
    serializer = CompanyInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            company = create_company(request.user, serializer.validated_data)
    except IntegrityError:
        return Response(
            {"detail": "El NIT ya está registrado. Solicita acceso a su propietario."}, status=400
        )
    return Response({"id": company.pk, "name": company.name}, status=201)
