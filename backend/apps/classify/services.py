import re
import unicodedata
from decimal import Decimal

from .models import ClassificationRule

INCOME = ["Ventas", "Servicios", "Financiación", "Otros"]
EXPENSE = [
    "Nómina",
    "Proveedores",
    "Arriendo",
    "Servicios públicos",
    "Impuestos",
    "Software",
    "Transporte",
    "Marketing",
    "Deuda",
    "Inventario",
    "Otros",
]


def normalize(description: str) -> str:
    """Normaliza acentos/case/espacios; conserva referencias numéricas para evitar falsas coincidencias."""
    text = "".join(
        c for c in unicodedata.normalize("NFKD", description) if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"\w+", text.upper()))


def categories(amount: Decimal) -> list[str]:
    return INCOME if amount > 0 else EXPENSE if amount < 0 else ["Otros"]


def classify(company_id: int, description: str, amount: Decimal) -> tuple[str, str]:
    if not amount:
        return "Otros", "unclassified"
    direction = "in" if amount > 0 else "out"
    normalized = normalize(description)
    remembered = ClassificationRule.objects.filter(
        company_id=company_id,
        normalized_description=normalized,
        direction=direction,
    ).first()
    if remembered and remembered.category in categories(amount):
        return remembered.category, "company_rule"
    tokens = set(normalized.split())
    rules = (
        [("Ventas", {"VENTA", "VENTAS"})]
        if amount > 0
        else [
            ("Nómina", {"NOMINA"}),
            ("Arriendo", {"ARRIENDO", "ALQUILER"}),
            ("Software", {"ADOBE", "MICROSOFT", "GITHUB"}),
            ("Servicios públicos", {"CENS", "ACUEDUCTO"}),
            ("Impuestos", {"DIAN", "IMPUESTO", "IMPUESTOS"}),
            ("Proveedores", {"PROVEEDOR", "PROVEEDORES", "INSUMOS"}),
        ]
    )
    matches = {category for category, keywords in rules if tokens & keywords}
    return (matches.pop(), "rule") if len(matches) == 1 else ("Otros", "unclassified")
