"""Canonical FastAPI application for the GenAI Personalization service.

DS-01 establishes architecture only: the app boots and exposes ``GET /health``.
The Phase 6 generation endpoint is intentionally not created yet — the request
and response contracts live in ``app.models`` and are validated by tests.
"""

from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title="GenAI Personalization Service",
    description=(
        "Phase 6: generates personalized multi-channel marketing content for "
        "already-approved product recommendations. The service never decides "
        "which product to offer — product, eligibility, propensity, and "
        "reasons arrive as trusted upstream inputs."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness probe returning a simple, deterministic payload."""
    return {"status": "ok", "service": settings.service_name}
