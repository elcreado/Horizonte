from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import RateLimitBucket


class Command(BaseCommand):
    help = "Elimina únicamente límites de acceso ya vencidos."

    def handle(self, *args, **options):
        count, _ = RateLimitBucket.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(f"Límites vencidos eliminados: {count}.")
