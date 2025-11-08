# 🚀 Gemini CLI - Qolaba MCP Server Setup

Diese Anleitung hilft dir, den Qolaba MCP Server in Gemini CLI zu integrieren.

## 📋 Voraussetzungen

- ✅ Docker und docker-compose installiert
- ✅ Qolaba MCP Server Container läuft (Port 8003)
- ✅ Node.js und npm installiert

---

## Schritt 1: Gemini CLI Installation prüfen/installieren

### 1.1 Prüfe ob Gemini CLI installiert ist

```bash
# Gemini CLI Version prüfen
gemini --version

# Wenn installiert, siehst du z.B.: "Gemini CLI v1.2.3"
```

### 1.2 Falls NICHT installiert - Installiere Gemini CLI

```bash
# Option A: NPM Global Installation (empfohlen)
npm install -g @google/gemini-cli

# Option B: Falls Permission-Fehler
sudo npm install -g @google/gemini-cli

# Prüfe Installation
gemini --version
```

### 1.3 Gemini API Key konfigurieren

Wenn du Gemini CLI noch nicht konfiguriert hast:

```bash
# Starte Gemini CLI zum ersten Mal
gemini

# Du wirst nach einem API Key gefragt
# Hole dir einen kostenlosen Key: https://aistudio.google.com/apikey

# Oder konfiguriere manuell:
gemini config set apiKey YOUR_GEMINI_API_KEY_HERE
```

---

## Schritt 2: Qolaba Container Status prüfen

### 2.1 Prüfe ob Container läuft

```bash
# Wechsle ins Projektverzeichnis
cd ~/Qolaba-mcp

# Prüfe Container Status
docker ps | grep qolaba

# Du solltest sehen:
# qolaba-mcp-server ... Up ... 0.0.0.0:8003->8003/tcp
```

### 2.2 Falls Container NICHT läuft

```bash
# Container starten
docker compose up -d

# Logs prüfen
docker compose logs -f qolaba-mcp

# CTRL+C zum Beenden
```

### 2.3 Health Check prüfen

```bash
# Health Endpoint testen
curl http://localhost:8003/health

# Erwartete Antwort: {"status": "healthy"}
```

---

## Schritt 3: Gemini CLI Settings konfigurieren

### 3.1 Settings-Verzeichnis erstellen

```bash
# Erstelle Gemini CLI Konfigurationsverzeichnis
mkdir -p ~/.gemini

# Prüfe ob es existiert
ls -la ~/.gemini
```

### 3.2 Settings.json Datei erstellen/bearbeiten

```bash
# Öffne mit deinem bevorzugten Editor
nano ~/.gemini/settings.json

# Oder mit vim
vim ~/.gemini/settings.json

# Oder mit VS Code
code ~/.gemini/settings.json
```

### 3.3 Qolaba MCP Server Konfiguration hinzufügen

**Falls die Datei LEER ist oder NICHT existiert**, füge ein:

```json
{
  "selectedAuthType": "gemini-api-key",
  "mcpServers": {
    "qolaba": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "http://localhost:8003/sse"
      ]
    }
  }
}
```

**Falls die Datei bereits EXISTIERT** und andere Einstellungen hat:

```json
{
  "selectedAuthType": "gemini-api-key",
  "theme": "Dracula",
  "preferredEditor": "vscode",
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "qolaba": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "http://localhost:8003/sse"
      ]
    }
  }
}
```

> 💡 **Wichtig**: Füge `"qolaba"` zu den existierenden `mcpServers` hinzu!

### 3.4 Datei speichern

- **nano**: CTRL+O → Enter → CTRL+X
- **vim**: ESC → `:wq` → Enter
- **VS Code**: CTRL+S

---

## Schritt 4: Gemini CLI testen

### 4.1 Gemini CLI starten

```bash
# Starte Gemini CLI
gemini

# Du solltest den Gemini CLI Prompt sehen
```

### 4.2 MCP Server Status prüfen

Innerhalb von Gemini CLI:

```
/mcp
```

**Erwartete Ausgabe:**
```
MCP Servers:
  qolaba: ✓ Connected
```

### 4.3 Verfügbare Tools anzeigen

```
/tools
```

**Erwartete Ausgabe:**
```
Available Tools:
  - qolaba_chat: Chat mit verschiedenen AI-Modellen
  - qolaba_list_models: Verfügbare Modelle auflisten
  - qolaba_upload_document: Dokument hochladen
  - qolaba_search: Dokumente durchsuchen
```

### 4.4 Qolaba testen

Schreibe im Gemini CLI Chat:

```
Nutze das qolaba_chat Tool um mir eine kurze Geschichte über einen Roboter zu schreiben. Verwende das Modell "flash".
```

**Erwartete Antwort:**
- Gemini CLI sollte das `qolaba_chat` Tool aufrufen
- Du siehst die Anfrage an Qolaba
- Du erhältst eine Geschichte zurück

---

## 🎯 Schnelltest-Checkliste

Führe diese Befehle nacheinander aus:

