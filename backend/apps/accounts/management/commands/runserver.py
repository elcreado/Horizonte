"""Run the local database queue alongside Django, including with the autoreloader."""

import os
import subprocess
import sys

from django.conf import settings
from django.core.management.commands.runserver import Command as DjangoRunserver


class Command(DjangoRunserver):
    def inner_run(self, *args, **options):
        worker = None
        if (
            settings.DEBUG
            and settings.BACKGROUND_MODE == "database"
            and os.environ.get("DJANGO_LOCAL_WORKER", "1") == "1"
        ):
            worker = subprocess.Popen(
                [sys.executable, str(settings.BASE_DIR / "manage.py"), "run_background"],
                env=os.environ.copy(),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            self.stdout.write("Cola local activa: las importaciones se procesan automáticamente.")
        try:
            return super().inner_run(*args, **options)
        finally:
            if worker is not None:
                worker.terminate()
                try:
                    worker.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait()
