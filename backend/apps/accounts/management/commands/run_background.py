import signal
from threading import Event

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from config.background import run_one


class Command(BaseCommand):
    help = "Procesa la cola persistida en BD, sin Redis ni Docker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Procesa como máximo una tarea disponible y termina.",
        )

    def handle(self, *args, **options):
        if settings.BACKGROUND_MODE != "database":
            raise CommandError("Este worker requiere BACKGROUND_MODE=database.")
        if options["once"]:
            close_old_connections()
            run_one()
            return
        stopped = Event()

        def stop(*unused):
            stopped.set()

        previous = {
            number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)
        }
        try:
            while not stopped.is_set():
                try:
                    close_old_connections()
                    if not run_one():
                        stopped.wait(10)
                except Exception:
                    self.stderr.write("La cola no pudo procesar la tarea; se reintentará.")
                    stopped.wait(10)
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
