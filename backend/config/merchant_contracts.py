"""Contratos de consulta y edición del nombre visible de comercios."""

from apps.banking.merchant_views import MerchantAliasInput, MerchantNameInput

from .auth_contracts import object_response, string_input


def apply_merchant_contract(path: str, method: str, operation: dict):
    if path == "/api/companies/{company_id}/merchant-aliases/":
        apply_alias_contract(method, operation)
        return
    if (path, method) not in {
        ("/api/companies/{company_id}/merchants/", "get"),
        ("/api/companies/{company_id}/merchants/{merchant_id}/name/", "patch"),
    }:
        return
    operation["x-contract-status"] = "merchant-fields-documented"
    operation["responses"].pop("2XX")
    identity = {"id": {"type": "integer"}, "display_name": {"type": "string", "maxLength": 250}}
    if method == "get":
        operation["description"] = (
            "Comercios explícitos de la empresa, ordenados por nombre visible e ID. Veinte por página; requiere membresía. can_edit informa rol owner/accountant."
        )
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            }
        )
        link = {"type": "string", "format": "uri", "nullable": True}
        response = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": link,
                "previous": link,
                "can_edit": {"type": "boolean"},
                "results": {
                    "type": "array",
                    "maxItems": 20,
                    "items": object_response(
                        {
                            **identity,
                            "normalized_name": {"type": "string"},
                            "movement_count": {"type": "integer", "minimum": 0},
                        }
                    ),
                },
            }
        )
    else:
        operation["description"] = (
            "Cambia solo el nombre visible, con owner/accountant. Conserva identidad normalizada, alias, vínculos y descripciones originales. Audita cambios efectivos; repetir el mismo nombre no genera otra auditoría. No consolida comercios ni reasigna alias."
        )
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": string_input(MerchantNameInput)}},
        }
        response = object_response(identity)
        operation["responses"]["400"] = {
            "description": "Nombre vacío o mayor de 250 caracteres; errores por campo."
        }
    operation["responses"]["200"] = {
        "description": "Resultado exitoso.",
        "content": {"application/json": {"schema": response}},
    }
    operation["responses"]["403"] = {
        "description": "Sesión/CSRF rechazados o rol de escritura insuficiente."
    }
    operation["responses"]["404"] = {
        "description": "Membresía/comercio de la empresa o página no encontrados."
    }


def apply_alias_contract(method: str, operation: dict):
    operation["x-contract-status"] = "merchant-alias-fields-documented"
    operation["responses"].pop("2XX", None)
    identity = {"id": {"type": "integer"}, "merchant_id": {"type": "integer"}}
    if method == "post":
        operation.pop("x-request-schema-pending", None)
        schema = string_input(MerchantAliasInput)
        schema["properties"]["provider"] = {"type": "string", "enum": ["manual_upload", "mock"]}
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": schema}},
        }
        operation["description"] = (
            "Owner/accountant asigna una etiqueta normalizada a un comercio de la empresa. "
            "La clave es empresa, fuente y etiqueta. Reemplaza la asignación previa y afecta "
            "solo futuras importaciones; conserva movimientos y descripciones anteriores. "
            "Audita cambios efectivos; repetir la misma asignación no duplica auditoría."
        )
        response = object_response(identity)
        operation["responses"]["201"] = {
            "description": "Nueva etiqueta creada.",
            "content": {"application/json": {"schema": response}},
        }
        operation["responses"]["400"] = {
            "description": "Fuente inválida, ID no positivo o etiqueta vacía/excesiva antes o después de normalizar."
        }
    else:
        operation["description"] = (
            "Consulta de alias de la empresa; requiere membresía. Veinte por página, "
            "ordenados por fuente, etiqueta normalizada e ID."
        )
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            }
        )
        link = {"type": "string", "format": "uri", "nullable": True}
        response = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": link,
                "previous": link,
                "can_edit": {"type": "boolean"},
                "results": {
                    "type": "array",
                    "maxItems": 20,
                    "items": object_response(
                        {
                            **identity,
                            "provider": {"type": "string"},
                            "normalized_name": {"type": "string", "maxLength": 250},
                            "merchant_display_name": {"type": "string", "maxLength": 250},
                        }
                    ),
                },
            }
        )
    operation["responses"]["200"] = {
        "description": "Listado o asignación de una etiqueta existente.",
        "content": {"application/json": {"schema": response}},
    }
    operation["responses"]["403"] = {"description": "Sesión/CSRF rechazados o rol insuficiente."}
    operation["responses"]["404"] = {
        "description": "Membresía, comercio de la empresa o página no encontrados."
    }
