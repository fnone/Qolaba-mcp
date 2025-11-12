#!/bin/bash
# MCP SSE Bridge für Claude CLI
# Verbindet zu Remote Qolaba MCP Server über Python Bridge

# Pfad zum Script-Verzeichnis
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Aktiviere Python venv falls vorhanden
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Führe Python Bridge aus
exec python3 "$SCRIPT_DIR/mcp_sse_bridge.py" "http://192.168.188.62:8004/sse"
