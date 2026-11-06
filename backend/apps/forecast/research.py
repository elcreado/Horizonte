"""Evaluación de caja fuera de muestra sobre un dataset sintético versionado."""

import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from .arima_candidate import ArimaFitError, predict_arima
from .baselines import predict_baseline
from .recurrences import detect_recurrences, expand_dates, occurrence_key
from .recurring_forecast import estimate_recurrences


def research_recurrences(commitments, cutoff, horizon):
    """Simula revisión perfecta de categorías sintéticas, sin consultar pagos futuros."""
    observed = [
        SimpleNamespace(
            pk=item["id"],
            account_id=1,
            date=item["due"],
            amount=item["amount"],
            description=item["kind"],
            normalized_description=item["kind"],
        )
        for item in commitments
        if item["due"] <= cutoff
    ]
    candidates = detect_recurrences(observed, cutoff)
    visible = [
        SimpleNamespace(
            pk=item["id"],
            reference=item["id"],
            description=item["kind"],
            due_date=item["due"],
            direction="in" if item["amount"] > 0 else "out",
            outstanding_amount=abs(item["amount"]),
            cancelled=False,
        )
        for item in commitments
        if item["announced"] <= cutoff < item["due"]
    ]
    linked = {}
    for candidate in candidates:
        for day in expand_dates(candidate, observed, cutoff, horizon):
            obligation = next(
                (
                    row
                    for row in visible
                    if row.due_date.isoformat() == day
                    and row.description == candidate["description"]
                ),
                None,
            )
            if obligation:
                linked[occurrence_key({**candidate, "next_date": day})] = obligation
    return estimate_recurrences(candidates, observed, cutoff, horizon, visible, linked)[0]


