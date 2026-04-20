"""Outils pour la gestion des fournisseurs."""
from typing import Any
from ..client import PennylaneClient


async def list_suppliers(
    client: PennylaneClient,
    limit: int = 20,
    cursor: str | None = None,
    filter_query: str | None = None,
    sort: str = "-id"
) -> dict[str, Any]:
    """Liste les fournisseurs."""
    params = {"limit": limit, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    if filter_query:
        params["filter"] = filter_query
    
    return await client.get("suppliers", params)


async def get_supplier(client: PennylaneClient, supplier_id: int) -> dict[str, Any]:
    """Récupère les détails d'un fournisseur."""
    return await client.get(f"suppliers/{supplier_id}")


async def create_supplier(
    client: PennylaneClient,
    name: str,
    postal_address: dict[str, str] | None = None,
    emails: list[str] | None = None,
    iban: str | None = None,
    vat_number: str | None = None,
    reg_no: str | None = None,
    establishment_no: str | None = None,
    supplier_payment_method: str | None = None,
    supplier_due_date_delay: int | None = None,
    supplier_due_date_rule: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Crée un nouveau fournisseur.
    
    Args:
        name: Nom du fournisseur (requis)
        postal_address: Adresse postale avec:
            - address (str): Rue
            - postal_code (str): Code postal
            - city (str): Ville
            - country_alpha2 (str): Code pays (ex: "FR")
        emails: Liste d'emails
        iban: IBAN du fournisseur
        vat_number: Numéro de TVA
        reg_no: SIREN (9 chiffres, France uniquement)
        establishment_no: SIRET (14 chiffres, France uniquement)
        supplier_payment_method: Méthode de paiement
            (automatic_transfer, manual_transfer, automatic_debiting, 
             bill_of_exchange, check, cash, card)
        supplier_due_date_delay: Délai d'échéance (jours)
        supplier_due_date_rule: Règle d'échéance (days, days_or_end_of_month)
        **kwargs: Autres paramètres optionnels
    """
    data = {"name": name}
    
    if postal_address:
        data["postal_address"] = postal_address
    if emails:
        data["emails"] = emails
    if iban:
        data["iban"] = iban
    if vat_number:
        data["vat_number"] = vat_number
    if reg_no:
        data["reg_no"] = reg_no
    if establishment_no:
        data["establishment_no"] = establishment_no
    if supplier_payment_method:
        data["supplier_payment_method"] = supplier_payment_method
    if supplier_due_date_delay:
        data["supplier_due_date_delay"] = supplier_due_date_delay
    if supplier_due_date_rule:
        data["supplier_due_date_rule"] = supplier_due_date_rule
    
    data.update(kwargs)
    
    return await client.post("suppliers", data)


async def update_supplier(
    client: PennylaneClient,
    supplier_id: int,
    **kwargs
) -> dict[str, Any]:
    """
    Met à jour un fournisseur.
    
    Args:
        supplier_id: ID du fournisseur
        **kwargs: Champs à mettre à jour (name, emails, iban, etc.)
    """
    return await client.put(f"suppliers/{supplier_id}", kwargs)

async def import_supplier_invoice(
    client: PennylaneClient,
    file_attachment_id: int,
    supplier_id: int,
    date: str,
    deadline: str,
    currency_amount_before_tax: str,
    currency_tax: str,
    currency_amount: str,
    invoice_lines: list[dict[str, Any]],
    currency: str = "EUR",
) -> dict[str, Any]:
    """
    Importe une facture fournisseur à partir d'un PDF déjà uploadé.
    La somme des currency_amount des lignes doit égaler currency_amount total.
    """
    data = {
        "file_attachment_id": file_attachment_id,
        "supplier_id": supplier_id,
        "date": date,
        "deadline": deadline,
        "currency_amount_before_tax": currency_amount_before_tax,
        "currency_tax": currency_tax,
        "currency_amount": currency_amount,
        "currency": currency,
        "invoice_lines": invoice_lines,
    }
    return await client.post("supplier_invoices/import", data)    