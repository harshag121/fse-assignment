"""Standalone MCP Server — runs on port 8001.

This is the MCP *server* process. It exposes all tools via the MCP protocol
over SSE transport. The main FastAPI app (port 8000) connects to this server
as an MCP *client* — giving a true MCP client-server separation.

Run:  python mcp_server_main.py
      (or via docker-compose mcp-server service)
"""
import asyncio
import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport

from app.core.config import settings
from app.models.database import init_db
from app.mcp_server.tools import register_tools
from app.mcp_server.resources import register_resources
from app.mcp_server.prompts import register_prompts

# ── Build the MCP server ───────────────────────────────────────────────────────

mcp_server = Server(settings.MCP_SERVER_NAME)
register_tools(mcp_server)
register_resources(mcp_server)
register_prompts(mcp_server)

sse_transport = SseServerTransport("/messages/")


async def _asgi_app(scope, receive, send):
    """Minimal ASGI router — avoids Starlette Route's teardown TypeError.

    Starlette's Route handler calls `await response(scope, receive, send)` where
    response is the return value of the endpoint function.  The SSE transport
    manages the ASGI send callable itself and the handler returns None, which
    causes `TypeError: NoneType not callable` during teardown.

    Bypassing Starlette's Route entirely and writing a bare ASGI callable solves
    the problem cleanly: we own scope/receive/send directly.
    """
    if scope["type"] != "http":
        return

    path = scope.get("path", "")

    if path == "/sse":
        async with sse_transport.connect_sse(scope, receive, send) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )
    elif path.startswith("/messages/"):
        await sse_transport.handle_post_message(scope, receive, send)
    else:
        await send({"type": "http.response.start", "status": 404, "headers": []})
        await send({"type": "http.response.body", "body": b"not found", "more_body": False})


app = _asgi_app


async def main():
    # Initialise DB tables before the server starts handling requests
    await init_db()
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
