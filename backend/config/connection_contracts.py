"""Contratos del conector sintético; no documentan una integración bancaria externa."""

from .auth_contracts import object_response


def apply_connection_contract(path, method, operation):
    root = "/api/companies/{company_id}/bank-connections/"
    if not path.startswith(root):
        return
    identifier = {"type": "integer"}
    timestamp = {"type": "string", "format": "date-time"}
    nullable_timestamp = {**timestamp, "nullable": True}
    connection = object_response(
        {
            "id": identifier,
            "provider": {"type": "string", "enum": ["mock"]},
            "status": {"type": "string", "enum": ["active", "revoked"]},
            "created_at": timestamp,
            "revoked_at": nullable_timestamp,
            "account_id": identifier,
            "consent": object_response(
                {
                    "id": identifier,
                    "scopes": {"type": "array", "items": {"type": "string"}},
                    "granted_at": timestamp,
                    "revoked_at": nullable_timestamp,
                }
            ),
        }
    )
    job = object_response(
        {
            "id": identifier,
            "connection_id": identifier,
            "status": {"type": "string", "enum": ["queued", "completed", "failed"]},
            "created_count": {"type": "integer", "minimum": 0},
            "duplicate_count": {"type": "integer", "minimum": 0},
            "error": {"type": "string"},
            "created_at": timestamp,
            "finished_at": nullable_timestamp,
        }
    )
    operation["x-contract-status"] = "mock-bank-fields-documented"
    operation["responses"].pop("2XX", None)
    operation.pop("x-request-schema-pending", None)
    if path == root and method == "get":
        schema = object_response(
            {
                "can_manage": {"type": "boolean"},
                "connections": {"type": "array", "items": connection},
                "jobs": {"type": "array", "maxItems": 20, "items": job},
            }
        )
        code = "200"
        description = "Conexiones de la empresa y veinte jobs más recientes. Requiere membresía."
    elif path == root:
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": object_response(
                        {
                            "provider": {"type": "string", "enum": ["mock"]},
                            "consent": {"type": "boolean", "enum": [True]},
                        }
                    )
                }
            },
        }
        schema = object_response({"connection": connection, "job": job})
        code = "201"
        description = "Owner/accountant autoriza saldo y movimientos sintéticos; crea o reactiva conexión y solicita sincronización. Consultar status del job: 201 no acredita tarea completada."
        operation["responses"]["400"] = {
            "description": "Fuente no mock o consentimiento distinto de true."
        }
        operation["responses"]["409"] = {
            "description": "Conexión ya activa, conflicto de identidad o cortes de cuentas no unificados."
        }
        operation["responses"]["503"] = {
            "description": "No se pudo persistir el trabajo y su mensaje; operación revertida."
        }
    elif path.endswith("/sync/"):
        schema, code = job, "202"
        description = "Owner/accountant solicita sincronización asíncrona. 202 significa queued, no ejecución completada."
        operation["responses"]["409"] = {"description": "Conexión revocada o job pendiente."}
        operation["responses"]["503"] = {
            "description": "Cola no disponible; puede devolver job fallido o error de persistencia."
        }
    else:
        schema, code = connection, "200"
        description = "Owner/accountant revoca consentimiento; cancela jobs pendientes. Repetir la revocación es idempotente; conserva movimientos previos."
    operation["description"] = description
    operation["responses"][code] = {
        "description": "Resultado de la operación.",
        "content": {"application/json": {"schema": schema}},
    }
    operation["responses"]["403"] = {"description": "Sesión/CSRF rechazados o rol insuficiente."}
    operation["responses"]["404"] = {
        "description": "Membresía o conexión de la empresa no encontrada."
    }
