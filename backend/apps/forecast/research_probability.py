"""Evaluación fuera de muestra de cuantiles experimentales de saldo sintético."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from .empirical_quantiles import weekly_cash_quantiles
from .probability_metrics import evaluate_quantiles
from .research import load_dataset, research_recurrences


def evaluate_probability(directory: Path, *, min_train: int = 180, step: int = 30) -> dict:
    if min_train < 90 or step < 1:
        raise ValueError("Entrenamiento mínimo 90 días y paso positivo.")
    manifest, series, commitments = load_dataset(directory)
    metrics, profile_metrics = [], []
    for horizon in (30, 60, 90):
        actual, predicted = [], []
        windows = unavailable = 0
        groups = defaultdict(
            lambda: {"actual": [], "predicted": [], "windows": 0, "unavailable": 0}
        )
        for company, rows in series.items():
            group = groups[rows[0]["profile"]]
            for origin in range(min_train, len(rows) - horizon + 1, step):
                history = [row["variable"] for row in rows[:origin]]
                cutoff = rows[origin - 1]["date"]
                visible = defaultdict(lambda: Decimal("0"))
                for item in commitments[company]:
                    if item["announced"] <= cutoff < item["due"]:
                        visible[item["due"]] += item["amount"]
                recurring = research_recurrences(commitments[company], cutoff, horizon)
                future = rows[origin : origin + horizon]
                flows = [
                    visible[row["date"]] + recurring.get(row["date"], Decimal("0"))
                    for row in future
                ]
                # El mismo mínimo se aplica antes de ver el saldo futuro.
                if len(range(7, len(history) - horizon + 1, 7)) < 20:
                    unavailable += 1
                    group["unavailable"] += 1
                    continue
                points, _ = weekly_cash_quantiles(history, rows[origin - 1]["balance"], flows)
                predicted.extend(points)
                actual.extend(row["balance"] for row in future)
                group["predicted"].extend(points)
                group["actual"].extend(row["balance"] for row in future)
                group["windows"] += 1
                windows += 1
        if not actual:
            raise ValueError("No hay ventanas suficientes para evaluar cuantiles.")
        metrics.append(
            {
                "horizon": horizon,
                "windows": windows,
                "unavailable_windows": unavailable,
                **evaluate_quantiles(actual, predicted),
            }
        )
        for profile, group in sorted(groups.items()):
            profile_metrics.append(
                {
                    "profile": profile,
                    "horizon": horizon,
                    "windows": group["windows"],
                    "unavailable_windows": group["unavailable"],
                    **evaluate_quantiles(group["actual"], group["predicted"]),
                }
            )
    return {
        "evaluation": "weekly_empirical_errors_v1",
        "dataset": manifest,
        "min_train": min_train,
        "step": step,
        "metrics": metrics,
        "profile_metrics": profile_metrics,
        "limitations": [
            "Datos sintéticos y etiquetas de flujo variable perfectas; no mide eficacia real.",
            "Recurrencias simulan revisión y vínculo perfectos con información disponible al corte.",
            "Cuantiles condicionados a compromisos puntuales, sin incertidumbre de cumplimiento.",
            "Ventanas solapadas; cobertura puntual agregada no demuestra calibración condicional.",
            "No se seleccionan parámetros usando estas ventanas de prueba.",
        ],
    }


def render_probability_report(report: dict) -> str:
    lines = [
        "# Evaluación sintética de cuantiles experimentales",
        "",
        "Generada por `research_probability`; no demuestra precisión con empresas reales.",
        "",
        f"Dataset: {report['dataset']['companies']} empresas; entrenamiento mínimo {report['min_train']} días; paso {report['step']} días.",
        "",
        "| Días | Ventanas | No disponibles | Cobertura puntual | Amplitud COP | Pinball P10 | Pinball P50 | Pinball P90 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in report["metrics"]:
        values = [
            row["horizon"],
            row["windows"],
            row["unavailable_windows"],
            f"{Decimal(row['pointwise_coverage']):.4f}",
            f"{Decimal(row['mean_interval_width']):.2f}",
        ]
        values.extend(f"{Decimal(row['pinball'][key]):.2f}" for key in ("p10", "p50", "p90"))
        lines.append("| " + " | ".join(map(str, values)) + " |")
    lines.extend(
        ["", "Cobertura nominal P10–P90: 0,8. Métricas por día, no por trayectoria completa.", ""]
    )
    lines.extend(
        [
            "## Desglose por perfil",
            "",
            "| Perfil | Días | Ventanas | Cobertura puntual | Amplitud COP | Pinball P50 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in report["profile_metrics"]:
        lines.append(
            f"| {row['profile']} | {row['horizon']} | {row['windows']} | "
            f"{Decimal(row['pointwise_coverage']):.4f} | "
            f"{Decimal(row['mean_interval_width']):.2f} | "
            f"{Decimal(row['pinball']['p50']):.2f} |"
        )
    lines.append("")
    lines.extend("- " + value for value in report["limitations"])
    return "\n".join(lines) + "\n"
