# Multi-stage build für optimale Image-Größe
FROM python:3.11-slim as builder

# Build-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime Stage
FROM python:3.11-slim

# Runtime-Dependencies (nur curl für Health Check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Non-root user erstellen für Sicherheit
RUN groupadd -r mcpuser && useradd -r -g mcpuser -u 1000 mcpuser

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python Dependencies von builder stage kopieren
COPY --from=builder /root/.local /home/mcpuser/.local

# Application Files kopieren
COPY --chown=mcpuser:mcpuser qolaba_server.py .

# Logs-Verzeichnis erstellen
RUN mkdir -p /app/logs && chown -R mcpuser:mcpuser /app/logs

# Environment Variables
ENV PATH=/home/mcpuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    QOLABA_API_TOKEN="" \
    QOLABA_ORG_ID="" \
    MCP_TRANSPORT="http" \
    PORT=8000

# Expose Port für HTTP Transport
EXPOSE 8000

# Zu non-root user wechseln
USER mcpuser

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Entrypoint Script
# Unterstützt beide Transport-Modi: stdio und http
ENTRYPOINT ["python", "qolaba_server.py"]
CMD ["--transport", "http", "--port", "8000"]
