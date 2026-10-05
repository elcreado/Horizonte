import base64
import hashlib

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, CompanyMember
from config.background import create_job, dispatch_job

from .models import BankAccount, ImportJob, Transaction
from .tasks import import_csv


@api_view(["GET"])
def accounts(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    rows = list(
        BankAccount.objects.filter(company_id=company_id).values(
            "id",
            "name",
            "connection_id",
            "currency",
            "balance",
            "balance_date",
            "history_complete_from",
            "history_complete_through",
        )
    )
    for row in rows:
        # El encoder JSON de DRF convierte Decimal en float: conservar céntimos en texto.
        row["balance"] = str(row["balance"])
    return Response(
        {
            "can_import": member.role in ("owner", "accountant"),
            "accounts": rows,
        }
    )


def job_data(job: ImportJob) -> dict:
    return {
        key: getattr(job, key)
        for key in (
            "id",
            "account_id",
            "file_format",
            "status",
            "created_count",
            "duplicate_count",
            "error",
            "created_at",
            "finished_at",
        )
    }


@api_view(["GET", "POST"])
def imports(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    if request.method == "GET":
        jobs = ImportJob.objects.filter(account__company_id=company_id).order_by("-id")[:20]
        return Response([job_data(job) for job in jobs])
    if member.role not in ("owner", "accountant"):
        return Response({"detail": "Tu rol solo permite consultar."}, status=403)
    try:
        account_id = int(request.data.get("account_id", ""))
    except (ValueError, TypeError):
        return Response({"detail": "Selecciona una cuenta."}, status=400)
    account = get_object_or_404(BankAccount, pk=account_id, company_id=company_id)
    if account.connection_id:
        return Response({"detail": "La cuenta conectada se actualiza desde su fuente."}, status=409)
    upload = request.FILES.get("file")
    if (
        not upload
        or not upload.name.lower().endswith((".csv", ".xlsx"))
        or upload.size > 2 * 1024 * 1024
    ):
        return Response({"detail": "Selecciona un CSV o XLSX de hasta 2 MB."}, status=400)
    raw = upload.read()
    file_format = "xlsx" if upload.name.lower().endswith(".xlsx") else "csv"
    try:
        content = (
            base64.b64encode(raw).decode("ascii")
            if file_format == "xlsx"
            else raw.decode("utf-8-sig")
        )
    except UnicodeDecodeError:
        return Response({"detail": "El CSV debe estar codificado en UTF-8."}, status=400)
    job = create_job(
        import_csv,
        ImportJob,
        account=account,
        user=request.user,
        content=content,
        file_format=file_format,
        checksum=hashlib.sha256(raw).hexdigest(),
    )
    try:
        dispatch_job(import_csv, args=[job.pk], retry=False)
    except Exception:
        job.status = "failed"
        job.error = (
            "La cola no está disponible. Vuelve a cargar el archivo cuando se recupere el servicio."
        )
        job.content = ""
        job.finished_at = timezone.now()
        job.save()
        return Response({"detail": job.error}, status=503)
    return Response(job_data(job), status=202)


class AccountBalanceInput(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance_date = serializers.DateField()


@api_view(["PATCH"])
def update_balance(request, company_id, account_id):
    serializer = AccountBalanceInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    if values["balance_date"] > timezone.localdate():
        return Response({"detail": "El corte no puede estar en el futuro."}, status=400)
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        account = get_object_or_404(
            BankAccount.objects.select_for_update(), pk=account_id, company_id=company_id
        )
        if account.connection_id:
            return Response(
                {"detail": "La cuenta conectada se actualiza desde su fuente."}, status=409
            )
        if Transaction.objects.filter(account=account, date__gt=values["balance_date"]).exists():
            return Response(
                {"detail": "El corte no puede dejar movimientos registrados en el futuro."},
                status=409,
            )
        before = {
            "balance": str(account.balance),
            "balance_date": account.balance_date.isoformat(),
            "history_complete_from": account.history_complete_from.isoformat()
            if account.history_complete_from
            else None,
            "history_complete_through": account.history_complete_through.isoformat()
            if account.history_complete_through
            else None,
        }
        account.balance = values["balance"]
        changed_cut = account.balance_date != values["balance_date"]
        account.balance_date = values["balance_date"]
        if changed_cut:
            account.history_complete_from = None
            account.history_complete_through = None
            account.history_confirmed_at = None
            account.history_confirmed_by = None
        account.save(
            update_fields=[
                "balance",
                "balance_date",
                "history_complete_from",
                "history_complete_through",
                "history_confirmed_at",
                "history_confirmed_by",
            ]
        )
        after = {
            "balance": str(account.balance),
            "balance_date": account.balance_date.isoformat(),
            "history_complete_from": account.history_complete_from.isoformat()
            if account.history_complete_from
            else None,
            "history_complete_through": account.history_complete_through.isoformat()
            if account.history_complete_through
            else None,
        }
        if before != after:
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="account.balance_updated",
                entity="BankAccount",
                entity_id=str(account.pk),
                before=before,
                after=after,
            )
    return Response(after)
