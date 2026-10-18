"""Prepare isolated, reproducible local demo companies without resetting existing data."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import AuditLog
from apps.accounts.onboarding import create_company
from apps.banking.models import BankAccount, ManualEntry, Transaction
from apps.banking.normalization import normalize_movement
from apps.classify.services import classify
from apps.forecast.models import Obligation


class Command(BaseCommand):
    help = "Crea dos empresas nuevas para demostrar la V1 en SQLite local, sin borrar datos ni cambiar usuarios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="Usuario local existente que será propietario de las empresas nuevas.",
        )
        parser.add_argument(
            "--as-of",
            type=date.fromisoformat,
            default=None,
            help="Corte YYYY-MM-DD (hoy por defecto, nunca futuro).",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Muestra los escenarios sin escribir datos."
        )

    def handle(self, *args, **options):
        if not settings.DEBUG or connection.vendor != "sqlite":
            raise CommandError(
                "Este comando requiere desarrollo con SQLite local; no se ejecuta sobre PostgreSQL ni producción."
            )
        user = get_user_model().objects.filter(username=options["username"], is_active=True).first()
        if user is None:
            raise CommandError(
                "El usuario local no existe o está inactivo. Crea primero tu cuenta desde la web."
            )
        cutoff = options["as_of"] or timezone.localdate()
        if cutoff > timezone.localdate():
            raise CommandError("El corte no puede estar en el futuro.")
        if cutoff < date(1900, 1, 7) or cutoff > date(9998, 12, 31):
            raise CommandError(
                "El corte debe permitir siete días de historial y 90 días de proyección."
            )
        self.stdout.write(f"Corte: {cutoff.isoformat()} · propietario: {user.username}")
        self.stdout.write(
            "Obligaciones: saldo 500000 + cobro 119000 (día 10) - pago 700000 (día 15) = -81000 COP."
        )
        self.stdout.write(
            "Historial manual: ingreso 70000 - egreso 140000 en siete días completos = -10000 COP/día; saldo final 30/60/90 = 200000/-100000/-400000 COP."
        )
        if options["dry_run"]:
            self.stdout.write(
                "Simulación: no se crearon empresas, cuentas, movimientos ni auditorías."
            )
            return
        batch = uuid4().hex[:12]
        with transaction.atomic():
            created = []
            for scenario in ("Obligaciones", "Historial manual"):
                company = create_company(
                    user,
                    {
                        "company_name": f"Demo V1 {scenario} · {cutoff} · {batch}",
                        "nit": f"DEMO-{batch}-{'O' if scenario == 'Obligaciones' else 'H'}",
                        "account_name": "Caja sintética V1",
                        "opening_balance": Decimal("500000.00"),
                        "balance_date": cutoff,
                    },
                )
                company.liquidity_threshold = Decimal("100000.00")
                company.save(update_fields=["liquidity_threshold"])
                account = BankAccount.objects.get(company=company)
                if scenario == "Obligaciones":
                    for ref, description, direction, offset, amount in [
                        ("cobro-demo", "Cobro de demostración", "in", 10, "119000.00"),
                        ("pago-demo", "Pago de demostración", "out", 15, "700000.00"),
                    ]:
                        Obligation.objects.create(
                            company=company,
                            reference=ref,
                            description=description,
                            direction=direction,
                            due_date=cutoff + timedelta(days=offset),
                            outstanding_amount=Decimal(amount),
                        )
                else:
                    for direction, amount, offset, description in [
                        ("in", Decimal("70000.00"), 6, "Venta sintética V1"),
                        ("out", Decimal("140000.00"), 0, "Insumos sintéticos V1"),
                    ]:
                        request_id = uuid4()
                        day = cutoff - timedelta(days=offset)
                        signed = amount if direction == "in" else -amount
                        category, source = classify(company.pk, description, signed)
                        movement = Transaction.objects.create(
                            account=account,
                            external_id=f"manual:{request_id}",
                            date=day,
                            amount=signed,
                            description=description,
                            category=category,
                            classification_source=source,
                            **normalize_movement(description),
                        )
                        payload = {
                            "request_id": str(request_id),
                            "account_id": account.pk,
                            "date": day.isoformat(),
                            "direction": direction,
                            "amount": str(amount),
                            "description": description,
                            "category": "",
                        }
                        ManualEntry.objects.create(
                            company=company,
                            request_id=request_id,
                            transaction=movement,
                            payload=payload,
                            user=user,
                        )
                        AuditLog.objects.create(
                            company=company,
                            user=user,
                            action="transaction.manual_created",
                            entity="Transaction",
                            entity_id=str(movement.pk),
                            after={**payload, "entry_source": "manual", "coverage_revoked": False},
                        )
                    account.history_complete_from = cutoff - timedelta(days=6)
                    account.history_complete_through = cutoff
                    account.history_confirmed_by = user
                    account.history_confirmed_at = timezone.now()
                    account.save(
                        update_fields=[
                            "history_complete_from",
                            "history_complete_through",
                            "history_confirmed_by",
                            "history_confirmed_at",
                        ]
                    )
                AuditLog.objects.create(
                    company=company,
                    user=user,
                    action="demo.prepared",
                    entity="Company",
                    entity_id=str(company.pk),
                    after={
                        "scenario": scenario,
                        "cutoff": cutoff.isoformat(),
                        "batch": batch,
                        "synthetic": True,
                    },
                )
                created.append((company.pk, company.name))
        for identifier, name in created:
            self.stdout.write(self.style.SUCCESS(f"Empresa {identifier}: {name}"))
        self.stdout.write(
            "Entra con tu cuenta y selecciona cada empresa en la barra superior. Las empresas anteriores permanecen intactas."
        )
