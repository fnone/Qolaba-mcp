#!/usr/bin/env python3
"""
MCP SSE-to-STDIO Bridge
Verbindet Claude CLI (stdio) mit einem Remote MCP SSE Server über HTTP/SSE
"""
import sys
import json
import asyncio
import logging
from contextlib import AsyncExitStack

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

# Logging für Debugging (optional)
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

# SSE Server URL (wird als Argument übergeben oder hardcoded)
SSE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://192.168.188.62:8004/sse"


async def stdio_to_sse_bridge():
    """
    Bridge zwischen Claude CLI (stdio) und Remote MCP Server (SSE)

    Liest JSON-RPC von stdin, forwarded zu SSE Server, schreibt Antworten zu stdout
    """
    async with AsyncExitStack() as stack:
        # Verbinde zum SSE Server
        logger.info(f"Connecting to SSE server: {SSE_URL}")

        read_stream, write_stream = await stack.enter_async_context(
            sse_client(SSE_URL)
        )

        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # Initialize Session
        await session.initialize()
        logger.info("Session initialized")

        # Tools vom Server abrufen und zu stdout ausgeben
        tools = await session.list_tools()

        # Sende initialize response
        init_response = {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "qolaba-bridge",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        print(json.dumps(init_response), flush=True)

        # Main loop: Forward stdio <-> SSE
        try:
            while True:
                # Lies von stdin (non-blocking)
                loop = asyncio.get_event_loop()
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                try:
                    message = json.loads(line.strip())
                    logger.debug(f"Received from stdin: {message}")

                    # Handle verschiedene Message-Typen
                    method = message.get("method")

                    if method == "initialize":
                        # Already sent above
                        continue
                    elif method == "tools/list":
                        # Forward zu Server
                        tools = await session.list_tools()
                        response = {
                            "jsonrpc": "2.0",
                            "result": {"tools": [t.model_dump() for t in tools]},
                            "id": message.get("id")
                        }
                        print(json.dumps(response), flush=True)
                    elif method == "tools/call":
                        # Forward tool call
                        params = message.get("params", {})
                        tool_name = params.get("name")
                        arguments = params.get("arguments", {})

                        result = await session.call_tool(tool_name, arguments)
                        response = {
                            "jsonrpc": "2.0",
                            "result": {"content": result.content},
                            "id": message.get("id")
                        }
                        print(json.dumps(response), flush=True)
                    else:
                        # Unknown method
                        error = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32601, "message": f"Method not found: {method}"},
                            "id": message.get("id")
                        }
                        print(json.dumps(error), flush=True)

                except json.JSONDecodeError as e:
                    error = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": f"Parse error: {e}"},
                        "id": None
                    }
                    print(json.dumps(error), flush=True)
                except Exception as e:
                    logger.exception("Error processing message")
                    error = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": f"Internal error: {e}"},
                        "id": message.get("id") if 'message' in locals() else None
                    }
                    print(json.dumps(error), flush=True)

        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(stdio_to_sse_bridge())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)
