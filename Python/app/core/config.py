"""Minimal application configuration for the GenAI Personalization service.

DS-01 establishes structure only: no secrets, no .env loading, and no
environment-dependent behavior. Values are structural defaults used for
service identity and future generation metadata.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable, minimal service configuration."""

    service_name: str = "genai-personalization"
    app_env: str = "development"
    prompt_version: str = "v1"
    catalogue_version: str = "1.0.0"


settings = Settings()
