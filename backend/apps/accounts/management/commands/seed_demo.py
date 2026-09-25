import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, Transaction
from apps.forecast.models import Obligation


class Command(BaseCommand):
    help = "Crea datos sintéticos idempotentes y un usuario local demo."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("La demo solo se genera en desarrollo.")
        password = os.environ.get("DEMO_PASSWORD")
        if not password or len(password) < 12:
            raise CommandError("Define DEMO_PASSWORD con al menos 12 caracteres.")
        user, created = get_user_model().objects.get_or_create(username="demo")
        if created:
            user.set_password(password)
            user.save()
        company, _ = Company.objects.get_or_create(
            nit="SYNTHETIC-001", defaults={"name": "Café Horizonte · Demo"}
        )
        CompanyMember.objects.get_or_create(company=company, user=user, defaults={"role": "owner"})
        account, _ = BankAccount.objects.get_or_create(
            company=company,
            name="Cuenta sintética",
            defaults={
                "balance": Decimal("8500000"),
                "balance_date": timezone.localdate(),
            },
        )
        as_of = account.balance_date
        for i in range(60):
            Transaction.objects.get_or_create(
                account=account,
                external_id=f"demo-{i}",
                defaults={
                    "date": as_of - timedelta(days=i),
                    "amount": Decimal("180000") if i % 3 else Decimal("-240000"),
                    "description": "Ventas del día" if i % 3 else "Compra de insumos",
                    "category": "Ventas" if i % 3 else "Proveedores",
                },
            )
        for ref, label, direction, day, amount in [
            ("rent", "Arriendo del local", "out", 5, "2200000"),
            ("sales", "Cobro cliente mayorista", "in", 10, "3100000"),
            ("supplier", "Pago de proveedores", "out", 16, "4800000"),
            ("payroll", "Nómina", "out", 23, "5800000"),
            ("client", "Cobro de catering", "in", 28, "2400000"),
        ]:
            Obligation.objects.get_or_create(
                company=company,
                reference=ref,
                defaults={
                    "description": label,
                    "direction": direction,
                    "due_date": as_of + timedelta(days=day),
                    "outstanding_amount": Decimal(amount),
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Demo disponible. Usuario: demo. Se conservan usuarios y datos existentes."
            )
        )
