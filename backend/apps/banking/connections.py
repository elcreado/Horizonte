"""Autorización local y ciclo de vida de conectores bancarios."""

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, Company, CompanyMember
from config.background import create_job, dispatch_job

from .models import BankAccount, BankConnection, BankConsent, BankSyncJob
from .sync import sync_bank


def serialize(connection):
    return {
        "id": connection.pk,
        "provider": connection.provider,
        "status": connection.status,
        "created_at": connection.created_at,
        "revoked_at": connection.revoked_at,
        "account_id": connection.bankaccount.pk,
        "consent": {
            "id": connection.consent_id,
            "scopes": connection.consent.scopes,
            "granted_at": connection.consent.granted_at,
            "revoked_at": connection.consent.revoked_at,
        },
    }


def serialize_job(job):
    return {
        "id": job.pk,
        "connection_id": job.connection_id,
        "status": job.status,
        "created_count": job.created_count,
        "duplicate_count": job.duplicate_count,
        "error": job.error,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }


@api_view(["GET", "POST"])
def bank_connections(request, company_id):
    member = get_object_or_404(CompanyMember, company_id=company_id, user=request.user)
    if request.method == "GET":
        rows = (
            BankConnection.objects.filter(company_id=company_id)
            .select_related("consent", "bankaccount")
            .order_by("-pk")
        )
        jobs = BankSyncJob.objects.filter(connection__company_id=company_id).order_by("-pk")[:20]
        return Response(
            {
                "can_manage": member.role in ("owner", "accountant"),
                "connections": [serialize(row) for row in rows],
                "jobs": [serialize_job(job) for job in jobs],
            }
        )
    if member.role not in ("owner", "accountant"):
        return Response({"detail": "Tu rol solo permite consultar."}, status=403)
    if request.data.get("provider") != "mock" or request.data.get("consent") is not True:
        return Response(
            {"detail": "Selecciona Mock Bank y autoriza la lectura de saldo y movimientos."},
            status=400,
        )
    try:
        with transaction.atomic():
            company = get_object_or_404(Company.objects.select_for_update(), pk=company_id)
            member = get_object_or_404(
                CompanyMember.objects.select_for_update(), company=company, user=request.user
            )
            if member.role not in ("owner", "accountant"):
                return Response({"detail": "Tu rol solo permite consultar."}, status=403)
            connection = (
                BankConnection.objects.select_for_update()
                .filter(company=company, provider="mock")
                .first()
            )
            reconnecting = connection is not None
            if connection and connection.status == "active":
                return Response({"detail": "Ya hay una conexión Mock Bank activa."}, status=409)
            if not connection:
                cuts = set(
                    BankAccount.objects.filter(company=company).values_list(
                        "balance_date", flat=True
                    )
                )
                if len(cuts) > 1:
                    return Response(
                        {
                            "detail": "Unifica los cortes de las cuentas antes de conectar otra fuente."
                        },
                        status=409,
                    )
                cutoff = cuts.pop() if cuts else timezone.localdate()
            consent = BankConsent.objects.create(
                company=company, user=request.user, scopes=["balances:read", "transactions:read"]
            )
            if connection:
                connection.consent = consent
                connection.status = "active"
                connection.revoked_at = None
                connection.save(update_fields=["consent", "status", "revoked_at"])
            else:
                connection = BankConnection.objects.create(
                    company=company, consent=consent, provider="mock"
                )
                BankAccount.objects.create(
                    company=company,
                    connection=connection,
                    name="Mock Bank · cuenta sintética",
                    balance="5000000.00",
                    balance_date=cutoff,
                )
            job = create_job(sync_bank, BankSyncJob, connection=connection, user=request.user)
            AuditLog.objects.create(
                company=company,
                user=request.user,
                action="bank.reconnected" if reconnecting else "bank.connected",
                entity="BankConnection",
                entity_id=str(connection.pk),
                after={"provider": "mock", "scopes": consent.scopes, "consent_id": consent.pk},
            )
    except IntegrityError:
        return Response({"detail": "Esta empresa ya utilizó Mock Bank."}, status=409)
    try:
        dispatch_job(sync_bank, args=[job.pk], retry=False)
    except Exception:
        BankSyncJob.objects.filter(pk=job.pk, status="queued").update(
            status="failed",
            error="La cola no está disponible. Reintenta la sincronización.",
            finished_at=timezone.now(),
        )
    connection = BankConnection.objects.select_related("consent", "bankaccount").get(
        pk=connection.pk
    )
    job.refresh_from_db()
    return Response({"connection": serialize(connection), "job": serialize_job(job)}, status=201)


@api_view(["POST"])
def bank_sync(request, company_id, connection_id):
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        connection = get_object_or_404(
            BankConnection.objects.select_for_update(), pk=connection_id, company_id=company_id
        )
        if connection.status != "active":
            return Response({"detail": "La conexión está revocada."}, status=409)
        if BankSyncJob.objects.filter(connection=connection, status="queued").exists():
            return Response({"detail": "Ya hay una sincronización pendiente."}, status=409)
        job = create_job(sync_bank, BankSyncJob, connection=connection, user=request.user)
    try:
        dispatch_job(sync_bank, args=[job.pk], retry=False)
    except Exception:
        BankSyncJob.objects.filter(pk=job.pk, status="queued").update(
            status="failed",
            error="La cola no está disponible. Reintenta la sincronización.",
            finished_at=timezone.now(),
        )
    job.refresh_from_db()
    return Response(serialize_job(job), status=202 if job.status == "queued" else 503)


@api_view(["POST"])
def bank_revoke(request, company_id, connection_id):
    with transaction.atomic():
        member = get_object_or_404(
            CompanyMember.objects.select_for_update(), company_id=company_id, user=request.user
        )
        if member.role not in ("owner", "accountant"):
            return Response({"detail": "Tu rol solo permite consultar."}, status=403)
        connection = get_object_or_404(
            BankConnection.objects.select_for_update().select_related("consent"),
            pk=connection_id,
            company_id=company_id,
        )
        if connection.status == "active":
            now = timezone.now()
            connection.status = "revoked"
            connection.revoked_at = now
            connection.save(update_fields=["status", "revoked_at"])
            connection.consent.revoked_at = now
            connection.consent.save(update_fields=["revoked_at"])
            BankSyncJob.objects.filter(connection=connection, status="queued").update(
                status="failed",
                error="La autorización fue revocada antes de sincronizar.",
                finished_at=now,
            )
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="bank.revoked",
                entity="BankConnection",
                entity_id=str(connection.pk),
                after={"provider": connection.provider},
            )
    return Response(serialize(connection))
