#!/bin/bash
# MCP SSE Bridge für Claude CLI
# Verbindet zu Remote Qolaba MCP Server

exec npx -y @modelcontextprotocol/client http://192.168.188.62:8004/sse
