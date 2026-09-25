import re
import unicodedata


def normalize_movement(description: str) -> dict[str, str]:
    """Conserva números de nombres; elimina solo referencias etiquetadas al final.

    Comercio solo se extrae de una etiqueta explícita, nunca de una categoría.
    La descripción original y el ID bancario permanecen intactos.
    """
    text = "".join(
        c for c in unicodedata.normalize("NFKD", description) if not unicodedata.combining(c)
    ).upper()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"(?:\s*[;|]\s*|\s+)(?:REF(?:ERENCIA)?|AUT(?:ORIZACION)?)[.:#\s]+[A-Z0-9-]+\s*$", "", text
    )
    match = re.search(r"(?:^|[;|])\s*(?:COMERCIO|ESTABLECIMIENTO)\s*:\s*([^;|]+)", text)
    merchant = " ".join(re.findall(r"\w+", match.group(1))) if match else ""
    return {"normalized_description": " ".join(re.findall(r"\w+", text)), "merchant_name": merchant}
