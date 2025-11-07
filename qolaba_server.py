#!/usr/bin/env python3
"""
Qolaba MCP Server - Model Context Protocol Server für Qolaba AI API
Unterstützt Chat, Model-Listing, Document Upload und Web-Suche
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

# Environment Variables laden
load_dotenv()

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/qolaba_mcp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Qolaba API Configuration
QOLABA_API_BASE = "https://qolaba-server-b2b.up.railway.app/api/v1/studio"
QOLABA_API_TOKEN = os.getenv("QOLABA_API_TOKEN")
QOLABA_ORG_ID = os.getenv("QOLABA_ORG_ID")

# Validierung der Credentials
if not QOLABA_API_TOKEN or not QOLABA_ORG_ID:
    logger.error("QOLABA_API_TOKEN und QOLABA_ORG_ID müssen gesetzt sein!")
    logger.info("Bitte setze die Umgebungsvariablen in der .env Datei")
    # Im Entwicklungsmodus weiterlaufen lassen
    if os.getenv("ALLOW_NO_CREDENTIALS") != "true":
        sys.exit(1)

# FastMCP Server initialisieren
mcp = FastMCP("Qolaba AI MCP Server")

# Modell-Mapping: Nutzer-freundliche Namen → Qolaba API Format
MODEL_MAPPING = {
    # Gemini
    "gemini-2.5-pro": ("GeminiAI", "gemini-2.5-pro"),
    "gemini-2.5-flash": ("GeminiAI", "gemini-2.5-flash"),
    "gemini-1.5-flash": ("GeminiAI", "gemini-2.5-flash"),  # Fallback auf 2.5
    "gemini-1.5-pro": ("GeminiAI", "gemini-2.5-pro"),      # Fallback auf 2.5

    # Claude
    "claude-3-7-sonnet-latest": ("ClaudeAI", "claude-3-7-sonnet-latest"),
    "claude-opus-4-20250514": ("ClaudeAI", "claude-opus-4-20250514"),
    "claude-sonnet-4-20250514": ("ClaudeAI", "claude-sonnet-4-20250514"),
    "claude-3-5-sonnet-20240620": ("ClaudeAI", "claude-3-7-sonnet-latest"),  # Fallback
    "claude-3-opus-20240229": ("ClaudeAI", "claude-opus-4-20250514"),       # Fallback

    # OpenAI
    "gpt-4.1-mini-2025-04-14": ("OpenAI", "gpt-4.1-mini-2025-04-14"),
    "gpt-4o-mini": ("OpenAI", "gpt-4o-mini"),
    "gpt-4.1-2025-04-14": ("OpenAI", "gpt-4.1-2025-04-14"),
    "gpt-4o": ("OpenAI", "gpt-4.1-2025-04-14"),  # Fallback
    "o3-mini": ("OpenAI", "o3-mini"),
    "o1": ("OpenAI", "o1"),
    "o3": ("OpenAI", "o3"),

    # OpenRouter
    "grok-3-beta": ("OpenRouterAI", "x-ai/grok-3-beta"),
    "grok-3-mini-beta": ("OpenRouterAI", "x-ai/grok-3-mini-beta"),
    "sonar-pro": ("OpenRouterAI", "perplexity/sonar-pro"),
    "deepseek-chat": ("OpenRouterAI", "deepseek/deepseek-chat"),
    "deepseek-r1": ("OpenRouterAI", "deepseek/deepseek-r1"),
}


def parse_model(model_input: str) -> tuple[str, str]:
    """
    Konvertiert Modellnamen in Qolaba API Format (llm, llm_model).

    Args:
        model_input: Modellname vom User (z.B. "gemini-2.5-flash" oder "claude-3-7-sonnet-latest")

    Returns:
        Tuple (llm, llm_model) für Qolaba API
    """
    model_lower = model_input.lower().strip()

    if model_lower in MODEL_MAPPING:
        return MODEL_MAPPING[model_lower]

    # Auto-Detect basierend auf Prefix
    if "gemini" in model_lower:
        return ("GeminiAI", "gemini-2.5-flash")  # Default
    elif "claude" in model_lower:
        return ("ClaudeAI", "claude-3-7-sonnet-latest")  # Default
    elif "gpt" in model_lower or "o3" in model_lower or "o1" in model_lower:
        return ("OpenAI", "gpt-4o-mini")  # Default
    elif "grok" in model_lower or "deepseek" in model_lower or "sonar" in model_lower:
        return ("OpenRouterAI", model_input)
    else:
        # Fallback: Gemini
        logger.warning(f"Unbekanntes Modell '{model_input}', nutze gemini-2.5-flash")
        return ("GeminiAI", "gemini-2.5-flash")


# HTTP Client für API Requests
async def get_http_client() -> httpx.AsyncClient:
    """Erstellt einen konfigurierten HTTP Client für Qolaba API"""
    return httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {QOLABA_API_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=httpx.Timeout(60.0)
    )


@mcp.tool()
async def qolaba_chat(
    prompt: str,
    model: str = "gemini-2.5-flash",
    internet_search: bool = False,
    code_execution: bool = False,
    rag: bool = False,
    temperature: float = 0.7
) -> str:
    """
    Chattet mit einem AI-Modell über die Qolaba API.

    Args:
        prompt: Die Nachricht/Frage an das Modell
        model: Das zu verwendende Modell (gemini-2.5-flash, claude-3-7-sonnet-latest, gpt-4o-mini, etc.)
        internet_search: Aktiviert Web-Suche für aktuelle Informationen
        code_execution: Erlaubt dem Modell Python-Code auszuführen
        rag: Aktiviert Retrieval Augmented Generation (nutzt Vector Store)
        temperature: Kreativität (0.0-1.0)

    Returns:
        Die Antwort des AI-Modells
    """
    # Modell-Mapping
    llm, llm_model = parse_model(model)
    logger.info(f"Chat Request - LLM: {llm}, Model: {llm_model}, Internet: {internet_search}, Code: {code_execution}, RAG: {rag}")

    try:
        async with await get_http_client() as client:
            # Qolaba API Request Format (basierend auf offiziellem Beispielcode)
            payload = {
                "llm": llm,
                "llm_model": llm_model,
                "history": [
                    {
                        "role": "user",
                        "content": {
                            "text": prompt,
                            "image_data": []
                        }
                    }
                ],
                "temperature": temperature,
                "image_analyze": False,
                "enable_tool": internet_search or code_execution or rag,
                "system_msg": "You are a helpful AI assistant.",
                "tools": {
                    "tool_list": {
                        "internet_search": internet_search,
                        "python_code_execution_tool": code_execution,
                        "search_doc": rag,
                        "image_generation": False,
                        "image_generation1": False,
                        "image_editing": False,
                        "csv_analysis": False
                    },
                    "number_of_context": 3,
                    "pdf_references": [] if not rag else [""],
                    "embedding_model": ["text-embedding-3-large"] if rag else [],
                    "image_generation_parameters": {}
                },
                "token": QOLABA_API_TOKEN,
                "orgID": QOLABA_ORG_ID,
                "function_call_list": [],
                "systemId": "",
                "last_user_query": prompt
            }

            logger.debug(f"Request Payload: {json.dumps(payload, indent=2)}")

            # POST Request
            response = await client.post(
                f"{QOLABA_API_BASE}/chat",
                json=payload
            )
            response.raise_for_status()

            # Qolaba gibt Streaming Response zurück
            result = response.json()
            logger.info(f"Chat Response received - Status: {response.status_code}")

            # Antwort extrahieren
            if "output" in result and result["output"]:
                answer = result["output"]

                # Token-Metadaten wenn vorhanden
                metadata = []
                if result.get("promptTokens"):
                    metadata.append(f"Prompt Tokens: {result['promptTokens']}")
                if result.get("completionTokens"):
                    metadata.append(f"Completion Tokens: {result['completionTokens']}")

                if metadata:
                    answer += f"\n\n[{', '.join(metadata)}]"

                return answer
            else:
                # Fallback: Gesamte Response zurückgeben
                logger.warning(f"Unexpected response format: {result}")
                return str(result)

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        return f"Fehler bei der API-Anfrage: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Fehler: {error_msg}"


@mcp.tool()
async def qolaba_list_models() -> str:
    """
    Listet alle verfügbaren AI-Modelle in Qolaba auf.

    Returns:
        Liste der verfügbaren Modelle mit Details
    """
    logger.info("Listing available models")

    # Aktuelle Modelle laut Qolaba API Dokumentation (Stand: 2025)
    models = {
        "🌟 Google Gemini (GeminiAI)": [
            "gemini-2.5-pro - Leistungsstark für komplexe Tasks",
            "gemini-2.5-flash - Schnell und kosteneffizient (Standard)"
        ],
        "🧠 Anthropic Claude (ClaudeAI)": [
            "claude-3-7-sonnet-latest - Neueste Sonnet Version (Empfohlen)",
            "claude-opus-4-20250514 - Höchste Qualität",
            "claude-sonnet-4-20250514 - Balance aus Qualität und Geschwindigkeit"
        ],
        "🤖 OpenAI GPT": [
            "gpt-4.1-2025-04-14 - Neuestes GPT-4.1 Modell",
            "gpt-4.1-mini-2025-04-14 - GPT-4.1 Mini",
            "gpt-4o-mini - Schnell und günstig",
            "o3-mini - Reasoning Model (Mini)",
            "o1 - Advanced Reasoning",
            "o3 - Latest Reasoning Model"
        ],
        "🚀 OpenRouter (Spezialmodelle)": [
            "x-ai/grok-3-beta - xAI Grok 3",
            "x-ai/grok-3-mini-beta - xAI Grok 3 Mini",
            "perplexity/sonar-pro - Perplexity Suche",
            "perplexity/sonar-reasoning-pro - Reasoning + Suche",
            "perplexity/sonar-deep-research - Deep Research",
            "deepseek/deepseek-chat - DeepSeek Chat",
            "deepseek/deepseek-r1 - DeepSeek Reasoning"
        ]
    }

    output = ["📋 Verfügbare Modelle in Qolaba AI (2025)\n"]

    for provider, model_list in models.items():
        output.append(f"\n{provider}:")
        for model in model_list:
            output.append(f"  • {model}")

    output.append("\n\n💡 Empfehlungen:")
    output.append("  🎯 Allgemein: gemini-2.5-flash (schnell, günstig)")
    output.append("  🧠 Qualität: claude-3-7-sonnet-latest (beste Balance)")
    output.append("  🚀 Leistung: claude-opus-4-20250514 (höchste Qualität)")
    output.append("  🔬 Reasoning: deepseek-r1 oder o3 (logisches Denken)")
    output.append("  🔍 Recherche: perplexity/sonar-pro (mit Web-Suche)")

    output.append("\n\n🛠️ Features:")
    output.append("  • internet_search=true → Web-Recherche aktivieren")
    output.append("  • code_execution=true → Python Code ausführen")
    output.append("  • rag=true → Dokumente aus Vector Store nutzen")

    return "\n".join(output)


@mcp.tool()
async def qolaba_upload_document(
    file_path: str,
    document_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Lädt ein Dokument in den Qolaba Vector Store für RAG (Retrieval Augmented Generation).

    Args:
        file_path: Pfad zur Datei (PDF, CSV, TXT, DOC, DOCX)
        document_name: Optionaler Name für das Dokument
        metadata: Zusätzliche Metadaten als Dictionary

    Returns:
        Bestätigung des Uploads mit Document ID
    """
    logger.info(f"Document Upload Request - File: {file_path}")

    if not os.path.exists(file_path):
        return f"Fehler: Datei nicht gefunden: {file_path}"

    # Dateiformat validieren
    valid_extensions = ['.pdf', '.csv', '.txt', '.doc', '.docx']
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in valid_extensions:
        return f"Fehler: Ungültiges Dateiformat {file_ext}. Erlaubt: {', '.join(valid_extensions)}"

    try:
        async with await get_http_client() as client:
            # Datei lesen
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Multipart Form Data
            files = {
                'file': (os.path.basename(file_path), file_content)
            }

            data = {}
            if document_name:
                data['name'] = document_name
            if metadata:
                data['metadata'] = json.dumps(metadata)

            # NOTE: Der genaue Endpoint kann von der Qolaba API Dokumentation abweichen
            # Dies ist basierend auf der Vector Store API
            response = await client.post(
                f"{QOLABA_API_BASE}/documents/upload",
                files=files,
                data=data
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Document uploaded successfully: {result.get('id', 'N/A')}")

            return f"Dokument erfolgreich hochgeladen!\n" \
                   f"ID: {result.get('id', 'N/A')}\n" \
                   f"Name: {result.get('name', os.path.basename(file_path))}\n" \
                   f"Status: {result.get('status', 'processing')}\n\n" \
                   f"Das Dokument kann nun mit RAG=true in Chat-Anfragen verwendet werden."

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
        logger.error(error_msg)
        return f"Fehler beim Upload: {error_msg}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"Fehler: {error_msg}"


@mcp.tool()
async def qolaba_search(
    query: str,
    model: str = "gemini-1.5-flash",
    max_results: int = 5
) -> str:
    """
    Führt eine Web-Suche über Qolaba durch und fasst die Ergebnisse mit AI zusammen.

    Args:
        query: Die Suchanfrage
        model: Das Modell für die Zusammenfassung
        max_results: Anzahl der Suchergebnisse

    Returns:
        Zusammengefasste Suchergebnisse
    """
    logger.info(f"Web Search Request - Query: {query}")

    # Web-Suche durch Chat mit internet_search=True
    search_prompt = f"Bitte suche im Internet nach folgender Anfrage und fasse die Ergebnisse zusammen:\n\n{query}"

    result = await qolaba_chat(
        prompt=search_prompt,
        model=model,
        internet_search=True,
        temperature=0.3  # Niedrigere Temperatur für faktische Suche
    )

    return f"Web-Suchergebnisse für: '{query}'\n\n{result}"


# Health Check HTTP Server (läuft parallel zum MCP Server)
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Einfacher HTTP Handler für Health Checks"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            health_data = {
                "status": "healthy",
                "service": "qolaba-mcp-server",
                "timestamp": datetime.utcnow().isoformat(),
                "credentials_configured": bool(QOLABA_API_TOKEN and QOLABA_ORG_ID)
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Disable default logging to avoid clutter"""
        pass


def start_health_check_server(port: int = 8001):
    """Startet den Health Check HTTP Server in einem separaten Thread"""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health Check Server läuft auf Port {port}")
    server.serve_forever()


def main():
    """Hauptfunktion - Startet den MCP Server"""
    parser = argparse.ArgumentParser(description="Qolaba MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.getenv("MCP_TRANSPORT", "http"),
        help="Transport Modus: stdio für lokale Nutzung, http für Remote"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 8000)),
        help="Port für HTTP Transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host für HTTP Transport (default: 0.0.0.0)"
    )

    args = parser.parse_args()

    logger.info(f"Starting Qolaba MCP Server in {args.transport} mode")
    logger.info(f"API Token configured: {bool(QOLABA_API_TOKEN)}")
    logger.info(f"Organization ID configured: {bool(QOLABA_ORG_ID)}")

    if args.transport == "stdio":
        # STDIO Transport für lokale Claude Desktop Integration
        logger.info("Using STDIO transport")
        mcp.run(transport="stdio")
    else:
        # HTTP Transport mit SSE für Remote-Zugriff
        logger.info(f"Using HTTP transport on {args.host}:{args.port}")

        # Health Check Server in separatem Thread starten (auf Port 8001)
        health_thread = threading.Thread(
            target=start_health_check_server,
            args=(8001,),
            daemon=True
        )
        health_thread.start()

        # MCP Server starten (Blocking)
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port
        )


if __name__ == "__main__":
    main()
