"""Runnable entry point for the GenAI Personalization (Phase 6) service.

The canonical FastAPI application lives in ``app.main``; this module only
re-exports it and provides a convenience launcher so a single app instance
exists. Run from the ``Python/`` directory:

    uvicorn main:app --reload
    # or
    python main.py
"""

import uvicorn

from app.main import app

__all__ = ["app"]


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
