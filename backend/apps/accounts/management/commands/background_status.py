import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from apps.accounts.models import BackgroundTask


class Command(BaseCommand):
    help = "Diagnóstico agregado de cola, sin argumentos privados ni afirmación de worker vivo."

    def handle(self, *args, **options):
        if settings.BACKGROUND_MODE != "database":
            self.stdout.write(
                json.dumps(
                    {
                        "mode": settings.BACKGROUND_MODE,
                        "notice": "Este comando no inspecciona workers Celery.",
                    }
                )
            )
            return
        now = timezone.now()
        aggregate = BackgroundTask.objects.aggregate(
            queued=Count("pk", filter=Q(status="queued")),
            ready=Count("pk", filter=Q(status="queued", available_at__lte=now)),
            running=Count("pk", filter=Q(status="running")),
            expired_leases=Count("pk", filter=Q(status="running", available_at__lte=now)),
            failed=Count("pk", filter=Q(status="failed")),
            completed=Count("pk", filter=Q(status="completed")),
            oldest_pending=Min("created_at", filter=Q(status__in=["queued", "running"])),
            last_completed=Max("finished_at", filter=Q(status="completed")),
        )
        self.stdout.write(
            json.dumps(
                {
                    "mode": "database",
                    "observed_at": now.isoformat(),
                    **aggregate,
                    "notice": "Snapshot de tareas; no acredita worker vivo. "
                    "Leases vencidos pueden recuperarse al procesar la cola.",
                },
                default=str,
            )
        )
