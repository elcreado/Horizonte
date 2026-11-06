"""Comprobación Django únicamente contra una restauración en localhost.

Recibe configuración por stdin; no imprime credenciales ni cuerpos de respuestas.
"""

import json
import os
import sys
from pathlib import Path


def check(config):
    if config["host"] != "127.0.0.1" or config["user"] != "restore_check":
        raise ValueError("Solo se permite la instancia temporal local.")
    os.environ.update(
        DJANGO_SETTINGS_MODULE="config.settings",
        DJANGO_DEBUG="1",
        DJANGO_ALLOWED_HOSTS="testserver,127.0.0.1,localhost",
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_PORT=str(config["port"]),
        POSTGRES_USER="restore_check",
        POSTGRES_PASSWORD=config["password"],
        POSTGRES_DB="postgres",
        POSTGRES_SCHEMA=config["schema"],
        POSTGRES_SSLMODE="disable",
        EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend",
        BACKGROUND_MODE="database",
    )
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
    import django

    django.setup()
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.test import Client

    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise RuntimeError("Migraciones pendientes en la copia restaurada.")
    credentials = json.loads(Path(config["qa_account"]).read_text(encoding="utf-8"))
    client = Client(enforce_csrf_checks=True)
    statuses = {}

    def expect(path, expected=200):
        response = client.get(path)
        statuses[path] = response.status_code
        if response.status_code != expected:
            raise RuntimeError("Consulta funcional no aprobada.")
        return response

    expect("/api/auth/me/", 403)
    token = expect("/api/auth/csrf/").json()["csrfToken"]
    response = client.post(
        "/api/auth/login/",
        {"username": credentials["username"], "password": credentials["password"]},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    if response.status_code != 200:
        raise RuntimeError("La cuenta QA no pudo iniciar sesión en la copia.")
    expect("/api/auth/me/")
    companies = expect("/api/companies/").json()
    company = credentials["company_id"]
    if company not in {row["id"] for row in companies}:
        raise RuntimeError("La empresa QA no está restaurada.")
    for suffix in ("accounts/", "movements/", "history/", "invoices/", "obligations/"):
        expect(f"/api/companies/{company}/{suffix}")
    for horizon in (30, 60, 90):
        expect(f"/api/companies/{company}/dashboard/?horizon={horizon}")
    token = expect("/api/auth/csrf/").json()["csrfToken"]
    logout = client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token)
    if logout.status_code != 204:
        raise RuntimeError("Cierre de sesión no aprobado.")
    expect("/api/auth/me/", 403)
    connection.close()
    return {
        "migrations_current": True,
        "login_logout_verified": True,
        "financial_queries_verified": True,
        "endpoint_statuses": statuses,
        "notice": "Client Django local, sin navegador; no valida interfaz Electron ni correos.",
    }


if __name__ == "__main__":
    try:
        print(json.dumps(check(json.load(sys.stdin))))
    except Exception:
        raise SystemExit("Comprobación funcional no aprobada; datos privados omitidos.") from None
