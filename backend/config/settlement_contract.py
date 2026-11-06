"""Conciliaciones idempotentes y reversión sin alterar el saldo declarado."""

from apps.forecast.serializers import SettlementInput

from .auth_contracts import object_response, string_input


def apply_settlement_contract(path, method, operation):
    base = "/api/companies/{company_id}/obligations/{obligation_id}/settlements/"
    reverse = base + "{settlement_id}/reverse/"
    if (path, method) not in ((base, "get"), (base, "post"), (reverse, "post")):
        return
    row = object_response(
        {
            "id": {"type": "integer"},
            "transaction_id": {"type": "integer"},
            "amount": {"type": "string", "description": "Importe decimal exacto COP conciliado."},
            "request_id": {"type": "string", "format": "uuid"},
            "created_at": {"type": "string", "format": "date-time"},
            "reversed_at": {"type": "string", "format": "date-time", "nullable": True},
        }
    )
    operation["x-contract-status"] = "settlement-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    operation["description"] = (
        "GET para todos los miembros; POST solo propietario/contador. Conciliar reduce el "
        "pendiente usando un movimiento existente del mismo tenant/sentido, incluido en su "
        "corte. No modifica saldo bancario ni crea movimientos. No puede superar pendiente "
        "o disponible no asignado del movimiento; obligación cancelada rechazada. "
        "request_id se reutiliza por obligación: mismo movimiento/importe devuelve 200 incluso "
        "si ya fue revertido, sin conciliar de nuevo; contenido distinto devuelve 400. "
        "Revertir restaura pendiente una sola vez y deja evidencia/auditoría. No borra la conciliación."
    )
    if method == "get":
        schema = {"type": "array", "items": row}
        statuses = {"200": "Lista completa, sin paginación, ID descendente; incluye revertidas."}
    else:
        schema = row
        statuses = {"200": "Conciliación existente o reversión idempotente."}
        if path == base:
            statuses["201"] = "Conciliación creada."
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": string_input(SettlementInput)}},
            }
        else:
            operation["description"] += (
                " Reversión no necesita cuerpo; cualquier campo enviado se ignora."
            )
    for code, description in statuses.items():
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": schema}},
        }
    for code, description in {
        "403": "Sesión/CSRF/rol rechazado.",
        "404": "Empresa/membresía, obligación, movimiento o conciliación no encontrada en su tenant.",
    }.items():
        operation["responses"][code] = {
            "description": description,
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
    if path == base and method == "post":
        operation["responses"]["400"] = {
            "description": "Validación de campos o regla de conciliación incumplida.",
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {
                                "type": "object",
                                "additionalProperties": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {"type": "array", "items": {"type": "string"}},
                                    ]
                                },
                            },
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    }
                }
            },
        }
