import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forecast.research_probability import evaluate_probability, render_probability_report


class Command(BaseCommand):
    help = "Evalúa cuantiles sobre el dataset sintético ya generado, sin servicios externos."

    def add_arguments(self, parser):
        parser.add_argument("--input", default="data/generated")
        parser.add_argument("--report", default="docs/PROBABILITY_RESULTS.md")
        parser.add_argument("--step", type=int, default=30)

    def handle(self, *args, **options):
        directory = Path(options["input"])
        result = evaluate_probability(directory, step=options["step"])
        (directory / "probability-evaluation.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report = Path(options["report"])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(render_probability_report(result), encoding="utf-8")
        self.stdout.write(f"Evaluación probabilística guardada en {report}.")
