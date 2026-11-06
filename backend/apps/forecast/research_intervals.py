"""Comparación emparejada de intervalos en cortes posteriores a la calibración."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from .calibrated_intervals import temporal_cash_intervals
from .empirical_quantiles import weekly_cash_quantiles
from .research import load_dataset, research_recurrences


def interval_metrics(observed: list[Decimal], intervals: list[dict]) -> dict:
    if not observed or len(observed) != len(intervals):
        raise ValueError("Observaciones e intervalos deben tener igual longitud positiva.")
    covered = 0
    width = score = Decimal("0")
    for actual, point in zip(observed, intervals, strict=True):
        lower, upper = point["lower"], point["upper"]
        if not all(value.is_finite() for value in (actual, lower, upper)) or lower > upper:
            raise ValueError("Intervalos finitos y ordenados requeridos.")
        covered += lower <= actual <= upper
        width += upper - lower
        score += upper - lower + 10 * max(lower - actual, actual - upper, Decimal("0"))
    count = Decimal(len(observed))
    return {
        "predictions": len(observed),
        "coverage": str(Decimal(covered) / count),
        "mean_width": str(width / count),
        "mean_interval_score": str(score / count),
    }


def evaluate_intervals(directory: Path, *, step: int = 30) -> dict:
    if step < 1:
        raise ValueError("Paso positivo requerido.")
    manifest, series, commitments = load_dataset(directory)
    metrics = []
    for horizon in (30, 60, 90):
        groups = defaultdict(lambda: {"actual": [], "empirical": [], "corrected": [], "windows": 0})
        # 20 orígenes de ajuste y 20 de calibración, con resultados completos antes del corte.
        minimum = 7 + 19 * 7 + horizon + horizon + 19 * 7
        for company, rows in series.items():
            for origin in range(minimum, len(rows) - horizon + 1, step):
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
                corrected, _ = temporal_cash_intervals(history, rows[origin - 1]["balance"], flows)
                empirical, _ = weekly_cash_quantiles(history, rows[origin - 1]["balance"], flows)
                for name in ("all", rows[0]["profile"]):
                    group = groups[name]
                    group["actual"].extend(row["balance"] for row in future)
                    group["empirical"].extend(
                        {"lower": p["p10"], "upper": p["p90"]} for p in empirical
                    )
                    group["corrected"].extend(corrected)
                    group["windows"] += 1
        if not groups:
            raise ValueError("Historia insuficiente para evaluar después de calibrar.")
        for profile, group in sorted(groups.items()):
            for method in ("empirical", "corrected"):
                metrics.append(
                    {
                        "horizon": horizon,
                        "profile": profile,
                        "method": method,
                        "windows": group["windows"],
                        **interval_metrics(group["actual"], group[method]),
                    }
                )
    return {
        "evaluation": "paired_temporal_intervals_v1",
        "dataset": manifest,
        "step": step,
        "metrics": metrics,
        "nominal_coverage": "0.8",
    }


def render_interval_report(report: dict) -> str:
    lines = [
        "# Evaluación emparejada de intervalos temporales",
        "",
        f"Dataset sintético: {report['dataset']['companies']} empresas; semilla {report['dataset']['seed']}; paso {report['step']} días.",
        "Ambos métodos comparten cortes y resultados futuros; cobertura nominal 0,8.",
        "",
        "| Días | Perfil | Método | Ventanas | Cobertura | Amplitud COP | Interval score COP |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in report["metrics"]:
        lines.append(
            f"| {row['horizon']} | {row['profile']} | {row['method']} | {row['windows']} | "
            f"{Decimal(row['coverage']):.4f} | {Decimal(row['mean_width']):.2f} | "
            f"{Decimal(row['mean_interval_score']):.2f} |"
        )
    lines.extend(
        [
            "",
            "Menor interval score es mejor: penaliza amplitud y observaciones fuera del intervalo.",
            "No es una probabilidad de déficit ni prueba de cobertura conjunta de la trayectoria.",
            "El método corregido reserva historia y puede empeorar ante cambios de régimen.",
            "Ventanas solapadas, clasificación/revisión perfectas y compromisos puntuales sintéticos:",
            "no demuestran calibración en empresas reales ni intercambiabilidad.",
            "",
        ]
    )
    return "\n".join(lines)
