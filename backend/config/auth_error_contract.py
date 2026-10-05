"""Errores de autenticación; CSRF público puede devolver HTML de Django."""

from .auth_contracts import object_response


def apply_auth_error_contract(path, method, operation):
    protected = {
        "/api/auth/me/",
        "/api/auth/logout/",
        "/api/auth/profile/",
        "/api/companies/create/",
    }
    public_mutations = {
        "/api/auth/login/",
        "/api/auth/register/",
        "/api/auth/recover-password/",
        "/api/auth/reset-password/",
    }
    if path not in protected | public_mutations:
        return
    detail = object_response({"detail": {"type": "string"}})
    content = {"application/json": {"schema": detail}}
    if path in public_mutations:
        content["text/html"] = {
            "schema": {"type": "string"},
            "example": "Página de rechazo CSRF de Django; no interpretar como JSON.",
        }
    operation["responses"]["403"] = {
        "description": "Sesión ausente/rechazada o CSRF inválido. En endpoints públicos protegidos por csrf_protect, el rechazo puede ser HTML.",
        "content": content,
    }
    if method in ("post", "patch") and path != "/api/auth/logout/":
        errors = {
            "type": "object",
            "additionalProperties": {
                "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
            },
        }
        operation["responses"]["400"] = {
            "description": "Credenciales, token, formato JSON o validación de campos inválidos; detail o errores por campo/non_field_errors.",
            "content": {"application/json": {"schema": errors}},
        }
        operation["responses"]["415"] = {
            "description": "Tipo de contenido no admitido por el parser.",
            "content": {"application/json": {"schema": detail}},
        }
    if path in public_mutations:
        operation["responses"]["429"] = {
            "description": "Límite persistente alcanzado; esperar Retry-After. Login/registro comparten límite y recuperación/reset otro.",
            "headers": {
                "Retry-After": {
                    "description": "Segundos antes de reintentar.",
                    "schema": {"type": "integer", "minimum": 1},
                }
            },
            "content": {"application/json": {"schema": detail}},
        }
    if path == "/api/auth/recover-password/":
        operation["responses"]["503"] = {
            "description": "No se pudo encolar la recuperación; no demuestra existencia del usuario ni entrega de correo.",
            "content": {"application/json": {"schema": detail}},
        }
