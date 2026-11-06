"""Contrato de consulta administrativa, sin operaciones de escritura."""

from .auth_contracts import object_response


def apply_platform_contract(path, method, operation):
    if (path, method) != ("/api/platform/users/", "get"):
        return
    text, boolean = {"type": "string"}, {"type": "boolean"}
    item = object_response(
        {
            "id": {"type": "integer"},
            "username": text,
            "email": text,
            "is_active": boolean,
            "is_staff": boolean,
            "is_superuser": boolean,
            "company_count": {"type": "integer", "minimum": 0},
        }
    )
    link = {"type": "string", "format": "uri", "nullable": True}
    operation["description"] = (
        "Consulta transversal de usuarios para superusuario activo con is_staff. Owner/accountant/viewer y staff sin superusuario no autorizan acceso. Datos personales, sin contraseñas ni hashes; orden por ID ascendente, veinte por página. No permite modificar cuentas."
    )
    operation["x-contract-status"] = "platform-fields-documented"
    operation["x-required-role"] = "active-staff-superuser"
    operation["parameters"].append(
        {
            "name": "page",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "default": 1},
        }
    )
    operation["responses"].pop("2XX")
    operation["responses"]["200"] = {
        "description": "Usuarios visibles al administrador.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "count": {"type": "integer", "minimum": 0},
                        "next": link,
                        "previous": link,
                        "results": {"type": "array", "maxItems": 20, "items": item},
                    }
                )
            }
        },
    }
    operation["responses"]["403"] = {
        "description": "Sesión no autorizada para administración de plataforma."
    }
    operation["responses"]["404"] = {"description": "Página no encontrada."}
