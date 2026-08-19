import os
import json
import logging
import re as _re_gs
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from ai_engine.indian_calendar import get_festival_context_for_prompt

load_dotenv()

logger = logging.getLogger(__name__)

# Hard-cap prompts at ~6 400 tokens (25 600 chars) before sending to Groq
def _trim_prompt(text: str, max_chars: int = 25_600) -> str:
    if len(text) <= max_chars:
        return text
    keep_head = int(max_chars * 0.6)
    keep_tail = max_chars - keep_head
    return text[:keep_head] + "\n...[trimmed]...\n" + text[-keep_tail:]

# ─────────────────────────────────────────────────────────────────────────────
# Time-context helpers (Zomato-style awareness)
# ─────────────────────────────────────────────────────────────────────────────

def _time_context() -> dict:
    """Return rich time context for dynamic marketing personalisation."""
    now   = datetime.now()
    hour  = now.hour
    dow   = now.strftime("%A")           # e.g. "Monday"
    month = now.month

    # Time of day bucket
    if 5 <= hour < 12:
        tod        = "morning"
        tod_hook   = "Start your day with a smart financial move."
    elif 12 <= hour < 17:
        tod        = "afternoon"
        tod_hook   = "A quick afternoon check-in on your finances."
    elif 17 <= hour < 21:
        tod        = "evening"
        tod_hook   = "Unwind and let your money work harder for you."
    else:
        tod        = "night"
        tod_hook   = "Planning for tomorrow? Here's something to consider."

    # Day-of-week flavour
    is_weekend = dow in ("Saturday", "Sunday")
    if is_weekend:
        day_hook = f"It's the weekend — a great time to review your finances."
    elif dow == "Monday":
        day_hook = "New week, new financial goals — let's make Monday count."
    elif dow == "Friday":
        day_hook = "It's Friday! Wrap up the week with a smart financial move."
    else:
        day_hook = f"Happy {dow}!"

    # Season / month flavour
    if month in (1, 2, 3):
        season_context = "It's the start of the year — perfect for setting financial goals."
    elif month in (3, 4):
        season_context = "Tax season is here — great time to maximise 80C savings."
    elif month in (6, 7, 8):
        season_context = "Monsoon season — a quiet time to review your investments."
    elif month in (10, 11):
        season_context = "Festival season — reward yourself smartly with the right card."
    else:
        season_context = ""

    return {
        "time_of_day":      tod,
        "day_of_week":      dow,
        "is_weekend":       is_weekend,
        "hour":             hour,
        "tod_hook":         tod_hook,
        "day_hook":         day_hook,
        "season_context":   season_context,
        "greeting":         f"Good {tod}, {{name}}",
    }



