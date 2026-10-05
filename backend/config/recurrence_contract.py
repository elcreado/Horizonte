"""Patrones sugeridos, revisión y materialización de ocurrencias."""

from .auth_contracts import object_response


def apply_recurrence_contract(path, method, operation):
    base = "/api/companies/{company_id}/recurrences/"
    unlink = "/api/companies/{company_id}/recurrence-occurrences/{occurrence_id}/unlink/"
    if path not in (base, unlink):
        return
    text = {"type": "string"}
    identifier = {"type": "integer"}
    date = {"type": "string", "format": "date"}
    amount = {"type": "string", "description": "Decimal exacto COP."}
    operation["x-contract-status"] = "recurrence-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    statuses = {}
    if path == unlink:
        operation["description"] = (
            "Solo propietario/contador. Elimina vínculo, conservando obligación, pagos y efecto en proyección; audita una vez. No requiere cuerpo. Repetir devuelve 404, no una segunda reversión ni una cancelación."
        )
        statuses["200"] = object_response({"detail": text})
    else:
        operation["parameters"].append(
            {
                "name": "horizon",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "enum": [30, 60, 90], "default": 30},
            }
        )
        operation["description"] = (
            "GET para todos los miembros, POST propietario/contador. Saldos COP con corte común. "
            "Detecta historial de 370 días hasta el corte, agrupado por cuenta/descripción/signo; "
            "tres fechas distintas como mínimo y montos dentro del 10% de la mediana. "
            "Lista completa sin paginación, orden próxima fecha/cuenta/descripción; puede incluir "
            "patrones cuya próxima fecha quede fuera del horizonte y sin ocurrencias. Revisar "
            "no cancela obligaciones. create/link requieren revisión confirmed vigente y fecha "
            "expandida dentro del horizonte query. Un vínculo ya existente devuelve 200; nuevo 201. "
            "Crear evita obligación ambigua del mismo sentido/fecha; vincular exige obligación "
            "pendiente no cancelada, misma fecha/sentido y sin vínculo. No cambia saldo bancario."
        )
        if method == "get":
            matching = object_response(
                {
                    "id": identifier,
                    "reference": text,
                    "description": text,
                    "outstanding_amount": amount,
                }
            )
            occurrence = object_response(
                {
                    "date": date,
                    "link_id": {**identifier, "nullable": True},
                    "obligation_id": {**identifier, "nullable": True},
                    "cancelled": {"type": "boolean"},
                    "matching_obligations": {"type": "array", "items": matching},
                }
            )
            candidate = object_response(
                {
                    "account_id": identifier,
                    "description": text,
                    "direction": {"type": "string", "enum": ["in", "out"]},
                    "cadence": {"type": "string", "enum": ["monthly", "weekly"]},
                    "amount": amount,
                    "next_date": date,
                    "observations": {"type": "integer", "minimum": 3},
                    "transaction_ids": {"type": "array", "items": identifier},
                    "fingerprint": text,
                    "status": {"type": "string", "enum": ["pending", "confirmed", "rejected"]},
                    "occurrences": {"type": "array", "items": occurrence},
                }
            )
            statuses["200"] = object_response(
                {
                    "as_of": date,
                    "horizon": {"type": "integer", "enum": [30, 60, 90]},
                    "can_edit": {"type": "boolean"},
                    "results": {"type": "array", "items": candidate},
                    "notice": text,
                }
            )
        else:
            request = object_response(
                {
                    "fingerprint": text,
                    "status": {
                        "type": "string",
                        "enum": ["confirmed", "rejected", "pending", "create", "link"],
                    },
                }
            )
            request["properties"].update(
                {
                    "occurrence_date": {
                        **date,
                        "description": "create/link: por defecto next_date; debe pertenecer al patrón/horizonte.",
                    },
                    "obligation_id": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2**63 - 1,
                        "description": "Requerido para link de una nueva ocurrencia.",
                    },
                }
            )
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": request}},
            }
            created = object_response({"obligation_id": identifier})
            reviewed = object_response(
                {"status": {"type": "string", "enum": ["confirmed", "rejected", "pending"]}}
            )
            statuses["200"] = {"oneOf": [reviewed, created]}
            statuses["201"] = created
    for code, schema in statuses.items():
        operation["responses"][code] = {
            "description": "Resultado de consulta/revisión/vínculo según operación.",
            "content": {"application/json": {"schema": schema}},
        }
    errors = {
        "403": "Sesión/CSRF/rol rechazado.",
        "404": "Empresa/membresía, obligación u ocurrencia no encontrada en su tenant.",
    }
    if path == base:
        errors.update(
            {
                "400": "Horizonte, estado, fecha o identificador inválido.",
                "409": "Saldos incompatibles, patrón cambiado/no confirmado, vínculo incompatible o obligación ambigua.",
            }
        )
    for code, description in errors.items():
        operation["responses"][code] = {
            "description": description,
            "content": {"application/json": {"schema": object_response({"detail": text})}},
        }
