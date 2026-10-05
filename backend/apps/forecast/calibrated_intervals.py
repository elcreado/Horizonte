"""Candidato de intervalos marginales con bloque temporal reservado.

Inspirado en https://arxiv.org/abs/1905.03222. Las ventanas dependientes
no cumplen intercambiabilidad: no se afirma garantía conformal de cobertura.
Los extremos corregidos son límites de intervalo, no cuantiles P10/P90.
"""

from decimal import ROUND_CEILING, Decimal

from .baselines import predict_baseline
from .empirical_quantiles import weekly_cash_quantiles


def temporal_cash_intervals(
    history: list[Decimal], balance: Decimal, future_flows: list[Decimal]
) -> tuple[list[dict[str, Decimal]], dict]:
    """Reserva 20 orígenes semanales posteriores al ajuste del error base.

    Corrige por día del horizonte mediante el estadístico de orden 17/20,
    ceil((20+1)*0.8). Expande únicamente; no ajusta la mediana ni asigna
    probabilidades de déficit a partir de los extremos.
    """
    horizon = len(future_flows)
    if horizon not in (30, 60, 90):
        raise ValueError("Horizonte requerido: 30, 60 o 90.")
    if any(not value.is_finite() for value in history + future_flows + [balance]):
        raise ValueError("Saldos y flujos deben ser finitos.")
    calibration_start = len(history) - horizon - 19 * 7
    if calibration_start < 1:
        raise ValueError("Historial insuficiente para separar ajuste y calibración.")
    zero_flows = [Decimal("0")] * horizon
    training = history[:calibration_start]
    base, evidence = weekly_cash_quantiles(training, Decimal("0"), zero_flows)
    training_forecast = predict_baseline(training, horizon, "seasonal_naive")
    total = Decimal("0")
    error_bounds = []
    for point, flow in zip(base, training_forecast, strict=True):
        total += flow
        error_bounds.append({key: value - total for key, value in point.items()})
    scores = [[] for _ in range(horizon)]
    for origin in range(calibration_start, len(history) - horizon + 1, 7):
        forecast = predict_baseline(history[:origin], horizon, "seasonal_naive")
        actual = predicted = Decimal("0")
        for offset, flow in enumerate(forecast):
            predicted += flow
            actual += history[origin + offset]
            bounds = error_bounds[offset]
            scores[offset].append(
                max(predicted + bounds["p10"] - actual, actual - predicted - bounds["p90"])
            )
    rank = int((Decimal("21") * Decimal("0.8")).to_integral_value(rounding=ROUND_CEILING))
    corrections = [max(Decimal("0"), sorted(values)[rank - 1]) for values in scores]
    forecast = predict_baseline(history, horizon, "seasonal_naive")
    points = []
    for offset, (flow, known) in enumerate(zip(forecast, future_flows, strict=True)):
        balance += flow + known
        bounds = error_bounds[offset]
        points.append(
            {
                "lower": balance + bounds["p10"] - corrections[offset],
                "median": balance + bounds["p50"],
                "upper": balance + bounds["p90"] + corrections[offset],
            }
        )
    return points, {
        "version": "temporal_holdout_interval_v1",
        "training_days": calibration_start,
        "training_origins": evidence["historical_origins"],
        "calibration_origins": 20,
        "calibration_start_index": calibration_start,
        "calibration_end_index": len(history) - 1,
        "nominal_coverage": "0.8",
        "corrections": [str(value) for value in corrections],
        "notice": "Intervalos experimentales: ventanas dependientes, sin garantía de cobertura; "
        "compromisos futuros puntuales. Los límites no son cuantiles calibrados.",
    }
