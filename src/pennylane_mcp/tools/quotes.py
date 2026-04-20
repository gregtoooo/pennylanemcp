"""Outils pour la gestion des devis."""
from typing import Any
from ..client import PennylaneClient


async def list_quotes(
    client: PennylaneClient,
    limit: int = 30,
    cursor: str | None = None,
    filter_query: str | None = None,
    sort: str = "-id"
) -> dict[str, Any]:
    """Liste les devis."""
    params = {"limit": limit, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    if filter_query:
        params["filter"] = filter_query
    
    return await client.get("quotes", params)


async def get_quote(client: PennylaneClient, quote_id: int) -> dict[str, Any]:
    """Récupère les détails d'un devis."""
    return await client.get(f"quotes/{quote_id}")


async def list_quote_invoice_line_sections(
    client: PennylaneClient,
    quote_id: int,
    limit: int = 100,
    cursor: str | None = None,
    sort: str = "-id"
) -> dict[str, Any]:
    """Liste les sections de lignes d'un devis."""
    params = {"limit": limit, "sort": sort}
    if cursor:
        params["cursor"] = cursor
    
    return await client.get(f"quotes/{quote_id}/invoice_line_sections", params)


async def list_quote_appendices(
    client: PennylaneClient,
    quote_id: int,
    limit: int = 20,
    cursor: str | None = None
) -> dict[str, Any]:
    """Liste les annexes (fichiers joints) d'un devis."""
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    
    return await client.get(f"quotes/{quote_id}/appendices", params)


async def create_quote(
    client: PennylaneClient,
    customer_id: int,
    invoice_lines: list[dict[str, Any]],
    date: str,
    deadline: str,
    currency: str = "EUR",
    language: str = "fr_FR",
    **kwargs
) -> dict[str, Any]:
    """
    Crée un devis.
    
    Args:
        customer_id: ID du client
        invoice_lines: Lignes du devis
        date: Date du devis (YYYY-MM-DD)
        deadline: Date limite (YYYY-MM-DD)
        currency: Devise (EUR, USD, etc.)
        language: Langue (fr_FR, en_GB, de_DE)
        **kwargs: Autres paramètres (discount, invoice_line_sections, quote_template_id, etc.)
    """
    data = {
        "customer_id": customer_id,
        "invoice_lines": invoice_lines,
        "date": date,
        "deadline": deadline,
        "currency": currency,
        "language": language,
        **kwargs
    }
    return await client.post("quotes", data)


async def update_quote(
    client: PennylaneClient,
    quote_id: int,
    **kwargs
) -> dict[str, Any]:
    """
    Met à jour un devis.
    
    Args:
        quote_id: ID du devis
        **kwargs: Champs à mettre à jour (customer_id, deadline, invoice_lines, etc.)
    """
    return await client.put(f"quotes/{quote_id}", kwargs)


async def update_quote_status(
    client: PennylaneClient,
    quote_id: int,
    status: str
) -> dict[str, Any]:
    """
    Met à jour le statut d'un devis.
    
    Args:
        quote_id: ID du devis
        status: Nouveau statut (pending, accepted, denied, invoiced, expired)
    """
    return await client.put(f"quotes/{quote_id}/update_status", {"status": status})


async def add_quote_appendix(
    client: PennylaneClient,
    quote_id: int,
    file_path: str,
    file_name: str
) -> dict[str, Any]:
    """
    Ajoute un fichier en annexe à un devis.
    
    Args:
        quote_id: ID du devis
        file_path: Chemin du fichier à uploader
        file_name: Nom du fichier
    """
    # Note: Cette fonction nécessite une implémentation spéciale pour l'upload de fichiers
    # Pour l'instant, on retourne une erreur explicite
    raise NotImplementedError(
        "L'upload de fichiers nécessite une implémentation spéciale avec multipart/form-data. "
        "Cette fonctionnalité sera ajoutée dans une version future."
    )
async def create_invoice_from_quote(
    client: PennylaneClient,
    quote_id: int,
    draft: bool = True,
    external_reference: str | None = None,
    customer_invoice_template_id: int | None = None,
) -> dict[str, Any]:
    """
    Crée une facture client à partir d'un devis existant.
    La facture hérite de toutes les données du devis (client, lignes, montants, etc.).
    """
    data: dict[str, Any] = {
        "quote_id": quote_id,
        "draft": draft,
    }
    if external_reference:
        data["external_reference"] = external_reference
    if customer_invoice_template_id:
        data["customer_invoice_template_id"] = customer_invoice_template_id

    return await client.post_with_params(
        "customer_invoices/create_from_quote",
        data,
        params={"use_2026_api_changes": "true"},
    )