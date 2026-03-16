#!/bin/bash
# start.sh — Production startup script for Render (and any single-container deployment).
#
# PURPOSE:
#   The app requires TWO processes:
#     1. MCP Server  — port 8001 (MCP *server*, exposes tools via SSE protocol)
#     2. FastAPI App — port $PORT (MCP *client* + REST API)
#
#   docker-compose.yml handles this automatically (separate services).
#   For Render/single-container deployments this script starts both in one dyno.

set -e

echo "[start.sh] Launching MCP server on port 8001..."
python /app/mcp_server_main.py &
MCP_PID=$!

echo "[start.sh] Waiting for MCP server to be ready..."
for i in $(seq 1 20); do
    # /sse is a streaming SSE endpoint (never closes on its own), so we must
    # check the HTTP response code rather than curl's exit code (which will be
    # 28/timeout even when the server IS alive).
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://localhost:8001/sse 2>/dev/null || true)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[start.sh] MCP server is up (attempt $i)."
        break
    fi
    echo "[start.sh] Waiting... ($i/20) got HTTP $HTTP_CODE"
    sleep 1
done

echo "[start.sh] Launching FastAPI backend on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
