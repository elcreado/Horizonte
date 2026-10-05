"""Contrato del escenario contractual y evidencia histórica del dashboard."""

from .auth_contracts import object_response


def apply_dashboard_contract(path, method, operation):
    if path != "/api/companies/{company_id}/dashboard/" or method != "get":
        return
    amount = {"type": "string", "description": "Importe decimal exacto en COP."}
    date = {"type": "string", "format": "date"}
    nullable_date = {**date, "nullable": True}
    count = {"type": "integer", "minimum": 0}
    text = {"type": "string"}
    account = object_response(
        {
            "account_id": {"type": "integer"},
            "name": text,
            "state": {"type": "string", "enum": ["empty", "limited", "extended"]},
            "count": count,
            "first": nullable_date,
            "last": nullable_date,
            "span_days": count,
            "active_days": count,
            "days_since_last": {**count, "nullable": True},
            "other_category_count": count,
        }
    )
    fields = {
        "company": text,
        "currency": {"type": "string", "enum": ["COP"]},
        "as_of": date,
        "balance": amount,
        "horizon": {"type": "integer", "enum": [30, 60, 90]},
        "method": text,
        "notice": text,
        "receivable": amount,
        "payable": amount,
        "overdue_count": count,
        "first_deficit": nullable_date,
        "minimum_balance": amount,
        "points": {
            "type": "array",
            "minItems": 30,
            "maxItems": 90,
            "items": object_response({"date": date, "balance": amount}),
            "description": "Un punto por día futuro; longitud igual a horizon, sin incluir el corte.",
        },
        "liquidity_alert": object_response(
            {
                "threshold": amount,
                "currently_below": {"type": "boolean"},
                "first_below": nullable_date,
                "projected_days_below": count,
                "shortfall_at_minimum": amount,
            }
        ),
        "coverage": object_response(
            {
                "start": date,
                "as_of": date,
                "accounts": {"type": "array", "items": account},
                "method": {"type": "string", "enum": ["obligations_only"]},
                "notice": text,
            }
        ),
        "obligations": {
            "type": "array",
            "items": object_response(
                {
                    "id": {"type": "integer"},
                    "description": text,
                    "due_date": date,
                    "direction": {"type": "string", "enum": ["in", "out"]},
                    "amount": amount,
                }
            ),
        },
        "transactions": {
            "type": "array",
            "maxItems": 20,
            "items": object_response(
                {
                    "id": {"type": "integer"},
                    "date": date,
                    "description": text,
                    "category": text,
                    "amount": amount,
                }
            ),
        },
    }
    operation["x-contract-status"] = "dashboard-fields-documented"
    operation["description"] = (
        "Todos los miembros de la empresa. Suma saldos COP con corte común y proyecta "
        "pendientes no cancelados posteriores al corte hasta horizon, suponiendo pago puntual. "
        "Los vencidos solo se cuentan; no se trasladan al futuro. first_deficit y minimum_balance "
        "consideran puntos futuros; liquidity_alert incluye el saldo actual. coverage observa "
        "365 días hasta el corte, sin certificar completitud ni confianza predictiva. "
        "transactions contiene los 20 movimientos más recientes, incluso posteriores al corte. "
        "No entrega probabilidades ni cuantiles estadísticos."
    )
    operation["parameters"].append(
        {
            "name": "horizon",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "enum": [30, 60, 90], "default": 30},
        }
    )
    operation["responses"].pop("2XX", None)
    operation["responses"]["200"] = {
        "description": "Escenario contractual y evidencia observada.",
        "content": {"application/json": {"schema": object_response(fields)}},
    }
    for code, description in {
        "400": "Horizonte inválido.",
        "403": "Sesión ausente o rechazada.",
        "404": "Empresa o membresía no encontrada.",
        "409": "Sin cuentas, moneda distinta de COP o fechas de corte diferentes.",
    }.items():
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": object_response({"detail": text})}},
        }
