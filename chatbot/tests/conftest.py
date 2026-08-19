"""Shared pytest fixtures for the chatbot test suite.

Unit-test fixtures are cheap and always available.  The full-stack
fixture (``stack``) is session-scoped: FastEmbed model load and Qdrant
local mode are paid once for the whole run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Default the whole test session to LOCAL Qdrant so the suite never
# depends on live cloud infrastructure or the credentials in
# chatbot/.env.  ``from_env()`` loads chatbot/.env with override=False,
# so pre-setting these (even empty) wins.  Set CHATBOT_TESTS_ALLOW_CLOUD=1
# to run the integration tests against the cluster configured in
# chatbot/.env instead.
if os.environ.get("CHATBOT_TESTS_ALLOW_CLOUD") != "1":
    os.environ.setdefault("QDRANT_URL", "")
    os.environ.setdefault("QDRANT_API_KEY", "")
    # setdefault: an explicitly exported empty/unset value stays; a value
    # exported by the runner is respected only when cloud is allowed above.

# Repo root on sys.path so `chatbot.` imports resolve when pytest runs
# from any directory.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from chatbot.app.config import ChatbotSettings, REPO_ROOT as CFG_REPO_ROOT  # noqa: E402


@pytest.fixture(scope="session")
def settings() -> ChatbotSettings:
    return ChatbotSettings.from_env()


@pytest.fixture(scope="session")
def credit_cards_df(settings: ChatbotSettings) -> pd.DataFrame:
    return pd.read_csv(settings.credit_cards_csv)


@pytest.fixture(scope="session")
def loans_df(settings: ChatbotSettings) -> pd.DataFrame:
    return pd.read_csv(settings.loans_csv)


@pytest.fixture(scope="session")
def stack(settings: ChatbotSettings):
    """Full ChatbotStack with real engines, FastEmbed, and local Qdrant.

    Requires the knowledge corpus to have been ingested (see
    ``chatbot/scripts/ingest_hdfc_knowledge.py``); tests that depend on
    populated Qdrant data check the point count themselves and skip
    with a clear reason when the collection is empty.

    This fixture also installs itself as the global singleton so the
    TestClient's lazy ``get_stack()`` reuses the same Qdrant client
    (local Qdrant locks the storage directory).
    """
    from chatbot.app.services.dependencies import ChatbotStack, _stack, _stack_lock

    instance = ChatbotStack(settings)
    instance.initialize()

    # Install as the global singleton so TestClient reuses this instance
    # (avoids a second Qdrant client locking the same local directory).
    import chatbot.app.services.dependencies as dep
    with _stack_lock:
        dep._stack = instance

    yield instance

    # Clean up
    with _stack_lock:
        dep._stack = None
