"""Consultas básicas de empresas y disponibilidad de la base de datos."""

from .auth_contracts import object_response


def apply_basic_queries_contract(path, method, operation):
    if method != "get" or path not in ("/api/companies/", "/api/health/"):
        return
    operation["x-contract-status"] = "basic-query-fields-documented"
    operation["responses"].pop("2XX", None)
    if path == "/api/health/":
        operation["description"] = (
            "Público. Ejecuta SELECT 1 en la base configurada. No verifica worker, correo ni recorrido funcional. No expone diagnóstico privado de fallos."
        )
        for code, status in (("200", "ok"), ("503", "unavailable")):
            operation["responses"][code] = {
                "description": "Resultado de conectividad de BD.",
                "content": {
                    "application/json": {
                        "schema": object_response({"status": {"type": "string", "enum": [status]}})
                    }
                },
            }
    else:
        operation["description"] = (
            "Sesión requerida. Lista completa sin paginación de empresas donde el usuario tiene membresía; puede estar vacía. No garantiza orden ni acceso administrativo implícito."
        )
        operation["responses"]["200"] = {
            "description": "Empresas de la sesión.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "array",
                        "items": object_response(
                            {"id": {"type": "integer"}, "name": {"type": "string"}}
                        ),
                    }
                }
            },
        }
        operation["responses"]["403"] = {
            "description": "Sesión ausente o rechazada.",
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
