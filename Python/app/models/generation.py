"""Structured provider-output model for Phase 6 generation.

``GeneratedContent`` is what an LLM provider returns: per-channel marketing
copy keyed by channel. It reuses the DS-01 channel content models
(``PushContent``, ``SmsContent``, ``EmailContent``, ``InAppContent``,
``RelationshipManagerContent``) so the same schema is not duplicated.

Unlike DS-01's ``ChannelContent`` (which requires all five channels), only the
requested channels are populated here — the provider boundary must not emit
content for channels the customer did not request.
"""

from pydantic import model_validator

from app.models.personalization import Channel, StrictModel
from app.models.personalization import (
    EmailContent,
    InAppContent,
    PushContent,
    RelationshipManagerContent,
    SmsContent,
)


class GeneratedContent(StrictModel):
    """Structured generation output; at least one channel must be present."""

    push: PushContent | None = None
    sms: SmsContent | None = None
    email: EmailContent | None = None
    in_app: InAppContent | None = None
    relationship_manager: RelationshipManagerContent | None = None

    @model_validator(mode="after")
    def _at_least_one_channel(self) -> "GeneratedContent":
        if not any(
            (
                self.push,
                self.sms,
                self.email,
                self.in_app,
                self.relationship_manager,
            )
        ):
            raise ValueError("generated content contains no channel output")
        return self

    def populated_channels(self) -> list[Channel]:
        """Channels that have content, in the canonical Phase 6 order."""
        present = {
            Channel.PUSH: self.push,
            Channel.SMS: self.sms,
            Channel.EMAIL: self.email,
            Channel.IN_APP: self.in_app,
            Channel.RELATIONSHIP_MANAGER: self.relationship_manager,
        }
        return [channel for channel, content in present.items() if content is not None]
