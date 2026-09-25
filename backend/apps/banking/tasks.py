import base64
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import CompanyMember
from apps.classify.services import classify
from config.celery import app

from .imports import parse_csv
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
            created = 0
            for row in rows:
                if row["date"] > account.balance_date.isoformat():
                    raise ValueError(
                        "Hay movimientos posteriores al corte del saldo. Actualiza el corte antes de importarlos."
                    )
                movement, new = Transaction.objects.get_or_create(
                    account=account,
                    external_id=row["external_id"],
                    defaults={
                        **{key: row[key] for key in ["date", "amount", "description"]},
                        **normalize_movement(row["description"]),
                    },
                )
                if not new and (
                    str(movement.date) != row["date"]
                    or str(movement.amount) != row["amount"]
                    or movement.description != row["description"]
                ):
                    raise ValueError(
                        "Un ID existente tiene datos distintos. No se importó ninguna fila."
                    )
                if new:
                    movement.category, movement.classification_source = classify(
                        account.company_id, row["description"], Decimal(row["amount"])
                    )
                    movement.save(update_fields=["category", "classification_source"])
                created += int(new)
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
