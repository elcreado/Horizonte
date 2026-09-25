from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AuditLog, Company, CompanyMember
from config.celery import app

from .models import Invoice, InvoiceImport
from .parser import parse_invoice


@app.task(acks_late=True, reject_on_worker_lost=True)
def import_invoice(job_id: int) -> None:
    try:
        with transaction.atomic():
            job = InvoiceImport.objects.select_for_update().get(pk=job_id)
            if job.status != "queued":
                return
            if not CompanyMember.objects.filter(
                company=job.company,
                user=job.user,
                user__is_active=True,
                role__in=["owner", "accountant"],
            ).exists():
                raise ValueError("El usuario ya no tiene permiso para importar facturas.")
            company = Company.objects.select_for_update().get(pk=job.company_id)
            data = parse_invoice(job.content, company.nit)
            invoice, created = Invoice.objects.get_or_create(
                company=company,
                cufe=data["cufe"],
                defaults={
                    "number": data["number"],
                    "direction": data["direction"],
                    "data": data,
                },
            )
            if not created and invoice.data != data:
                raise ValueError(
                    "El CUFE existente tiene datos diferentes. No se reemplazó la factura."
                )
            job.invoice = invoice
            job.duplicate = not created
            job.content = ""
            job.status = "completed"
            job.finished_at = timezone.now()
            job.save()
            AuditLog.objects.create(
                company=company,
                user=job.user,
                entity="invoice",
                entity_id=str(invoice.id),
                action="invoice.imported" if created else "invoice.duplicate",
                after={"job_id": job.id},
            )
    except Exception as error:
        InvoiceImport.objects.filter(pk=job_id, status="queued").update(
            content="",
            status="failed",
            finished_at=timezone.now(),
            error=str(error)[:300]
            if isinstance(error, ValueError)
            else "No se pudo importar la factura. Intenta nuevamente.",
        )
