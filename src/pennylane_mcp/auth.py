"""
Authentification et sécurité du serveur MCP.
Utilise un Bearer Token avec comparaison en temps constant
pour éviter les attaques par timing.
"""
import os
import secrets
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

_AUTH_TOKEN: str | None = None


def load_auth_token() -> str:
    """Charge le token d'auth depuis l'environnement (une seule fois)."""
    global _AUTH_TOKEN
    if _AUTH_TOKEN is None:
        token = os.getenv("MCP_AUTH_TOKEN", "").strip()
        if not token or len(token) < 32:
            raise ValueError(
                "MCP_AUTH_TOKEN est requis et doit faire au moins 32 caractères. "
                "Génère-le avec : python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        _AUTH_TOKEN = token
    return _AUTH_TOKEN


async def require_auth(request: Request) -> None:
    """
    Dépendance FastAPI : vérifie le Bearer Token sur chaque requête protégée.
    Lève une HTTPException 401 si le token est absent ou invalide.
    """
    try:
        expected_token = load_auth_token()
    except ValueError as e:
        logger.critical(str(e))
        raise HTTPException(status_code=500, detail="Server misconfiguration")

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        _log_unauthorized(request, "Authorization header manquant ou mal formé")
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provided_token = auth_header[7:]  # Enlève "Bearer "

    # Comparaison en temps constant — évite les timing attacks
    if not secrets.compare_digest(
        provided_token.encode("utf-8"),
        expected_token.encode("utf-8"),
    ):
        _log_unauthorized(request, "Token invalide")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _log_unauthorized(request: Request, reason: str) -> None:
    """Log une tentative d'accès non autorisée sans exposer le token."""
    client_ip = request.client.host if request.client else "unknown"
    # Ne jamais logger les headers Authorization complets
    logger.warning(
        f"Unauthorized access | IP: {client_ip} | "
        f"Path: {request.url.path} | Reason: {reason}"
    )


def sanitize_arguments(arguments: dict) -> dict:
    """
    Nettoie les arguments avant de les logger.
    Masque les champs potentiellement sensibles.
    """
    SENSITIVE_KEYS = {
        "api_key", "token", "password", "secret", "iban",
        "bic", "bank_account", "siret", "siren",
    }
    return {
        k: ("***" if k.lower() in SENSITIVE_KEYS else "[provided]")
        for k in arguments.keys()
    }
