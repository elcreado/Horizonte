"""Respaldo del esquema de aplicación con clientes PostgreSQL nativos, sin Docker."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def connection_environment(values: dict) -> tuple[dict, str]:
    required = ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    if any(not values.get(key) for key in required):
        raise ValueError("Faltan variables de conexión PostgreSQL.")
    schema = values.get("POSTGRES_SCHEMA", "horizonte")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise ValueError("Esquema inválido.")
    ssl = values.get("POSTGRES_SSLMODE", "require")
    if ssl not in ("require", "verify-ca", "verify-full"):
        raise ValueError("El respaldo alojado requiere SSL.")
    port = values.get("POSTGRES_PORT", "5432")
    if not re.fullmatch(r"[0-9]{1,5}", port) or not 1 <= int(port) <= 65535:
        raise ValueError("Puerto PostgreSQL inválido.")
    # libpq interpreta un dbname con '=' o URI como otra configuración de conexión.
    if "=" in values["POSTGRES_DB"] or "://" in values["POSTGRES_DB"]:
        raise ValueError("POSTGRES_DB debe contener solo el nombre de la base de datos.")
    # No heredar servicios, hostaddr, opciones o certificados de otra conexión libpq.
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("PG")
    }
    environment.update(
        PGHOST=values["POSTGRES_HOST"],
        PGDATABASE=values["POSTGRES_DB"],
        PGUSER=values["POSTGRES_USER"],
        PGPASSWORD=values["POSTGRES_PASSWORD"],
        PGPORT=port,
        PGSSLMODE=ssl,
        PGCONNECT_TIMEOUT="10",
    )
    if values.get("POSTGRES_SSLROOTCERT"):
        environment["PGSSLROOTCERT"] = values["POSTGRES_SSLROOTCERT"]
    return environment, schema


def read_environment(path: Path | None) -> dict:
    values = os.environ.copy()
    if path:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not separator:
                raise ValueError("Archivo de variables mal formado.")
            if key.startswith("POSTGRES_"):
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]
                values[key] = value
    return values


def run_tool(arguments: list[str], environment: dict):
    completed = subprocess.run(
        arguments,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
        check=False,
    )
    if completed.returncode:
        # stderr puede contener credenciales, host o información privada: no publicarlo.
        raise RuntimeError(
            "Falló la herramienta PostgreSQL; revisa conexión, permisos y versión del cliente."
        )


def backup(values: dict, output: Path, bin_directory: Path | None = None) -> dict:
    environment, schema = connection_environment(values)
    tools = {}
    for name in ("pg_dump", "pg_restore"):
        candidate = (
            str(bin_directory / (name + (".exe" if sys.platform == "win32" else "")))
            if bin_directory
            else name
        )
        tools[name] = shutil.which(candidate)
        if not tools[name]:
            raise RuntimeError(
                "Instala clientes PostgreSQL compatibles y configura --pg-bin o PATH."
            )
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = output / f"horizonte-{stamp}-{uuid.uuid4().hex[:8]}.dump"
    partial = archive.with_suffix(".partial")
    try:
        run_tool(
            [
                tools["pg_dump"],
                "--no-password",
                "--format=custom",
                "--no-owner",
                "--no-acl",
                "--strict-names",
                f"--schema={schema}",
                "--lock-wait-timeout=10000",
                f"--file={partial}",
            ],
            environment,
        )
        if partial.stat().st_size < 100:
            raise RuntimeError("Respaldo vacío o incompleto.")
        run_tool([tools["pg_restore"], "--list", str(partial)], environment)
        digest = hashlib.sha256()
        with partial.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        partial.replace(archive)
        result = {
            "archive": str(archive),
            "schema": schema,
            "bytes": archive.stat().st_size,
            "sha256": digest.hexdigest(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "archive_list_verified": True,
            "restore_verified": False,
            "encrypted": False,
        }
        archive.with_suffix(".json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        return result
    finally:
        partial.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--pg-bin", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent.parent / ".local-backups"
    )
    options = parser.parse_args()
    try:
        result = backup(read_environment(options.env_file), options.output, options.pg_bin)
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print(
            "Respaldo no verificado. Revisa variables, SSL, clientes PostgreSQL y permisos; no se imprimen secretos.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
