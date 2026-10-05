"""Contrato del calendario agregado mensual de compromisos pendientes."""

from .auth_contracts import object_response


def apply_calendar_contract(path, method, operation):
    if path != "/api/companies/{company_id}/obligation-calendar/" or method != "get":
        return
    operation["x-contract-status"] = "calendar-fields-documented"
    operation["responses"].pop("2XX", None)
    operation["description"] = (
        "Consulta para todos los roles de la empresa. Agrega todas las obligaciones del mes "
        "por vencimiento y sentido; excluye canceladas y pendientes iguales a cero. "
        "No depende de la paginación de obligaciones ni informa pagos realizados. "
        "Incluye todos los días del mes, con importes/conteos cero cuando no hay pendientes."
    )
    operation["parameters"].append(
        {
            "name": "month",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "pattern": r"^[0-9]{4}-[0-9]{2}$"},
            "description": "Mes calendario válido YYYY-MM (años 0001–9999); por defecto mes local America/Bogota.",
        }
    )
    amount = {"type": "string", "description": "Suma decimal exacta COP de importes pendientes."}
    count = {"type": "integer", "minimum": 0}
    day = object_response(
        {
            "date": {"type": "string", "format": "date"},
            "receivable": amount,
            "payable": amount,
            "receivable_count": count,
            "payable_count": count,
        }
    )
    operation["responses"]["200"] = {
        "description": "Calendario mensual completo, sin paginación.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "month": {"type": "string"},
                        "currency": {"type": "string", "enum": ["COP"]},
                        "days": {"type": "array", "minItems": 28, "maxItems": 31, "items": day},
                        "notice": {"type": "string"},
                    }
                )
            }
        },
    }
    for code, description in {
        "400": "Mes con formato o fecha inválidos.",
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa o membresía no encontrada.",
    }.items():
        operation["responses"][code] = {
            "description": description,
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
