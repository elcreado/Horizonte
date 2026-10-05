import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.forecast.research import evaluate_dataset
from apps.forecast.research_report import render_report
from apps.forecast.synthetic import generate_dataset


class Command(BaseCommand):
    help = "Genera 100 empresas sintéticas ×24 meses y evalúa baselines sin servicios externos."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="data/generated")
        parser.add_argument("--companies", type=int, default=100)
        parser.add_argument("--seed", type=int, default=20261004)
        parser.add_argument("--step", type=int, default=30)
        parser.add_argument("--report", default="docs/RESEARCH_RESULTS.md")

    def handle(self, *args, **options):
        output = Path(options["output"])
        manifest = generate_dataset(output, companies=options["companies"], seed=options["seed"])
        report = evaluate_dataset(output, step=options["step"])
        (output / "evaluation.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report_path = Path(options["report"])
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_report(report), encoding="utf-8")
        self.stdout.write(
            f"Dataset: {manifest['companies']} empresas, {manifest['daily_rows']} días-empresa."
        )
        self.stdout.write(f"Resultados reproducibles: {output / 'evaluation.json'}")
