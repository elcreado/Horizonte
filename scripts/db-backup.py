"""Respalda PostgreSQL local y, opcionalmente, ensaya la restauración aislada.

Usa el pg_dump/pg_restore de la imagen postgres:16, sin requerir cliente local.
Nunca restaura encima de la base usada por la aplicación.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUPS = ROOT / ".local-backups"
DATABASE = "liquidity"
SERVICE = "postgres"
USER = "liquidity"


def docker(*args: str, input_file: Path | None = None, output_file: Path | None = None) -> str:
    command = ["docker", "compose", "exec", "-T", SERVICE, *args]
    with (
        input_file.open("rb") if input_file else open_null() as incoming,
        output_file.open("wb") if output_file else open_null() as outgoing,
    ):
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdin=incoming if input_file else subprocess.DEVNULL,
            stdout=outgoing if output_file else subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if completed.returncode:
        reason = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Falló {' '.join(command[:5])}: {reason}")
    return completed.stdout.decode("utf-8", errors="replace").strip() if not output_file else ""


def open_null():
    return open(Path("NUL") if sys.platform == "win32" else Path("/dev/null"), "rb")


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def restore_check(archive: Path) -> dict[str, int]:
    name = f"liquidity_restore_check_{uuid.uuid4().hex[:12]}"
    created = False
    try:
        docker("createdb", "-U", USER, name)
        created = True
        docker(
            "pg_restore",
            "-U",
            USER,
            "--no-owner",
            "--no-acl",
            "--exit-on-error",
            "--dbname",
            name,
            input_file=archive,
        )
        result = docker(
            "psql",
            "-U",
            USER,
            "-d",
            name,
            "-At",
            "-c",
            "SELECT (SELECT count(*) FROM django_migrations), "
            "(SELECT count(*) FROM accounts_company), "
            "(SELECT count(*) FROM banking_transaction);",
        )
        migrations, companies, movements = (int(value) for value in result.split("|"))
        if migrations < 1:
            raise RuntimeError("La restauración no contiene migraciones Django.")
        return {"migrations": migrations, "companies": companies, "movements": movements}
    finally:
        if created:
            if not name.startswith("liquidity_restore_check_"):
                raise RuntimeError("Nombre de base temporal inválido; no se elimina.")
            docker("dropdb", "-U", USER, name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup de la base local de Horizonte")
    parser.add_argument(
        "--restore-check", action="store_true", help="Ensaya restauración en una base temporal"
    )
    arguments = parser.parse_args()
    BACKUPS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = BACKUPS / f"liquidity-{timestamp}-{uuid.uuid4().hex[:8]}.dump"
    partial = archive.with_suffix(".partial")
    try:
        docker(
            "pg_dump",
            "-U",
            USER,
            "-d",
            DATABASE,
            "--format=custom",
            "--no-owner",
            "--no-acl",
            output_file=partial,
        )
        if partial.stat().st_size < 100:
            raise RuntimeError("El archivo de respaldo está vacío o incompleto.")
        docker("pg_restore", "--list", input_file=partial)
        partial.replace(archive)
        result = {
            "archive": str(archive),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": archive.stat().st_size,
            "sha256": checksum(archive),
            "restore_check": restore_check(archive) if arguments.restore_check else None,
        }
        archive.with_suffix(".json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, RuntimeError) as error:
        partial.unlink(missing_ok=True)
        print(f"Backup no verificado: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
