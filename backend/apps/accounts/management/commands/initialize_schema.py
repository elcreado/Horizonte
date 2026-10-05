import os

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Prepara un esquema PostgreSQL privado para el backend alojado."

    def handle(self, *args, **options):
        if connection.vendor == "postgresql":
            schema = os.environ.get("POSTGRES_SCHEMA", "public")
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {connection.ops.quote_name(schema)}")
