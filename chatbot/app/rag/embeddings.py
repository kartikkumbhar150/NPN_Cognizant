"""Embedding provider abstraction.

``EmbeddingProvider`` is the provider-neutral contract; the rest of the
application depends on it, never on a specific backend.  ``dimension``
metadata is sourced from the provider — the Qdrant collection vector
size is derived from it, never hardcoded.

No FastAPI, Qdrant, application, or customer models appear here, and no
model download or external client happens at import time: fastembed is
imported lazily and the ONNX model loads only on first embedding use.
"""

import math
import numbers
from typing import Protocol, Sequence, runtime_checkable

from chatbot.app.rag.errors import (
    EmbeddingDimensionError,
    EmbeddingGenerationError,
    EmbeddingInitializationError,
    EmbeddingInputError,
    RagConfigurationError,
)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Contract every embedding implementation must satisfy."""

    @property
    def model_name(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


# ── Shared validation helpers ─────────────────────────────────────────────────


def _ensure_valid_text(text: object, label: str) -> str:
    if not isinstance(text, str):
        raise EmbeddingInputError(f"{label} must be a string, got {type(text).__name__}")
    if not text.strip():
        raise EmbeddingInputError(f"{label} must not be empty or whitespace-only")
    return text


def _validate_vectors(
    rows: object,
    *,
    model_name: str,
    expected_dimension: int,
    expected_count: int,
) -> list[list[float]]:
    """Validate provider output shape; convert to plain ``list[list[float]]``."""
    rows = list(rows)  # type: ignore[arg-type]
    if len(rows) != expected_count:
        raise EmbeddingGenerationError(
            f"embedding model {model_name!r} returned {len(rows)} vectors "
            f"for {expected_count} inputs"
        )
    validated: list[list[float]] = []
    for row in rows:
        components = list(row)  # type: ignore[arg-type]
        converted: list[float] = []
        for value in components:
            if isinstance(value, bool) or not isinstance(value, numbers.Real):
                raise EmbeddingGenerationError(
                    f"embedding model {model_name!r} returned a non-numeric "
                    f"vector component: {value!r}"
                )
            numeric = float(value)
            if not math.isfinite(numeric):
                raise EmbeddingGenerationError(
                    f"embedding model {model_name!r} returned a non-finite "
                    f"vector component"
                )
            converted.append(numeric)
        if len(converted) != expected_dimension:
            raise EmbeddingDimensionError(model_name, expected_dimension, len(converted))
        validated.append(converted)
    return validated


# ── FastEmbed implementation ──────────────────────────────────────────────────


class FastEmbedProvider:
    """Local, CPU-only embedding provider backed by fastembed (ONNX).

    The fastembed package is imported lazily and the model is loaded only
    on first use, so constructing this class (and reading ``dimension``
    from the bundled supported-model registry) performs no network access
    and no model download.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise EmbeddingInitializationError("model name must be a non-empty string")
        self._model_name = model_name.strip()
        self._model = None  # lazily loaded ONNX model
        self._metadata: dict | None = None

    # ── Provider contract ──────────────────────────────────────────────────

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        """Vector dimension from the bundled registry — no model download."""
        return int(self._resolve_metadata()["dim"])

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if len(texts) == 0:
            raise EmbeddingInputError("embed_documents requires at least one text")
        cleaned = [_ensure_valid_text(t, f"texts[{i}]") for i, t in enumerate(texts)]
        model = self._get_model()
        try:
            raw_rows = list(model.embed(cleaned))
        except EmbeddingInputError:
            raise
        except Exception as exc:
            raise EmbeddingGenerationError(
                f"embedding generation failed for model {self._model_name!r}: "
                f"{type(exc).__name__}"
            ) from exc
        return _validate_vectors(
            raw_rows,
            model_name=self._model_name,
            expected_dimension=self.dimension,
            expected_count=len(cleaned),
        )

    def embed_query(self, text: str) -> list[float]:
        cleaned = _ensure_valid_text(text, "text")
        model = self._get_model()
        try:
            raw_rows = list(model.query_embed([cleaned]))
        except Exception as exc:
            raise EmbeddingGenerationError(
                f"embedding generation failed for model {self._model_name!r}: "
                f"{type(exc).__name__}"
            ) from exc
        rows = _validate_vectors(
            raw_rows,
            model_name=self._model_name,
            expected_dimension=self.dimension,
            expected_count=1,
        )
        return rows[0]

    # ── Lazy internals ─────────────────────────────────────────────────────

    def _resolve_metadata(self) -> dict:
        """Return the registry entry for the configured model (offline)."""
        if self._metadata is None:
            try:
                from fastembed import TextEmbedding
            except Exception as exc:
                raise EmbeddingInitializationError(
                    f"fastembed is not available: {type(exc).__name__}. "
                    f"Install chatbot/requirements.txt to use FastEmbedProvider."
                ) from exc
            supported = TextEmbedding.list_supported_models()
            for entry in supported:
                if entry.get("model") == self._model_name:
                    self._metadata = entry
                    break
            else:
                known = sorted({str(e.get("model")) for e in supported})[:5]
                raise EmbeddingInitializationError(
                    f"embedding model {self._model_name!r} is not supported by "
                    f"fastembed. Examples of supported models: "
                    f"{', '.join(known)}, …"
                )
        return self._metadata

    def _get_model(self):
        """Load the ONNX model on first use, validating the model name first."""
        if self._model is None:
            self._resolve_metadata()  # fail fast on unsupported names
            try:
                from fastembed import TextEmbedding

                self._model = TextEmbedding(model_name=self._model_name)
            except EmbeddingInitializationError:
                raise
            except Exception as exc:
                self._model = None
                raise EmbeddingInitializationError(
                    f"could not initialize embedding model {self._model_name!r}: "
                    f"{type(exc).__name__}"
                ) from exc
        return self._model

    @property
    def _model_loaded(self) -> bool:
        """Test/inspection hook: True once the ONNX model has been loaded."""
        return self._model is not None


# ── Factory ───────────────────────────────────────────────────────────────────


def create_embedding_provider(settings) -> EmbeddingProvider:
    """Build the configured embedding provider.

    ``settings`` is ``ChatbotSettings`` (or anything exposing
    ``embedding_provider`` / ``embedding_model``).  Unknown provider
    names fail with a clear configuration error so future providers can
    be added here without touching callers.
    """
    name = (getattr(settings, "embedding_provider", "") or "").strip().lower()
    if name == "fastembed":
        return FastEmbedProvider(model_name=settings.embedding_model)
    raise RagConfigurationError(
        f"unknown EMBEDDING_PROVIDER {name!r}; supported: fastembed"
    )
