# 📝 n8n + Qolaba AI Integration Guide

Nutze die Qolaba AI API direkt in n8n, um verschiedene LLMs (Claude, Gemini, GPT) mit deinen Qolaba-Credits zu verwenden.

## 🎯 Vorteile

- ✅ **Ein Qolaba-Account** für alle Modelle (Claude, Gemini, GPT, etc.)
- ✅ **Keine separaten API-Keys** für OpenAI, Anthropic, Google nötig
- ✅ **Kostengünstig** - Nutze deine Qolaba-Credits
- ✅ **Flexibel** - Wechsel zwischen Modellen je nach Aufgabe
- ✅ **Internet-Suche & RAG** - Erweiterte Features verfügbar

---

## 🚀 Quick Start: Qolaba API in n8n

### 1. HTTP Request Node erstellen

1. In n8n → **Neuer Workflow**
2. **Füge hinzu:** HTTP Request Node
3. **Konfiguration:**

**Method:** `POST`

**URL:**
```
https://qolaba-server-b2b.up.railway.app/api/v1/studio/chat
```

**Authentication:** None (wir nutzen Token im Body)

**Send Headers:**
- Header: `Authorization`
- Value: `Bearer DEIN_QOLABA_TOKEN`
- Header: `Content-Type`
- Value: `application/json`

**Send Body:** JSON

**Body Content:**
```json
{
  "llm": "GeminiAI",
  "llm_model": "gemini-2.5-flash",
  "history": [
    {
      "role": "user",
      "content": {
        "text": "Schreibe eine kurze Geschichte über einen Roboter",
        "image_data": []
      }
    }
  ],
  "temperature": 0.7,
  "image_analyze": false,
  "enable_tool": false,
  "system_msg": "Du bist ein hilfreicher AI-Assistent.",
  "tools": {
    "tool_list": {
      "internet_search": false,
      "python_code_execution_tool": false,
      "search_doc": false,
      "image_generation": false,
      "image_generation1": false,
      "image_editing": false,
      "csv_analysis": false
    },
    "number_of_context": 3,
    "pdf_references": [],
    "embedding_model": [],
    "image_generation_parameters": {}
  },
  "token": "DEIN_QOLABA_TOKEN",
  "orgID": "DEINE_ORG_ID",
  "function_call_list": [],
  "systemId": "",
  "last_user_query": "Schreibe eine kurze Geschichte über einen Roboter"
}
```

4. **Execute Node** → Du solltest eine Antwort erhalten!

---

## 📊 Verfügbare Modelle

### Gemini (Google)
```json
"llm": "GeminiAI",
"llm_model": "gemini-2.5-flash"     // Schnell, günstig
"llm_model": "gemini-2.5-pro"       // Bessere Qualität
```

### Claude (Anthropic)
```json
"llm": "ClaudeAI",
"llm_model": "claude-3-7-sonnet-latest"    // Sehr gut für Texte
"llm_model": "claude-opus-4-20250514"      // Beste Qualität (teuer)
"llm_model": "claude-sonnet-4-20250514"    // Balance
```

### GPT (OpenAI)
```json
"llm": "OpenAI",
"llm_model": "gpt-4.1-2025-04-14"    // GPT-4
"llm_model": "gpt-4o-mini"           // Günstig, schnell
"llm_model": "o1"                    // Reasoning Model
"llm_model": "o3-mini"               // Reasoning Mini
```

### OpenRouter (Grok, Perplexity, etc.)
```json
"llm": "OpenRouterAI",
"llm_model": "x-ai/grok-3-beta"              // Grok 3
"llm_model": "perplexity/sonar-pro"          // Perplexity
```

---

## 🤖 Workflow-Beispiel: Autor + Lektor Agenten

### Workflow-Struktur

