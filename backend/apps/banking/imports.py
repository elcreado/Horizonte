import csv
import io
import re
from datetime import date
from decimal import Decimal


def parse_csv(content: str) -> list[dict]:
    """Contrato CSV explícito: COP, montos firmados y un ID estable por cuenta."""
    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")), strict=True)
    expected = ["external_id", "date", "amount", "description"]
    if reader.fieldnames != expected:
        raise ValueError("Encabezados requeridos: external_id,date,amount,description")
    rows = []
    seen = {}
    try:
        for line, raw in enumerate(reader, start=2):
            if len(rows) >= 10000:
                raise ValueError("Máximo 10.000 movimientos por archivo.")
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"Fila {line}: número de columnas incorrecto.")
            item = {key: value.strip() for key, value in raw.items()}
            if not item["external_id"] or len(item["external_id"]) > 120:
                raise ValueError(f"Fila {line}: ID requerido, máximo 120 caracteres.")
            if not item["description"] or len(item["description"]) > 250:
                raise ValueError(f"Fila {line}: descripción requerida, máximo 250 caracteres.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["date"]):
                raise ValueError(f"Fila {line}: fecha debe ser AAAA-MM-DD.")
            try:
                date.fromisoformat(item["date"])
            except ValueError:
                raise ValueError(f"Fila {line}: fecha inválida.") from None
            if not re.fullmatch(r"-?\d{1,16}(\.\d{1,2})?", item["amount"]):
                raise ValueError(
                    f"Fila {line}: monto decimal sin separadores de miles, máximo dos decimales."
                )
            item["amount"] = str(Decimal(item["amount"]).quantize(Decimal("0.01")))
            if item["external_id"] in seen and seen[item["external_id"]] != item:
                raise ValueError(f"Fila {line}: ID repetido con datos distintos.")
            seen[item["external_id"]] = item
            rows.append(item)
    except csv.Error:
        raise ValueError("CSV mal formado.") from None
    if not rows:
        raise ValueError("El archivo no contiene movimientos.")
    return rows
