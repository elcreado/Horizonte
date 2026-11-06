"""Candidato ARIMA(1,0,0) para investigación; no se usa en las rutas de producción.

API: https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html
Orden fijado antes de evaluar; no se selecciona usando el conjunto de prueba.
"""

import math
from decimal import ROUND_HALF_UP, Decimal


class ArimaFitError(ValueError):
    """Fallo recuperable de ajuste; no incluye errores de datos o dependencias."""


def predict_arima(history: list[Decimal], horizon: int) -> list[Decimal]:
    if horizon not in (30, 60, 90):
        raise ValueError("Horizonte requerido: 30, 60 o 90.")
    if len(history) < 60 or any(not value.is_finite() for value in history):
        raise ValueError("ARIMA requiere al menos 60 días completos y finitos.")
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        raise ImportError("Instala backend/requirements-research.txt para evaluar ARIMA.") from None
    # Ventana y escala fijas, calculadas exclusivamente con el entrenamiento.
    training = history[-730:]
    scale = max(max(abs(value) for value in training), Decimal("1"))
    values = [float(value / scale) for value in training]
    fitted = ARIMA(values, order=(1, 0, 0), trend="c", enforce_stationarity=True).fit(
        method_kwargs={"maxiter": 100}
    )
    if not fitted.mle_retvals.get("converged", False):
        raise ArimaFitError("El ajuste ARIMA no convergió; registrar la ventana como fallida.")
    forecast = fitted.forecast(steps=horizon)
    if len(forecast) != horizon or any(not math.isfinite(float(value)) for value in forecast):
        raise ArimaFitError("ARIMA produjo un pronóstico no finito o incompleto.")
    return [
        (Decimal(str(float(value))) * scale).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for value in forecast
    ]
