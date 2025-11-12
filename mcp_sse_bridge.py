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
    session = None
    initialized = False

    # Main loop: Forward stdio <-> SSE
    try:
        while True:
            # Lies von stdin
            loop = asyncio.get_event_loop()
            line = await loop.run_in_executor(None, sys.stdin.readline)

            if not line:
                break

            try:
                message = json.loads(line.strip())
                logger.debug(f"Received from stdin: {message}")

                method = message.get("method")
                msg_id = message.get("id")

                if method == "initialize":
                    # Jetzt erst zum SSE Server verbinden
                    logger.info(f"Connecting to SSE server: {SSE_URL}")

                    async with AsyncExitStack() as stack:
                        read_stream, write_stream = await stack.enter_async_context(
                            sse_client(SSE_URL)
                        )

                        session = await stack.enter_async_context(
                            ClientSession(read_stream, write_stream)
                        )

                        await session.initialize()
                        logger.info("Session initialized")

                        # Sende initialize response mit korrekter ID
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
                            "id": msg_id
                        }
                        print(json.dumps(init_response), flush=True)
                        initialized = True

                        # Bleibe in der Session und handle weitere Requests
                        while True:
                            line = await loop.run_in_executor(None, sys.stdin.readline)
                            if not line:
                                return

                            try:
                                message = json.loads(line.strip())
                                method = message.get("method")
                                msg_id = message.get("id")

                                if method == "tools/list":
                                    tools = await session.list_tools()
                                    response = {
                                        "jsonrpc": "2.0",
                                        "result": {"tools": [t.model_dump() for t in tools]},
                                        "id": msg_id
                                    }
                                    print(json.dumps(response), flush=True)

                                elif method == "tools/call":
                                    params = message.get("params", {})
                                    tool_name = params.get("name")
                                    arguments = params.get("arguments", {})

                                    result = await session.call_tool(tool_name, arguments)
                                    response = {
                                        "jsonrpc": "2.0",
                                        "result": {"content": result.content},
                                        "id": msg_id
                                    }
                                    print(json.dumps(response), flush=True)

                                else:
                                    error = {
                                        "jsonrpc": "2.0",
                                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                                        "id": msg_id
                                    }
                                    print(json.dumps(error), flush=True)

                            except json.JSONDecodeError:
                                pass
                            except Exception as e:
                                logger.exception("Error in inner loop")
                                error = {
                                    "jsonrpc": "2.0",
                                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                                    "id": msg_id if 'msg_id' in locals() else None
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
                logger.exception("Error in outer loop")
                error = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
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
