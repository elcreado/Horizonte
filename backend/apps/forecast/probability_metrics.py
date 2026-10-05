"""Métricas de cuantiles; no generan ni certifican un modelo probabilístico.

Pinball: https://scikit-learn.org/stable/modules/model_evaluation.html
La cobertura es puntual por día, no la probabilidad de cubrir toda una trayectoria.
"""

from decimal import Decimal


def pinball(observed: Decimal, predicted: Decimal, quantile: Decimal) -> Decimal:
    if not all(value.is_finite() for value in (observed, predicted, quantile)):
        raise ValueError("Observación, predicción y cuantil deben ser finitos.")
    if not Decimal("0") < quantile < Decimal("1"):
        raise ValueError("El cuantil debe estar entre cero y uno.")
    error = observed - predicted
    return quantile * error if error >= 0 else (quantile - 1) * error


def evaluate_quantiles(observed: list[Decimal], predicted: list[dict[str, Decimal]]) -> dict:
    """Evalúa P10/P50/P90 de saldo emparejados por día fuera de entrenamiento.

    El llamador garantiza cortes temporales y emparejamiento de empresa/fecha. No se
    corrigen cuantiles cruzados ni se descartan silenciosamente observaciones.
    """
    if not observed or len(observed) != len(predicted):
        raise ValueError("Observaciones y predicciones deben tener igual longitud positiva.")
    levels = {"p10": Decimal("0.1"), "p50": Decimal("0.5"), "p90": Decimal("0.9")}
    losses = {key: Decimal("0") for key in levels}
    below = {key: 0 for key in levels}
    covered = 0
    width = Decimal("0")
    for actual, point in zip(observed, predicted, strict=True):
        if not all(key in point for key in levels):
            raise ValueError("Cada predicción requiere p10, p50 y p90.")
        for key, level in levels.items():
            losses[key] += pinball(actual, point[key], level)
            below[key] += actual <= point[key]
        if not point["p10"] <= point["p50"] <= point["p90"]:
            raise ValueError("Cuantiles cruzados: P10 debe ser menor o igual a P50 y P90.")
        covered += point["p10"] <= actual <= point["p90"]
        width += point["p90"] - point["p10"]
    count = Decimal(len(observed))
    return {
        "predictions": len(observed),
        "pinball": {key: str(value / count) for key, value in losses.items()},
        "empirical_cdf": {key: str(Decimal(value) / count) for key, value in below.items()},
        "pointwise_coverage": str(Decimal(covered) / count),
        "nominal_coverage": "0.8",
        "mean_interval_width": str(width / count),
        "notice": "Cobertura puntual empírica; no certifica calibración ni cobertura conjunta.",
    }
