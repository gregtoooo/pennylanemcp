"""Outils pour l'upload de fichiers (pièces jointes PDF)."""

import base64
import httpx
from typing import Any
from ..client import PennylaneClient


async def upload_file_attachment(
    client: PennylaneClient,
    filename: str = "invoice.pdf",
    file_url: str | None = None,
    file_base64: str | None = None,
) -> dict[str, Any]:
    """
    Upload un PDF vers Pennylane.
    Fournir soit file_url (URL publique) soit file_base64 (contenu encodé en base64).
    Retourne un dict avec 'id' (file_attachment_id) à utiliser dans les endpoints d'import.
    """
    if file_url:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.get(file_url)
            response.raise_for_status()
            file_content = response.content
            if filename == "invoice.pdf":
                url_filename = file_url.split("/")[-1].split("?")[0]
                if url_filename and url_filename.endswith(".pdf"):
                    filename = url_filename
    elif file_base64:
        file_content = base64.b64decode(file_base64)
    else:
        raise ValueError("Fournir soit file_url soit file_base64.")

    return await client.upload_file(file_content, filename)