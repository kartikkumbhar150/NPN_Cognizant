"""Versioned prompt templates for Phase 6.

Versioning rule (immutable versions)
-----------------------------------
A prompt version directory (``v1/``) is treated as immutable once shipped.
Future prompt changes MUST create a new version directory (``v2/``) instead of
silently rewriting ``v1``. The prompt builder resolves templates from
``prompts/<version>/`` and reports the version in every ``PromptPackage``.

All templates are rendered as **data-only context**: no raw customer
identifiers, no propensity, no eligibility details ever reach the rendered
prompt (see ``app.services.prompt_builder``).
"""
