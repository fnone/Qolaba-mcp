#!/usr/bin/env python3
"""
MCP SSE-to-STDIO Bridge
Verbindet Claude CLI (stdio) mit einem Remote MCP SSE Server
Verwendet die offizielle MCP Python SDK
"""
import sys
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """
    Startet einen MCP Client, der sich mit dem Remote SSE Server verbindet
    und stdio für die Kommunikation mit Claude CLI verwendet
    """
    # Für SSE-Server verwenden wir einen HTTP-Transport
    # Dies ist ein Platzhalter - in der Praxis würde man einen SSE-Client verwenden
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-client", "http://192.168.188.62:8004/sse"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Halte die Session offen
            while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
