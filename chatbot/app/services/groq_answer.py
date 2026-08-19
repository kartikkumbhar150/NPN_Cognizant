"""Groq LLM answer generation for the chatbot service.

Takes the fully assembled context (RAG chunks + customer C360 profile +
NBO recommendations) and calls Groq to produce a fluent, personalized
natural-language answer.

Design invariants:
- Groq is called AFTER all retrieval/NBO logic — it only synthesizes.
- If Groq fails or is unavailable, the deterministic compose_answer()
  fallback is used so the chatbot never goes dark.
- The customer's real PII (phone, email, account numbers) is NEVER
  included in the prompt.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_MODEL = "qwen/qwen3.6-27b"


def _strip_think(text: str) -> str:
    """Remove <think>...</think> blocks AND anything before </think> if tag is truncated."""
    # Full block present
    text = re.sub(r"<think>[\s\S]*?</think>", "", text)
    # Truncated block — model ran out of tokens inside <think>
    if "<think>" in text:
        text = text[text.rfind("<think>"):]
        # Remove from <think> to end (nothing useful after)
        text = re.sub(r"<think>[\s\S]*", "", text)
    # If </think> exists without opening tag, strip everything before it
    if "</think>" in text:
        text = text[text.index("</think>") + len("</think>"):]
    return text.strip()


def _build_customer_summary(authorized_context) -> str:
    """Build a concise, PII-free customer summary from the authorized context."""
    if authorized_context is None:
        return ""

    data = getattr(authorized_context, "customer_data", {}) or {}
    features = getattr(authorized_context, "features", None)
    gaps = getattr(authorized_context, "financial_gaps", []) or []
    events = getattr(authorized_context, "events", []) or []

    parts: List[str] = []

    # Demographics (no PII)
    age = data.get("age")
    segment = data.get("customer_segment_type") or data.get("segment")
    credit_score = data.get("credit_score")
    income = data.get("annual_income")

    if age:
        parts.append(f"Age: {age}")
    if segment:
        parts.append(f"Segment: {segment}")
    if credit_score:
        parts.append(f"Credit Score: {credit_score}")
    if income:
        parts.append(f"Annual Income: ₹{int(income):,}")

    # Features
    if features:
        avg_income = getattr(features, "monthly_income_avg", None)
        if avg_income:
            parts.append(f"Avg Monthly Income: ₹{int(avg_income):,}")
        held_cards = getattr(features, "held_card_names", None)
        if held_cards:
            parts.append(f"Current Cards: {', '.join(held_cards)}")
        held_loans = getattr(features, "held_loan_categories", None)
        if held_loans:
            parts.append(f"Active Loans: {', '.join(held_loans)}")

    # Financial gaps
    if gaps:
        gap_codes = [g.get("code", str(g)) for g in gaps[:3]]
        parts.append(f"Financial Gaps: {', '.join(str(g) for g in gap_codes)}")

    # Life events
    if events:
        event_types = [e.get("event_type", str(e)) for e in events[:3]]
        parts.append(f"Detected Life Events: {', '.join(str(e) for e in event_types)}")

    return "\n".join(parts)


def _build_rag_context(chunks: List[Any]) -> str:
    """Format retrieved RAG chunks as numbered knowledge snippets."""
    if not chunks:
        return ""
    lines = []
    for i, chunk in enumerate(chunks[:5], 1):
        title = getattr(chunk, "title", "Knowledge")
        content = getattr(chunk, "content", "") or ""
        lines.append(f"[{i}] {title}\n{content[:400]}")
    return "\n\n".join(lines)


def _build_recommendations_context(recommendations: List[Any]) -> str:
    """Format NBO recommendations as a structured summary."""
    if not recommendations:
        return ""
    lines = []
    for rec in recommendations[:3]:
        name = getattr(rec, "product_name", "Product")
        reason = getattr(rec, "recommendation_text", "") or ""
        lines.append(f"• {name}: {reason[:200]}")
    return "\n".join(lines)


class GroqAnswerService:
    """Generates natural-language answers using Groq (qwen/qwen3.6-27b).

    Usage::

        service = GroqAnswerService()
        answer = service.generate(
            user_message="...",
            intent="PERSONALIZED_RECOMMENDATION",
            rag_chunks=[...],
            authorized_context=ctx,
            recommendations=[...],
            fallback_answer="...",
        )
    """

    def __init__(self) -> None:
        api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
        if api_key:
            from groq import Groq
            self._client = Groq(api_key=api_key)
            self._available = True
            logger.info("GroqAnswerService initialized with model %s", _MODEL)
        else:
            self._client = None
            self._available = False
            logger.warning("GROQ_API_KEY not set — GroqAnswerService will use fallback answers")

    @property
    def available(self) -> bool:
        return self._available

    def generate(
        self,
        user_message: str,
        intent: str,
        rag_chunks: List[Any],
        authorized_context: Optional[Any] = None,
        recommendations: List[Any] = (),
        fallback_answer: str = "",
    ) -> str:
        """Generate a Groq answer. Falls back to *fallback_answer* on error."""
        if not self._available:
            return fallback_answer

        try:
            prompt = self._build_prompt(
                user_message=user_message,
                intent=intent,
                customer_summary=_build_customer_summary(authorized_context),
                rag_context=_build_rag_context(list(rag_chunks)),
                recommendations_context=_build_recommendations_context(list(recommendations)),
            )

            response = self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "/no_think\n"
                            "You are a concise NPN Bank assistant. "
                            "Reply in 1-2 short sentences only. "
                            "Use the provided knowledge and customer context. "
                            "Never invent facts. No markdown, no bullet points, no preamble."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
                temperature=0.3,
            )

            raw = response.choices[0].message.content or ""
            cleaned = _strip_think(raw)
            return cleaned if cleaned else fallback_answer

        except Exception as exc:
            logger.warning("Groq answer generation failed: %s — using fallback", exc)
            return fallback_answer

    def _build_prompt(
        self,
        user_message: str,
        intent: str,
        customer_summary: str,
        rag_context: str,
        recommendations_context: str,
    ) -> str:
        sections: List[str] = [f"Customer question: {user_message}"]

        if customer_summary:
            sections.append(f"--- Customer Profile (internal, do not repeat PII) ---\n{customer_summary}")

        if rag_context:
            sections.append(f"--- Verified Bank Knowledge ---\n{rag_context}")

        if recommendations_context:
            sections.append(f"--- Personalized Product Recommendations ---\n{recommendations_context}")

        sections.append(
            f"Intent classified as: {intent}\n"
            "Please answer the customer's question using the information above. "
            "If recommending a product, briefly explain why it fits the customer."
        )

        return "\n\n".join(sections)
