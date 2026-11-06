"""Comprueba provisión administrativa sin imprimir cuentas ni secretos."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Comprueba que existe un superusuario activo de plataforma, sin listar sus datos."

    def handle(self, *args, **options):
        exists = (
            get_user_model()
            .objects.filter(is_active=True, is_staff=True, is_superuser=True)
            .exists()
        )
        if not exists:
            raise CommandError(
                "No hay administrador activo de plataforma. Provisiona una cuenta propia con createsuperuser."
            )
        self.stdout.write(
            "Hay administrador activo de plataforma; esto no valida una interfaz administrativa."
        )
