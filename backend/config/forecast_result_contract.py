"""Campos del resultado actual, conservando lectura de ejecuciones históricas."""

from .auth_contracts import object_response


def forecast_result_schema():
    amount = {"type": "string", "description": "Decimal exacto COP."}
    date = {"type": "string", "format": "date"}
    count = {"type": "integer", "minimum": 0}
    point = object_response(
        {"date": date, "known_flow": amount, "estimated_flow": amount, "balance": amount}
    )
    point["properties"].update(
        {"recurring_flow": amount, **{key: amount for key in ("p10", "p50", "p90")}}
    )
    point["description"] = (
        "Un día futuro. Cuantiles presentes solo cuando quantiles.status=experimental; recurring_flow puede faltar en versiones antiguas."
    )
    unavailable = object_response(
        {"status": {"type": "string", "enum": ["unavailable"]}, "notice": {"type": "string"}}
    )
    experimental = object_response(
        {
            "status": {"type": "string", "enum": ["experimental"]},
            "version": {"type": "string", "enum": ["weekly_empirical_errors_v1"]},
            "historical_origins": count,
            "history_days": count,
            "origin_step_days": count,
            "horizon": {"type": "integer", "enum": [30, 60, 90]},
            "last_calibration_end_index": count,
            "notice": {"type": "string"},
        }
    )
    result = object_response(
        {
            "status": {"type": "string", "enum": ["experimental"]},
            "method": {
                "type": "string",
                "enum": ["naive", "seasonal_naive", "ses", "hybrid_weekly"],
            },
            "horizon": {"type": "integer", "enum": [30, 60, 90]},
            "as_of": date,
            "training_start": date,
            "training_days": count,
            "observed_movements": count,
            "excluded_recurring_movements": count,
            "balance": amount,
            "known_future_obligations": count,
            "estimated_recurrence_occurrences": count,
            "points": {"type": "array", "minItems": 30, "maxItems": 90, "items": point},
            "quantiles": {"oneOf": [unavailable, experimental]},
            "first_deficit": {**date, "nullable": True},
            "minimum_balance": amount,
            "liquidity_alert": object_response(
                {
                    "threshold": amount,
                    "currently_below": {"type": "boolean"},
                    "first_below": {**date, "nullable": True},
                    "projected_days_below": count,
                    "shortfall_at_minimum": amount,
                }
            ),
            "notice": {"type": "string"},
        }
    )
    # Las filas históricas no se migran ni recalculan al añadir nuevos campos del modelo.
    for optional in (
        "quantiles",
        "estimated_recurrence_occurrences",
        "excluded_recurring_movements",
    ):
        result["required"].remove(optional)
    result["description"] = (
        "Resultado congelado. Los campos opcionales pueden faltar en ejecuciones anteriores. "
        "known_flow son obligaciones; estimated_flow es flujo variable; recurring_flow suma "
        "recurrencias estimadas separadas. P10/P50/P90 experimentales no calibrados no expresan "
        "probabilidad de déficit ni cobertura conjunta. No completar campos históricos ausentes con cero."
    )
    return result
