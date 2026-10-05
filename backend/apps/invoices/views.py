import hashlib
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.accounts.models import AuditLog
from apps.forecast.models import Obligation
from apps.forecast.obligations import membership
from config.background import create_job, dispatch_job

from .models import Invoice, InvoiceImport
from .tasks import import_invoice


def invoice_data(row: Invoice) -> dict:
    return {
        "id": row.id,
        **row.data,
        "obligation_id": row.obligation_id,
        "outstanding_amount": str(row.obligation.outstanding_amount) if row.obligation else None,
        "cancelled": row.obligation.cancelled if row.obligation else False,
    }


@api_view(["GET"])
def invoices(request, company_id):
    member = membership(request, company_id)
    rows = (
        Invoice.objects.filter(company_id=company_id).select_related("obligation").order_by("-id")
    )
    pagination = PageNumberPagination()
    pagination.page_size = 20
    result = pagination.get_paginated_response(
        [invoice_data(row) for row in pagination.paginate_queryset(rows, request)]
    )
    result.data["can_edit"] = member.role in ("owner", "accountant")
    return result


@api_view(["GET", "POST"])
def invoice_imports(request, company_id):
    if request.method == "GET":
        membership(request, company_id)
        return Response(
            list(
                InvoiceImport.objects.filter(company_id=company_id)
                .order_by("-id")
                .values(
                    "id", "status", "error", "invoice_id", "duplicate", "created_at", "finished_at"
                )[:20]
            )
        )
    with transaction.atomic():
        membership(request, company_id, write=True)
        upload = request.FILES.get("file")
        if not upload or not upload.name.lower().endswith(".xml") or upload.size > 2 * 1024 * 1024:
            raise ValidationError("Selecciona un archivo XML UTF-8 de hasta 2 MB.")
        try:
            content = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValidationError("El archivo debe utilizar UTF-8.") from None
        job = create_job(
            import_invoice, InvoiceImport, company_id=company_id, user=request.user, content=content
        )
    try:
        dispatch_job(import_invoice, args=[job.id], retry=False)
    except Exception:
        job.status = "failed"
        job.error = "La cola no está disponible. Vuelve a cargar el XML cuando se recupere la cola."
        job.content = ""
        job.finished_at = timezone.now()
        job.save()
        return Response({"detail": job.error}, status=503)
    return Response({"id": job.id, "status": job.status}, status=202)


class ConfirmInvoice(serializers.Serializer):
    due_date = serializers.DateField()
    outstanding_amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal(0)
    )


@api_view(["POST"])
def confirm_invoice(request, company_id, invoice_id):
    with transaction.atomic():
        membership(request, company_id, write=True)
        invoice = get_object_or_404(
            Invoice.objects.select_for_update(), pk=invoice_id, company_id=company_id
        )
        if invoice.obligation_id:
            return Response(invoice_data(invoice))
        serializer = ConfirmInvoice(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if values["due_date"].isoformat() < invoice.data["issue_date"]:
            raise ValidationError("La fecha esperada no puede ser anterior a la emisión.")
        if values["outstanding_amount"] > Decimal(invoice.data["payable"]):
            raise ValidationError("El pendiente no puede exceder el importe pagadero del XML.")
        reference = "xml:" + hashlib.sha256(invoice.cufe.encode()).hexdigest()
        if Obligation.objects.filter(company_id=company_id, reference=reference).exists():
            raise ValidationError(
                "La referencia está ocupada por una obligación existente; revisa la coincidencia."
            )
        invoice.obligation = Obligation.objects.create(
            company_id=company_id,
            reference=reference,
            description=f"Factura {invoice.number}",
            counterparty=invoice.data["customer"]
            if invoice.direction == "in"
            else invoice.data["supplier"],
            direction=invoice.direction,
            **values,
        )
        invoice.save(update_fields=["obligation"])
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            entity="invoice",
            entity_id=str(invoice.id),
            action="invoice.confirmed",
            after={
                "obligation_id": invoice.obligation_id,
                "due_date": str(values["due_date"]),
                "outstanding_amount": str(values["outstanding_amount"]),
            },
        )
    return Response(invoice_data(invoice), status=201)


class LinkObligation(serializers.Serializer):
    obligation_id = serializers.IntegerField(min_value=1)


@api_view(["GET", "POST"])
def link_obligation(request, company_id, invoice_id):
    if request.method == "GET":
        membership(request, company_id)
        invoice = get_object_or_404(Invoice, pk=invoice_id, company_id=company_id)
        rows = Obligation.objects.filter(
            company_id=company_id,
            direction=invoice.direction,
            cancelled=False,
            invoice__isnull=True,
            outstanding_amount__lte=Decimal(invoice.data["payable"]),
            due_date__gte=invoice.data["issue_date"],
        ).order_by("due_date", "id")
        pagination = PageNumberPagination()
        pagination.page_size = 20
        return pagination.get_paginated_response(
            [
                {
                    "id": row.id,
                    "reference": row.reference,
                    "description": row.description,
                    "counterparty": row.counterparty,
                    "due_date": row.due_date,
                    "outstanding_amount": str(row.outstanding_amount),
                }
                for row in pagination.paginate_queryset(rows, request)
            ]
        )
    with transaction.atomic():
        membership(request, company_id, write=True)
        invoice = get_object_or_404(
            Invoice.objects.select_for_update(), pk=invoice_id, company_id=company_id
        )
        serializer = LinkObligation(data=request.data)
        serializer.is_valid(raise_exception=True)
        obligation_id = serializer.validated_data["obligation_id"]
        if invoice.obligation_id:
            if invoice.obligation_id != obligation_id:
                raise ValidationError("La factura ya está vinculada a otra obligación.")
            return Response(invoice_data(invoice))
        obligation = get_object_or_404(
            Obligation.objects.select_for_update(), pk=obligation_id, company_id=company_id
        )
        if obligation.cancelled or obligation.direction != invoice.direction:
            raise ValidationError(
                "La obligación debe estar vigente y tener el mismo sentido que la factura."
            )
        if obligation.due_date.isoformat() < invoice.data[
            "issue_date"
        ] or obligation.outstanding_amount > Decimal(invoice.data["payable"]):
            raise ValidationError(
                "La fecha o el valor pendiente de la obligación no son compatibles con la factura."
            )
        if Invoice.objects.filter(obligation=obligation).exists():
            raise ValidationError("La obligación ya está vinculada a otra factura.")
        invoice.obligation = obligation
        invoice.save(update_fields=["obligation"])
        details = {
            "invoice_id": invoice.id,
            "obligation_id": obligation.id,
            "outstanding_amount": str(obligation.outstanding_amount),
            "due_date": str(obligation.due_date),
        }
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            entity="invoice",
            entity_id=str(invoice.id),
            action="invoice.obligation_linked",
            after=details,
        )
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            entity="obligation",
            entity_id=str(obligation.id),
            action="invoice.obligation_linked",
            after=details,
        )
    return Response(invoice_data(invoice))
