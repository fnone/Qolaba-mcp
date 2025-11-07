#!/bin/bash
# Rebuild Script für Qolaba MCP Server
# Stoppt Container, löscht altes Image, baut neu und startet

set -e

echo "🛑 Stoppe laufenden Container..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true

echo "🗑️  Lösche altes Image..."
docker rmi qolaba-mcp-server:latest 2>/dev/null || true

echo "🔨 Baue neues Image..."
docker compose build --no-cache || docker-compose build --no-cache

echo "🚀 Starte Container..."
docker compose up -d || docker-compose up -d

echo ""
echo "✅ Container neu gestartet!"
echo ""
echo "📊 Status:"
docker ps | grep qolaba-mcp-server || echo "Container läuft nicht!"

echo ""
echo "📋 Logs (letzten 20 Zeilen):"
docker compose logs --tail=20 qolaba-mcp-server || docker-compose logs --tail=20 qolaba-mcp-server

echo ""
echo "🔍 Weitere Logs anzeigen:"
echo "  docker compose logs -f qolaba-mcp-server"
echo ""
echo "🏥 Health Check (in ca. 30 Sekunden):"
echo "  docker inspect --format='{{.State.Health.Status}}' qolaba-mcp-server"
