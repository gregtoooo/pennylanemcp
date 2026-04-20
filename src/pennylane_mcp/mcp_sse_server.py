"""
MCP SSE Server sécurisé — compatible Dust remote MCP.

Sécurités implémentées :
  - Authentification Bearer Token sur tous les endpoints sensibles
  - CORS restreint aux origines configurées
  - Rate limiting par IP (60 req/min)
  - Logging sanitisé (aucune donnée sensible dans les logs)
  - Masquage des détails d'erreur internes
  - Timeout sur les requêtes Pennylane
"""
import os
import json
import asyncio
import time
import logging
from collections import defaultdict
from typing import Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .client import PennylaneClient
from .tools import invoices, customers, quotes, transactions, accounting, suppliers, journals, attachments
from .all_tools_definition import ALL_TOOLS
from .auth import require_auth, sanitize_arguments

# ---------------------------------------------------------------------------
# Logging — niveau WARNING en prod pour éviter de leaker des données
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARNING),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiter simple en mémoire (par IP)
# ---------------------------------------------------------------------------
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


def check_rate_limit(client_ip: str) -> None:
    """Lève HTTPException 429 si l'IP dépasse la limite."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    requests = _rate_limit_store[client_ip]

    # Nettoyer les entrées hors fenêtre
    _rate_limit_store[client_ip] = [t for t in requests if t > window_start]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded | IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    _rate_limit_store[client_ip].append(now)


# ---------------------------------------------------------------------------
# Application FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Pennylane MCP Server",
    docs_url=None,   # Désactive Swagger UI en production
    redoc_url=None,  # Désactive ReDoc en production
    openapi_url=None,  # Désactive l'exposition du schéma OpenAPI
)

# CORS — restreint aux origines déclarées dans les variables d'env
_raw_origins = os.getenv("ALLOWED_ORIGINS", "https://dust.tt")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---------------------------------------------------------------------------
# Client Pennylane — initialisé depuis les variables d'environnement
# ---------------------------------------------------------------------------
_pennylane_api_key = os.getenv("PENNYLANE_API_KEY", "").strip()
_pennylane_base_url = os.getenv(
    "PENNYLANE_BASE_URL", "https://app.pennylane.com/api/external/v2"
)

if not _pennylane_api_key:
    raise ValueError("PENNYLANE_API_KEY est requis")

pennylane_client = PennylaneClient(
    api_key=_pennylane_api_key,
    base_url=_pennylane_base_url,
)

# ---------------------------------------------------------------------------
# Endpoints publics (pas d'auth requise)
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check public — ne révèle aucune info sensible."""
    return {"status": "ok", "service": "Pennylane MCP Server"}


