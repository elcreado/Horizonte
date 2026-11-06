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


def classify(
    company_id: int, description: str, amount: Decimal, remembered_rules: dict | None = None
) -> tuple[str, str]:
    if not amount:
        return "Otros", "unclassified"
    direction = "in" if amount > 0 else "out"
    normalized = normalize(description)
    if remembered_rules is None:
        remembered = ClassificationRule.objects.filter(
            company_id=company_id, normalized_description=normalized, direction=direction
        ).first()
        category = remembered.category if remembered else None
    else:
        category = remembered_rules.get((normalized, direction))
    if category in categories(amount):
        return category, "company_rule"
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


def suggest_category(company_id: int, movement) -> dict:
    from apps.banking.models import Transaction

    from .tfidf import fit_tfidf

    if movement.account.company_id != company_id or not movement.amount:
        raise ValueError("Movimiento fuera de la empresa o sin dirección financiera.")
    query = Transaction.objects.filter(
        account__company_id=company_id, classification_source="manual"
    )
    query = query.filter(amount__gt=0) if movement.amount > 0 else query.filter(amount__lt=0)
    target = normalize(movement.description)
    examples = []
    for row in query.exclude(pk=movement.pk).order_by("-id")[:1000]:
        text = normalize(row.description)
        if (
            text != target
            and row.category in categories(movement.amount)
            and row.category != "Otros"
        ):
            examples.append((text, row.category))
    return fit_tfidf(examples).suggest(target)
