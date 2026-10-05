"""Comprueba los datos PostgreSQL locales sin imprimir credenciales ni conectarse."""

import argparse
from pathlib import Path

from hosted_backup import connection_environment, read_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", type=Path, default=Path(".env.hosted"))
    arguments = parser.parse_args()
    if not arguments.env.is_file():
        print("Falta el archivo de configuración. Crea .env.hosted según docs/HOSTING_FREE.md.")
        return 1
    try:
        values = read_environment(arguments.env)
        required = (
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        )
        missing = [key for key in required if not values.get(key)]
        if missing:
            print("Variables pendientes: " + ", ".join(missing))
            print(
                "Obtén estos datos en Supabase → Connect → Session pooler; las claves API no los sustituyen."
            )
            return 1
        connection_environment(values)
    except (ValueError, OSError) as error:
        # Los errores de validación definidos por connection_environment no incluyen valores.
        print(
            str(error)
            if isinstance(error, ValueError)
            else "No se pudo leer el archivo de configuración."
        )
        return 1
    print(
        "Configuración PostgreSQL válida. No se ha probado conectividad, permisos ni migraciones."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
