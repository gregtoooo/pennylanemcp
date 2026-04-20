"""Outils pour la gestion des factures."""
from typing import Any
from ..client import PennylaneClient


async def list_customer_invoices(
    client: PennylaneClient,
    limit: int = 20,
    cursor: str | None = None,
    filter_query: str | None = None,
    sort: str = "-id"
) -> dict[str, Any]:
    """Liste les factures clients."""
    params = {"limit": limit, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    if filter_query:
        params["filter"] = filter_query
    
    return await client.get("customer_invoices", params)


async def get_customer_invoice(client: PennylaneClient, invoice_id: int) -> dict[str, Any]:
    """Récupère les détails d'une facture client."""
    return await client.get(f"customer_invoices/{invoice_id}")


async def create_customer_invoice(
    client: PennylaneClient,
    customer_id: int,
    date: str,
    deadline: str,
    invoice_lines: list[dict[str, Any]],
    draft: bool = True,
    currency: str = "EUR",
    language: str = "fr_FR",
    **kwargs
) -> dict[str, Any]:
    """
    Crée une nouvelle facture client.
    
    Args:
        customer_id: ID du client
        date: Date de la facture (YYYY-MM-DD) - OBLIGATOIRE
        deadline: Date limite de paiement (YYYY-MM-DD) - OBLIGATOIRE
        invoice_lines: Liste des lignes de facture avec structure OBLIGATOIRE:
            - label (str): Description de la ligne
            - raw_currency_unit_price (str): Prix unitaire HT (ex: "750.00")
            - quantity (number): Quantité
            - unit (str): Unité (ex: "jour", "unité", "lot")
            - vat_rate (str): Taux de TVA (ex: "FR_200" pour 20%, "FR_100" pour 10%)
            - description (str, optionnel): Description détaillée
        draft: OBLIGATOIRE - True = brouillon modifiable, False = facture finalisée
        currency: Devise (EUR, USD, etc.)
        language: Langue (fr_FR, en_GB, de_DE)
        **kwargs: Paramètres optionnels (pdf_invoice_subject, pdf_description, 
                 special_mention, external_reference, discount, etc.)
    """
    data = {
        "customer_id": customer_id,
        "date": date,
        "deadline": deadline,
        "invoice_lines": invoice_lines,
        "draft": draft,
        "currency": currency,
        "language": language,
        **kwargs
    }
    return await client.post("customer_invoices", data)


async def finalize_customer_invoice(client: PennylaneClient, invoice_id: int) -> dict[str, Any]:
    """Finalise une facture client (la rend non modifiable). Utilise PUT."""
    return await client.put(f"customer_invoices/{invoice_id}/finalize")


async def send_customer_invoice_by_email(
    client: PennylaneClient,
    invoice_id: int,
    recipients: list[str] | None = None
) -> dict[str, Any]:
    """
    Envoie une facture client par email.
    
    Args:
        invoice_id: ID de la facture
        recipients: Liste d'emails. Si vide, utilise les emails du client.
    """
    data = {"recipients": recipients or []}
    return await client.post(f"customer_invoices/{invoice_id}/send_by_email", data)


async def list_supplier_invoices(
    client: PennylaneClient,
    limit: int = 20,
    cursor: str | None = None,
    filter_query: str | None = None,
    sort: str = "-id"
) -> dict[str, Any]:
    """Liste les factures fournisseurs."""
    params = {"limit": limit, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    if filter_query:
        params["filter"] = filter_query
    
    return await client.get("supplier_invoices", params)


async def get_supplier_invoice(client: PennylaneClient, invoice_id: int) -> dict[str, Any]:
    """Récupère les détails d'une facture fournisseur."""
    return await client.get(f"supplier_invoices/{invoice_id}")


async def categorize_invoice(
    client: PennylaneClient,
    invoice_id: int,
    invoice_type: str,  # "customer" ou "supplier"
    categories: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Catégorise une facture.
    
    Args:
        invoice_id: ID de la facture
        invoice_type: Type ("customer" ou "supplier")
        categories: Liste des catégories avec structure:
            - category_id (int): ID de la catégorie
            - weight (str): Poids/proportion (ex: "1.0" pour 100%)
    """
    endpoint = f"{invoice_type}_invoices/{invoice_id}/categories"
    return await client.put(endpoint, {"categories": categories})

    async def import_customer_invoice(
    client: PennylaneClient,
    file_attachment_id: int,
    customer_id: int,
    date: str,
    deadline: str,
    currency_amount_before_tax: str,
    currency_tax: str,
    currency_amount: str,
    invoice_lines: list[dict[str, Any]],
    currency: str = "EUR",
) -> dict[str, Any]:
    """
    Importe une facture client à partir d'un PDF déjà uploadé.
    La somme des currency_amount des lignes doit égaler currency_amount total.
    """
    data = {
        "file_attachment_id": file_attachment_id,
        "customer_id": customer_id,
        "date": date,
        "deadline": deadline,
        "currency_amount_before_tax": currency_amount_before_tax,
        "currency_tax": currency_tax,
        "currency_amount": currency_amount,
        "currency": currency,
        "invoice_lines": invoice_lines,
    }
    return await client.post("customer_invoices/import", data)