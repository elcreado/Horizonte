"""Sincronización idempotente de fuentes bancarias autorizadas."""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AuditLog, CompanyMember
from apps.classify.models import ClassificationRule
from apps.classify.services import classify
from config.celery import app

from .merchants import resolve_merchants
from .models import BankAccount, BankConnection, BankSyncJob, Transaction
from .normalization import normalize_movement
from .providers import PROVIDERS


@app.task(acks_late=True, reject_on_worker_lost=True)
def sync_bank(job_id: int) -> None:
    try:
        with transaction.atomic():
            connection_id = BankSyncJob.objects.values_list("connection_id", flat=True).get(
                pk=job_id
            )
            connection = (
                BankConnection.objects.select_for_update()
                .select_related("consent")
                .get(pk=connection_id)
            )
            job = BankSyncJob.objects.select_for_update().get(pk=job_id)
            if job.status != "queued":
                return
            if connection.status != "active" or connection.consent.revoked_at:
                raise ValueError("La conexión ya no está autorizada.")
            if not CompanyMember.objects.filter(
                company_id=connection.company_id,
                user_id=job.user_id,
                user__is_active=True,
                role__in=["owner", "accountant"],
            ).exists():
                raise ValueError("El usuario ya no tiene permiso para sincronizar.")
            account = BankAccount.objects.select_for_update().get(connection=connection)
            balance, movements = PROVIDERS[connection.provider].snapshot(
                connection.pk, account.balance_date
            )
            if not movements or any(row.date > account.balance_date for row in movements):
                raise ValueError("La fuente entregó un periodo inválido.")
            existing = {
                row.external_id: row
                for row in Transaction.objects.filter(
                    account=account, external_id__in=[row.external_id for row in movements]
                )
            }
            remembered_rules = {
                (rule.normalized_description, rule.direction): rule.category
                for rule in ClassificationRule.objects.filter(company_id=connection.company_id)
            }
            pending = []
            for row in movements:
                old = existing.get(row.external_id)
                if old:
                    if (old.date, old.amount, old.description) != (
                        row.date,
                        row.amount,
                        row.description,
                    ):
                        raise ValueError("La fuente cambió un movimiento existente.")
                    continue
                category, source = classify(
                    connection.company_id, row.description, row.amount, remembered_rules
                )
                pending.append(
                    Transaction(
                        account=account,
                        external_id=row.external_id,
                        date=row.date,
                        amount=row.amount,
                        description=row.description,
                        **normalize_movement(row.description),
                        category=category,
                        classification_source=source,
                    )
                )
            merchant_ids = resolve_merchants(
                connection.company_id,
                connection.provider,
                (item.merchant_name for item in pending),
            )
            for item in pending:
                item.merchant_id = merchant_ids.get(item.merchant_name)
            Transaction.objects.bulk_create(pending, batch_size=500)
            account.balance = balance
            account.history_complete_from = min(row.date for row in movements)
            account.history_complete_through = account.balance_date
            account.history_confirmed_at = timezone.now()
            account.history_confirmed_by = None  # Cobertura declarada por la fuente sintética.
            account.save(
                update_fields=[
                    "balance",
                    "history_complete_from",
                    "history_complete_through",
                    "history_confirmed_at",
                    "history_confirmed_by",
                ]
            )
            job.status = "completed"
            job.created_count = len(pending)
            job.duplicate_count = len(movements) - len(pending)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "created_count", "duplicate_count", "finished_at"])
            AuditLog.objects.create(
                company_id=connection.company_id,
                user_id=job.user_id,
                action="bank.synced",
                entity="BankConnection",
                entity_id=str(connection.pk),
                after={
                    "job_id": job.pk,
                    "created": len(pending),
                    "duplicates": job.duplicate_count,
                },
            )
    except Exception as error:
        BankSyncJob.objects.filter(pk=job_id, status="queued").update(
            status="failed",
            error=str(error)[:300]
            if isinstance(error, ValueError)
            else "No se pudo sincronizar la fuente bancaria.",
            finished_at=timezone.now(),
        )
