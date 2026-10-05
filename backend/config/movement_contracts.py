"""Contratos de movimientos y corrección explícita de clasificación."""

from .auth_contracts import object_response


def apply_movement_contract(path, method, operation):
    if (path, method) in {
        ("/api/companies/{company_id}/classification-rules/", "get"),
        ("/api/companies/{company_id}/classification-rules/{rule_id}/", "delete"),
    }:
        apply_rule_contract(method, operation)
        return
    if (path, method) not in {
        ("/api/companies/{company_id}/movements/", "get"),
        ("/api/companies/{company_id}/movements/{transaction_id}/category/", "patch"),
    }:
        return
    text = {"type": "string"}
    operation["x-contract-status"] = "movement-fields-documented"
    operation["responses"].pop("2XX")
    if method == "get":
        operation["description"] = (
            "Movimientos de la empresa por fecha e ID descendentes; veinte por página. Requiere membresía. categories contiene opciones válidas según el signo. Sin filtros adicionales implementados."
        )
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            }
        )
        item = object_response(
            {
                "id": {"type": "integer"},
                "date": {"type": "string", "format": "date"},
                "description": text,
                "normalized_description": text,
                "merchant_name": text,
                "merchant_id": {"type": "integer", "nullable": True},
                "merchant_display_name": {"type": "string", "nullable": True},
                "amount": {"type": "string", "description": "Importe decimal exacto."},
                "category": text,
                "source": text,
                "categories": {"type": "array", "items": text},
            }
        )
        link = {"type": "string", "format": "uri", "nullable": True}
        response = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": link,
                "previous": link,
                "can_edit": {"type": "boolean"},
                "results": {"type": "array", "maxItems": 20, "items": item},
            }
        )
    else:
        operation["description"] = (
            "Corrección explícita por owner/accountant. category debe estar en las opciones del movimiento. remember es booleano JSON, opcional false; crea/actualiza regla por descripción normalizada y dirección de esta empresa. No admite recordar movimientos cero. Registra cada corrección."
        )
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["category"],
                        "properties": {
                            "category": text,
                            "remember": {"type": "boolean", "default": False},
                        },
                    }
                }
            },
        }
        response = object_response(
            {"category": text, "source": {"type": "string", "enum": ["manual"]}}
        )
        operation["responses"]["400"] = {
            "description": "Categoría/preferencia inválidas o regla solicitada para valor cero."
        }
    operation["responses"]["200"] = {
        "description": "Resultado exitoso.",
        "content": {"application/json": {"schema": response}},
    }
    operation["responses"]["403"] = {"description": "Sesión/CSRF rechazados o rol insuficiente."}
    operation["responses"]["404"] = {
        "description": "Membresía/movimiento de la empresa o página no encontrados."
    }


def apply_rule_contract(method, operation):
    operation["x-contract-status"] = "classification-rule-fields-documented"
    operation["responses"].pop("2XX")
    if method == "get":
        operation["description"] = (
            "Reglas recordadas de la empresa, por descripción normalizada/ID, veinte por página. Requiere membresía; can_edit indica owner/accountant. No vuelve a clasificar movimientos al consultar."
        )
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            }
        )
        text = {"type": "string"}
        item = object_response(
            {
                "id": {"type": "integer"},
                "normalized_description": text,
                "direction": {"type": "string", "enum": ["in", "out"]},
                "category": text,
                "updated_at": {"type": "string", "format": "date-time"},
            }
        )
        link = {"type": "string", "format": "uri", "nullable": True}
        schema = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": link,
                "previous": link,
                "can_edit": {"type": "boolean"},
                "results": {"type": "array", "maxItems": 20, "items": item},
            }
        )
        operation["responses"]["200"] = {
            "description": "Reglas visibles.",
            "content": {"application/json": {"schema": schema}},
        }
    else:
        operation["description"] = (
            "Elimina la regla de esta empresa con owner/accountant y auditoría. No cambia categorías de movimientos existentes. No requiere cuerpo JSON; CSRF sigue requerido."
        )
        operation.pop("x-request-schema-pending", None)
        operation["responses"]["204"] = {"description": "Regla eliminada; sin cuerpo."}
    operation["responses"]["403"] = {"description": "Sesión/CSRF rechazados o rol insuficiente."}
    operation["responses"]["404"] = {
        "description": "Membresía, regla de la empresa o página no encontrada."
    }
