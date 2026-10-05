"""Entradas congeladas del cálculo y variantes de evidencia recurrente."""

from .auth_contracts import object_response
from .forecast_result_contract import forecast_result_schema


def forecast_evidence_schema():
    money = {"type": "string", "description": "Decimal exacto COP."}
    date = {"type": "string", "format": "date"}
    count = {"type": "integer", "minimum": 0}
    text = {"type": "string"}
    common = {"key": text, "date": date}
    estimated = object_response(
        {
            **common,
            "state": {"type": "string", "enum": ["estimated"]},
            "amount": money,
            "account_id": {"type": "integer"},
            "description": text,
        }
    )
    managed = object_response(
        {
            **common,
            "state": {"type": "string", "enum": ["managed"]},
            "obligation_id": {"type": "integer"},
            "actual_due_date": date,
            "cancelled": {"type": "boolean"},
            "outstanding_amount": money,
        }
    )
    model = forecast_result_schema()["properties"]["quantiles"]["oneOf"][1]
    model["properties"].pop("status")
    model["required"].remove("status")
    inputs = object_response(
        {
            "training_start": date,
            "training_series": {"type": "array", "items": money},
            "future_flows": {"type": "array", "items": money},
            "model": model,
        }
    )
    evidence = object_response(
        {
            "version": {
                "type": "string",
                "description": "baseline_v1 o hybrid_weekly_v2 actuales; puede conservar una versión histórica.",
            },
            "method": {"type": "string"},
            "horizon": {"type": "integer", "enum": [30, 60, 90]},
            "as_of": date,
            "training_start": date,
            "balance": money,
            "threshold": money,
            "source_digest": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "accounts": count,
            "movements": count,
            "settlement_allocations": count,
            "excluded_recurring_movements": count,
            "known_future_obligations": count,
            "training_series": {"type": "array", "items": money},
            "known_flows": {
                "type": "object",
                "additionalProperties": money,
                "description": "Claves fecha ISO; flujo firmado agregado de obligaciones futuras.",
            },
            "recurrence_estimates": {"type": "array", "items": {"oneOf": [estimated, managed]}},
            "quantile_inputs": {"oneOf": [{"type": "object", "maxProperties": 0}, inputs]},
        }
    )
    for field in ("quantile_inputs", "recurrence_estimates", "excluded_recurring_movements"):
        evidence["required"].remove(field)
    evidence["description"] = (
        "Instantánea inmutable; counts no contienen IDs. training_series guarda flujo variable "
        "residual desde training_start hasta as_of. quantile_inputs usa su propio entrenamiento "
        "de 270 días cuando está disponible; {} significa ausente, no serie cero. Una ocurrencia "
        "managed conserva el vínculo incluso cancelado/saldado y no se estima de nuevo. "
        "source_digest identifica las fuentes, no es una firma ni garantiza exactitud. "
        "Campos añadidos después pueden faltar en ejecuciones históricas."
    )
    return evidence
