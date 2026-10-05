"""Contrato del umbral de liquidez, sin atribuir probabilidades a la alerta."""

from apps.forecast.alerts import ThresholdInput

from .auth_contracts import object_response, string_input


def apply_threshold_contract(path, method, operation):
    if path != "/api/companies/{company_id}/liquidity-threshold/":
        return
    operation["x-contract-status"] = "threshold-fields-documented"
    operation["responses"].pop("2XX", None)
    operation["description"] = (
        "Consulta el umbral no negativo de la empresa y si el usuario puede editarlo. "
        "Solo el propietario puede modificarlo; se auditan cambios efectivos. "
        "El umbral produce alertas determinísticas, no probabilidades calibradas."
    )
    if method == "patch":
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": string_input(ThresholdInput)}},
        }
        operation["responses"]["400"] = {
            "description": "Umbral negativo, no finito o fuera de precisión decimal 18/2."
        }
    operation["responses"]["200"] = {
        "description": "Umbral vigente y permiso de edición.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "threshold": {"type": "string", "description": "Importe decimal exacto."},
                        "can_edit": {"type": "boolean"},
                    }
                )
            }
        },
    }
    operation["responses"]["403"] = {
        "description": "Sesión/CSRF rechazados o escritura sin rol propietario."
    }
    operation["responses"]["404"] = {"description": "Empresa o membresía no encontrada."}
