"""Referencias determinísticas para evaluación; no producen cuantiles ni confianza.

Métodos: https://otexts.com/fpp3/simple-methods.html
La evaluación recibe una serie preparada con información disponible en cada corte.
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

SES_ALPHA = Decimal("0.30")


def daily_residual(
    rows,
    start: date,
    cutoff: date,
    settled_amounts: dict,
    recurring_ids: set,
    *,
    coverage_confirmed: bool,
) -> list[Decimal]:
    """Resta conciliaciones parciales y excluye recurrencias sin descontarlas dos veces.

    El llamador debe aportar vínculos conocidos al corte; datos actuales no sirven
    para simular decisiones históricas. Los ceros requieren cobertura confirmada.
    """
    if not coverage_confirmed:
        raise ValueError(
            "Confirma cobertura completa antes de interpretar días sin movimientos como cero."
        )
    if start > cutoff or (cutoff - start).days > 3650:
        raise ValueError("Ventana de historial inválida.")
    values = [Decimal("0") for _ in range((cutoff - start).days + 1)]
    seen = set()
    for row in rows:
        if not start <= row.date <= cutoff:
            continue
        if row.pk in seen:
            raise ValueError("Movimiento repetido en el historial.")
        seen.add(row.pk)
        amount = Decimal(row.amount)
        settled = Decimal(settled_amounts.get(row.pk, 0))
        if (
            not amount.is_finite()
            or not settled.is_finite()
            or settled < 0
            or settled > abs(amount)
        ):
            raise ValueError("Monto o conciliación inválidos.")
        residual = (
            Decimal("0")
            if row.pk in recurring_ids
            else amount - (settled if amount >= 0 else -settled)
        )
        values[(row.date - start).days] += residual
    return values


def predict_baseline(history: list[Decimal], horizon: int, method: str) -> list[Decimal]:
    if horizon not in (30, 60, 90):
        raise ValueError("Horizonte requerido: 30, 60 o 90.")
    if not history or any(not value.is_finite() for value in history):
        raise ValueError("Historial vacío o no finito.")
    if method == "naive":
        return [history[-1]] * horizon
    if method == "seasonal_naive":
        if len(history) < 7:
            raise ValueError("Seasonal naive requiere al menos siete días completos.")
        return [history[-7 + offset % 7] for offset in range(horizon)]
    if method == "ses":
        level = history[0]
        for observed in history[1:]:
            level = SES_ALPHA * observed + (Decimal("1") - SES_ALPHA) * level
        return [level.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)] * horizon
    raise ValueError("Método de referencia desconocido.")


def hybrid_points(
    balance: Decimal,
    cutoff: date,
    residual_forecast: list[Decimal],
    known_flows: dict[date, Decimal],
) -> list[dict]:
    """Solo integra flujos futuros; balance ya contiene el historial bancario."""
    points = []
    for offset, residual in enumerate(residual_forecast, start=1):
        day = cutoff + timedelta(days=offset)
        known = known_flows.get(day, Decimal("0"))
        balance += known + residual
        points.append(
            {
                "date": day.isoformat(),
                "known_flow": str(known),
                "estimated_flow": str(residual),
                "balance": str(balance),
            }
        )
    return points


def evaluate_baselines(
    series: list[Decimal], horizon: int, *, min_train: int = 28, step: int = 7
) -> dict:
    """Rolling origin: cada entrenamiento termina antes de su ventana de prueba.

    La serie debe estar preparada sin vínculos o etiquetas obtenidos posteriormente.
    Métricas de flujo diario; no equivalen a exactitud del saldo acumulado.
    """
    if min_train < 7 or step < 1 or horizon not in (30, 60, 90):
        raise ValueError("Configuración de evaluación inválida.")
    result = {}
    for method in ("naive", "seasonal_naive", "ses"):
        errors, relative, origins = [], [], 0
        for origin in range(min_train, len(series) - horizon + 1, step):
            prediction = predict_baseline(series[:origin], horizon, method)
            actual = series[origin : origin + horizon]
            for predicted, observed in zip(prediction, actual):
                if not observed.is_finite():
                    raise ValueError("Observación no finita.")
                error = predicted - observed
                errors.append(error)
                denominator = abs(predicted) + abs(observed)
                relative.append(Decimal("0") if not denominator else 200 * abs(error) / denominator)
            origins += 1
        if not errors:
            raise ValueError("Historial insuficiente para evaluar este horizonte.")
        n = Decimal(len(errors))
        result[method] = {
            "origins": origins,
            "predictions": len(errors),
            "mae": str(sum(map(abs, errors)) / n),
            "rmse": str((sum(error * error for error in errors) / n).sqrt()),
            "smape_percent": str(sum(relative) / n),
        }
    return result
