"""MCP Server - initializes and wires together tools, resources, and prompts."""
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request

from app.core.config import settings
from app.mcp_server.tools import register_tools
from app.mcp_server.resources import register_resources
from app.mcp_server.prompts import register_prompts


def create_mcp_server() -> Server:
    """Create and configure the MCP server instance."""
    server = Server(settings.MCP_SERVER_NAME)
    register_tools(server)
    register_resources(server)
    register_prompts(server)
    return server


def create_mcp_starlette_app(mcp_server: Server) -> Starlette:
    """Wrap the MCP server in a Starlette app via SSE transport.
    This app is mounted at /mcp in main.py, so paths here are relative to that."""
    sse = SseServerTransport("/mcp/messages/")

    async def handle_sse(request: Request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )
