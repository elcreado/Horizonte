"""Contrato del histórico registrado, separado del saldo y del pronóstico."""

from .auth_contracts import object_response


def apply_history_contract(path, method, operation):
    if path != "/api/companies/{company_id}/history/" or method != "get":
        return
    money = {
        "type": "string",
        "description": "Importe decimal exacto COP; egresos como magnitud positiva.",
    }
    count = {"type": "integer", "minimum": 0}
    date = {"type": "string", "format": "date"}
    operation["x-contract-status"] = "history-fields-documented"
    operation["description"] = (
        "Todos los roles de empresa pueden consultar. Doce meses hasta el corte común de "
        "cuentas COP, inclusive; mes actual posiblemente parcial. Mes sin filas se muestra "
        "con ceros y count=0, sin afirmar ausencia de actividad. Solo movimientos de esta "
        "empresa; neto mensual no equivale a saldo bancario. Categorías en orden alfabético."
    )
    operation["responses"].pop("2XX", None)
    operation["responses"]["200"] = {
        "description": "Histórico mensual y por categorías, sin paginación.",
        "content": {
            "application/json": {
                "schema": object_response(
                    {
                        "start": date,
                        "as_of": date,
                        "first_transaction": {**date, "nullable": True},
                        "count": count,
                        "notice": {"type": "string"},
                        "months": {
                            "type": "array",
                            "minItems": 12,
                            "maxItems": 12,
                            "items": object_response(
                                {
                                    "month": {"type": "string", "pattern": r"^\d{4}-\d{2}$"},
                                    "income": money,
                                    "expense": money,
                                    "net": money,
                                    "count": count,
                                }
                            ),
                        },
                        "categories": {
                            "type": "array",
                            "items": object_response(
                                {"category": {"type": "string"}, "income": money, "expense": money}
                            ),
                        },
                    }
                )
            }
        },
    }
    error = {"application/json": {"schema": object_response({"detail": {"type": "string"}})}}
    for status, description in {
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa o membresía no encontrada.",
        "409": "Sin cuentas, cortes distintos o moneda distinta de COP.",
    }.items():
        operation["responses"][status] = {"description": description, "content": error}
