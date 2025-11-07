# Qolaba MCP Server 🚀

Ein containerisierter **Model Context Protocol (MCP) Server** für die [Qolaba AI API](https://qolaba.ai). Ermöglicht die Integration von Qolaba's AI-Funktionen in Claude Desktop und andere MCP-kompatible Clients.

## ✨ Features

- 🤖 **Multi-Model Support**: Zugriff auf Gemini, Claude, GPT und weitere Modelle
- 🌐 **Internet-Suche**: Web-Recherche direkt aus Claude heraus
- 📚 **RAG (Retrieval Augmented Generation)**: Dokument-Upload und intelligente Suche
- 💻 **Code-Ausführung**: Modelle können Code direkt ausführen
- 🐳 **Docker-Ready**: Vollständig containerisiert mit Health Checks
- 🔒 **Sicher**: Non-root User, Resource Limits, Environment-basierte Secrets
- 📊 **Logging**: Automatische Log-Rotation und Monitoring

## 📋 Voraussetzungen

- Docker und Docker Compose installiert
- Qolaba AI Account mit API-Zugang ([Registrierung](https://qolaba.ai))
- Für lokale Nutzung: Claude Desktop ([Download](https://claude.ai/download))

## 🚀 Schnellstart

### 1. Repository klonen

```bash
git clone https://github.com/YOUR_USERNAME/qolaba-mcp-server.git
cd qolaba-mcp-server
```

### 2. Umgebungsvariablen konfigurieren

Erstelle eine `.env` Datei aus der Vorlage:

```bash
cp .env.example .env
```

Öffne `.env` und trage deine Credentials ein:

```env
QOLABA_API_TOKEN=dein_api_token_hier
QOLABA_ORG_ID=deine_organization_id_hier
```

> 💡 **Credentials erhalten**: Gehe zu [https://qolaba.ai/dashboard](https://qolaba.ai/dashboard) und erstelle einen API-Token.

### 3. Container starten

```bash
docker-compose up -d
```

### 4. Status überprüfen

```bash
# Container-Logs anzeigen
docker-compose logs -f

# Container Health Status prüfen
docker ps | grep qolaba-mcp-server

# Detaillierter Health Check Status
docker inspect --format='{{.State.Health.Status}}' qolaba-mcp-server

# MCP Server Endpoint (SSE) testen
curl http://localhost:8003/sse
```

> 💡 **Hinweis**: Der Container hat einen internen Health Check auf Port 8001, der automatisch von Docker überwacht wird. Der MCP SSE-Server läuft auf Port 8000 (extern als 8003).

## 🔧 Claude Desktop Integration

Es gibt **zwei Methoden**, um den MCP Server mit Claude Desktop zu verbinden:

### Methode 1: HTTP/SSE Transport (Empfohlen für Remote-Server)

Bearbeite `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) oder `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "qolaba": {
      "url": "http://localhost:8003/sse"
    }
  }
}
```

Für Remote-Server ersetze `localhost` mit der IP deines Servers.

### Methode 2: Docker Exec + STDIO Transport (Für lokale Installation)

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

Nach der Konfiguration **Claude Desktop neu starten**.

## 🛠️ Verfügbare Tools

Der MCP Server stellt folgende Tools bereit:

### 1. `qolaba_chat`
Chattet mit verschiedenen AI-Modellen.

**Parameter:**
- `prompt` (string): Deine Nachricht/Frage
- `model` (string, optional): Modell-ID (Standard: `gemini-1.5-flash`)
- `internet_search` (bool, optional): Aktiviert Web-Suche (Standard: `false`)
- `code_execution` (bool, optional): Erlaubt Code-Ausführung (Standard: `false`)
- `rag` (bool, optional): Nutzt hochgeladene Dokumente (Standard: `false`)
- `temperature` (float, optional): Kreativität 0.0-1.0 (Standard: `0.7`)
- `max_tokens` (int, optional): Max. Antwortlänge (Standard: `2048`)

**Beispiel:**
```
Verwende qolaba_chat mit dem Prompt "Was ist Quantencomputing?" und aktiviere internet_search
```

### 2. `qolaba_list_models`
Listet alle verfügbaren Modelle auf.

**Beispiel:**
```
Zeige mir alle verfügbaren Qolaba Modelle
```

### 3. `qolaba_upload_document`
Lädt ein Dokument in den Vector Store für RAG.

**Parameter:**
- `file_path` (string): Pfad zur Datei
- `document_name` (string, optional): Name für das Dokument
- `metadata` (dict, optional): Zusätzliche Metadaten

**Unterstützte Formate:** PDF, CSV, TXT, DOC, DOCX

**Beispiel:**
```
Lade das Dokument /path/to/document.pdf in Qolaba hoch
```

### 4. `qolaba_search`
Führt eine Web-Suche mit AI-Zusammenfassung durch.

**Parameter:**
- `query` (string): Suchanfrage
- `model` (string, optional): Modell für Zusammenfassung
- `max_results` (int, optional): Anzahl Ergebnisse (Standard: `5`)

**Beispiel:**
```
Suche im Internet nach "neueste KI Entwicklungen 2024"
```

## 📦 Portainer Deployment auf NAS

### Für Anfänger: Schritt-für-Schritt Anleitung

#### Schritt 1: Portainer öffnen

1. Öffne deinen Browser
2. Gehe zu deiner Portainer-URL (z.B. `http://192.168.1.100:9000`)
3. Logge dich ein

#### Schritt 2: Stack erstellen

1. Klicke links im Menü auf **"Stacks"**
2. Klicke oben rechts auf **"+ Add stack"**
3. Gebe dem Stack einen Namen: `qolaba-mcp`

#### Schritt 3: Docker Compose einfügen

1. Wähle **"Web editor"**
2. Kopiere den kompletten Inhalt aus `docker-compose.yml` in das Textfeld
3. Scrolle nach unten zu **"Environment variables"**

#### Schritt 4: Umgebungsvariablen setzen

Klicke auf **"+ Add environment variable"** und füge hinzu:

| Name | Value |
|------|-------|
| `QOLABA_API_TOKEN` | `dein_api_token_hier` |
| `QOLABA_ORG_ID` | `deine_organization_id_hier` |

> ⚠️ **Wichtig**: Ersetze die Werte mit deinen echten Credentials von [qolaba.ai/dashboard](https://qolaba.ai/dashboard)

#### Schritt 5: Stack deployen

1. Scrolle nach unten
2. Klicke auf **"Deploy the stack"**
3. Warte, bis der Status "running" anzeigt (ca. 30-60 Sekunden)

#### Schritt 6: Überprüfen

1. Klicke auf den Stack-Namen `qolaba-mcp`
2. Du solltest einen Container namens `qolaba-mcp-server` mit Status **"running"** sehen
3. Klicke auf den Container
4. Klicke auf **"Logs"** um die Ausgaben zu sehen

#### Schritt 7: Testen

1. In Portainer, schaue nach dem Container-Status. Es sollte **"healthy"** neben dem grünen Symbol stehen.

2. Klicke auf den Container, dann auf **"Logs"**. Du solltest sehen:
   ```
   Starting Qolaba MCP Server in http mode
   Health Check Server läuft auf Port 8001
   Using HTTP transport on 0.0.0.0:8000
   ```

3. Teste den MCP SSE Endpoint im Browser oder Terminal:
   ```bash
   curl http://DEINE_NAS_IP:8003/sse
   ```

✅ Wenn der Container Status "healthy" ist und die Logs keine Fehler zeigen, funktioniert alles!

### Alternative: Repository-basiertes Deployment

Wenn dein NAS direkten Git-Zugriff hat:

1. In Portainer: **Stacks** → **+ Add stack**
2. Wähle **"Repository"**
3. Trage ein:
   - **Repository URL**: `https://github.com/YOUR_USERNAME/qolaba-mcp-server`
   - **Compose path**: `docker-compose.yml`
   - **Environment variables**: Wie oben beschrieben
4. Klicke auf **"Deploy the stack"**

## 🔍 Troubleshooting

### Container startet nicht

```bash
# Logs anzeigen
docker-compose logs qolaba-mcp

# Container Status prüfen
docker ps -a | grep qolaba
```

**Häufige Probleme:**
- ❌ **"QOLABA_API_TOKEN must be set"**: `.env` Datei fehlt oder ist leer
- ❌ **"Permission denied"**: Führe `chmod +x qolaba_server.py` aus
- ❌ **Port bereits belegt**: Ändere `8003` in `docker-compose.yml`

### API-Fehler

```bash
# Container Health Status prüfen
docker inspect --format='{{.State.Health.Status}}' qolaba-mcp-server

# Container Logs prüfen
docker-compose logs qolaba-mcp-server | tail -20
```

Wenn der Container unhealthy ist oder Credential-Fehler auftreten:
- Überprüfe die `.env` Datei (müssen QOLABA_API_TOKEN und QOLABA_ORG_ID gesetzt sein)
- Container neu starten: `docker-compose restart`
- Logs prüfen auf "credentials_configured: false"

### Claude Desktop verbindet nicht

1. **Config-Datei Pfad prüfen:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **JSON Syntax validieren:**
   ```bash
   # macOS/Linux
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

3. **Claude Desktop komplett neu starten** (nicht nur Fenster schließen)

4. **Logs prüfen:**
   ```bash
   docker-compose logs -f
   ```

### Port-Konflikte

Wenn Port 8003 bereits belegt ist:

```yaml
# In docker-compose.yml ändern
ports:
  - "8004:8000"  # Ändere 8003 zu 8004 (oder einen freien Port)
```

Container neu starten:
```bash
docker-compose down
docker-compose up -d
```

## 📊 Monitoring

### Logs anzeigen

```bash
# Alle Logs
docker-compose logs -f

# Nur letzte 50 Zeilen
docker-compose logs --tail=50 qolaba-mcp

# Log-Datei im Container
docker exec qolaba-mcp-server tail -f /app/logs/qolaba_mcp.log
```

### Resource-Nutzung

```bash
# CPU/Memory Stats
docker stats qolaba-mcp-server

# Container Infos
docker inspect qolaba-mcp-server
```

### Health Check

```bash
# Container Health Status
docker inspect --format='{{.State.Health.Status}}' qolaba-mcp-server

# Health Check Details
docker inspect --format='{{json .State.Health}}' qolaba-mcp-server | python -m json.tool

# Direkter Health Check im Container (nur intern verfügbar)
docker exec qolaba-mcp-server curl -s http://localhost:8001/health
```

## 🔒 Sicherheit

### Best Practices

✅ **Umgesetzt:**
- Container läuft als non-root User (`mcpuser`)
- Secrets über Environment Variables (nicht im Code)
- Resource Limits (max. 512MB RAM, 1 CPU)
- Health Checks für Monitoring
- Log-Rotation (max. 10MB pro Datei, 3 Dateien)
- Minimales Base Image (python:3.11-slim)

⚠️ **Zusätzlich empfohlen:**
- Reverse Proxy mit HTTPS (z.B. Traefik, Nginx)
- Firewall-Regeln für Port 8003
- Regelmäßige Updates: `docker-compose pull && docker-compose up -d`

## 🔄 Updates

### Server aktualisieren

```bash
# Code pullen
git pull origin main

# Container neu bauen und starten
docker-compose up -d --build

# Alte Images aufräumen
docker image prune -f
```

### In Portainer

1. Gehe zu **Stacks** → `qolaba-mcp`
2. Klicke auf **"Update the stack"** (wenn Repository-basiert)
3. Oder: Klicke **"Editor"**, ändere die Config, klicke **"Update the stack"**

## 📚 Weitere Ressourcen

- [Qolaba AI Dokumentation](https://docs.qolaba.ai)
- [Model Context Protocol Spezifikation](https://modelcontextprotocol.io)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Claude Desktop](https://claude.ai/download)

## 🤝 Support

Bei Problemen:

1. Überprüfe die [Troubleshooting](#-troubleshooting) Sektion
2. Prüfe die Logs: `docker-compose logs`
3. Erstelle ein Issue auf GitHub mit:
   - Fehlerbeschreibung
   - Logs (ohne Credentials!)
   - System-Infos (OS, Docker Version)

## 📝 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

---

**Erstellt mit ❤️ für die Claude & Qolaba Community**
