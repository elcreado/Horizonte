"""Contratos de administración de empresas y membresías."""

from apps.accounts.models import CompanyMember
from apps.accounts.team import AddMember, CompanyName, RoleInput

from .auth_contracts import object_response, string_input


def apply_team_contract(path, method, operation):
    root = "/api/companies/{company_id}/team/"
    rename = path == "/api/companies/{company_id}/name/"
    if not path.startswith(root) and not rename:
        return
    operation["x-contract-status"] = "team-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    operation["description"] = (
        "Consulta del equipo para todos los roles. Alta, cambio de rol, baja y nombre "
        "reservados a propietarios de esta empresa y auditados. Las mutaciones se "
        "serializan por empresa; no se puede retirar ni degradar al último propietario activo. "
        "Añadir requiere usuario activo existente y sin membresía previa; no envía invitación."
    )
    identifier = {"type": "integer"}
    role = {"type": "string", "enum": [value for value, _ in CompanyMember.Role.choices]}
    member = object_response(
        {
            "id": identifier,
            "username": {"type": "string"},
            "role": role,
            "active": {"type": "boolean"},
        }
    )
    if method == "get":
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1},
                "description": "Página de 20 miembros, orden por ID ascendente.",
            }
        )
        schema = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": {"type": "array", "items": member},
                "can_manage": {"type": "boolean"},
                "my_membership_id": identifier,
            }
        )
        status, description = "200", "Equipo paginado y capacidad de administración."
    elif method in ("post", "patch"):
        serializer = CompanyName if rename else AddMember if method == "post" else RoleInput
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": string_input(serializer)}},
        }
        if rename:
            schema = object_response({"id": identifier, "name": {"type": "string"}})
            status, description = "200", "Nombre de empresa actualizado."
        elif method == "post":
            schema = object_response({"id": identifier, "role": role})
            status, description = "201", "Membresía creada."
        else:
            schema = None
            status, description = "204", "Rol actualizado; sin cuerpo."
    else:
        schema = None
        status, description = "204", "Membresía eliminada; usuario y datos financieros conservados."
    operation["responses"][status] = {"description": description}
    if schema:
        operation["responses"][status]["content"] = {"application/json": {"schema": schema}}
    for code, detail in {
        "400": "Entrada inválida, usuario no activo, membresía duplicada o último propietario.",
        "403": "Sesión/CSRF rechazados o mutación sin rol propietario.",
        "404": "Empresa/membresía ausentes, miembro ajeno o página inexistente.",
    }.items():
        operation["responses"][code] = {"description": detail}
