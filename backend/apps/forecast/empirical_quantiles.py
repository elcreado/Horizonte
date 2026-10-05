"""Cuantiles experimentales de error acumulado semanal, usando únicamente pasado.

No asume errores diarios independientes: conserva sus trayectorias observadas.
No ofrece garantía de calibración ni incertidumbre de obligaciones/recurrencias.
"""

from decimal import ROUND_HALF_UP, Decimal

from .baselines import predict_baseline


def empirical_quantile(values: list[Decimal], probability: Decimal) -> Decimal:
    """Interpolación lineal entre estadísticos ordenados, índice (n-1)*q."""
    if not probability.is_finite() or any(not value.is_finite() for value in values):
        raise ValueError("Muestra y probabilidad deben ser finitas.")
    if not values or not Decimal("0") <= probability <= Decimal("1"):
        raise ValueError("Muestra o probabilidad inválida.")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower])


def weekly_cash_quantiles(
    history: list[Decimal],
    balance: Decimal,
    future_flows: list[Decimal],
    *,
    step: int = 7,
    min_origins: int = 20,
) -> tuple[list[dict[str, Decimal]], dict]:
    """Estima saldo marginal condicionado a futuros compromisos puntuales.

    history contiene flujo variable diario completo hasta el corte, sin flujos
    conocidos/recurrentes. future_flows suma obligaciones y recurrencias ya
    disponibles al corte; no debe incluir pagos desconocidos obtenidos del futuro.
    Cada origen histórico utiliza su propia última semana y una ventana posterior
    enteramente observada antes del corte actual.
    """
    horizon = len(future_flows)
    if horizon not in (30, 60, 90) or step < 1 or min_origins < 20:
        raise ValueError("Horizonte 30/60/90, paso positivo y al menos 20 orígenes requeridos.")
    if not balance.is_finite() or any(not value.is_finite() for value in history + future_flows):
        raise ValueError("Saldos y flujos deben ser finitos.")
    origins = list(range(7, len(history) - horizon + 1, step))
    if len(origins) < min_origins:
        raise ValueError("Historial insuficiente para estimar errores de este horizonte.")
    errors = [[] for _ in range(horizon)]
    for origin in origins:
        forecast = predict_baseline(history[:origin], horizon, "seasonal_naive")
        accumulated = Decimal("0")
        for offset in range(horizon):
            accumulated += history[origin + offset] - forecast[offset]
            errors[offset].append(accumulated)
    forecast = predict_baseline(history, horizon, "seasonal_naive")
    points = []
    for offset, (variable, known) in enumerate(zip(forecast, future_flows, strict=True)):
        balance += variable + known
        points.append(
            {
                key: (balance + empirical_quantile(errors[offset], probability)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                for key, probability in (
                    ("p10", Decimal("0.1")),
                    ("p50", Decimal("0.5")),
                    ("p90", Decimal("0.9")),
                )
            }
        )
    return points, {
        "version": "weekly_empirical_errors_v1",
        "historical_origins": len(origins),
        "history_days": len(history),
        "origin_step_days": step,
        "horizon": horizon,
        "last_calibration_end_index": origins[-1] + horizon - 1,
        "notice": "Cuantiles experimentales no calibrados; compromisos futuros tratados como puntuales. "
        "Ventanas históricas pueden solaparse y no equivalen a muestras independientes.",
    }
