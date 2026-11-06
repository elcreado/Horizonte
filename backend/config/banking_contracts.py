"""Contratos verificados de saldo y declaración de cobertura bancaria."""

from apps.banking.coverage import CoverageInput
from apps.banking.views import AccountBalanceInput

from .auth_contracts import object_response, string_input


def apply_banking_contract(path: str, method: str, operation: dict):
    if path == "/api/companies/{company_id}/accounts/" and method == "get":
        date = {"type": "string", "format": "date"}
        item = object_response(
            {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "connection_id": {"type": "integer", "nullable": True},
                "currency": {"type": "string", "enum": ["COP"]},
                "balance": {
                    "type": "string",
                    "description": "Importe decimal exacto con dos decimales.",
                },
                "balance_date": date,
                "history_complete_from": {**date, "nullable": True},
                "history_complete_through": {**date, "nullable": True},
            }
        )
        operation["description"] = (
            "Cuentas de la empresa; requiere membresía. can_import indica rol owner/accountant, no autorización para cargar en una cuenta conectada. Sin paginación ni orden garantizado."
        )
        operation["x-contract-status"] = "banking-fields-documented"
        operation["responses"].pop("2XX")
        operation["responses"]["200"] = {
            "description": "Cuentas visibles.",
            "content": {
                "application/json": {
                    "schema": object_response(
                        {
                            "can_import": {"type": "boolean"},
                            "accounts": {"type": "array", "items": item},
                        }
                    )
                }
            },
        }
        operation["responses"]["403"] = {"description": "Sesión rechazada."}
        operation["responses"]["404"] = {"description": "Membresía no encontrada."}
        return
    if path == "/api/companies/{company_id}/imports/":
        apply_import_contract(method, operation)
        return
    nullable_date = {"type": "string", "format": "date", "nullable": True}
    coverage = {
        "history_complete_from": nullable_date,
        "history_complete_through": nullable_date,
    }
    contracts = {
        ("/api/companies/{company_id}/accounts/{account_id}/balance/", "patch"): (
            AccountBalanceInput,
            object_response(
                {
                    "balance": {"type": "string"},
                    "balance_date": {"type": "string", "format": "date"},
                    **coverage,
                }
            ),
            "Actualiza saldo manual. Corte no futuro ni anterior a movimientos existentes. Cambiar el corte elimina la declaración de cobertura. Registra auditoría si cambia el estado.",
            "Cuenta conectada o movimientos posteriores al corte solicitado.",
        ),
        ("/api/companies/{company_id}/accounts/{account_id}/coverage/", "post"): (
            CoverageInput,
            object_response(coverage),
            "Declara historial completo desde start hasta el corte de la cuenta, o lo retira con confirmed=false. Start debe estar entre el corte menos 3650 días y el corte, inclusive. No verifica por sí mismo la integridad de los movimientos.",
            "Cuenta conectada cuya cobertura procede de su fuente.",
        ),
    }
    contract = contracts.get((path, method))
    if contract is None:
        return
    serializer, response, description, conflict = contract
    operation["description"] = description + " Requiere membresía owner/accountant de la empresa."
    operation["x-contract-status"] = "banking-fields-documented"
    operation.pop("x-request-schema-pending", None)
    operation["requestBody"] = {
        "required": True,
        "content": {"application/json": {"schema": string_input(serializer)}},
    }
    operation["responses"].pop("2XX")
    operation["responses"]["200"] = {
        "description": "Estado actualizado.",
        "content": {"application/json": {"schema": response}},
    }
    for code, reason in {
        "400": "Datos inválidos; errores de campos o detail según la validación.",
        "403": "Sesión/CSRF rechazados o rol de solo consulta.",
        "404": "Membresía o cuenta de esta empresa no encontrada.",
        "409": conflict,
    }.items():
        operation["responses"][code] = {"description": reason}


def apply_import_contract(method: str, operation: dict):
    from apps.banking.models import ImportJob

    job = object_response(
        {
            "id": {"type": "integer"},
            "account_id": {"type": "integer"},
            "file_format": {
                "type": "string",
                "enum": [value for value, _ in ImportJob._meta.get_field("file_format").choices],
            },
            "status": {
                "type": "string",
                "enum": [value for value, _ in ImportJob._meta.get_field("status").choices],
            },
            "created_count": {"type": "integer", "minimum": 0},
            "duplicate_count": {"type": "integer", "minimum": 0},
            "error": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
            "finished_at": {"type": "string", "format": "date-time", "nullable": True},
        }
    )
    operation["x-contract-status"] = "banking-fields-documented"
    operation["responses"].pop("2XX")
    if method == "get":
        operation["description"] = (
            "Últimos 20 trabajos de la empresa, ordenados por ID descendente. Requiere membresía; no admite paginación. No expone el archivo original."
        )
        status, schema = "200", {"type": "array", "items": job, "maxItems": 20}
    else:
        operation["description"] = (
            "Encola CSV UTF-8 (BOM permitido) o XLSX, hasta 2 MiB y 10.000 filas. Requiere owner/accountant y cuenta manual de la empresa. 202 confirma aceptación, no importación exitosa: consultar estado mediante GET. El worker valida y procesa de forma atómica."
        )
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": object_response(
                        {
                            "account_id": {"type": "integer"},
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "Archivo .csv o .xlsx de hasta 2.097.152 bytes.",
                            },
                        }
                    )
                }
            },
        }
        status, schema = "202", job
        for code, reason in {
            "400": "Cuenta no seleccionada, archivo inválido o CSV no UTF-8.",
            "409": "Cuenta conectada: importar desde su fuente.",
            "503": "Cola no disponible; no se garantiza aceptación del trabajo.",
        }.items():
            operation["responses"][code] = {"description": reason}
    operation["responses"][status] = {
        "description": "Trabajos visibles."
        if method == "get"
        else "Trabajo aceptado para procesamiento asíncrono.",
        "content": {"application/json": {"schema": schema}},
    }
    operation["responses"]["403"] = {
        "description": "Sesión/CSRF rechazados o rol insuficiente para escritura."
    }
    operation["responses"]["404"] = {
        "description": "Membresía o cuenta de la empresa no encontrada."
    }
