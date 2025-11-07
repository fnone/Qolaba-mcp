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
from typing import Optional, List, Dict, Any
from datetime import datetime

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
QOLABA_API_BASE = "https://api.qolaba.ai/v1"
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

# HTTP Client für API Requests
async def get_http_client() -> httpx.AsyncClient:
    """Erstellt einen konfigurierten HTTP Client für Qolaba API"""
    return httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {QOLABA_API_TOKEN}",
            "Content-Type": "application/json",
            "X-Organization-ID": QOLABA_ORG_ID
        },
        timeout=httpx.Timeout(60.0)
    )


@mcp.tool()
async def qolaba_chat(
    prompt: str,
    model: str = "gemini-1.5-flash",
    internet_search: bool = False,
    code_execution: bool = False,
    rag: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> str:
    """
    Chattet mit einem AI-Modell über die Qolaba API.

    Args:
        prompt: Die Nachricht/Frage an das Modell
        model: Das zu verwendende Modell (gemini-1.5-flash, claude-3-5-sonnet-20240620, gpt-4o, etc.)
        internet_search: Aktiviert Web-Suche für aktuelle Informationen
        code_execution: Erlaubt dem Modell Code auszuführen
        rag: Aktiviert Retrieval Augmented Generation (nutzt Vector Store)
        temperature: Kreativität (0.0-1.0)
        max_tokens: Maximale Antwortlänge

    Returns:
        Die Antwort des AI-Modells
    """
    logger.info(f"Chat Request - Model: {model}, Internet: {internet_search}, RAG: {rag}")

    try:
        async with await get_http_client() as client:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "internet_search": internet_search,
                "code_execution": code_execution,
                "rag": rag
            }

            logger.debug(f"Request Payload: {json.dumps(payload, indent=2)}")

            response = await client.post(
                f"{QOLABA_API_BASE}/chat",
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Chat Response received - Status: {response.status_code}")

            # Antwort extrahieren
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]

                # Zusätzliche Metadaten wenn vorhanden
                metadata = []
                if result.get("usage"):
                    usage = result["usage"]
                    metadata.append(f"Tokens: {usage.get('total_tokens', 'N/A')}")

                if internet_search and result.get("search_results"):
                    metadata.append(f"Suchquellen: {len(result['search_results'])}")

                if metadata:
                    answer += f"\n\n[Metadata: {', '.join(metadata)}]"

                return answer
            else:
                return f"Keine Antwort erhalten. Response: {json.dumps(result)}"

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

    # Bekannte Modelle basierend auf Qolaba Dokumentation
    # Da die API keinen /models Endpoint hat, geben wir die dokumentierten zurück
    models = {
        "Google Gemini": [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ],
        "Anthropic Claude": [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        "OpenAI GPT": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "Other": [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant"
        ]
    }

    output = ["Verfügbare Modelle in Qolaba AI:\n"]

    for provider, model_list in models.items():
        output.append(f"\n{provider}:")
        for model in model_list:
            output.append(f"  • {model}")

    output.append("\n\nEmpfohlene Modelle:")
    output.append("  • gemini-1.5-flash: Schnell und günstig für einfache Tasks")
    output.append("  • claude-3-5-sonnet-20240620: Beste Balance aus Qualität und Geschwindigkeit")
    output.append("  • gpt-4o: Sehr leistungsfähig für komplexe Aufgaben")

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


# Health Check Endpoint für Docker
@mcp.route("/health")
async def health_check():
    """Health Check Endpoint für Docker und Monitoring"""
    return {
        "status": "healthy",
        "service": "qolaba-mcp-server",
        "timestamp": datetime.utcnow().isoformat(),
        "credentials_configured": bool(QOLABA_API_TOKEN and QOLABA_ORG_ID)
    }


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
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port
        )


if __name__ == "__main__":
    main()
