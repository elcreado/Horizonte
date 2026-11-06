import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.classify.corpus import evaluate_corpus


class Command(BaseCommand):
    help = "Evalúa un corpus etiquetado de una empresa sin consultar la BD ni servicios externos."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)
        parser.add_argument("--company", required=True)
        parser.add_argument("--direction", choices=("in", "out"), required=True)
        parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        source, target = Path(options["input"]), Path(options["output"])
        if source.resolve() == target.resolve():
            raise CommandError("La salida no puede reemplazar el corpus de entrada.")
        try:
            result = evaluate_corpus(
                source, options["company"], options["direction"], options["cutoff"]
            )
        except (OSError, ValueError, KeyError, TypeError):
            raise CommandError(
                "Corpus no evaluable; revisa columnas, fechas, empresa, grupos y soporte de etiquetas."
            ) from None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.stdout.write(f"Evaluación guardada en {target}; no se modificó ningún movimiento.")
