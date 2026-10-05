"""Consultas de evidencia y movimientos disponibles para una obligación."""

from .auth_contracts import object_response


def apply_obligation_queries_contract(path, method, operation):
    base = "/api/companies/{company_id}/obligations/{obligation_id}/"
    if method != "get" or path not in (base + "candidates/", base + "history/"):
        return
    identifier = {"type": "integer"}
    text = {"type": "string"}
    if path.endswith("candidates/"):
        row = object_response(
            {
                "id": identifier,
                "date": {"type": "string", "format": "date"},
                "description": text,
                "amount": {"type": "string", "description": "Decimal COP con signo original."},
                "available": {
                    "type": "string",
                    "description": "Valor absoluto menos conciliaciones activas, decimal COP positivo.",
                },
            }
        )
        description = (
            "Todos los miembros. Movimientos de la empresa y mismo sentido, incluidos en el "
            "corte de su cuenta, con importe disponible positivo. Conciliaciones revertidas no "
            "consumen disponible. No limita disponible al pendiente ni exige coincidencia de "
            "contraparte/fecha de vencimiento; no recomienda ni concilia automáticamente. "
            "Una obligación cancelada o saldada puede tener candidatos; POST conciliación "
            "valida si la operación está permitida. Orden fecha/ID descendente."
        )
    else:
        row = object_response(
            {
                "id": identifier,
                "user__username": text,
                "action": text,
                "before": {"type": "object", "additionalProperties": True},
                "after": {"type": "object", "additionalProperties": True},
                "created_at": {"type": "string", "format": "date-time"},
            }
        )
        description = (
            "Todos los miembros, incluido lector. Cambios auditados de esta obligación, "
            "ID descendente. before/after son instantáneas JSON según acción y versión, "
            "no una especificación de toda la auditoría de la empresa. No expone registros "
            "de otras entidades; user__username conserva el nombre de campo de la respuesta."
        )
    operation["x-contract-status"] = "obligation-queries-fields-documented"
    operation["description"] = description
    operation["parameters"].append(
        {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {
                "oneOf": [{"type": "integer", "minimum": 1}, {"type": "string", "enum": ["last"]}]
            },
            "description": "20 filas por página.",
        }
    )
    operation["responses"].pop("2XX", None)
    schema = object_response(
        {
            "count": {"type": "integer", "minimum": 0},
            "next": {"type": "string", "nullable": True},
            "previous": {"type": "string", "nullable": True},
            "results": {"type": "array", "maxItems": 20, "items": row},
        }
    )
    operation["responses"]["200"] = {
        "description": "Resultado paginado.",
        "content": {"application/json": {"schema": schema}},
    }
    for code, message in {
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa/membresía, obligación o página no encontrada.",
    }.items():
        operation["responses"][code] = {
            "description": message,
            "content": {"application/json": {"schema": object_response({"detail": text})}},
        }
