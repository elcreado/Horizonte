"""Carga de un corpus etiquetado con separación temporal y de grupos."""

import csv
import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path

from .evaluation import evaluate_classifier
from .services import categories


def evaluate_corpus(path: Path, company_id: str, direction: str, cutoff: date) -> dict:
    if direction not in ("in", "out") or not company_id:
        raise ValueError("Empresa y dirección in/out requeridas.")
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Corpus máximo 2 MB.")
    required = {
        "company_id",
        "direction",
        "date",
        "reviewed_on",
        "description",
        "category",
        "group_id",
    }
    training, testing = [], []
    train_groups, test_groups = set(), set()
    excluded = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or []) != required:
            raise ValueError("Columnas del corpus inválidas.")
        for index, row in enumerate(reader, start=2):
            if set(row) != required or any(value is None for value in row.values()):
                raise ValueError("Fila del corpus mal formada.")
            if index > 10001:
                raise ValueError("Corpus máximo 10.000 filas.")
            if row["company_id"] != company_id or row["direction"] != direction:
                raise ValueError("El corpus debe pertenecer a una única empresa y dirección.")
            day, reviewed = date.fromisoformat(row["date"]), date.fromisoformat(row["reviewed_on"])
            if (
                reviewed < day
                or not row["group_id"]
                or row["category"] not in categories(Decimal(1 if direction == "in" else -1))
            ):
                raise ValueError("Fecha de revisión, grupo o categoría inválidos.")
            example = (row["description"], row["category"])
            if day <= cutoff:
                if reviewed > cutoff:
                    excluded += 1
                    continue
                training.append(example)
                train_groups.add(row["group_id"])
            else:
                testing.append(example)
                test_groups.add(row["group_id"])
    if train_groups & test_groups:
        raise ValueError("Comercios/plantillas comparten grupos entre entrenamiento y prueba.")
    result = evaluate_classifier(training, testing)
    result["corpus"] = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "company_id": company_id,
        "direction": direction,
        "cutoff": cutoff.isoformat(),
        "excluded_late_labels": excluded,
        "training_groups": len(train_groups),
        "testing_groups": len(test_groups),
    }
    return result
