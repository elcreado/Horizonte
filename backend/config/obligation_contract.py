"""Contrato de listado, creación y edición de compromisos pendientes."""

from apps.forecast.serializers import ObligationEdit, ObligationInput

from .auth_contracts import object_response, string_input


def apply_obligation_contract(path, method, operation):
    collection = "/api/companies/{company_id}/obligations/"
    detail = collection + "{obligation_id}/"
    if (path, method) not in ((collection, "get"), (collection, "post"), (detail, "patch")):
        return
    row = object_response(
        {
            "id": {"type": "integer"},
            "reference": {"type": "string", "maxLength": 120},
            "description": {"type": "string", "maxLength": 200},
            "counterparty": {"type": "string", "maxLength": 200},
            "direction": {"type": "string", "enum": ["in", "out"]},
            "due_date": {"type": "string", "format": "date"},
            "outstanding_amount": {
                "type": "string",
                "description": "Decimal COP pendiente; puede ser cero después de conciliar.",
            },
            "cancelled": {"type": "boolean"},
            "status": {"type": "string", "enum": ["cancelled", "settled", "pending"]},
        }
    )
    operation["x-contract-status"] = "obligation-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    operation["description"] = (
        "Lectura para todos los miembros; escritura solo propietario/contador. Referencia única "
        "por empresa. Crear no modifica saldo bancario. Cancelación prevalece sobre pendiente cero "
        "en status. Editar no permite cambiar referencia, dirección ni importe: el pendiente se "
        "reduce/restituye mediante conciliaciones/reversiones. Cambiar vencimiento no mueve dinero."
    )
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
                "description": "20 filas; no canceladas primero, vencimiento/ID ascendentes.",
            }
        )
        schema = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "can_edit": {"type": "boolean"},
                "results": {"type": "array", "maxItems": 20, "items": row},
            }
        )
        code = "200"
    else:
        body = string_input(ObligationInput if method == "post" else ObligationEdit)
        if method == "patch":
            body["additionalProperties"] = False
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": body}},
        }
        schema, code = row, "201" if method == "post" else "200"
    operation["responses"][code] = {
        "description": "Resultado de la operación.",
        "content": {"application/json": {"schema": schema}},
    }
    for code, description in {
        "403": "Sesión/CSRF/rol rechazado.",
        "404": "Empresa, membresía, obligación o página no encontrada.",
    }.items():
        operation["responses"][code] = {
            "description": description,
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
    if method != "get":
        operation["responses"]["400"] = {
            "description": "Campos inválidos, referencia duplicada o campos no editables. Errores por campo o lista de mensajes.",
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
                                    ],
                                },
                            },
                            {"type": "array", "items": {"type": "string"}},
                        ]
                    }
                }
            },
        }
