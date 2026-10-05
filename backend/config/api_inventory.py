"""Inventario OpenAPI de rutas; esquemas detallados requieren contratos explícitos."""

import re

from django.conf import settings
from django.urls import get_resolver
from rest_framework.permissions import AllowAny

from .alert_history_contract import apply_alert_history_contract
from .audit_contract import apply_audit_contract
from .auth_contracts import apply_auth_contract
from .banking_contracts import apply_banking_contract
from .calendar_contract import apply_calendar_contract
from .connection_contracts import apply_connection_contract
from .dashboard_contract import apply_dashboard_contract
from .experimental_forecast_contract import apply_experimental_forecast_contract
from .forecast_runs_contract import apply_forecast_runs_contract
from .history_contract import apply_history_contract
from .invoice_contracts import apply_invoice_contract
from .merchant_contracts import apply_merchant_contract
from .movement_contracts import apply_movement_contract
from .obligation_contract import apply_obligation_contract
from .platform_contracts import apply_platform_contract
from .team_contracts import apply_team_contract
from .threshold_contract import apply_threshold_contract


def build_inventory() -> dict:
    paths = {}
    for route in get_resolver().url_patterns:
        raw = str(route.pattern)
        if not raw.startswith("api/"):
            continue
        callback = route.callback
        view = getattr(callback, "cls", None)
        if view is None:
            # Endpoints Django públicos actuales: health y csrf, ambos require_GET.
            if raw not in ("api/health/", "api/auth/csrf/"):
                raise ValueError("Endpoint Django sin contrato de métodos en el inventario.")
            methods, public = ["get"], True
        else:
            methods = [
                method for method in view.http_method_names if method not in ("options", "head")
            ]
            public = AllowAny in view.permission_classes
        parameters = []
        for converter, name in re.findall(r"<([^:>]+):([^>]+)>", raw):
            parameters.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer" if converter == "int" else "string"},
                }
            )
        path = "/" + re.sub(r"<[^:>]+:([^>]+)>", r"{\1}", raw)
        operations = {}
        name = view.__name__ if view else callback.__name__
        for method in sorted(methods):
            operation = {
                "operationId": f"{name}_{method}",
                "summary": name,
                "security": [] if public else [{"sessionCookie": []}],
                "parameters": list(parameters),
                "responses": {
                    "2XX": {
                        "description": "Operación aceptada; contrato de cuerpo pendiente de documentación detallada."
                    },
                    "default": {
                        "description": "Error de validación, permiso, disponibilidad u otro fallo; ver contrato del endpoint."
                    },
                },
                "x-contract-status": "route-inventory-only",
                "description": "Inventario de método/ruta y autenticación. No representa esquema completo de entrada o salida.",
            }
            if method in ("post", "put", "patch", "delete"):
                operation["parameters"].append(
                    {
                        "name": "X-CSRFToken",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Token obtenido de /api/auth/csrf/; requiere cookie CSRF y Origin válido.",
                    }
                )
                operation["x-request-schema-pending"] = True
            apply_auth_contract(path, method, operation)
            apply_banking_contract(path, method, operation)
            apply_merchant_contract(path, method, operation)
            apply_movement_contract(path, method, operation)
            apply_platform_contract(path, method, operation)
            apply_invoice_contract(path, method, operation)
            apply_threshold_contract(path, method, operation)
            apply_connection_contract(path, method, operation)
            apply_history_contract(path, method, operation)
            apply_team_contract(path, method, operation)
            apply_audit_contract(path, method, operation)
            apply_alert_history_contract(path, method, operation)
            apply_calendar_contract(path, method, operation)
            apply_dashboard_contract(path, method, operation)
            apply_experimental_forecast_contract(path, method, operation)
            apply_obligation_contract(path, method, operation)
            apply_forecast_runs_contract(path, method, operation)
            operations[method] = operation
        paths[path] = operations
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Horizonte API — inventario parcial",
            "version": "0.1.0",
            "description": "Generado de Django. Esquemas detallados pendientes; no usar para generar clientes completos.",
        },
        "servers": [
            {
                "url": "/",
                "description": "Mismo origen que la aplicación web o el servicio alojado.",
            }
        ],
        "paths": dict(sorted(paths.items())),
        "components": {
            "securitySchemes": {
                "sessionCookie": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": settings.SESSION_COOKIE_NAME,
                    "description": "Sesión Django HttpOnly, establecida por login/registro.",
                }
            }
        },
    }
