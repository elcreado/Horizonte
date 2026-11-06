"""Contrato de flujos y saldos históricos reconstruidos, separado del pronóstico."""

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
    balance = {"type": "string", "pattern": r"^-?\d+\.\d{2}$"}
    operation["x-contract-status"] = "history-fields-documented"
    operation["description"] = (
        "Todos los roles de empresa pueden consultar. Doce meses hasta el corte común de "
        "cuentas COP, inclusive; mes actual posiblemente parcial. Mes sin filas se muestra "
        "con ceros y count=0, sin afirmar ausencia de actividad. Solo movimientos de esta "
        "empresa; neto mensual no equivale a saldo bancario. Categorías en orden alfabético. "
        "balance_history reconstruye cierres diarios hacia atrás desde el saldo declarado. "
        "Antes del corte exige cobertura de todas las cuentas; días sin cobertura tienen "
        "balance=null, no cero. El punto del corte siempre es declarado. No certifica saldos bancarios."
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
                        "balance_history": object_response(
                            {
                                "currency": {"type": "string", "enum": ["COP"]},
                                "cutoff": date,
                                "declared_balance": balance,
                                "complete_from": {**date, "nullable": True},
                                "notice": {"type": "string"},
                                "accounts": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": object_response(
                                        {
                                            "account_id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "declared_balance": balance,
                                            "balance_date": date,
                                            "complete_from": {**date, "nullable": True},
                                            "complete_through": {**date, "nullable": True},
                                            "coverage_valid": {"type": "boolean"},
                                            "coverage_source": {
                                                "type": "string",
                                                "enum": ["source", "manual_confirmation"],
                                            },
                                        }
                                    ),
                                },
                                "points": {
                                    "type": "array",
                                    "minItems": 1,
                                    "maxItems": 366,
                                    "items": object_response(
                                        {
                                            "date": date,
                                            "balance": {**balance, "nullable": True},
                                            "status": {
                                                "type": "string",
                                                "enum": ["declared", "reconstructed", "unknown"],
                                            },
                                        }
                                    ),
                                },
                            }
                        ),
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