@app.get("/health")
async def health():
    """Health check pour Railway."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Endpoint SSE — protégé par auth
# ---------------------------------------------------------------------------

@app.get("/sse", dependencies=[Depends(require_auth)])
async def sse_endpoint(request: Request):
    """SSE endpoint pour le protocole MCP (Dust compatible)."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    async def event_stream():
        try:
            base = str(request.base_url).rstrip("/").replace("http://", "https://")
            endpoint_url = f"{base}/message"

            yield f"event: endpoint\n"
            yield f"data: {endpoint_url}\n\n"

            logger.info(f"SSE connection established | IP: {client_ip}")

            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE disconnected | IP: {client_ip}")
                    break
                await asyncio.sleep(30)
                yield f": heartbeat\n\n"

        except Exception as e:
            logger.error(f"SSE error | IP: {client_ip} | {type(e).__name__}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Endpoint MCP principal — protégé par auth
# ---------------------------------------------------------------------------

@app.post("/message", dependencies=[Depends(require_auth)])
async def handle_message(request: Request):
    """Traite les messages JSON-RPC du protocole MCP."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    method = body.get("method")
    params = body.get("params", {})
    msg_id = body.get("id")

    # Ne logger que la méthode, jamais les params complets
    logger.info(f"MCP message | method: {method} | id: {msg_id} | IP: {client_ip}")

    if method == "initialize":
        return _build_response(msg_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pennylane-mcp", "version": "1.0.0"},
        })

    elif method == "tools/list":
        return _build_response(msg_id, {"tools": ALL_TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Log sanitisé — jamais les valeurs des arguments
        logger.info(
            f"Tool call | tool: {tool_name} | "
            f"args_keys: {list(sanitize_arguments(arguments).keys())} | IP: {client_ip}"
        )

        result_text = await _call_tool(tool_name, arguments)
        return _build_response(msg_id, {
            "content": [{"type": "text", "text": result_text}]
        })

    else:
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            },
        )


@app.post("/", dependencies=[Depends(require_auth)])
async def handle_message_root(request: Request):
    """Alias de /message pour compatibilité MCP Streamable HTTP."""
    return await handle_message(request)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_response(msg_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


async def _call_tool(name: str, arguments: dict) -> str:
    """
    Route les appels d'outils vers les handlers Pennylane.
    Les erreurs internes sont loggées mais jamais exposées en détail au client.
    """
    try:
        result = await _route_tool(name, arguments)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except ValueError as e:
        # Erreur métier (outil inconnu, argument manquant) — on peut exposer
        logger.warning(f"Tool error | tool: {name} | {e}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        # Erreur interne — on ne révèle PAS les détails
        logger.error(f"Internal tool error | tool: {name} | {type(e).__name__}", exc_info=True)
        return json.dumps({"error": "An internal error occurred. Check server logs."})


async def _route_tool(name: str, arguments: dict) -> Any:
    """Dispatch des outils MCP vers les modules métier."""

    # ── FACTURES CLIENTS ──────────────────────────────────────────────────
    if name == "pennylane_list_customer_invoices":
        return await invoices.list_customer_invoices(
            pennylane_client,
            limit=arguments.get("limit", 20),
            cursor=arguments.get("cursor"),
            filter_query=arguments.get("filter"),
            sort=arguments.get("sort", "-id"),
        )
    elif name == "pennylane_get_customer_invoice":
        return await invoices.get_customer_invoice(pennylane_client, arguments["invoice_id"])
    elif name == "pennylane_create_customer_invoice":
        return await invoices.create_customer_invoice(pennylane_client, **arguments)
    elif name == "pennylane_import_customer_invoice":
        return await invoices.import_customer_invoice(pennylane_client, **arguments)

    # ── CLIENTS ───────────────────────────────────────────────────────────
    elif name == "pennylane_list_customers":
        return await customers.list_customers(
            pennylane_client,
            limit=arguments.get("limit", 20),
            cursor=arguments.get("cursor"),
            filter_query=arguments.get("filter"),
            sort=arguments.get("sort", "-id"),
        )
    elif name == "pennylane_get_customer":
        return await customers.get_customer(pennylane_client, arguments["customer_id"])

    # ── DEVIS ─────────────────────────────────────────────────────────────
    elif name == "pennylane_list_quotes":
        return await quotes.list_quotes(
            pennylane_client,
            limit=arguments.get("limit", 30),
            cursor=arguments.get("cursor"),
            filter_query=arguments.get("filter"),
            sort=arguments.get("sort", "-id"),
        )
    elif name == "pennylane_get_quote":
        return await quotes.get_quote(pennylane_client, arguments["quote_id"])
    elif name == "pennylane_create_quote":
        return await quotes.create_quote(pennylane_client, **arguments)
    elif name == "pennylane_update_quote":
        return await quotes.update_quote(pennylane_client, **arguments)
    elif name == "pennylane_update_quote_status":
        return await quotes.update_quote_status(pennylane_client, **arguments)
    elif name == "pennylane_create_invoice_from_quote":
        return await quotes.create_invoice_from_quote(pennylane_client, **arguments)

    # ── FOURNISSEURS ──────────────────────────────────────────────────────
    elif name == "pennylane_list_suppliers":
        return await suppliers.list_suppliers(pennylane_client, **arguments)
    elif name == "pennylane_get_supplier":
        return await suppliers.get_supplier(pennylane_client, arguments["supplier_id"])
    elif name == "pennylane_import_supplier_invoice":
        return await suppliers.import_supplier_invoice(pennylane_client, **arguments)

    # ── TRANSACTIONS ──────────────────────────────────────────────────────
    elif name == "pennylane_list_transactions":
        return await transactions.list_transactions(
            pennylane_client,
            limit=arguments.get("limit", 20),
            cursor=arguments.get("cursor"),
            filter_query=arguments.get("filter"),
            sort=arguments.get("sort", "-id"),
        )

    # ── COMPTABILITÉ ──────────────────────────────────────────────────────
    elif name == "pennylane_list_bank_accounts":
        return await accounting.list_bank_accounts(pennylane_client)
    elif name == "pennylane_get_trial_balance":
        return await accounting.get_trial_balance(pennylane_client, **arguments)
    elif name == "pennylane_list_ledger_accounts":
        return await journals.list_ledger_accounts(pennylane_client, **arguments)
    elif name == "pennylane_get_ledger_account":
        return await journals.get_ledger_account(pennylane_client, arguments["account_id"])
    elif name == "pennylane_list_ledger_entries":
        return await journals.list_ledger_entries(pennylane_client, **arguments)
    elif name == "pennylane_create_ledger_entry":
        return await journals.create_ledger_entry(pennylane_client, **arguments)
    elif name == "pennylane_list_fiscal_years":
        return await journals.list_fiscal_years(
            pennylane_client,
            limit=arguments.get("limit", 20),
            page=arguments.get("page", 1),
        )

    # ── PIÈCES JOINTES ────────────────────────────────────────────────────
    elif name == "pennylane_upload_file_attachment":
        return await attachments.upload_file_attachment(pennylane_client, **arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("shutdown")
async def shutdown():
    """Ferme proprement le client HTTP Pennylane."""
    await pennylane_client.close()
    logger.info("Pennylane client closed")
