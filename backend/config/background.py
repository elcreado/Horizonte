"""Cola persistente opcional para un servicio gratuito sin broker externo."""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException


class QueueUnavailable(APIException):
    status_code = 503
    default_detail = (
        "No se pudo guardar la tarea. El servicio no está disponible; vuelve a intentarlo."
    )
    default_code = "queue_unavailable"


def enqueue(task, args=None, kwargs=None, retry=False):
    if settings.BACKGROUND_MODE == "celery":
        return task.apply_async(args=args, kwargs=kwargs, retry=retry)
    from apps.accounts.models import BackgroundTask

    if task.name not in task_registry():
        raise ValueError("Tarea no autorizada para la cola persistente.")
    return BackgroundTask.objects.create(
        name=task.name, args=args or [], kwargs=kwargs or {}, available_at=timezone.now()
    )


def task_registry():
    from apps.accounts.tasks import send_password_recovery
    from apps.banking.sync import sync_bank
    from apps.banking.tasks import import_csv
    from apps.invoices.tasks import import_invoice

    return {
        task.name: task for task in [send_password_recovery, sync_bank, import_csv, import_invoice]
    }


def create_job(task, model, **fields):
    """Guardar trabajo y mensaje juntos cuando ambos residen en PostgreSQL."""
    with transaction.atomic():
        job = model.objects.create(**fields)
        if settings.BACKGROUND_MODE == "database":
            try:
                enqueue(task, args=[job.pk])
            except (DatabaseError, OSError):
                # Salir del bloque atómico revierte también el trabajo de dominio.
                raise QueueUnavailable() from None
        return job


def dispatch_job(task, args, retry=False):
    if settings.BACKGROUND_MODE == "celery":
        return enqueue(task, args=args, retry=retry)
    return None


def fail_domain_job(job):
    from apps.banking.models import BankSyncJob, ImportJob
    from apps.banking.sync import sync_bank
    from apps.banking.tasks import import_csv
    from apps.invoices.models import InvoiceImport
    from apps.invoices.tasks import import_invoice

    models = {
        sync_bank.name: BankSyncJob,
        import_csv.name: ImportJob,
        import_invoice.name: InvoiceImport,
    }
    model = models.get(job.name)
    if model is None or not job.args:
        return
    updates = {
        "status": "failed",
        "error": "La tarea agotó sus reintentos. Vuelve a solicitar la operación.",
        "finished_at": timezone.now(),
    }
    if model in (ImportJob, InvoiceImport):
        updates["content"] = ""
    model.objects.filter(pk=job.args[0], status="queued").update(**updates)


def run_one():
    from apps.accounts.models import BackgroundTask

    now = timezone.now()
    with transaction.atomic():
        job = (
            BackgroundTask.objects.select_for_update()
            .filter(status__in=["queued", "running"], available_at__lte=now)
            .order_by("id")
            .first()
        )
        if not job:
            return False
        if job.attempts >= 3:
            fail_domain_job(job)
            job.status = "failed"
            job.args, job.kwargs = [], {}
            job.finished_at = now
            job.save()
            return True
        job.status = "running"
        job.attempts += 1
        job.lease = uuid.uuid4()
        job.available_at = now + timedelta(minutes=15)
        job.save()
    try:
        task_registry()[job.name].run(*job.args, **job.kwargs)
    except Exception:
        terminal = job.attempts >= 3
        updates = {
            "status": "failed" if terminal else "queued",
            "available_at": timezone.now() + timedelta(seconds=30 * job.attempts),
        }
        if terminal:
            updates.update(args=[], kwargs={}, finished_at=timezone.now())
    else:
        updates = {"status": "completed", "args": [], "kwargs": {}, "finished_at": timezone.now()}
    with transaction.atomic():
        owned = (
            BackgroundTask.objects.select_for_update()
            .filter(pk=job.pk, lease=job.lease, status="running")
            .first()
        )
        if owned:
            if updates["status"] == "failed":
                fail_domain_job(owned)
            BackgroundTask.objects.filter(pk=owned.pk).update(**updates)
    return True
