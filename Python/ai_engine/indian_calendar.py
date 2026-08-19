"""
Indian Calendar
===============
NPN Bank AI Pipeline v3.0

Hardcoded 2025-2026 Indian festival calendar with product affinities.
Returns current and upcoming events to inject festival context into
personalised marketing messages.

No external API calls — fully offline.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

# ── Full 2025-2026 Hindu & Indian National Calendar ──────────────────────────
# Each entry: name, date (YYYY-MM-DD), type, product affinities, tone_hint
INDIAN_EVENTS: List[Dict[str, Any]] = [
    # ── National Days ──────────────────────────────────────────────────────────
    {
        "name": "Republic Day",
        "date": "2026-01-26",
        "type": "national",
        "products": ["NPS", "SIP / Mutual Fund", "Fixed Deposit", "Home Loan"],
        "tone_hint": "patriotic, proud, nation-building",
        "emoji": "🇮🇳",
    },
    {
        "name": "Independence Day",
        "date": "2025-08-15",
        "type": "national",
        "products": ["SIP / Mutual Fund", "NPS", "Home Loan", "Fixed Deposit"],
        "tone_hint": "freedom, new beginnings, aspirational",
        "emoji": "🇮🇳",
    },
    {
        "name": "Gandhi Jayanti",
        "date": "2025-10-02",
        "type": "national",
        "products": ["Fixed Deposit", "NPS", "SIP / Mutual Fund"],
        "tone_hint": "simple, disciplined, savings-focused",
        "emoji": "🕊️",
    },
    # ── Major Hindu Festivals ─────────────────────────────────────────────────
    {
        "name": "Ganesh Chaturthi",
        "date": "2025-08-27",
        "type": "hindu",
        "products": ["Personal Loan", "Home Loan", "Gold Loan", "Credit Card"],
        "tone_hint": "joyful, celebratory, new beginnings",
        "emoji": "🙏",
    },
    {
        "name": "Navratri",
        "date": "2025-10-02",
        "type": "hindu",
        "products": ["Gold Loan", "Credit Card", "Personal Loan"],
        "tone_hint": "festive, energy, shopping, gifting",
        "emoji": "💃",
    },
    {
        "name": "Dussehra",
        "date": "2025-10-02",
        "type": "hindu",
        "products": ["Auto Loan", "Home Loan", "Personal Loan", "Credit Card"],
        "tone_hint": "victory, conquering goals, triumph",
        "emoji": "🏆",
    },
    {
        "name": "Dhanteras",
        "date": "2025-10-20",
        "type": "hindu",
        "products": ["Gold Loan", "Fixed Deposit", "Credit Card", "SIP / Mutual Fund"],
        "tone_hint": "prosperity, wealth, gold, auspicious buying",
        "emoji": "🪙",
    },
    {
        "name": "Diwali",
        "date": "2025-10-21",
        "type": "hindu",
        "products": ["Gold Loan", "Home Loan", "Credit Card", "Personal Loan", "Auto Loan"],
        "tone_hint": "grand celebration, gifting, prosperity, light, shopping",
        "emoji": "🪔",
    },
    {
        "name": "Bhai Dooj",
        "date": "2025-10-23",
        "type": "hindu",
        "products": ["Credit Card", "Personal Loan", "Travel Credit Card"],
        "tone_hint": "family bonds, gifting, love",
        "emoji": "🎁",
    },
    {
        "name": "Chhath Puja",
        "date": "2025-10-28",
        "type": "hindu",
        "products": ["Personal Loan", "Fixed Deposit"],
        "tone_hint": "devotion, simplicity, community",
        "emoji": "🌅",
    },
    {
        "name": "Makar Sankranti / Pongal",
        "date": "2026-01-14",
        "type": "hindu",
        "products": ["Home Loan", "Auto Loan", "Gold Loan", "Fixed Deposit"],
        "tone_hint": "harvest, new beginnings, prosperity, south India",
        "emoji": "🌾",
    },
    {
        "name": "Vasant Panchami",
        "date": "2026-02-02",
        "type": "hindu",
        "products": ["Education Loan", "SIP / Mutual Fund"],
        "tone_hint": "knowledge, learning, spring beginnings",
        "emoji": "📚",
    },
    {
        "name": "Maha Shivratri",
        "date": "2026-02-26",
        "type": "hindu",
        "products": ["Fixed Deposit", "NPS", "Personal Loan"],
        "tone_hint": "spiritual, focused, disciplined",
        "emoji": "🕉️",
    },
    {
        "name": "Holi",
        "date": "2026-03-14",
        "type": "hindu",
        "products": ["Travel Credit Card", "Personal Loan", "Credit Card", "Shopping"],
        "tone_hint": "colorful, fun, playful, joyful, celebrations",
        "emoji": "🎨",
    },
    {
        "name": "Ram Navami",
        "date": "2026-03-29",
        "type": "hindu",
        "products": ["Home Loan", "Personal Loan", "Gold Loan"],
        "tone_hint": "devotion, family values, auspicious",
        "emoji": "🙏",
    },
    {
        "name": "Hanuman Jayanti",
        "date": "2026-04-14",
        "type": "hindu",
        "products": ["Personal Loan", "Fixed Deposit"],
        "tone_hint": "strength, perseverance, dedication",
        "emoji": "💪",
    },
    {
        "name": "Akshaya Tritiya",
        "date": "2026-04-29",
        "type": "hindu",
        "products": ["Gold Loan", "Fixed Deposit", "SIP / Mutual Fund", "Home Loan"],
        "tone_hint": "auspicious investments, gold, eternal prosperity",
        "emoji": "🥇",
    },
    # ── Muslim Festivals ──────────────────────────────────────────────────────
    {
        "name": "Eid ul-Fitr",
        "date": "2026-03-30",
        "type": "muslim",
        "products": ["Gold Loan", "Personal Loan", "Travel Credit Card", "Credit Card"],
        "tone_hint": "celebration, joy, gifting, togetherness",
        "emoji": "🌙",
    },
    {
        "name": "Eid ul-Adha / Bakrid",
        "date": "2026-06-06",
        "type": "muslim",
        "products": ["Gold Loan", "Personal Loan", "Home Loan"],
        "tone_hint": "sacrifice, generosity, faith, family",
        "emoji": "🌙",
    },
    # ── Christian ─────────────────────────────────────────────────────────────
    {
        "name": "Christmas",
        "date": "2025-12-25",
        "type": "christian",
        "products": ["Travel Credit Card", "Credit Card", "Personal Loan"],
        "tone_hint": "gifting, travel, joy, year-end celebrations",
        "emoji": "🎄",
    },
    {
        "name": "New Year",
        "date": "2026-01-01",
        "type": "general",
        "products": ["SIP / Mutual Fund", "NPS", "Fixed Deposit", "Credit Card"],
        "tone_hint": "fresh start, resolutions, financial goals",
        "emoji": "🎊",
    },
    # ── Indian Financial Calendar ─────────────────────────────────────────────
    {
        "name": "Tax Season End",
        "date": "2026-03-31",
        "type": "financial",
        "products": ["NPS", "Fixed Deposit", "SIP / Mutual Fund", "Home Loan"],
        "tone_hint": "tax saving, 80C, last chance, urgency",
        "emoji": "📊",
    },
    {
        "name": "Financial Year Start",
        "date": "2026-04-01",
        "type": "financial",
        "products": ["SIP / Mutual Fund", "NPS", "Fixed Deposit", "Life Insurance"],
        "tone_hint": "fresh financial year, new investments, planning",
        "emoji": "📈",
    },
    {
        "name": "Mid-Year Review",
        "date": "2025-09-30",
        "type": "financial",
        "products": ["SIP / Mutual Fund", "Fixed Deposit", "NPS"],
        "tone_hint": "portfolio review, rebalancing, planning",
        "emoji": "📋",
    },
]


def get_upcoming_events(
    reference_date: Optional[date] = None,
    lookahead_days: int = 30,
    max_events: int = 3,
) -> List[Dict[str, Any]]:
    """
    Return the next N events occurring within `lookahead_days` from `reference_date`.
    Each event includes a `days_away` field.
    """
    ref = reference_date or date.today()
    window_end = ref + timedelta(days=lookahead_days)

    upcoming = []
    for ev in INDIAN_EVENTS:
        try:
            ev_date = date.fromisoformat(ev["date"])
        except (ValueError, KeyError):
            continue

        # Handle events from previous year cycle (look at next occurrence)
        if ev_date < ref:
            # Try next year
            ev_date = ev_date.replace(year=ev_date.year + 1)

        if ref <= ev_date <= window_end:
            days_away = (ev_date - ref).days
            upcoming.append({
                **ev,
                "date": ev_date.isoformat(),
                "days_away": days_away,
                "is_today": days_away == 0,
                "is_imminent": days_away <= 3,
            })

    upcoming.sort(key=lambda x: x["days_away"])
    return upcoming[:max_events]


def get_current_event(reference_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """Return an event if today is within ±1 day of a festival."""
    ref = reference_date or date.today()
    for ev in INDIAN_EVENTS:
        try:
            ev_date = date.fromisoformat(ev["date"])
        except (ValueError, KeyError):
            continue
        if abs((ev_date - ref).days) <= 1:
            return {**ev, "days_away": (ev_date - ref).days}
    return None


def get_festival_context_for_prompt(reference_date: Optional[date] = None) -> str:
    """
    Build a compact festival context string suitable for injecting into LLM prompts.
    Returns empty string if no relevant events found.
    """
    ref = reference_date or date.today()
    current = get_current_event(ref)
    upcoming = get_upcoming_events(ref, lookahead_days=30, max_events=2)

    lines = []

    if current:
        lines.append(
            f"TODAY IS {current['name'].upper()} {current['emoji']} — "
            f"Use festive energy in your message! "
            f"Tone: {current['tone_hint']}."
        )

    for ev in upcoming:
        if current and ev["name"] == current["name"]:
            continue  # skip duplicate
        if ev["days_away"] == 0:
            continue
        lines.append(
            f"Upcoming: {ev['emoji']} {ev['name']} in {ev['days_away']} days — "
            f"Subtly reference this if relevant. Tone: {ev['tone_hint']}."
        )

    return "\n".join(lines) if lines else ""


def get_campaign_suggestions_by_events(reference_date: Optional[date] = None) -> List[Dict]:
    """
    Returns campaign suggestions based on upcoming events.
    Used by the AI Campaign Suggester endpoint.
    """
    ref = reference_date or date.today()
    upcoming = get_upcoming_events(ref, lookahead_days=45, max_events=5)
    suggestions = []
    for ev in upcoming:
        for product in ev.get("products", [])[:2]:  # top 2 products per event
            suggestions.append({
                "product": product,
                "urgency": "high" if ev["days_away"] <= 7 else ("medium" if ev["days_away"] <= 21 else "low"),
                "festival_hook": ev["name"],
                "festival_emoji": ev["emoji"],
                "days_away": ev["days_away"],
                "tone_hint": ev["tone_hint"],
            })
    return suggestions
