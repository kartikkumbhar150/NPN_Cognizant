"""FastAPI router for the chatbot service (port 8001).

Endpoints:
- ``POST /chat``  — full response (intent, sources, recommendations, etc.)
- ``POST /ask``   — simple response: just {answer, conversation_id}
- ``GET  /health`` — liveness/readiness check
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from chatbot.app.models.chat_models import (
    ChatRequest,
    ChatResponse,
)
from chatbot.app.services.customer_context import CustomerNotFoundError
from chatbot.app.services.response_mapper import map_turn_result

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return a response.

    Accepts a single-turn message with optional customer context.
    You can identify the customer either by ``customer_id`` or by
    ``phone_number`` (the service resolves it automatically).
    Multi-turn conversation is tracked server-side via conversation_id.
    """
    start = time.monotonic()

    from chatbot.app.services.dependencies import get_stack

    stack = get_stack()
    orchestrator = stack.orchestrator

    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Chatbot orchestrator not initialized")

    # ── Resolve phone_number → customer_id ───────────────────────────────────
    resolved_customer_id = request.customer_id
    if request.phone_number and not resolved_customer_id:
        if stack.phone_lookup is None:
            raise HTTPException(
                status_code=503,
                detail="Phone lookup service not available (customer data not loaded)",
            )
        from chatbot.app.services.customer_context import PhoneNotFoundError
        try:
            resolved_customer_id = stack.phone_lookup.resolve(request.phone_number)
            logger.info(
                "Phone %s resolved to customer_id=%s",
                request.phone_number[-4:],  # log only last 4 digits for privacy
                resolved_customer_id,
            )
        except PhoneNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    try:
        turn_result = await orchestrator.handle_turn(
            message=request.message,
            customer_id=resolved_customer_id,
            session_id=str(request.conversation_id) if request.conversation_id else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error processing chat turn")
        raise HTTPException(status_code=500, detail="Internal server error")

    elapsed_ms = int((time.monotonic() - start) * 1000)

    response = map_turn_result(turn_result)
    return response


# ── /ask — simple endpoint, returns only the answer text ────────────────────

class AskRequest(ChatRequest):
    """Same as ChatRequest — alias for clarity."""


@router.post("/ask")
async def ask(request: AskRequest) -> Dict[str, str]:
    """Lightweight chat endpoint.

    Identical to POST /chat internally, but returns ONLY::

        {"answer": "...", "conversation_id": "..."}

    Use this when you don't need sources, recommendations, or intent metadata.
    """
    full = await chat(request)
    return {"answer": full.answer, "conversation_id": full.conversation_id}


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Liveness and readiness check.

    Returns component status for each subsystem.
    """
    from chatbot.app.services.dependencies import get_stack

    stack = get_stack()

    components: Dict[str, str] = {}
    # Safe mode indicator only — never the URL or credentials.
    components["qdrant_mode"] = stack.settings.qdrant_mode
    if stack.engines is not None:
        components["ai_engine"] = "loaded"
    else:
        components["ai_engine"] = "not_loaded"
    if stack.knowledge_retriever is not None:
        components["rag_pipeline"] = "loaded"
    else:
        components["rag_pipeline"] = "not_loaded"
    if stack.orchestrator is not None:
        components["orchestrator"] = "ready"
    else:
        components["orchestrator"] = "not_ready"

    try:
        if stack.qdrant_store is not None:
            count = stack.qdrant_store.count()
            components["qdrant_points"] = str(count)
    except Exception:
        components["qdrant_points"] = "error"

    if stack.product_resolver is not None:
        components["product_mappings"] = str(stack.product_resolver.mapping_count)

    return {
        "status": "healthy" if stack.orchestrator is not None else "degraded",
        "service": "chatbot",
        "version": "1.0.0",
        "components": components,
    }
