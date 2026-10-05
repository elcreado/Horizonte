"""Contrato de carga XML asíncrona, distinto de la confirmación de obligación."""

from apps.invoices.views import ConfirmInvoice, LinkObligation

from .auth_contracts import object_response, string_input


def invoice_response():
    text = {"type": "string"}
    date = {"type": "string", "format": "date"}
    fields = {
        name: text
        for name in (
            "supplier_nit",
            "customer_nit",
            "supplier",
            "customer",
            "subtotal",
            "total",
            "payable",
            "tax",
        )
    }
    return object_response(
        {
            **fields,
            "id": {"type": "integer"},
            "number": {"type": "string", "maxLength": 100},
            "cufe": {"type": "string", "maxLength": 150},
            "direction": {"type": "string", "enum": ["in", "out"]},
            "issue_date": date,
            "due_date": {**date, "nullable": True},
            "obligation_id": {"type": "integer", "nullable": True},
            "outstanding_amount": {"type": "string", "nullable": True},
            "cancelled": {"type": "boolean"},
        }
    )


def apply_invoice_contract(path, method, operation):
    if path == "/api/companies/{company_id}/invoices/{invoice_id}/obligation-link/":
        operation["x-contract-status"] = "invoice-link-fields-documented"
        operation["responses"].pop("2XX")
        if method == "get":
            operation["description"] = (
                "Candidatas de esta empresa con mismo sentido, vigentes, sin factura vinculada, fecha no anterior a emisión y pendiente no mayor al pagadero XML. Orden por vencimiento/ID; veinte por página. La coincidencia no implica equivalencia: revisar antes de vincular."
            )
            operation["parameters"].append(
                {
                    "name": "page",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer", "minimum": 1, "default": 1},
                }
            )
            text = {"type": "string"}
            item = object_response(
                {
                    "id": {"type": "integer"},
                    "reference": text,
                    "description": text,
                    "counterparty": text,
                    "due_date": {"type": "string", "format": "date"},
                    "outstanding_amount": text,
                }
            )
            link = {"type": "string", "format": "uri", "nullable": True}
            response = object_response(
                {
                    "count": {"type": "integer", "minimum": 0},
                    "next": link,
                    "previous": link,
                    "results": {"type": "array", "maxItems": 20, "items": item},
                }
            )
        else:
            operation["description"] = (
                "Vincula explícitamente obligación existente compatible, con owner/accountant y auditoría; no crea otra obligación. Rechaza obligación cancelada, distinta dirección, fecha/pendiente incompatibles o vínculo ocupado. Repetir el mismo vínculo devuelve la factura actual; otro vínculo se rechaza."
            )
            operation.pop("x-request-schema-pending", None)
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": string_input(LinkObligation)}},
            }
            response = invoice_response()
            operation["responses"]["400"] = {
                "description": "Datos o compatibilidad inválidos, o vínculo ocupado."
            }
        operation["responses"]["200"] = {
            "description": "Candidatas o factura vinculada.",
            "content": {"application/json": {"schema": response}},
        }
        operation["responses"]["403"] = {
            "description": "Sesión/CSRF rechazados o rol insuficiente."
        }
        operation["responses"]["404"] = {
            "description": "Membresía, factura, obligación de la empresa o página no encontrada."
        }
        return
    if (path, method) == ("/api/companies/{company_id}/invoices/", "get"):
        operation["description"] = (
            "Facturas de la empresa por ID descendente, veinte por página; requiere membresía. Importes COP en cadenas decimales. can_edit indica owner/accountant. Vencimiento XML y obligación pueden faltar; pendiente/cancelación proceden de la obligación vinculada."
        )
        operation["x-contract-status"] = "invoice-fields-documented"
        operation["parameters"].append(
            {
                "name": "page",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "minimum": 1, "default": 1},
            }
        )
        link = {"type": "string", "format": "uri", "nullable": True}
        response = object_response(
            {
                "count": {"type": "integer", "minimum": 0},
                "next": link,
                "previous": link,
                "can_edit": {"type": "boolean"},
                "results": {"type": "array", "maxItems": 20, "items": invoice_response()},
            }
        )
        operation["responses"].pop("2XX")
        operation["responses"]["200"] = {
            "description": "Facturas visibles.",
            "content": {"application/json": {"schema": response}},
        }
        operation["responses"]["403"] = {"description": "Sesión no autorizada."}
        operation["responses"]["404"] = {"description": "Membresía o página no encontrada."}
        return
    if (path, method) == ("/api/companies/{company_id}/invoices/{invoice_id}/confirm/", "post"):
        operation["description"] = (
            "Confirma explícitamente una factura para crear obligación, con owner/accountant. Fecha esperada no anterior a emisión, pendiente entre cero e importe pagadero del XML. Si ya tiene obligación devuelve estado actual sin volver a validar el cuerpo ni crear otra. Audita la creación."
        )
        operation["x-contract-status"] = "invoice-fields-documented"
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": string_input(ConfirmInvoice)}},
        }
        operation["responses"].pop("2XX")
        for code, detail in {
            "200": "Factura previamente confirmada.",
            "201": "Obligación creada y factura vinculada.",
            "400": "Campos/fecha/pendiente inválidos o referencia de obligación ocupada.",
            "403": "Sesión/CSRF rechazados o rol insuficiente.",
            "404": "Membresía o factura de la empresa no encontrada.",
        }.items():
            operation["responses"][code] = {"description": detail}
            if code in ("200", "201"):
                operation["responses"][code]["content"] = {
                    "application/json": {"schema": invoice_response()}
                }
        return
    if path != "/api/companies/{company_id}/invoices/imports/":
        return
    operation["x-contract-status"] = "invoice-import-fields-documented"
    operation["responses"].pop("2XX")
    identity = {"id": {"type": "integer"}, "status": {"type": "string"}}
    if method == "get":
        operation["description"] = (
            "Últimos veinte trabajos XML de la empresa por ID descendente; requiere membresía. Sin paginación; contenido original no expuesto."
        )
        item = object_response(
            {
                **identity,
                "error": {"type": "string"},
                "invoice_id": {"type": "integer", "nullable": True},
                "duplicate": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time"},
                "finished_at": {"type": "string", "format": "date-time", "nullable": True},
            }
        )
        status, response = "200", {"type": "array", "maxItems": 20, "items": item}
    else:
        operation["description"] = (
            "Carga XML UTF-8 (BOM permitido), extensión .xml, hasta 2 MiB. Requiere owner/accountant. 202 confirma encolado, no validación UBL ni creación de obligación: consultar trabajo, revisar factura y confirmar por separado. No certifica DIAN."
        )
        operation.pop("x-request-schema-pending", None)
        operation["requestBody"] = {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": object_response(
                        {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "XML de hasta 2.097.152 bytes.",
                            }
                        }
                    )
                }
            },
        }
        status, response = "202", object_response(identity)
        operation["responses"]["400"] = {
            "description": "Archivo no seleccionado, extensión/tamaño inválidos o codificación no UTF-8."
        }
        operation["responses"]["503"] = {
            "description": "Cola no disponible; no confirma aceptación."
        }
    operation["responses"][status] = {
        "description": "Resultado de solicitud, no certificación del documento.",
        "content": {"application/json": {"schema": response}},
    }
    operation["responses"]["403"] = {"description": "Sesión/CSRF rechazados o rol insuficiente."}
    operation["responses"]["404"] = {"description": "Membresía no encontrada."}