def load_dataset(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for name in ("daily.csv", "obligations.csv"):
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != manifest["sha256"][name]:
            raise ValueError("El dataset no coincide con el manifiesto.")
    series, commitments = defaultdict(list), defaultdict(list)
    with (directory / "daily.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series[row["company_id"]].append(
                {
                    "date": date.fromisoformat(row["date"]),
                    "profile": row["profile"],
                    "variable": Decimal(row["variable_flow"]),
                    "balance": Decimal(row["balance"]),
                }
            )
    with (directory / "obligations.csv").open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            commitments[row["company_id"]].append(
                {
                    "announced": date.fromisoformat(row["announced_on"]),
                    "due": date.fromisoformat(row["due_date"]),
                    "amount": Decimal(row["amount"]),
                    "id": row["id"],
                    "kind": row["kind"],
                }
            )
    return manifest, series, commitments


def evaluate_dataset(
    directory: Path,
    *,
    min_train: int = 180,
    step: int = 30,
    include_arima: bool = False,
    arima_ses_fallback: bool = False,
) -> dict:
    if min_train < 90 or step < 1:
        raise ValueError("Entrenamiento mínimo 90 días y paso positivo.")
    manifest, series, commitments = load_dataset(directory)
    metrics = []
    fallbacks = []
    if arima_ses_fallback and not include_arima:
        raise ValueError("El respaldo SES requiere incluir ARIMA.")
    for horizon in (30, 60, 90):
        methods = ("naive", "seasonal_naive", "ses", "hybrid_weekly")
        if include_arima:
            methods += ("arima_100_ses_fallback" if arima_ses_fallback else "arima_100",)
        for method in methods:
            fallback_count = 0
            absolute = squared = relative = deficit_error = Decimal("0")
            ongoing_deficit = 0
            predictions = windows = true_positive = false_positive = false_negative = (
                true_negative
            ) = paired = 0
            for company, rows in series.items():
                for origin in range(min_train, len(rows) - horizon + 1, step):
                    cutoff = rows[origin - 1]["date"]
                    history = [row["variable"] for row in rows[:origin]]
                    if method.startswith("arima_100"):
                        try:
                            forecast = predict_arima(history, horizon)
                        except ArimaFitError as error:
                            if not arima_ses_fallback:
                                raise
                            fallback_count += 1
                            fallbacks.append(
                                {
                                    "company": company,
                                    "cutoff": cutoff.isoformat(),
                                    "horizon": horizon,
                                    "reason": str(error),
                                }
                            )
                            forecast = predict_baseline(history, horizon, "ses")
                    else:
                        forecast = predict_baseline(
                            history,
                            horizon,
                            "seasonal_naive" if method == "hybrid_weekly" else method,
                        )
                    recurring = (
                        research_recurrences(commitments[company], cutoff, horizon)
                        if method == "hybrid_weekly"
                        else {}
                    )
                    visible = defaultdict(lambda: Decimal("0"))
                    for item in commitments[company]:
                        if item["announced"] <= cutoff < item["due"]:
                            visible[item["due"]] += item["amount"]
                    balance = rows[origin - 1]["balance"]
                    predicted_deficit = actual_deficit = None
                    for offset, (flow, row) in enumerate(
                        zip(forecast, rows[origin : origin + horizon]), 1
                    ):
                        balance += (
                            flow + visible[row["date"]] + recurring.get(row["date"], Decimal("0"))
                        )
                        actual = row["balance"]
                        error = balance - actual
                        absolute += abs(error)
                        squared += error * error
                        denominator = abs(balance) + abs(actual)
                        relative += (
                            Decimal("0") if not denominator else 200 * abs(error) / denominator
                        )
                        predictions += 1
                        if predicted_deficit is None and balance < 0:
                            predicted_deficit = offset
                        if actual_deficit is None and actual < 0:
                            actual_deficit = offset
                    windows += 1
                    if rows[origin - 1]["balance"] < 0:
                        ongoing_deficit += 1
                        continue
                    if predicted_deficit is not None and actual_deficit is not None:
                        true_positive += 1
                        paired += 1
                        deficit_error += abs(predicted_deficit - actual_deficit)
                    elif predicted_deficit is not None:
                        false_positive += 1
                    elif actual_deficit is not None:
                        false_negative += 1
                    else:
                        true_negative += 1
            if not predictions:
                raise ValueError("No hay ventanas completas para evaluar.")
            precision = (
                Decimal(true_positive) / (true_positive + false_positive)
                if true_positive + false_positive
                else None
            )
            recall = (
                Decimal(true_positive) / (true_positive + false_negative)
                if true_positive + false_negative
                else None
            )
            f1 = (
                2 * Decimal(true_positive) / (2 * true_positive + false_positive + false_negative)
                if 2 * true_positive + false_positive + false_negative
                else None
            )
            metrics.append(
                {
                    "horizon": horizon,
                    "method": method,
                    "fallback_windows": fallback_count,
                    "windows": windows,
                    "predictions": predictions,
                    "balance_mae": str(absolute / predictions),
                    "balance_rmse": str((squared / predictions).sqrt()),
                    "balance_smape_percent": str(relative / predictions),
                    "tp": true_positive,
                    "fp": false_positive,
                    "fn": false_negative,
                    "tn": true_negative,
                    "precision": str(precision) if precision is not None else None,
                    "recall": str(recall) if recall is not None else None,
                    "f1": str(f1) if f1 is not None else None,
                    "dlde_mean_days": str(deficit_error / paired) if paired else None,
                    "dlde_pairs": paired,
                    "ongoing_deficit_windows": ongoing_deficit,
                }
            )
    return {
        "evaluation": "rolling_origin_balance_v2",
        "dataset": manifest,
        "min_train": min_train,
        "step": step,
        "threshold": "0",
        "metrics": metrics,
        "arima_fallbacks": fallbacks,
        "limitations": [
            "Ventanas solapadas; los errores no son muestras independientes.",
            "Métricas agregadas sobre caja sintética; no prueba eficacia con empresas reales.",
            "No se optimizan parámetros ni se selecciona modelo usando estas ventanas de prueba.",
            "DLDE solo para pares con déficit; ausencias se reportan en la matriz de confusión.",
            "La detección de nuevo déficit excluye ventanas ya negativas al corte; se cuentan aparte.",
            "Sin intervalos: pinball y cobertura no se calculan todavía.",
            "El híbrido simula confirmación perfecta de recurrencias y vínculos por categoría sintética; la aplicación requiere revisión humana.",
        ],
    }
