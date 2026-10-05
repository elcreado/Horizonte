import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forecast.research_intervals import evaluate_intervals, render_interval_report


class Command(BaseCommand):
    help = "Compara intervalos corregidos y empíricos en el mismo corpus sintético."

    def add_arguments(self, parser):
        parser.add_argument("--input", default="data/generated")
        parser.add_argument("--report", default="docs/INTERVAL_RESULTS.md")
        parser.add_argument("--step", type=int, default=30)

    def handle(self, *args, **options):
        directory = Path(options["input"])
        result = evaluate_intervals(directory, step=options["step"])
        (directory / "interval-evaluation.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report = Path(options["report"])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(render_interval_report(result), encoding="utf-8")
        self.stdout.write(f"Comparación guardada en {report}.")
