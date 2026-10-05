"""Contratos explícitos de autenticación para ampliar el inventario OpenAPI."""

from rest_framework import serializers

from apps.accounts.onboarding import CompanyInput
from apps.accounts.profile import ProfileInput
from apps.accounts.recovery import RecoveryInput, ResetInput
from apps.accounts.registration import Registration


def string_input(serializer_class) -> dict:
    properties, required = {}, []
    for name, field in serializer_class().fields.items():
        if isinstance(field, serializers.IntegerField):
            schema = {"type": "integer"}
            if field.min_value is not None:
                schema["minimum"] = field.min_value
            if field.max_value is not None:
                schema["maximum"] = field.max_value
        elif isinstance(field, serializers.ChoiceField):
            schema = {"type": "string", "enum": list(field.choices)}
        elif isinstance(field, serializers.BooleanField):
            schema = {"type": "boolean"}
        elif isinstance(field, serializers.DecimalField):
            schema = {
                "oneOf": [{"type": "string"}, {"type": "number"}],
                "description": "Importe decimal; se recomienda cadena para conservar precisión.",
                "x-max-digits": field.max_digits,
                "x-decimal-places": field.decimal_places,
            }
            for attribute, keyword in (("min_value", "minimum"), ("max_value", "maximum")):
                bound = getattr(field, attribute)
                if bound is not None:
                    schema["oneOf"][1][keyword] = float(bound)
                    schema[f"x-decimal-{keyword}"] = str(bound)
        elif isinstance(field, serializers.DateField):
            schema = {"type": "string", "format": "date"}
        elif isinstance(field, serializers.UUIDField):
            schema = {"type": "string", "format": "uuid"}
        elif isinstance(field, serializers.CharField):
            schema = {"type": "string"}
            if field.max_length is not None:
                schema["maxLength"] = field.max_length
            minimum = field.min_length or (0 if field.allow_blank else 1)
            schema["minLength"] = minimum
            if isinstance(field, serializers.EmailField):
                schema["format"] = "email"
            if isinstance(field, serializers.RegexField):
                for validator in field.validators:
                    if hasattr(validator, "regex"):
                        schema["pattern"] = validator.regex.pattern
        else:
            raise ValueError("Campo no soportado en contrato de autenticación.")
        if name in ("password", "password_confirm", "current_password", "token"):
            schema["writeOnly"] = True
        properties[name] = schema
        if field.required:
            required.append(name)
    return {"type": "object", "properties": properties, "required": required}


def object_response(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties)}


def apply_auth_contract(path: str, method: str, operation: dict):
    text = {"type": "string"}
    contracts = {
        ("/api/auth/register/", "post"): (
            string_input(Registration),
            "201",
            object_response({"username": text, "company_id": {"type": "integer"}}),
            "Crea usuario, empresa, propietario y cuenta COP de forma atómica e inicia sesión. Rechaza sesiones ya iniciadas y usuario/NIT duplicados. NIT único sin distinguir mayúsculas; corte no futuro; contraseña confirmada y validada por Django. Límite 10/minuto compartido con login.",
        ),
        ("/api/auth/profile/", "get"): (
            None,
            "200",
            object_response({"username": text, "email": text}),
            "Consulta usuario y correo de la sesión.",
        ),
        ("/api/auth/profile/", "patch"): (
            string_input(ProfileInput),
            "200",
            object_response({"username": text, "email": text}),
            "Requiere contraseña actual correcta y correo o nueva contraseña. Una nueva contraseña requiere confirmación coincidente y validadores Django. Conserva la sesión actual al cambiarla.",
        ),
        ("/api/companies/create/", "post"): (
            string_input(CompanyInput),
            "201",
            object_response({"id": {"type": "integer"}, "name": text}),
            "Crea empresa, membresía de propietario y cuenta COP de forma atómica. NIT único sin distinguir mayúsculas; fecha de corte no futura.",
        ),
        ("/api/auth/csrf/", "get"): (
            None,
            "200",
            object_response({"csrfToken": text}),
            "Obtiene cookie/token CSRF; no inicia sesión.",
        ),
        ("/api/auth/me/", "get"): (
            None,
            "200",
            object_response({"username": text, "platform_admin": {"type": "boolean"}}),
            "Consulta el usuario de la sesión y su capacidad de administración de plataforma.",
        ),
        ("/api/auth/logout/", "post"): (
            None,
            "204",
            None,
            "Cierra la sesión; respuesta sin cuerpo.",
        ),
        ("/api/auth/login/", "post"): (
            {
                "type": "object",
                "required": ["username", "password"],
                "properties": {"username": text, "password": {"type": "string", "writeOnly": True}},
            },
            "200",
            object_response({"username": text}),
            "Valida credenciales y establece cookie de sesión. Límite 10/minuto compartido con registro.",
        ),
        ("/api/auth/recover-password/", "post"): (
            string_input(RecoveryInput),
            "202",
            object_response({"detail": text}),
            "Encola recuperación; respuesta genérica independientemente de existencia del usuario. No garantiza entrega. Límite 5/hora compartido con reset.",
        ),
        ("/api/auth/reset-password/", "post"): (
            string_input(ResetInput),
            "200",
            object_response({"detail": text}),
            "Token vigente y confirmación coincidente; validadores de contraseña Django. Cambiar contraseña invalida token y sesiones anteriores; vence en una hora.",
        ),
    }
    contract = contracts.get((path, method))
    if contract is None:
        return
    request, status, response, description = contract
    operation["description"] = description
    operation["x-contract-status"] = "auth-fields-documented"
    operation.pop("x-request-schema-pending", None)
    operation["responses"].pop("2XX")
    success = {"description": description}
    if response is not None:
        success["content"] = {"application/json": {"schema": response}}
    operation["responses"][status] = success
    if request is not None:
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": request}},
        }
