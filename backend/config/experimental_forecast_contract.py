"""Consulta del pronóstico experimental actual; no guarda una ejecución."""

from .auth_contracts import object_response
from .forecast_result_contract import forecast_result_schema


def apply_experimental_forecast_contract(path, method, operation):
    if path != "/api/companies/{company_id}/experimental-forecast/" or method != "get":
        return
    operation["x-contract-status"] = "experimental-forecast-fields-documented"
    operation["description"] = (
        "Todos los miembros. Calcula desde el corte común de saldos COP y cobertura declarada, "
        "sin guardar ejecución ni modificar saldos. Métodos de referencia experimentales; "
        "hybrid_weekly incorpora recurrencias confirmadas vigentes y obligaciones sin duplicarlas. "
        "No ofrece probabilidad de déficit ni cuantiles calibrados. Una declaración de cobertura "
        "no verifica que el extracto sea completo. Para congelar el resultado usar forecast-runs."
    )
    for name, schema in {
        "horizon": {"type": "integer", "enum": [30, 60, 90], "default": 30},
        "method": {
            "type": "string",
            "enum": ["naive", "seasonal_naive", "ses", "hybrid_weekly"],
            "default": "seasonal_naive",
        },
    }.items():
        operation["parameters"].append(
            {"name": name, "in": "query", "required": False, "schema": schema}
        )
    result = forecast_result_schema()
    # La consulta actual no contiene filas de versiones antiguas.
    result["required"] = list(result["properties"])
    result["properties"]["points"]["items"]["required"].append("recurring_flow")
    operation["responses"].pop("2XX", None)
    operation["responses"]["200"] = {
        "description": "Resultado calculado desde la evidencia actual.",
        "content": {"application/json": {"schema": result}},
    }
    for code, description in {
        "400": "Horizonte o método inválidos.",
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa o membresía no encontrada.",
        "409": "Saldos incompatibles, cobertura/evidencia insuficiente o recurrencias ambiguas.",
    }.items():
        fields = {"detail": {"type": "string"}}
        schema = object_response(fields)
        if code == "409":
            fields["accounts"] = {
                "type": "array",
                "items": {"type": "string"},
                "description": "Nombres de cuentas con cobertura insuficiente; campo opcional.",
            }
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": schema}},
        }
