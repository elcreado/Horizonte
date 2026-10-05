"""Envolvente de ejecuciones: las instantáneas versionadas siguen siendo JSON parcial."""

from .auth_contracts import object_response
from .forecast_result_contract import forecast_result_schema


def apply_forecast_runs_contract(path, method, operation):
    if path != "/api/companies/{company_id}/forecast-runs/":
        return
    row = object_response(
        {
            "id": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"},
            "method": {"type": "string"},
            "horizon": {"type": "integer", "enum": [30, 60, 90]},
            "as_of": {"type": "string", "format": "date"},
            "evidence": {
                "type": "object",
                "additionalProperties": True,
                "description": "Instantánea versionada congelada; esquema interno pendiente. Incluye source_digest y entradas del cálculo.",
            },
            "result": forecast_result_schema(),
        }
    )
    operation["x-contract-status"] = "forecast-runs-envelope-documented-snapshots-pending"
    operation["description"] = (
        "GET para todos los miembros; POST solo propietario/contador. Misma evidencia y método "
        "reutilizan ejecución (200); evidencia nueva crea ejecución (201) y auditoría. "
        "Ediciones posteriores no recalculan instantáneas guardadas. El fingerprint no se expone. "
        "No elimina ejecuciones ni permite editar resultados. Contrato de instantáneas aún parcial."
    )
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    if method == "get":
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "schema": {
                    "oneOf": [
                        {"type": "integer", "minimum": 1},
                        {"type": "string", "enum": ["last"]},
                    ]
                },
                "description": "Diez ejecuciones por página, fecha/ID descendentes; también admite last.",
            }
        )
        schema = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": {"type": "array", "maxItems": 10, "items": row},
                "can_save": {"type": "boolean"},
            }
        )
        statuses = {"200": ("Historial paginado.", schema)}
    else:
        operation["requestBody"] = {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "horizon": {"type": "integer", "enum": [30, 60, 90], "default": 30},
                            "method": {
                                "type": "string",
                                "enum": ["naive", "seasonal_naive", "ses", "hybrid_weekly"],
                                "default": "seasonal_naive",
                            },
                        },
                    }
                }
            },
        }
        statuses = {
            "200": ("Ejecución existente reutilizada.", row),
            "201": ("Nueva ejecución.", row),
        }
    for code, (description, schema) in statuses.items():
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": schema}},
        }
    errors = {
        "403": "Sesión ausente, CSRF rechazado o rol sin escritura.",
        "404": "Empresa/membresía o página no encontrada.",
    }
    if method == "post":
        errors.update(
            {
                "400": "Horizonte o método inválidos.",
                "409": "Evidencia insuficiente o incompatible; puede incluir accounts con diagnóstico de cobertura.",
            }
        )
    for code, description in errors.items():
        operation["responses"][code] = {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["detail"],
                        "properties": {"detail": {"type": "string"}},
                        "additionalProperties": True,
                    }
                }
            },
        }
