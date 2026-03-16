"""FastAPI application entry point.

This process (port 8000) is the MCP *client* + REST API.
The MCP *server* runs as a separate process on port 8001 (mcp_server_main.py).
LLMService connects to the MCP server via SSE to discover and call tools.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.database import init_db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Smart Doctor Appointment & Reporting Assistant powered by MCP",
        lifespan=lifespan,
    )

    # CORS
    _origins = ["http://localhost:3000", "http://localhost:5173"]
    if settings.FRONTEND_URL:
        _origins.append(settings.FRONTEND_URL)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST API routes
    app.include_router(router, prefix="/api")

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
