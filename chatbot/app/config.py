"""Chatbot configuration.

Environment-driven (repository convention): values come from env vars,
secrets have no defaults and never appear in repr/logs, and no external
client (Qdrant, embedding model, AI engine) is constructed at import
time anywhere in this package.

Path anchors (resolved from this file's location, not the CWD):
- ``REPO_ROOT``       = repository root (parent of ``chatbot/``)
- ``CHATBOT_DIR``     = this ``chatbot/`` directory
- relative ``QDRANT_LOCAL_PATH`` is anchored under ``chatbot/`` so all
  generated data stays inside this module's directory
- the existing AI engine + Database_csvs live under ``REPO_ROOT/Python``
  by default (override with ``AI_ENGINE_DIR``)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# chatbot/app/config.py → chatbot/app → chatbot → repo root
APP_DIR = Path(__file__).resolve().parent
CHATBOT_DIR = APP_DIR.parent
REPO_ROOT = CHATBOT_DIR.parent

DEFAULT_AI_ENGINE_DIR = REPO_ROOT / "Python"
DEFAULT_DATABASE_DIR = DEFAULT_AI_ENGINE_DIR / "Database_csvs"
DEFAULT_CORPUS_DIR = CHATBOT_DIR / "knowledge" / "hdfc"
DEFAULT_GENERAL_DIR = DEFAULT_CORPUS_DIR / "general"

DEFAULT_SERVICE_PORT = 8001


@dataclass(frozen=True)
class ChatbotSettings:
    """Immutable chatbot settings loaded from the environment.

    ``qdrant_url`` empty means local embedded mode (persistent directory
    under ``qdrant_local_path``; ``:memory:`` for tests).  Secret fields
    are hidden from ``repr()`` so they can never leak via logs.
    """

    qdrant_url: str = ""
    qdrant_api_key: str = ""  # secret: never given a default value
    qdrant_collection: str = "hdfc_banking_knowledge_v1"
    qdrant_local_path: str = ".qdrant"
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    rag_top_k: int = 5
    rag_max_top_k: int = 20
    rag_score_threshold: str = ""  # empty = no threshold; else float in [-1, 1]
    max_message_chars: int = 2000
    max_conversation_turns: int = 10
    conversation_ttl_seconds: float = 1800.0  # 30 minutes
    ai_engine_dir: str = str(DEFAULT_AI_ENGINE_DIR)
    service_port: int = DEFAULT_SERVICE_PORT

    # ── Path views (derived, not configurable duplicated state) ────────────

    @property
    def ai_engine_path(self) -> Path:
        path = Path(self.ai_engine_dir)
        return path if path.is_absolute() else (REPO_ROOT / path)

    @property
    def database_dir(self) -> Path:
        return self.ai_engine_path / "Database_csvs"

    @property
    def credit_cards_csv(self) -> Path:
        return self.database_dir / "credit_card_products.csv"

    @property
    def loans_csv(self) -> Path:
        return self.database_dir / "loan_products.csv"

    @property
    def corpus_dir(self) -> Path:
        return DEFAULT_CORPUS_DIR

    @property
    def general_knowledge_dir(self) -> Path:
        return DEFAULT_GENERAL_DIR

    # ── Secret-safe repr ────────────────────────────────────────────────────

    def __repr__(self) -> str:
        """Representation that redacts secret fields."""
        fields = dict(self.__dict__)
        if fields.get("qdrant_api_key"):
            fields["qdrant_api_key"] = "***"
        names = [f"{k}={v!r}" for k, v in fields.items()]
        return f"{type(self).__name__}({', '.join(names)})"

    @classmethod
    def from_env(cls) -> "ChatbotSettings":
        """Build settings from ``QDRANT_*`` / ``EMBEDDING_*`` / ``RAG_*`` vars."""
        return cls(
            qdrant_url=os.getenv("QDRANT_URL", "").strip(),
            qdrant_api_key=os.getenv("QDRANT_API_KEY", "").strip(),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "hdfc_banking_knowledge_v1").strip()
            or "hdfc_banking_knowledge_v1",
            qdrant_local_path=os.getenv("QDRANT_LOCAL_PATH", ".qdrant").strip() or ".qdrant",
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "fastembed").strip().lower()
            or "fastembed",
            embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
            or "BAAI/bge-small-en-v1.5",
            rag_top_k=int(os.getenv("RAG_TOP_K", "5")),
            rag_max_top_k=int(os.getenv("RAG_MAX_TOP_K", "20")),
            rag_score_threshold=os.getenv("RAG_SCORE_THRESHOLD", "").strip(),
            max_message_chars=int(os.getenv("CHAT_MAX_MESSAGE_CHARS", "2000")),
            ai_engine_dir=os.getenv("AI_ENGINE_DIR", str(DEFAULT_AI_ENGINE_DIR)).strip()
            or str(DEFAULT_AI_ENGINE_DIR),
            service_port=int(os.getenv("CHAT_SERVICE_PORT", str(DEFAULT_SERVICE_PORT))),
        )


def load_settings() -> ChatbotSettings:
    """Fresh settings from the environment (cheap; call sites stay testable)."""
    return ChatbotSettings.from_env()


def resolve_rag_score_threshold(settings: ChatbotSettings):
    """Return ``RAG_SCORE_THRESHOLD`` as float or ``None`` when unset/invalid.

    Invalid values resolve to ``None`` (fail-open on an optional knob)
    because a hard failure here would take down the whole service for a
    tuning parameter nobody depends on being present.
    """
    raw = (settings.rag_score_threshold or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