```
1. [Webhook/Trigger]
   ↓
2. [Lade Charakterdatei] (Read Binary File)
   ↓
3. [Lade Schreibstil-Datei] (Read Binary File)
   ↓
4. [AUTOR-AGENT] (HTTP Request → Claude Opus)
   ↓
5. [LEKTOR-AGENT] (HTTP Request → Gemini Pro)
   ↓
6. [Ergebnis speichern/senden]
```

---

## 📝 Agent 1: Autor-Agent (Claude Opus)

**Node Type:** HTTP Request

**Settings:**
- **Method:** POST
- **URL:** `https://qolaba-server-b2b.up.railway.app/api/v1/studio/chat`

**Headers:**
```json
{
  "Authorization": "Bearer {{$env.QOLABA_API_TOKEN}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "llm": "ClaudeAI",
  "llm_model": "claude-opus-4-20250514",
  "history": [
    {
      "role": "system",
      "content": {
        "text": "# CHARAKTER\n{{$node['Lade Charakterdatei'].json.data}}\n\n# SCHREIBSTIL\n{{$node['Lade Schreibstil-Datei'].json.data}}",
        "image_data": []
      }
    },
    {
      "role": "user",
      "content": {
        "text": "{{$json.thema}}\n\nSchreibe einen Text zu diesem Thema im definierten Stil.",
        "image_data": []
      }
    }
  ],
  "temperature": 0.8,
  "enable_tool": false,
  "system_msg": "Du bist ein professioneller Autor. Befolge exakt den definierten Charakter und Schreibstil.",
  "tools": {
    "tool_list": {
      "internet_search": false,
      "python_code_execution_tool": false
    }
  },
  "token": "{{$env.QOLABA_API_TOKEN}}",
  "orgID": "{{$env.QOLABA_ORG_ID}}",
  "function_call_list": [],
  "systemId": "",
  "last_user_query": "{{$json.thema}}"
}
```

**Wichtig:**
- `temperature: 0.8` für kreatives Schreiben
- System-Message enthält Charakter + Schreibstil

---

## ✏️ Agent 2: Lektor-Agent (Gemini Pro)

**Node Type:** HTTP Request

**Settings:**
- **Method:** POST
- **URL:** `https://qolaba-server-b2b.up.railway.app/api/v1/studio/chat`

**Headers:**
```json
{
  "Authorization": "Bearer {{$env.QOLABA_API_TOKEN}}",
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "llm": "GeminiAI",
  "llm_model": "gemini-2.5-pro",
  "history": [
    {
      "role": "user",
      "content": {
        "text": "Prüfe folgenden Text auf:\n1. Grammatik\n2. Rechtschreibung\n3. Schreibstil-Konsistenz\n4. Verbesserungsvorschläge\n\nTEXT:\n{{$node['AUTOR-AGENT'].json.response}}\n\nGib den korrigierten Text und eine Liste der Änderungen zurück.",
        "image_data": []
      }
    }
  ],
  "temperature": 0.3,
  "enable_tool": false,
  "system_msg": "Du bist ein professioneller Lektor. Prüfe Texte auf Grammatik, Rechtschreibung und Stil. Sei präzise und konstruktiv.",
  "tools": {
    "tool_list": {
      "internet_search": false,
      "python_code_execution_tool": false
    }
  },
  "token": "{{$env.QOLABA_API_TOKEN}}",
  "orgID": "{{$env.QOLABA_ORG_ID}}",
  "function_call_list": [],
  "systemId": "",
  "last_user_query": "Lektorat"
}
```

**Wichtig:**
- `temperature: 0.3` für präzise Korrekturen
- Nutzt Output vom Autor-Agent: `{{$node['AUTOR-AGENT'].json.response}}`

---

## 🔧 Environment Variables in n8n setzen

**In deiner n8n Installation:**

1. SSH zur NAS oder Portainer Terminal
2. Öffne n8n Container Environment Variables
3. Füge hinzu:

```env
QOLABA_API_TOKEN=dein_token_ohne_prefix
QOLABA_ORG_ID=deine_org_id_ohne_prefix
```

