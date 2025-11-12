# Claude CLI Bridge für Qolaba MCP Server

## Problem

**Claude CLI** unterstützt im Gegensatz zu **Claude Desktop** und **Gemini CLI** keine direkten SSE-URLs in der MCP-Konfiguration:

- ✅ **Claude Desktop**: `"url": "http://..."`
- ✅ **Gemini CLI**: `"url": "http://..."`
- ❌ **Claude CLI**: Benötigt `command` + `args` (stdio Transport)

## Lösung: Python Bridge Script

Das `mcp_sse_bridge.py` Script fungiert als Bridge zwischen:
- **Claude CLI** (stdio Transport)
- **Remote Qolaba MCP Server** (SSE Transport)

## Installation auf macOS

### Schritt 1: Repository klonen

```bash
cd ~/
git clone https://github.com/YOUR_USERNAME/qolaba-mcp-server.git
cd qolaba-mcp-server
```

### Schritt 2: Python Virtual Environment erstellen

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r bridge_requirements.txt
```

### Schritt 3: Bridge Script testen

```bash
# Teste ob die Dependencies installiert sind
python3 mcp_sse_bridge.py http://192.168.188.62:8004/sse
```

Das Script sollte sich verbinden und auf stdin warten (Strg+C zum Beenden).

### Schritt 4: Shell Wrapper ausführbar machen

```bash
chmod +x qolaba_bridge.sh
```

### Schritt 5: Claude CLI Konfiguration anpassen

Bearbeite `~/.claude.json`:

```json
{
  "mcpServers": {
    "qolaba": {
      "command": "/Users/DEIN_USERNAME/qolaba-mcp-server/qolaba_bridge.sh"
    }
  }
}
```

**Wichtig:** Ersetze `DEIN_USERNAME` mit deinem tatsächlichen Benutzernamen oder nutze den vollen Pfad.

### Schritt 6: Testen

```bash
claude /doctor
```

Der Qolaba Server sollte nun als "connected" erscheinen.

```bash
claude /mcp
```

Zeigt die verfügbaren Tools vom Qolaba Server.

## Wie es funktioniert

```
┌─────────────┐        stdio         ┌──────────────────┐       SSE/HTTP      ┌──────────────┐
│ Claude CLI  │ ◄──────────────────► │  Bridge Script   │ ◄──────────────────► │ Qolaba MCP   │
│  (lokaler   │   JSON-RPC over      │ (mcp_sse_bridge  │  MCP over SSE       │  Server      │
│   Mac)      │   stdin/stdout       │      .py)        │                     │ (Remote NAS) │
└─────────────┘                      └──────────────────┘                     └──────────────┘
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'mcp'"

Dependencies nicht installiert:

```bash
cd ~/qolaba-mcp-server
source venv/bin/activate
pip install -r bridge_requirements.txt
```

### "Connection refused"

Server läuft nicht oder falsche IP:

```bash
# Teste Server-Erreichbarkeit
curl http://192.168.188.62:8004/sse
```

### "command not found: python3"

Python 3 nicht installiert:

```bash
brew install python3
```

## Vergleich: Claude CLI vs. andere Clients

| Client         | SSE URL Support | Config Format                    |
|----------------|-----------------|----------------------------------|
| Claude Desktop | ✅ Ja           | `"url": "http://..."`            |
| Gemini CLI     | ✅ Ja           | `"url": "http://..."`            |
| Claude CLI     | ❌ Nein         | `"command": "..."`  (Bridge nötig)|

## Alternative: Docker Exec (nur für lokale Container)

Falls der Container auf demselben Mac läuft:

```json
{
  "mcpServers": {
    "qolaba": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "qolaba-mcp-server",
        "python",
        "qolaba_server.py",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

Dies funktioniert jedoch **nicht** für Remote-Server auf einem NAS.
