import base64
import io
import json
import time
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from openpyxl import Workbook

from apps.accounts.models import Company, CompanyMember
from apps.banking.models import BankAccount, ImportJob, Transaction
from apps.banking.tasks import import_csv


class Command(BaseCommand):
    help = "Mide 10.000 movimientos sintéticos y repetición; revierte todos los datos al finalizar."

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=["csv", "xlsx"], default="csv")

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Esta medición requiere PostgreSQL.")
        marker = "benchmark-" + uuid.uuid4().hex[:16]
        result = {
            "database": connection.vendor,
            "format": options["format"],
            "rows": 10000,
            "execution": "task directa, sin HTTP ni espera de cola; transacción exterior revertida",
        }
        with transaction.atomic():
            user = get_user_model().objects.create_user(username=marker)
            company = Company.objects.create(name=marker, nit=marker)
            CompanyMember.objects.create(company=company, user=user, role="owner")
            account = BankAccount.objects.create(
                company=company, name="Benchmark", balance="1000", balance_date=date(2026, 9, 23)
            )
            content = "external_id,date,amount,description\n" + "".join(
                f"bench-{i},2026-09-01,-10.25,Adobe\n" for i in range(10000)
            )
            result["bytes"] = len(content.encode())
            if options["format"] == "xlsx":
                book = Workbook(write_only=True)
                sheet = book.create_sheet("Movimientos")
                sheet.append(["external_id", "date", "amount", "description"])
                for i in range(10000):
                    sheet.append([f"bench-{i}", "2026-09-01", -10.25, "Adobe"])
                buffer = io.BytesIO()
                book.save(buffer)
                book.close()
                result["bytes"] = len(buffer.getvalue())
                content = base64.b64encode(buffer.getvalue()).decode("ascii")
            for name in ("initial", "repeat"):
                job = ImportJob.objects.create(
                    account=account, user=user, content=content, file_format=options["format"]
                )
                started = time.perf_counter()
                import_csv(job.pk)
                elapsed = time.perf_counter() - started
                job.refresh_from_db()
                if job.status != "completed":
                    raise CommandError(job.error)
                expected_created = 10000 if name == "initial" else 0
                if (
                    job.created_count != expected_created
                    or job.duplicate_count != 10000 - expected_created
                    or Transaction.objects.filter(account=account).count() != 10000
                ):
                    raise CommandError("Fallo de integridad en carga o duplicados.")
                result[name] = {
                    "seconds": round(elapsed, 3),
                    "created": job.created_count,
                    "duplicates": job.duplicate_count,
                }
                self.stdout.write(json.dumps({name: result[name]}))
            account.refresh_from_db()
            if str(account.balance) != "1000.00":
                raise CommandError("El importador alteró el saldo.")
            transaction.set_rollback(True)
        if (
            Company.objects.filter(nit=marker).exists()
            or get_user_model().objects.filter(username=marker).exists()
        ):
            raise CommandError("Los datos temporales no se revirtieron.")
        result["rollback_verified"] = True
        self.stdout.write(json.dumps(result))