class GenAIService:
    def __init__(self):
        self.api_key  = (os.environ.get("GROQ_API_KEY") or "").strip()
        self.use_mock = not bool(self.api_key)

        if not self.use_mock:
            self.client = Groq(api_key=self.api_key)

    def generate_marketing_message(self, customer_data, nbo_result, explanation, channel="email", features=None):
        """
        Phase 7: GenAI Personalization (v3.0 — Zomato-style time-aware messaging).
        Uses structured explanation + rich time context for hyper-personalised copy.
        LLM does NO decisioning here — it only translates reasons into engaging copy.
        """
        first_name = customer_data.get("first_name", "Customer")
        product    = nbo_result.get("specific_product", "our services")

        # Get customer-facing reasons from ExplainabilityEngine output
        reasons = explanation.get("customer_reasons", [])
        if not reasons:
            reasons = ["This product is well-suited to your current financial needs."]

        # Build portfolio summary from features
        portfolio_lines = []
        if features:
            if features.held_card_names:
                portfolio_lines.append(f"Credit Cards: {', '.join(features.held_card_names)}")
            else:
                portfolio_lines.append("Credit Cards: None")
            if features.held_loan_categories:
                portfolio_lines.append(f"Active Loans: {', '.join(features.held_loan_categories)} (EMI: ₹{features.total_emi_monthly:,.0f}/month)")
            else:
                portfolio_lines.append("Active Loans: None")
            if features.held_investment_categories:
                portfolio_lines.append(f"Investments: {', '.join(features.held_investment_categories)} (Value: ₹{features.total_assets_value:,.0f})")
            else:
                portfolio_lines.append("Investments: NONE")
            if features.held_insurance_categories:
                cover_str = f" | Total cover: ₹{features.total_insurance_cover:,.0f}" if features.total_insurance_cover > 0 else ""
                portfolio_lines.append(f"Insurance: {', '.join(features.held_insurance_categories)}{cover_str}")
            else:
                portfolio_lines.append("Insurance: NONE")
            if features.net_worth_indicator != 0:
                portfolio_lines.append(f"Estimated Net Worth: ₹{features.net_worth_indicator:,.0f}")

        portfolio_context = "\n".join(portfolio_lines) if portfolio_lines else "Portfolio data not available."

        # ── Zomato-style time context ──────────────────────────────────────────
        ctx = _time_context()
        greeting     = ctx["greeting"].format(name=first_name)
        time_summary = (
            f"Time of day: {ctx['time_of_day']} ({ctx['hour']:02d}:00)\n"
            f"Day: {ctx['day_of_week']} ({'Weekend' if ctx['is_weekend'] else 'Weekday'})\n"
            f"Contextual hook: {ctx['tod_hook']}\n"
            f"Day hook: {ctx['day_hook']}"
        )
        if ctx["season_context"]:
            time_summary += f"\nSeasonal note: {ctx['season_context']}"

        # Channel formatting
        max_words = 150 if channel == "email" else 45
        if channel == "email":
            format_instructions = (
                "1 compelling subject line, 1 personalised greeting using the exact time-of-day, "
                "2 short paragraphs, 1 clear CTA button label."
            )
        else:
            format_instructions = (
                "1 short punchy sentence (with a time-aware hook), 1 CTA. Max 2 sentences total."
            )

        # Festival context injection
        festival_context = ""
        try:
            festival_context = get_festival_context_for_prompt()
        except Exception:
            pass

        # Travel-specific features for frequent flyers
        travel_features_block = ""
        if features and hasattr(features, "travel_profile"):
            tp = features.travel_profile
            if tp.get("is_frequent_flyer"):
                travel_features_block = f"""

CUSTOMER TRAVEL PROFILE (use these specifics in the message!):
- Travel frequency: {tp.get('travel_frequency', 'frequent')}
- Flight spend (90 days): ₹{tp.get('flight_spend_90d', 0):,.0f}
- Hotel spend (90 days): ₹{tp.get('hotel_spend_90d', 0):,.0f}
- International transactions: {tp.get('international_txn_count', 0)}
- Avg trip value: ₹{tp.get('avg_trip_value', 0):,.0f}

CARD FEATURES TO HIGHLIGHT (weave these naturally into the message):
- Unlimited complimentary airport lounge access (250+ lounges pan-India)
- Earn 5x miles on every ₹100 spent on flights & hotels
- 10% instant discount on IndiGo & Air India via this card
- Zero forex markup on international transactions
- Complimentary travel insurance up to ₹50 lakh
"""

        prompt = f"""You are a world-class banking marketing copywriter who writes like Zomato — witty, warm, hyper-personalised.
Write a {channel} message for the customer below.

CUSTOMER NAME: {first_name}
RECOMMENDED PRODUCT: {product}

CUSTOMER PORTFOLIO:
{portfolio_context}

TIME & CONTEXT (use this to make the message feel timely and alive):
{time_summary}
Greeting to use: "{greeting}"
{festival_context}
{travel_features_block}
WHY WE ARE RECOMMENDING THIS (use these exact reasons, do not invent new ones):
{chr(10).join(['- ' + r for r in reasons])}

STRICT INSTRUCTIONS:
1. Open with the time-aware greeting above — make it feel like a push notification that arrived at exactly the right moment.
2. Reference the customer's actual portfolio (cards, loans, investments) to make the message feel genuinely personal.
3. Do NOT invent product features, interest rates, or eligibility claims.
4. Tone: witty, warm, conversational — like a smart friend at a bank (Zomato-style).
5. Max words: {max_words}
6. Format: {format_instructions}
7. IMPORTANT: Be SHORT and PUNCHY. Every word must earn its place. Cut anything generic.

OUTPUT FORMAT: Return ONLY valid JSON matching this exact schema:
{{
  "subject": "Catchy subject line or notification title",
  "body": "The main message body text"
}}"""

        if self.use_mock:
            return self._mock_llm_call(first_name, product, reasons, channel, ctx)
        else:
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a banking marketing API that writes personalised messages. Always respond with valid JSON only.",
                        },
                        {
                            "role": "user",
                            "content": _trim_prompt(prompt),
                        },
                    ],
                    model="qwen/qwen3.6-27b",
                    temperature=0.7,
                    max_tokens=1200,
                )
                content = response.choices[0].message.content.strip()
                parsed  = self._extract_json(content)
                if parsed:
                    return f"Subject: {parsed.get('subject', '')}\n\n{parsed.get('body', '')}"
                else:
                    logger.warning("GenAI returned no parseable JSON — using mock fallback")
                    return self._mock_llm_call(first_name, product, reasons, channel, ctx)
            except Exception as e:
                logger.error(f"GenAI Service Error: {e}")
                return self._mock_llm_call(first_name, product, reasons, channel, ctx)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_json(self, text: str) -> dict:
        """Robustly extract a JSON object from model output, even if wrapped in markdown."""
        import re
        # Remove closed <think> blocks
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        
        # Handle unclosed <think> block (model ran out of tokens while thinking)
        if "<think>" in text:
            text = text[:text.index("<think>")]
        if "</think>" in text:
            text = text[text.rindex("</think>") + len("</think>"):]
        
        text = text.strip()
        
        # Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()
        
        if not text:
            return {}
        
        # Robustly extract JSON object ignoring conversational preamble
        match = re.search(r'(\{.*\})', text, flags=re.DOTALL)
        if match:
            text = match.group(1).strip()
            
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _mock_llm_call(self, first_name, product, reasons, channel, ctx=None):
        """Structured mock fallback when no LLM is available or it fails."""
        reason_text = reasons[0] if reasons else "We believe this will help you achieve your financial goals."
        if ctx:
            greeting = ctx["greeting"].format(name=first_name)
            hook     = ctx["tod_hook"]
        else:
            greeting = f"Hi {first_name}"
            hook     = ""

        if channel == "email":
            return (
                f"Subject: {first_name}, a personalized recommendation just for you\n\n"
                f"{greeting}\n\n"
                f"{hook} {reason_text}\n\n"
                f"We recommend exploring {product} — it's designed to align with your current financial patterns.\n\n"
                f"Tap here to view the details in your banking app.\n\n"
                f"Best regards,\nNPN Bank"
            )
        else:
            return (
                f"Subject: New Recommendation: {product}\n\n"
                f"{greeting} {reason_text.lower()} Check out {product} in your app today."
            )

