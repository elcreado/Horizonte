"""Contrato de evaluaciones contractuales guardadas; no son probabilidades."""

from .auth_contracts import object_response


def apply_alert_history_contract(path, method, operation):
    if path != "/api/companies/{company_id}/alert-history/":
        return
    money = {"type": "string", "description": "Importe decimal exacto COP."}
    identifier = {"type": "integer"}
    date = {"type": "string", "format": "date"}
    evidence = object_response(
        {
            "method": {"type": "string", "enum": ["obligations_v1"]},
            "as_of": date,
            "horizon": {"type": "integer", "enum": [30, 60, 90]},
            "threshold": money,
            "balance": money,
            "accounts": {
                "type": "array",
                "items": object_response({"id": identifier, "balance": money}),
            },
            "obligations": {
                "type": "array",
                "items": object_response(
                    {
                        "id": identifier,
                        "description": {"type": "string"},
                        "date": date,
                        "direction": {"type": "string", "enum": ["in", "out"]},
                        "amount": money,
                    }
                ),
            },
        }
    )
    result = object_response(
        {
            "threshold": money,
            "currently_below": {"type": "boolean"},
            "first_below": {**date, "nullable": True},
            "projected_days_below": {"type": "integer", "minimum": 0},
            "shortfall_at_minimum": money,
        }
    )
    row = object_response(
        {
            "id": identifier,
            "created_at": {"type": "string", "format": "date-time"},
            "evidence": evidence,
            "result": result,
        }
    )
    operation["x-contract-status"] = "alert-history-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    operation["description"] = (
        "Evalúa solo obligaciones pendientes no canceladas y saldo declarado, con umbral "
        "determinístico. Evidencia congelada; no predice cobros ni probabilidad de déficit. "
        "El mismo fingerprint reutiliza la evaluación y no duplica la auditoría. "
        "first_below es el corte si el saldo actual está bajo el umbral; en otro caso la "
        "primera fecha futura, o null. projected_days_below cuenta únicamente días futuros."
    )
    if method == "get":
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1},
                "description": "Página de 10 evaluaciones; fecha/ID descendente.",
            }
        )
        schema = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": {"type": "array", "items": row},
                "can_save": {"type": "boolean"},
            }
        )
        statuses = {"200": ("Consulta para todos los roles de la empresa.", schema)}
    else:
        operation["requestBody"] = {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "horizon": {"type": "integer", "enum": [30, 60, 90], "default": 30}
                        },
                    }
                }
            },
        }
        statuses = {
            "200": ("Evaluación existente reutilizada.", row),
            "201": ("Evaluación creada por propietario o contador y auditada.", row),
        }
        for code, description in {
            "400": "Horizonte inválido.",
            "409": "Sin cuentas COP con corte común.",
        }.items():
            operation["responses"][code] = {
                "description": description,
                "content": {
                    "application/json": {"schema": object_response({"detail": {"type": "string"}})}
                },
            }
    for code, (description, schema) in statuses.items():
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": schema}},
        }
    for code, description in {
        "403": "Sesión/CSRF rechazados o escritura sin rol permitido.",
        "404": "Empresa/membresía o página inexistente.",
    }.items():
        operation["responses"][code] = {
            "description": description,
            "content": {
                "application/json": {"schema": object_response({"detail": {"type": "string"}})}
            },
        }
