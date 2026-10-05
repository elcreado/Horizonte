import json
from pathlib import Path

from django.core.management.base import BaseCommand

from config.api_inventory import build_inventory


class Command(BaseCommand):
    help = "Exporta inventario OpenAPI parcial de rutas/métodos y autenticación actuales."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path, default=Path("docs/openapi-inventory.json"))

    def handle(self, *args, **options):
        inventory = build_inventory()
        destination = options["output"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        self.stdout.write(
            f"Inventario parcial: {len(inventory['paths'])} rutas. Esquemas detallados pendientes."
        )
