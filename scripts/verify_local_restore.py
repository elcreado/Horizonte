"""Restaura una copia en un clúster temporal local; nunca conecta con el servidor alojado."""

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg


def verify(archive: Path, pg_bin: Path, qa_account: Path | None = None) -> dict:
    archive = archive.resolve(strict=True)
    root = Path(__file__).resolve().parent.parent / ".local-backups"
    if not archive.is_relative_to(root.resolve()):
        raise ValueError("La copia debe estar en .local-backups.")
    manifest = json.loads(archive.with_suffix(".json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != manifest["sha256"]:
        raise ValueError("Checksum de copia distinto del manifiesto.")
    environment = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
    password = secrets.token_urlsafe(32)
    environment["PGPASSWORD"] = password
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    work = Path(tempfile.mkdtemp(prefix="restore-check-", dir=root))
    data = work / "cluster"
    password_file = work / "init-password"
    password_file.write_text(password, encoding="utf-8")

    def run(name, *arguments):
        result = subprocess.run(
            [str(pg_bin / (name + ".exe")), *map(str, arguments)],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            # No imprimir diagnósticos que puedan contener datos de la copia.
            raise RuntimeError(f"Falló {name}; código {result.returncode}.")

    started = False
    try:
        run(
            "initdb",
            "-D",
            data,
            "-U",
            "restore_check",
            "--auth=scram-sha-256",
            "--pwfile",
            password_file,
            "--encoding=UTF8",
            "--no-locale",
        )
        password_file.unlink()
        run(
            "pg_ctl",
            "-D",
            data,
            "-l",
            work / "server.log",
            "-o",
            f"-h 127.0.0.1 -p {port}",
            "-w",
            "start",
        )
        started = True
        run(
            "pg_restore",
            "--exit-on-error",
            "--single-transaction",
            "--no-owner",
            "--no-acl",
            "-h",
            "127.0.0.1",
            "-p",
            port,
            "-U",
            "restore_check",
            "-d",
            "postgres",
            archive,
        )
        with psycopg.connect(
            host="127.0.0.1",
            port=port,
            user="restore_check",
            password=password,
            dbname="postgres",
            sslmode="disable",
        ) as connection:
            with connection.cursor() as cursor:
                schema = manifest["schema"]
                cursor.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename",
                    (schema,),
                )
                tables = [row[0] for row in cursor.fetchall()]
                counts = {}
                for table in tables:
                    cursor.execute(
                        psycopg.sql.SQL("SELECT count(*) FROM {}.{}").format(
                            psycopg.sql.Identifier(schema), psycopg.sql.Identifier(table)
                        )
                    )
                    counts[table] = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname=%s AND NOT c.convalidated",
                    (schema,),
                )
                unvalidated = cursor.fetchone()[0]
                if not tables or unvalidated:
                    raise RuntimeError("Restauración sin tablas o con restricciones no validadas.")
        report = {
            "archive_sha256": digest,
            "schema": schema,
            "restore_completed": True,
            "table_counts": counts,
            "unvalidated_constraints": unvalidated,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "notice": "Restauración estructural local; no demuestra recorrido funcional ni respaldo automático.",
        }
        if qa_account:
            child_environment = {
                k: v
                for k, v in os.environ.items()
                if not k.upper().startswith(
                    ("PG", "POSTGRES", "DJANGO", "EMAIL", "RESEND", "CELERY")
                )
            }
            functional = subprocess.run(
                [sys.executable, str(Path(__file__).with_name("restore_functional_check.py"))],
                input=json.dumps(
                    {
                        "host": "127.0.0.1",
                        "port": port,
                        "user": "restore_check",
                        "password": password,
                        "schema": schema,
                        "qa_account": str(qa_account.resolve(strict=True)),
                    }
                ),
                env=child_environment,
                text=True,
                capture_output=True,
                timeout=60,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if functional.returncode:
                raise RuntimeError("Recorrido funcional no aprobado.")
            report["functional"] = json.loads(functional.stdout)
            report["notice"] = (
                "Restauración y recorrido Client Django locales verificados; "
                "no demuestra interfaz Electron, correo ni respaldo automático."
            )
        archive.with_suffix(".restore.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report
    finally:
        password_file.unlink(missing_ok=True)
        if started or (data / "postmaster.pid").exists():
            run("pg_ctl", "-D", data, "-m", "fast", "-w", "stop")
        # Se conserva el clúster apagado dentro del directorio autorizado, sin borrados recursivos.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--pg-bin", required=True, type=Path)
    parser.add_argument(
        "--qa-account", type=Path, help="Cuenta QA local privada para comprobar Django."
    )
    options = parser.parse_args()
    try:
        result = verify(options.archive, options.pg_bin, options.qa_account)
        print(
            json.dumps(
                {
                    "restore_completed": result["restore_completed"],
                    "tables": len(result["table_counts"]),
                    "unvalidated_constraints": result["unvalidated_constraints"],
                    "functional_verified": bool(result.get("functional")),
                }
            )
        )
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, psycopg.Error):
        raise SystemExit(
            "Restauración no verificada; diagnósticos privados no publicados."
        ) from None
