"""Safe prompt builder for Phase 6 (DS-03).

Pipeline
--------
    PersonalizationRequest + GroundedProductFacts
        -> explicit safe context projection
        -> versioned Jinja2 templates (v1)
        -> PromptPackage

The builder prepares LLM input only. It never calls an LLM.

Core security rule
------------------
The future LLM receives only the minimum information required to write
marketing copy. ``PersonalizationRequest`` is NEVER serialized wholesale
(no ``request.model_dump()`` into prompt context). The following never enter
a rendered prompt: ``customer_id``, ``recommendation_id``, ``source_event_id``,
account/card/transaction IDs, contact/address data, income, credit score,
employer, exact transaction amounts, receiver identifiers, KYC data,
relationship manager ID, propensity, and detailed eligibility/ownership data.

Context is limited to controlled, non-identifying projections:
segment label, generic event labels, persuasion reason labels, language,
requested channels, and the approved grounded product facts.

Prompt versioning
-----------------
``v1`` is immutable. Template directories live under ``prompts/<version>/``.
Future prompt changes MUST create a new version (``v2/``) instead of silently
rewriting ``v1``; the version is reported on every ``PromptPackage``.

Policy: unknown mapping values fail at this boundary (``PromptContextError``)
rather than leaking raw codes into the prompt or being silently dropped.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.models.personalization import Channel, PersonalizationRequest
from app.models.product import GroundedFactCategory, GroundedProductFacts
from app.models.prompt import PromptPackage

PROMPT_VERSION = "v1"

# --------------------------------------------------------------------------
# Controlled mappings (first slice) — deterministic, non-identifying.
# --------------------------------------------------------------------------

SEGMENT_LABELS: dict[str, str] = {
    "FREQUENT_TRAVELLER": "frequent traveller",
}

EVENT_LABELS: dict[str, str] = {
    "FLIGHT_PURCHASE": "recent flight purchase",
}

REASON_LABELS: dict[str, str] = {
    "HIGH_TRAVEL_SPEND": "high travel spending",
    "RECENT_FLIGHT_PURCHASE": "recent flight purchase",
    "NO_CONFLICTING_TRAVEL_CARD": "no conflicting travel card identified",
    "PRODUCT_ELIGIBLE": "product eligibility was confirmed upstream",
}

# Only these reason codes are customer-persuasion context. The others
# (NO_CONFLICTING_TRAVEL_CARD, PRODUCT_ELIGIBLE) are business/safety state and
# are validated but deliberately excluded from the prompt — the system prompt
# already states the product was selected and approved upstream.
PERSUASION_REASON_CODES: frozenset[str] = frozenset(
    {"HIGH_TRAVEL_SPEND", "RECENT_FLIGHT_PURCHASE"}
)

# v1 supports English generation only; unsupported languages are rejected here
# rather than silently translated.
SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"en"})

# Channel output order is fixed so rendered prompts are deterministic.
CHANNEL_ORDER: tuple[Channel, ...] = (
    Channel.PUSH,
    Channel.SMS,
    Channel.EMAIL,
    Channel.IN_APP,
    Channel.RELATIONSHIP_MANAGER,
)

# Prototype length limits — configurable constants injected into templates.
LIMITS: dict[str, int] = {
    "push_title_max": 60,
    "push_body_max": 160,
    "sms_body_max": 160,
}


class PromptError(Exception):
    """Base class for prompt-builder domain errors."""

    code = "PROMPT_ERROR"


class PromptTemplateNotFoundError(PromptError):
    """A required template file is missing from the prompt version directory."""

    code = "PROMPT_TEMPLATE_NOT_FOUND"

    def __init__(self, template: str, version: str) -> None:
        super().__init__(f"prompt template not found: {template!r} for version {version!r}")
        self.template = template
        self.version = version


class PromptRenderError(PromptError):
    """The template engine failed to render a prompt."""

    code = "PROMPT_RENDER_ERROR"


class PromptContextError(PromptError):
    """The request contains context this version cannot safely project."""

    code = "PROMPT_CONTEXT_INVALID"


def _ordered_channels(requested: list[Channel]) -> list[Channel]:
    """Filter requested channels and order them deterministically."""
    requested_set = set(requested)
    return [channel for channel in CHANNEL_ORDER if channel in requested_set]


class PromptBuilder:
    """Builds a versioned, privacy-safe prompt package for Phase 6."""

    def __init__(self, prompt_version: str = PROMPT_VERSION, prompts_root: Path | None = None) -> None:
        self._version = prompt_version
        root = prompts_root if prompts_root is not None else Path(__file__).resolve().parents[1] / "prompts"
        self._env = Environment(
            loader=FileSystemLoader(str(root)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            # Preserve template trailing newlines so included channel sections
            # stay separated (Jinja2 strips them otherwise).
            keep_trailing_newline=True,
        )

    @property
    def prompt_version(self) -> str:
        return self._version

    def build(self, request: PersonalizationRequest, grounded: GroundedProductFacts) -> PromptPackage:
        """Render a privacy-safe prompt package for the given request + grounded product."""
        self._validate_language(request)
        self._validate_channels(request)

        segment_label = self._segment_label(request)
        event_labels = self._event_labels(request)
        reason_labels = self._persuasion_reason_labels(request)

        facts = self._project_facts(grounded)
        allowed_fact_ids = sorted(fact["fact_id"] for fact in facts)
        requested_channels = _ordered_channels(request.preferences.requested_channels)
        channel_names = [channel.value for channel in requested_channels]
        # Paths are relative to the loader root (dynamic {% include %} does not
        # resolve relative to the including template).
        channel_templates = [
            f"{self._version}/channels/{channel.value.lower()}.jinja2" for channel in requested_channels
        ]

        context = {
            "language": request.preferences.language,
            "segment_label": segment_label,
            "event_labels": event_labels,
            "reason_labels": reason_labels,
            "facts": facts,
            "product_tags": grounded.product_tags,
            "channel_names": channel_names,
            "channel_templates": channel_templates,
            "allowed_fact_ids": allowed_fact_ids,
            "limits": LIMITS,
        }

        return PromptPackage(
            prompt_version=self._version,
            system_prompt=self._render(f"{self._version}/system.jinja2", {}),
            user_prompt=self._render(f"{self._version}/personalization.jinja2", context),
            requested_channels=requested_channels,
            allowed_fact_ids=allowed_fact_ids,
            language=request.preferences.language,
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, template_name: str, context: dict) -> str:
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as exc:
            raise PromptTemplateNotFoundError(str(exc.name), self._version) from exc
        except PromptError:
            raise
        except Exception as exc:  # pragma: no cover - jinja render failures
            raise PromptRenderError(f"failed to render template {template_name!r}: {exc}") from exc

    # ------------------------------------------------------------------
    # Safe context projection
    # ------------------------------------------------------------------

    def _validate_language(self, request: PersonalizationRequest) -> None:
        if request.preferences.language.casefold() not in SUPPORTED_LANGUAGES:
            raise PromptContextError(
                f"unsupported language {request.preferences.language!r} "
                f"for prompt version {self._version!r} (supported: {sorted(SUPPORTED_LANGUAGES)})"
            )

    def _validate_channels(self, request: PersonalizationRequest) -> None:
        if not request.preferences.requested_channels:
            raise PromptContextError("no channels requested; cannot render channel output requirements")

    def _segment_label(self, request: PersonalizationRequest) -> str:
        code = request.decision_context.segment_code
        try:
            return SEGMENT_LABELS[code]
        except KeyError:
            raise PromptContextError(f"unknown segment code {code!r} for prompt version {self._version!r}") from None

    def _event_labels(self, request: PersonalizationRequest) -> list[str]:
        labels: list[str] = []
        for event in request.decision_context.recent_events:
            try:
                labels.append(EVENT_LABELS[event.event_type])
            except KeyError:
                raise PromptContextError(
                    f"unknown event type {event.event_type!r} for prompt version {self._version!r}"
                ) from None
        return labels

    def _persuasion_reason_labels(self, request: PersonalizationRequest) -> list[str]:
        """Validate every reason code; return only the persuasion subset."""
        labels: list[str] = []
        for code in request.decision_context.reason_codes:
            try:
                REASON_LABELS[code]
            except KeyError:
                raise PromptContextError(
                    f"unknown reason code {code!r} for prompt version {self._version!r}"
                ) from None
            if code in PERSUASION_REASON_CODES:
                labels.append(REASON_LABELS[code])
        return labels

    def _project_facts(self, grounded: GroundedProductFacts) -> list[dict[str, str]]:
        """Project grounded facts into the prompt; only approved facts appear.

        ``approved_description`` (when present) is surfaced with the stable
        fact ID ``approved_description`` so the LLM can reference it.
        """
        facts: list[dict[str, str]] = [
            {"fact_id": fact.fact_id, "value": fact.value, "category": fact.category.value}
            for fact in grounded.facts
        ]
        if grounded.approved_description:
            facts.append(
                {
                    "fact_id": "approved_description",
                    "value": grounded.approved_description,
                    "category": GroundedFactCategory.DESCRIPTION.value,
                }
            )
        return facts