```bash
# 1. Container läuft?
docker ps | grep qolaba

# 2. Health Check OK?
curl http://localhost:8003/health

# 3. Gemini CLI installiert?
gemini --version

# 4. Settings.json existiert?
cat ~/.gemini/settings.json

# 5. Gemini CLI starten und testen
gemini
```

Dann in Gemini CLI:
```
/mcp
/tools
Nutze qolaba_chat um "Hallo Welt" auf Deutsch zu sagen mit Modell "flash"
```

---

## ❌ Troubleshooting

### Problem 1: "gemini: command not found"

**Lösung:**
```bash
# Prüfe npm global bin Pfad
npm config get prefix

# Sollte /usr/local oder ~/.npm-global sein
# Füge zu PATH hinzu (in ~/.bashrc oder ~/.zshrc):
export PATH="$PATH:$(npm config get prefix)/bin"

# Neu laden
source ~/.bashrc  # oder source ~/.zshrc

# Erneut prüfen
gemini --version
```

### Problem 2: MCP Server wird nicht angezeigt

**Lösung:**
```bash
# 1. Prüfe settings.json Syntax
cat ~/.gemini/settings.json | python3 -m json.tool

# Sollte ohne Fehler formatieren
# Falls Fehler: Syntax korrigieren

# 2. Prüfe Container läuft
docker ps | grep qolaba

# 3. Prüfe Port 8003
netstat -tulpn | grep 8003

# 4. Gemini CLI neu starten
# Exit mit /exit oder CTRL+D
gemini
```

### Problem 3: "qolaba: ✗ Disconnected"

**Lösung:**
```bash
# 1. Container Logs prüfen
docker compose logs -f qolaba-mcp

# 2. Container neu starten
docker compose restart qolaba-mcp

# 3. Health Check prüfen
curl http://localhost:8003/health

# 4. MCP Client Paket installieren
npx -y @modelcontextprotocol/client --version
```

### Problem 4: Tools funktionieren nicht

**Lösung:**
```bash
# 1. Prüfe .env Datei
cat ~/Qolaba-mcp/.env

# Credentials korrekt? (OHNE Prefixes!)
# QOLABA_API_TOKEN=abc123xyz  (NICHT qol_live_abc123xyz)
# QOLABA_ORG_ID=org789xyz     (NICHT org_org789xyz)

# 2. Container mit neuen ENV Variablen neu starten
cd ~/Qolaba-mcp
docker compose down
docker compose up -d

# 3. Logs prüfen
docker compose logs -f qolaba-mcp
```

### Problem 5: Permission Fehler

**Lösung:**
```bash
# Gemini Settings Verzeichnis Rechte prüfen
ls -la ~/.gemini

# Falls nötig, Rechte setzen
chmod 755 ~/.gemini
chmod 644 ~/.gemini/settings.json
```

---

## 🔄 Vergleich: Claude Desktop vs Gemini CLI

| Feature | Claude Desktop | Gemini CLI |
|---------|----------------|------------|
| **Konfig-Datei** | `~/.config/Claude/claude_desktop_config.json` | `~/.gemini/settings.json` |
| **MCP Syntax** | Identisch | Identisch |
| **Port** | 8003 | 8003 |
| **Transport** | HTTP/SSE empfohlen | HTTP/SSE empfohlen |
| **Gleichzeitig nutzbar?** | ✅ Ja | ✅ Ja |

Beide können den **gleichen** Docker Container nutzen!

---

## 📊 Nächste Schritte

Nachdem Qolaba in Gemini CLI funktioniert:

1. **Weitere Tools**: Füge andere MCP Server hinzu (z.B. GitHub, Git, Firebase)
2. **Workflows**: Kombiniere Qolaba mit anderen Tools
3. **Automatisierung**: Nutze Gemini CLI in Skripten

Beispiel für mehrere MCP Server:
```json
{
  "mcpServers": {
    "qolaba": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/client", "http://localhost:8003/sse"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

---

## 💡 Tipps

1. **Mehrere AI Models testen**: Nutze verschiedene Qolaba-Modelle
   ```
   Nutze qolaba_chat mit Modell "claude-3-5-sonnet" um...
   Nutze qolaba_chat mit Modell "gpt-4o" um...
   ```

2. **Modelle vergleichen**: Stelle die gleiche Frage an verschiedene Modelle
   ```
   Liste mir alle verfügbaren Modelle auf mit qolaba_list_models
   ```

3. **Container Status überwachen**:
   ```bash
   # Terminal 1: Logs live verfolgen
   docker compose logs -f qolaba-mcp

   # Terminal 2: Gemini CLI nutzen
   gemini
   ```

---

## 📚 Weiterführende Ressourcen

- [Gemini CLI Dokumentation](https://github.com/google-gemini/gemini-cli)
- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [Qolaba API Dokumentation](https://qolaba.ai/docs)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)

---

## ✅ Fertig!

Wenn alles funktioniert, hast du jetzt:
- ✅ Gemini CLI installiert und konfiguriert
- ✅ Qolaba MCP Server in Gemini CLI integriert
- ✅ Zugriff auf 4 Qolaba-Tools in Gemini CLI
- ✅ Multi-Client Setup (Claude Desktop + Gemini CLI)

**Viel Spaß beim Experimentieren! 🚀**
