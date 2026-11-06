import os
import sys

if len(sys.argv) > 1 and sys.argv[1] == "runserver":
    os.environ.setdefault("BACKGROUND_MODE", "database")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.management import execute_from_command_line  # noqa: E402

execute_from_command_line(sys.argv)
