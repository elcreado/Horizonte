import re
from datetime import date
from decimal import Decimal

from defusedxml.ElementTree import fromstring

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}
INVOICE_TAG = "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice"
ATTACHED_TAG = "{urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2}AttachedDocument"


def parse_invoice(content: str, company_nit: str) -> dict:
    """Extrae Invoice UBL; no verifica firma digital ni validación fiscal DIAN."""
    try:
        root = fromstring(content, forbid_dtd=True, forbid_entities=True, forbid_external=True)
        if root.tag == ATTACHED_TAG:
            embedded = root.find("cac:Attachment/cac:ExternalReference/cbc:Description", NS)
            if embedded is None or not embedded.text:
                raise ValueError("El AttachedDocument no contiene la factura XML.")
            root = fromstring(
                embedded.text, forbid_dtd=True, forbid_entities=True, forbid_external=True
            )
    except Exception:
        raise ValueError(
            "XML inválido o inseguro. No se permiten DTD ni entidades externas."
        ) from None
    if root.tag != INVOICE_TAG:
        raise ValueError(
            "Se requiere una factura Invoice UBL 2.1, no una nota crédito u otro documento."
        )

    def text(path: str, required: bool = True, maximum: int = 200) -> str:
        nodes = root.findall(path, NS)
        if len(nodes) > 1:
            raise ValueError(f"Campo XML repetido: {path}.")
        value = (nodes[0].text or "").strip() if nodes else ""
        if (required and not value) or len(value) > maximum:
            raise ValueError(f"Campo XML ausente o demasiado largo: {path}.")
        return value

    def money(path: str) -> str:
        value = text(path)
        node = root.find(path, NS)
        if node.get("currencyID") != "COP" or not re.fullmatch(r"\d{1,16}(\.\d{1,2})?", value):
            raise ValueError(
                "Los montos deben ser no negativos, en COP y con máximo dos decimales."
            )
        return str(Decimal(value).quantize(Decimal("0.01")))

    def business_date(value: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Fecha XML inválida; se espera AAAA-MM-DD.")
        date.fromisoformat(value)
        return value

    if text("cbc:UBLVersionID") != "2.1" or text("cbc:DocumentCurrencyCode") != "COP":
        raise ValueError("Esta integración admite UBL 2.1 en COP.")
    supplier = text("cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID")
    customer = text("cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID")

    def normalize(value: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", value.upper())

    is_supplier, is_customer = (
        normalize(supplier) == normalize(company_nit),
        normalize(customer) == normalize(company_nit),
    )
    if is_supplier == is_customer:
        raise ValueError(
            "El NIT de la empresa debe coincidir exclusivamente con el emisor o el receptor."
        )
    issue = business_date(text("cbc:IssueDate"))
    due = text("cbc:DueDate", required=False) or text(
        "cac:PaymentMeans/cbc:PaymentDueDate", required=False
    )
    if due:
        due = business_date(due)
        if due < issue:
            raise ValueError("El vencimiento no puede ser anterior a la emisión.")
    data = {
        "number": text("cbc:ID", maximum=100),
        "cufe": text("cbc:UUID", maximum=150),
        "direction": "in" if is_supplier else "out",
        "issue_date": issue,
        "due_date": due or None,
        "supplier_nit": supplier,
        "customer_nit": customer,
        "supplier": text(
            "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:RegistrationName"
        ),
        "customer": text(
            "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:RegistrationName"
        ),
        "subtotal": money("cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount"),
        "total": money("cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"),
        "payable": money("cac:LegalMonetaryTotal/cbc:PayableAmount"),
    }
    if Decimal(data["total"]) < Decimal(data["subtotal"]):
        raise ValueError("El total no puede ser menor al subtotal.")
    data["tax"] = str(Decimal(data["total"]) - Decimal(data["subtotal"]))
    return data
