"""Contrato del historial de auditoría por empresa."""

from .auth_contracts import object_response


def apply_audit_contract(path, method, operation):
    if path != "/api/companies/{company_id}/audit/" or method != "get":
        return
    operation["x-contract-status"] = "audit-fields-documented"
    operation["responses"].pop("2XX", None)
    operation["description"] = (
        "Solo propietario y contador de esta empresa. Orden descendente por fecha e ID. "
        "Snapshots before/after específicos de cada evento, sin esquema uniforme; "
        "esta ruta no modifica ni elimina registros."
    )
    operation["parameters"].extend(
        [
            {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1},
                "description": "Página de 20 registros.",
            },
            {
                "name": "action",
                "in": "query",
                "schema": {"type": "string", "maxLength": 80},
                "description": "Coincidencia exacta tras retirar espacios exteriores; vacío no filtra.",
            },
        ]
    )
    event = object_response(
        {
            "id": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"},
            "username": {"type": "string"},
            "action": {"type": "string"},
            "entity": {"type": "string"},
            "entity_id": {"type": "string"},
            "before": {"type": "object", "additionalProperties": True},
            "after": {"type": "object", "additionalProperties": True},
        }
    )
    operation["responses"]["200"] = {
        "description": "Eventos paginados del tenant autorizado.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "count": {"type": "integer", "minimum": 0},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {"type": "array", "items": event},
                    }
                )
            }
        },
    }
    for status, detail in {
        "400": "Filtro action mayor a 80 caracteres.",
        "403": "Sesión ausente o rol sin acceso a auditoría.",
        "404": "Empresa, membresía o página no encontrada.",
    }.items():
        operation["responses"][status] = {
            "description": detail,
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
