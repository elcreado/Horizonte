"""Monthly manual schedule contracts."""

from .auth_contracts import object_response


def apply_monthly_contract(path, method, operation):
    base = "/api/companies/{company_id}/monthly-schedules/"
    if path not in (base, base + "{schedule_id}/cancel/"):
        return
    text = {"type": "string"}
    day = {"type": "string", "format": "date"}
    fields = {
        "id": {"type": "integer"},
        "description": text,
        "direction": {"type": "string", "enum": ["in", "out"]},
        "amount": {"type": "string", "description": "Decimal positivo exacto COP."},
        "day": {"type": "integer", "minimum": 1, "maximum": 31},
        "start_date": day,
        "end_date": {**day, "nullable": True},
        "active": {"type": "boolean"},
    }
    row = object_response(fields)
    operation["description"] = (
        "Programaciones mensuales manuales. Lectura para miembros; creación/cancelación para propietario/contador con CSRF. Cada vencimiento genera una obligación única, disponible en calendario, resumen y pronóstico; no realiza transferencias. Días ausentes usan el último día del mes. Se mantiene una ventana móvil de vencimientos futuros. Cancelar detiene expansión y cancela obligaciones futuras sin conciliaciones; conserva historial."
    )
    operation["x-contract-status"] = "monthly-schedules-fields-documented"
    operation.pop("x-request-schema-pending", None)
    operation["responses"].pop("2XX", None)
    if method == "get":
        schema = object_response(
            {"can_edit": {"type": "boolean"}, "results": {"type": "array", "items": row}}
        )
        statuses = {"200": schema}
    elif path == base:
        inputs = {key: value for key, value in fields.items() if key not in ("id", "active")}
        inputs["request_id"] = {"type": "string", "format": "uuid"}
        schema = {
            "type": "object",
            "properties": inputs,
            "required": ["request_id", "description", "amount", "day"],
        }
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": schema}},
        }
        statuses = {"200": row, "201": row}
        operation["responses"]["409"] = {"description": "Misma clave con otros datos."}
    else:
        statuses = {"200": row}
    for status, schema in statuses.items():
        operation["responses"][status] = {
            "description": "Resultado; creación idempotente por UUID/empresa.",
            "content": {"application/json": {"schema": schema}},
        }
    for status, description in {
        "400": "Campos inválidos o rango de fechas invertido.",
        "403": "Sesión, CSRF o rol rechazados.",
        "404": "Empresa/membresía/programación propia no encontrada.",
    }.items():
        operation["responses"][status] = {"description": description}