**In Portainer:**
1. **Containers** → Finde deinen n8n Container
2. **Duplicate/Edit** → Scroll zu **Environment variables**
3. Füge hinzu:
   - `QOLABA_API_TOKEN` = `dein_token`
   - `QOLABA_ORG_ID` = `deine_org_id`
4. **Restart** Container

**In n8n Workflow (Alternative):**

Nutze `{{$env.QOLABA_API_TOKEN}}` in den Nodes - n8n liest automatisch die ENV-Variablen!

---

## 📁 Datei-Handling: Charakter & Schreibstil

### Option A: Dateien im n8n-Container speichern

**Via SSH/Portainer Terminal:**
```bash
# Wechsel in n8n Container
docker exec -it dein-n8n-container bash

# Erstelle Ordner
mkdir -p /data/qolaba-prompts

# Verlasse Container
exit

# Kopiere Dateien vom Host
docker cp charakter.txt dein-n8n-container:/data/qolaba-prompts/
docker cp schreibstil.txt dein-n8n-container:/data/qolaba-prompts/
```

**In n8n - Read Binary File Node:**
- **File Path:** `/data/qolaba-prompts/charakter.txt`
- **Property Name:** `data`
- **As UTF-8:** ✅

### Option B: Dateien in n8n Workflow einbetten

**Nutze "Set" Node:**

```json
{
  "charakter": "Name: Dr. Alexandra Winters\nBeruf: KI-Forscherin\nPersönlichkeit: Analytisch, präzise, freundlich\nSchreibstil: Wissenschaftlich aber zugänglich",
  "schreibstil": "- Kurze, prägnante Sätze\n- Aktive Sprache\n- Fachbegriffe erklärt\n- Beispiele nutzen"
}
```

Dann im Autor-Agent:
```json
"text": "# CHARAKTER\n{{$node['Charakter-Setup'].json.charakter}}\n\n# SCHREIBSTIL\n{{$node['Charakter-Setup'].json.schreibstil}}"
```

### Option C: Dateien aus externem Storage (Cloud, NAS)

**Read Binary File Node** mit HTTP Request:
- **URL:** `http://nas-ip/share/charakter.txt`
- Oder Google Drive, Dropbox, etc.

---

## 🎨 Erweiterte Features

### Internet-Suche aktivieren

```json
{
  "enable_tool": true,
  "tools": {
    "tool_list": {
      "internet_search": true,
      "python_code_execution_tool": false
    }
  }
}
```

### RAG (Retrieval Augmented Generation)

Für Dokument-basierte Antworten:

```json
{
  "enable_tool": true,
  "tools": {
    "tool_list": {
      "search_doc": true
    },
    "pdf_references": ["dokument_id_1", "dokument_id_2"],
    "embedding_model": ["text-embedding-3-large"]
  }
}
```

### Code-Ausführung

```json
{
  "enable_tool": true,
  "tools": {
    "tool_list": {
      "python_code_execution_tool": true
    }
  }
}
```

---

## 🔄 Multi-Turn Conversations

Für längere Gespräche mit Kontext:

```json
{
  "history": [
    {
      "role": "user",
      "content": {"text": "Erste Nachricht", "image_data": []}
    },
    {
      "role": "assistant",
      "content": {"text": "Antwort vom AI", "image_data": []}
    },
    {
      "role": "user",
      "content": {"text": "Follow-up Frage", "image_data": []}
    }
  ]
}
```

In n8n kannst du die `history` in einer Variable speichern und erweitern:

```javascript
// Code Node
const history = $('AUTOR-AGENT').first().json.history || [];
history.push({
  role: "user",
  content: {text: $json.neue_nachricht, image_data: []}
});
return {history};
```

---

## 💰 Kosten-Optimierung

### Richtige Modelle für richtige Aufgaben

