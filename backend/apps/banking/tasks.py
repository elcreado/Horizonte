import base64
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import CompanyMember
from apps.classify.models import ClassificationRule
from apps.classify.services import classify
from config.celery import app

from . import sync  # noqa: F401 - registra la tarea en el worker Celery
from .imports import parse_csv
from .merchants import resolve_merchants
from .models import BankAccount, ImportJob, Transaction
from .normalization import normalize_movement
from .xlsx import parse_xlsx


@app.task(acks_late=True, reject_on_worker_lost=True)
def import_csv(job_id: int) -> None:
    """Carga atómica; el lock de cuenta serializa importaciones concurrentes."""
    try:
        with transaction.atomic():
            job = ImportJob.objects.select_for_update().get(pk=job_id)
            if job.status != "queued":
                return
            if not CompanyMember.objects.filter(
                company_id=job.account.company_id,
                user_id=job.user_id,
                user__is_active=True,
                role__in=["owner", "accountant"],
            ).exists():
                raise ValueError("El usuario ya no tiene permiso para importar.")
            account = BankAccount.objects.select_for_update().get(pk=job.account_id)
            rows = (
                parse_xlsx(base64.b64decode(job.content, validate=True))
                if job.file_format == "xlsx"
                else parse_csv(job.content)
            )
            unique_rows = {row["external_id"]: row for row in rows}
            identifiers = list(unique_rows)
            existing = {}
            for offset in range(0, len(identifiers), 1000):
                existing.update(
                    {
                        item.external_id: item
                        for item in Transaction.objects.filter(
                            account=account, external_id__in=identifiers[offset : offset + 1000]
                        )
                    }
                )
            remembered_rules = {
                (rule.normalized_description, rule.direction): rule.category
                for rule in ClassificationRule.objects.filter(company_id=account.company_id)
            }
            pending = []
            for row in unique_rows.values():
                if row["date"] > account.balance_date.isoformat():
                    raise ValueError(
                        "Hay movimientos posteriores al corte del saldo. Actualiza el corte antes de importarlos."
                    )
                movement = existing.get(row["external_id"])
                if movement:
                    if (
                        str(movement.date) != row["date"]
                        or movement.amount != Decimal(row["amount"])
                        or movement.description != row["description"]
                    ):
                        raise ValueError(
                            "Un ID existente tiene datos distintos. No se importó ninguna fila."
                        )
                    continue
                category, source = classify(
                    account.company_id, row["description"], Decimal(row["amount"]), remembered_rules
                )
                pending.append(
                    Transaction(
                        account=account,
                        **row,
                        **normalize_movement(row["description"]),
                        category=category,
                        classification_source=source,
                    )
                )
            merchant_ids = resolve_merchants(
                account.company_id, "manual_upload", (item.merchant_name for item in pending)
            )
            for item in pending:
                item.merchant_id = merchant_ids.get(item.merchant_name)
            # El lock de cuenta serializa importadores; la restricción única sigue siendo obligatoria.
            Transaction.objects.bulk_create(pending, batch_size=500)
            created = len(pending)
            if (
                created
                and account.history_complete_from
                and any(
                    account.history_complete_from.isoformat()
                    <= row["date"]
                    <= account.history_complete_through.isoformat()
                    for row in unique_rows.values()
                    if row["external_id"] not in existing
                )
            ):
                account.history_complete_from = None
                account.history_complete_through = None
                account.history_confirmed_at = None
                account.history_confirmed_by = None
                account.save(
                    update_fields=[
                        "history_complete_from",
                        "history_complete_through",
                        "history_confirmed_at",
                        "history_confirmed_by",
                    ]
                )
            job.status = "completed"
            job.created_count = created
            job.duplicate_count = len(rows) - created
            job.content = ""
            job.finished_at = timezone.now()
            job.save()
    except Exception as error:
        ImportJob.objects.filter(pk=job_id, status="queued").update(
            status="failed",
            content="",
            finished_at=timezone.now(),
            error=str(error)[:300]
            if isinstance(error, ValueError)
            else "No se pudo procesar el archivo. Intenta cargarlo nuevamente.",
        )
