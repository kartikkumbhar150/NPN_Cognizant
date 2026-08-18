"""FastAPI application factory for the standalone chatbot service.

Creates the ASGI app with the chatbot router.  The ChatbotStack is
initialized lazily on first request (via ``get_stack()``), not at import
time, so the server starts fast and heavy resources (FastEmbed model,
Qdrant connection) load only once.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure the repo root (containing Python/) is on sys.path so the
# ai_engine_adapter can find Python/ai_engine modules.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT / "Python") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "Python"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot.app.api.router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="NPN Chatbot Service",
        description="Standalone chatbot with RAG, NBO recommendations, and multi-turn conversation",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("Chatbot service starting (port 8001)...")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Chatbot service shutting down")
        from chatbot.app.services.dependencies import reset_stack
        reset_stack()

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chatbot.app.main:app", host="0.0.0.0", port=8001, reload=False)