| Aufgabe | Empfohlenes Modell | Kosten |
|---------|-------------------|--------|
| **Kreatives Schreiben** | Claude Opus | Hoch |
| **Lektorat/Korrektur** | Gemini Pro | Mittel |
| **Einfache Zusammenfassungen** | Gemini Flash | Niedrig |
| **Reasoning/Logik** | GPT o1/o3-mini | Mittel-Hoch |
| **Schnelle Antworten** | GPT-4o-mini | Niedrig |

### Temperature-Einstellungen

- **Kreativ (0.7-1.0):** Geschichten, Marketing-Texte
- **Balanced (0.5-0.7):** Normale Konversation
- **Präzise (0.0-0.3):** Korrekturen, Fakten, Code

---

## 🧪 Testing & Debugging

### 1. Test einzelne Nodes

- Rechtsklick auf HTTP Request Node → **"Execute Node"**
- Prüfe Response im Output-Panel

### 2. Response auslesen

Die Qolaba API gibt zurück:

```json
{
  "response": "Der generierte Text...",
  "model_used": "claude-opus-4-20250514",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 500
  }
}
```

Zugriff in n8n:
- Text: `{{$json.response}}`
- Modell: `{{$json.model_used}}`
- Tokens: `{{$json.usage.input_tokens}}`

### 3. Error Handling

Füge einen **IF Node** nach dem API-Call hinzu:

```
IF: {{$json.response}} is not empty
  → SUCCESS Branch
ELSE
  → ERROR Handling (Send Notification, Retry, etc.)
```

---

## 🔐 Sicherheit

### Credentials schützen

1. **Nutze n8n Credentials Manager:**
   - n8n → Settings → Credentials
   - Erstelle "Header Auth" Credential
   - Nutze in HTTP Request Nodes

2. **Environment Variables:**
   - Speichere Token in ENV (siehe oben)
   - Nutze `{{$env.QOLABA_API_TOKEN}}`

3. **Niemals im Code hardcoden!**

---

## 📋 Vollständiges Workflow-Beispiel (JSON Export)

