import base64
import hashlib

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import CompanyMember

from .models import BankAccount, ImportJob
from .tasks import import_csv


@api_view(["GET"])
def accounts(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    return Response(
        {
            "can_import": member.role in ("owner", "accountant"),
            "accounts": list(
                BankAccount.objects.filter(company_id=company_id).values(
                    "id", "name", "currency", "balance_date"
                )
            ),
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
    job = ImportJob.objects.create(
        account=account,
        user=request.user,
        content=content,
        file_format=file_format,
        checksum=hashlib.sha256(raw).hexdigest(),
    )
    try:
        import_csv.apply_async(args=[job.pk], retry=False)
    except Exception:
        job.status = "failed"
        job.error = "La cola no está disponible. Comprueba Redis y vuelve a cargar el archivo."
        job.content = ""
        job.finished_at = timezone.now()
        job.save()
        return Response({"detail": job.error}, status=503)
    return Response(job_data(job), status=202)
