"""Client HTTP pour l'API Pennylane."""
import httpx
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class PennylaneClient:
    """Client pour interagir avec l'API Pennylane."""
    
    def __init__(self, api_key: str, base_url: str = "https://app.pennylane.com/api/external/v2"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Effectue une requête GET."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def post(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Effectue une requête POST."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def put(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Effectue une requête PUT."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = await self.client.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def delete(self, endpoint: str) -> dict[str, Any]:
        """Effectue une requête DELETE."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = await self.client.delete(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    async def upload_file(self, file_content: bytes, filename: str) -> dict[str, Any]:
        """Upload a PDF file via multipart/form-data."""
        url = f"{self.base_url}/file_attachments"
        try:
            async with httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                timeout=60.0,
            ) as tmp_client:
                files = {"file": (filename, file_content, "application/pdf")}
                response = await tmp_client.post(url, files=files)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    async def post_with_params(self, endpoint: str, data: Optional[dict[str, Any]] = None, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Effectue une requête POST avec query params."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = await self.client.post(url, json=data, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
            
    async def close(self):
        """Ferme le client HTTP."""
        await self.client.aclose()