```json
{
  "name": "Qolaba Autor + Lektor Workflow",
  "nodes": [
    {
      "parameters": {},
      "name": "Workflow Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "thema",
              "value": "Die Zukunft der KI in der Medizin"
            },
            {
              "name": "charakter",
              "value": "Name: Dr. Alexandra Winters\\nBeruf: KI-Forscherin\\nExpertise: Medizinische AI\\nTon: Wissenschaftlich, aber zugänglich"
            },
            {
              "name": "schreibstil",
              "value": "- Kurze, prägnante Sätze\\n- Fachbegriffe erklären\\n- Beispiele nutzen\\n- Optimistisch aber realistisch"
            }
          ]
        }
      },
      "name": "Setup",
      "type": "n8n-nodes-base.set",
      "position": [450, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://qolaba-server-b2b.up.railway.app/api/v1/studio/chat",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "Bearer {{$env.QOLABA_API_TOKEN}}"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": []
        },
        "jsonBody": "={\n  \"llm\": \"ClaudeAI\",\n  \"llm_model\": \"claude-opus-4-20250514\",\n  \"history\": [\n    {\n      \"role\": \"system\",\n      \"content\": {\n        \"text\": \"# CHARAKTER\\n{{$node['Setup'].json.charakter}}\\n\\n# SCHREIBSTIL\\n{{$node['Setup'].json.schreibstil}}\",\n        \"image_data\": []\n      }\n    },\n    {\n      \"role\": \"user\",\n      \"content\": {\n        \"text\": \"Thema: {{$node['Setup'].json.thema}}\\n\\nSchreibe einen informativen Artikel zu diesem Thema. Nutze den definierten Charakter und Schreibstil.\",\n        \"image_data\": []\n      }\n    }\n  ],\n  \"temperature\": 0.8,\n  \"enable_tool\": false,\n  \"system_msg\": \"Du bist ein professioneller Autor. Befolge exakt den Charakter und Schreibstil.\",\n  \"tools\": {\"tool_list\": {\"internet_search\": false}},\n  \"token\": \"{{$env.QOLABA_API_TOKEN}}\",\n  \"orgID\": \"{{$env.QOLABA_ORG_ID}}\",\n  \"function_call_list\": [],\n  \"systemId\": \"\",\n  \"last_user_query\": \"{{$node['Setup'].json.thema}}\"\n}"
      },
      "name": "AUTOR-AGENT",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://qolaba-server-b2b.up.railway.app/api/v1/studio/chat",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "Bearer {{$env.QOLABA_API_TOKEN}}"
            }
          ]
        },
        "sendBody": true,
        "jsonBody": "={\n  \"llm\": \"GeminiAI\",\n  \"llm_model\": \"gemini-2.5-pro\",\n  \"history\": [\n    {\n      \"role\": \"user\",\n      \"content\": {\n        \"text\": \"Prüfe folgenden Text auf:\\n1. Grammatik\\n2. Rechtschreibung\\n3. Stil-Konsistenz\\n4. Verbesserungen\\n\\nTEXT:\\n{{$node['AUTOR-AGENT'].json.response}}\\n\\nGib den korrigierten Text zurück.\",\n        \"image_data\": []\n      }\n    }\n  ],\n  \"temperature\": 0.3,\n  \"enable_tool\": false,\n  \"system_msg\": \"Du bist ein professioneller Lektor. Prüfe präzise und konstruktiv.\",\n  \"token\": \"{{$env.QOLABA_API_TOKEN}}\",\n  \"orgID\": \"{{$env.QOLABA_ORG_ID}}\",\n  \"tools\": {\"tool_list\": {}},\n  \"function_call_list\": [],\n  \"systemId\": \"\",\n  \"last_user_query\": \"Lektorat\"\n}"
      },
      "name": "LEKTOR-AGENT",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    }
  ],
  "connections": {
    "Workflow Trigger": {
      "main": [[{"node": "Setup", "type": "main", "index": 0}]]
    },
    "Setup": {
      "main": [[{"node": "AUTOR-AGENT", "type": "main", "index": 0}]]
    },
    "AUTOR-AGENT": {
      "main": [[{"node": "LEKTOR-AGENT", "type": "main", "index": 0}]]
    }
  }
}
```

**Import in n8n:**
1. Kopiere das JSON
2. n8n → Workflows → "Import from JSON"
3. Füge ein und importiere
4. Setze ENV-Variablen
5. Execute!

---

## 🎯 Nächste Schritte

1. **Teste mit einem einfachen Workflow** (nur AUTOR-AGENT)
2. **Erweitere** mit LEKTOR-AGENT
3. **Optimiere** Temperature und Modelle
4. **Speichere** Charakter/Schreibstil als Dateien
5. **Baue** komplexere Pipelines

---

## 💡 Tipps & Tricks

### Kosten sparen
- Nutze **Gemini Flash** für einfache Tasks
- Nutze **Claude Opus** nur für kritische Qualität
- Setze **max_tokens** limits

### Qualität verbessern
- **System Messages** sind wichtig - nutze sie!
- **Temperature** richtig wählen
- **Beispiele** in Prompts einbauen
- **Multi-Turn** für Kontext

### Debugging
- Logge Requests/Responses
- Teste Modelle einzeln
- Prüfe Token-Usage
- Nutze n8n Error Workflows

---

## 📚 Ressourcen

- **Qolaba API Docs:** [qolaba.ai/docs](https://qolaba.ai/docs)
- **n8n Docs:** [docs.n8n.io](https://docs.n8n.io)
- **Claude Prompt Engineering:** [docs.anthropic.com/prompting](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- **Gemini Best Practices:** [ai.google.dev/gemini](https://ai.google.dev/gemini-api/docs)

---

## 🆘 Support

Bei Fragen oder Problemen:
1. Prüfe die Logs in n8n
2. Teste die API direkt (Postman/curl)
3. Checke Qolaba Credits/Status
4. Siehe README.md für MCP Server Setup

---

**Viel Erfolg mit deinen AI-Workflows! 🚀**
