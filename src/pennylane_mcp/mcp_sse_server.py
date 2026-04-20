"""MCP SSE Server for remote access (Dust compatible)."""
import os
import json
import asyncio
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from .client import PennylaneClient
from .tools import invoices, customers, quotes, transactions, accounting, suppliers, journals, attachments
from .all_tools_definition import ALL_TOOLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser le client Pennylane
api_key = os.getenv("PENNYLANE_API_KEY")
base_url = os.getenv("PENNYLANE_BASE_URL", "https://app.pennylane.com/api/external/v2")

if not api_key:
    raise ValueError("PENNYLANE_API_KEY environment variable is required")

pennylane_client = PennylaneClient(api_key=api_key, base_url=base_url)


@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "Pennylane MCP SSE Server",
        "protocol": "mcp/sse",
        "version": "1.0.0"
    }


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol."""
    
    async def event_stream():
        """Generate SSE events for MCP protocol."""
        try:
            # Get the base URL from request (use https for Railway)
            base_url = str(request.base_url).rstrip('/').replace('http://', 'https://')
            endpoint_url = f"{base_url}/message"
            
            # Send endpoint event - just the URL string
            yield f"event: endpoint\n"
            yield f"data: {endpoint_url}\n\n"
            
            logger.info(f"SSE connection established, endpoint: {endpoint_url}")
            
            # Keep connection alive with heartbeat
            while True:
                if await request.is_disconnected():
                    logger.info("Client disconnected from SSE")
                    break
                await asyncio.sleep(30)
                yield f": heartbeat\n\n"
                
        except Exception as e:
            logger.error(f"SSE error: {e}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/")
async def handle_message_root(request: Request):
    """Handle MCP Streamable HTTP transport at root."""
    return await handle_message(request)
    
@app.post("/message")
async def handle_message(request: Request):
    """Handle MCP JSON-RPC messages."""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        msg_id = body.get("id")
        
        logger.info(f"Received MCP message: {method} (id: {msg_id})")
        logger.debug(f"Full request body: {body}")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "pennylane-mcp",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": ALL_TOOLS
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result_text = await call_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


async def call_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool and return result as JSON string."""
    try:
        # FACTURES CLIENTS
        if name == "pennylane_list_customer_invoices":
            result = await invoices.list_customer_invoices(pennylane_client, **arguments)
        elif name == "pennylane_get_customer_invoice":
            result = await invoices.get_customer_invoice(pennylane_client, arguments["invoice_id"])
        elif name == "pennylane_create_customer_invoice":
            result = await invoices.create_customer_invoice(pennylane_client, **arguments)
        
        # CLIENTS
        elif name == "pennylane_list_customers":
            result = await customers.list_customers(pennylane_client, limit=arguments.get("limit", 20))
        elif name == "pennylane_get_customer":
            result = await customers.get_customer(pennylane_client, arguments["customer_id"])
        elif name == "pennylane_create_customer":
            result = await customers.create_customer(pennylane_client, **arguments)
        
        # DEVIS
        elif name == "pennylane_list_quotes":
            result = await quotes.list_quotes(pennylane_client, limit=arguments.get("limit", 30))
        elif name == "pennylane_get_quote":
            result = await quotes.get_quote(pennylane_client, arguments["quote_id"])
        elif name == "pennylane_create_quote":
            result = await quotes.create_quote(pennylane_client, **arguments)
        elif name == "pennylane_update_quote":
            result = await quotes.update_quote(pennylane_client, **arguments)
        elif name == "pennylane_update_quote_status":
            result = await quotes.update_quote_status(pennylane_client, arguments["quote_id"], arguments["status"])
        
        # TRANSACTIONS
        elif name == "pennylane_list_transactions":
            result = await transactions.list_transactions(pennylane_client, limit=arguments.get("limit", 20))
        elif name == "pennylane_create_transaction":
            result = await transactions.create_transaction(pennylane_client, **arguments)
        
        # COMPTABILITÉ
        elif name == "pennylane_list_bank_accounts":
            result = await accounting.list_bank_accounts(pennylane_client)
        
        # FOURNISSEURS
        elif name == "pennylane_list_suppliers":
            result = await suppliers.list_suppliers(pennylane_client, limit=arguments.get("limit", 20))
        elif name == "pennylane_create_supplier":
            result = await suppliers.create_supplier(pennylane_client, **arguments)
        
        # JOURNAUX COMPTABLES
        elif name == "pennylane_list_journals":
            result = await journals.list_journals(pennylane_client, **arguments)
        elif name == "pennylane_get_journal":
            result = await journals.get_journal(pennylane_client, arguments["journal_id"])
        elif name == "pennylane_create_journal":
            result = await journals.create_journal(pennylane_client, arguments["code"], arguments["label"])
        
        # COMPTES GÉNÉRAUX
        elif name == "pennylane_list_ledger_accounts":
            result = await journals.list_ledger_accounts(pennylane_client, **arguments)
        elif name == "pennylane_get_ledger_account":
            result = await journals.get_ledger_account(pennylane_client, arguments["account_id"])
        elif name == "pennylane_create_ledger_account":
            result = await journals.create_ledger_account(pennylane_client, **arguments)
        
        # ÉCRITURES COMPTABLES
        elif name == "pennylane_list_ledger_entries":
            result = await journals.list_ledger_entries(pennylane_client, **arguments)
        elif name == "pennylane_list_ledger_entry_lines":
            result = await journals.list_ledger_entry_lines(pennylane_client, arguments["ledger_entry_id"], 
                                                           limit=arguments.get("limit", 20), 
                                                           page=arguments.get("page", 1))
        elif name == "pennylane_create_ledger_entry":
            result = await journals.create_ledger_entry(pennylane_client, **arguments)
        elif name == "pennylane_update_ledger_entry":
            result = await journals.update_ledger_entry(pennylane_client, **arguments)
        
        # LIGNES D'ÉCRITURE
        elif name == "pennylane_list_all_ledger_entry_lines":
            result = await journals.list_all_ledger_entry_lines(pennylane_client, **arguments)
        elif name == "pennylane_get_ledger_entry_line":
            result = await journals.get_ledger_entry_line(pennylane_client, arguments["line_id"])
        elif name == "pennylane_list_lettered_ledger_entry_lines":
            result = await journals.list_lettered_ledger_entry_lines(pennylane_client, arguments["line_id"],
                                                                     limit=arguments.get("limit", 20),
                                                                     page=arguments.get("page", 1))
        elif name == "pennylane_list_ledger_entry_line_categories":
            result = await journals.list_ledger_entry_line_categories(pennylane_client, arguments["line_id"],
                                                                      limit=arguments.get("limit", 20),
                                                                      page=arguments.get("page", 1))
        elif name == "pennylane_link_categories_to_ledger_entry_line":
            result = await journals.link_categories_to_ledger_entry_line(pennylane_client, arguments["line_id"], arguments["categories"])
        elif name == "pennylane_letter_ledger_entry_lines":
            result = await journals.letter_ledger_entry_lines(pennylane_client, arguments["ledger_entry_lines"],
                                                             arguments.get("unbalanced_lettering_strategy", "none"))
        elif name == "pennylane_unletter_ledger_entry_lines":
            result = await journals.unletter_ledger_entry_lines(pennylane_client, arguments["ledger_entry_lines"],
                                                               arguments.get("unbalanced_lettering_strategy", "none"))
        
        # BALANCE ET EXERCICES FISCAUX
        elif name == "pennylane_get_trial_balance":
            result = await journals.get_trial_balance(pennylane_client, **arguments)
        elif name == "pennylane_list_fiscal_years":
            result = await journals.list_fiscal_years(pennylane_client, 
                                                     limit=arguments.get("limit", 20),
                                                     page=arguments.get("page", 1))
        
        elif name == "pennylane_upload_file_attachment":
            result = await attachments.upload_file_attachment(pennylane_client, **arguments)

        elif name == "pennylane_import_customer_invoice":
            result = await invoices.import_customer_invoice(pennylane_client, **arguments)

        elif name == "pennylane_import_supplier_invoice":
            result = await suppliers.import_supplier_invoice(pennylane_client, **arguments)

        elif name == "pennylane_create_invoice_from_quote":
            result = await quotes.create_invoice_from_quote(pennylane_client, **arguments)
        
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
        
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


@app.on_event("shutdown")
async def shutdown():
    """Cleanup."""
    await pennylane_client.close()
