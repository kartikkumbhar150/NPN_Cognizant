import os
import json
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

logger = logging.getLogger(__name__)

class GenAIService:
    def __init__(self):
        self.api_key  = (os.environ.get("GROQ_API_KEY") or "").strip()
        self.use_mock = not bool(self.api_key)

        if not self.use_mock:
            self.client = Groq(api_key=self.api_key)

    def generate_marketing_message(self, customer_data, nbo_result, explanation, channel="email", features=None):
        """
        Phase 7: GenAI Personalization.
        Uses structured explanation and outputs strict JSON.
        LLM does NO decisioning here — it only translates reasons into a nice tone.
        """
        first_name = customer_data.get("first_name", "Customer")
        product = nbo_result.get("specific_product", "our services")
        
        # Get customer-facing reasons from ExplainabilityEngine output
        reasons = explanation.get("customer_reasons", [])
        if not reasons:
            reasons = ["This product is well-suited to your current financial needs."]

        # Build portfolio summary from features (v3.0 upgrade)
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
                portfolio_lines.append(f"Insurance: {', '.join(features.held_insurance_categories)}")
            else:
                portfolio_lines.append("Insurance: NONE")
            if features.net_worth_indicator != 0:
                portfolio_lines.append(f"Estimated Net Worth: ₹{features.net_worth_indicator:,.0f}")
        
        portfolio_context = "\n".join(portfolio_lines) if portfolio_lines else "Portfolio data not available."

        # Structured constraints
        max_words = 150 if channel == "email" else 40
        format_instructions = "1 subject line, 1 short greeting, 2 short paragraphs, 1 CTA." if channel == "email" else "1 short sentence, 1 CTA link."

        prompt = f"""You are a world-class banking marketing copywriter.
Write a personalized {channel} for the customer below.

CUSTOMER NAME: {first_name}
RECOMMENDED PRODUCT: {product}

CUSTOMER PORTFOLIO:
{portfolio_context}

WHY WE ARE RECOMMENDING THIS (Use these exact reasons, do not invent new ones):
{chr(10).join(['- ' + r for r in reasons])}

STRICT INSTRUCTIONS:
1. Do NOT invent product features, interest rates, or eligibility claims.
2. Reference the customer's portfolio to make the message feel genuinely personal.
3. Tone: professional, empathetic, clear.
4. Max words: {max_words}
5. Format: {format_instructions}

OUTPUT FORMAT: You MUST return valid JSON exactly matching this schema:
{{
  "subject": "Catchy subject line (or notification title)",
  "body": "The main message body text"
}}
"""

        if self.use_mock:
            return self._mock_llm_call(first_name, product, reasons, channel)
        else:
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a banking marketing API. You only respond with valid JSON.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    model="qwen/qwen3.6-27b",
                    temperature=0.4,
                    max_tokens=300,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content.strip()
                parsed = json.loads(content)
                return f"Subject: {parsed.get('subject', '')}\n\n{parsed.get('body', '')}"
            except Exception as e:
                logger.error(f"GenAI Service Error: {e}")
                return self._mock_llm_call(first_name, product, reasons, channel)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _mock_llm_call(self, first_name, product, reasons, channel):
        """Structured mock fallback when no LLM is available or it fails."""
        reason_text = reasons[0] if reasons else "We believe this will help you achieve your financial goals."
        
        if channel == "email":
            return (
                f"Subject: {first_name}, a personalized recommendation just for you\n\n"
                f"Hi {first_name},\n\n"
                f"{reason_text}\n\n"
                f"We recommend exploring {product} as a way to support your financial journey. "
                f"It's designed to align with your current patterns.\n\n"
                f"Tap here to view the details in your banking app.\n\n"
                f"Best regards,\nNPN Bank"
            )
        else:
            return (
                f"Subject: New Recommendation: {product}\n\n"
                f"Hi {first_name}, {reason_text.lower()} Check out {product} in your app today."
            )
