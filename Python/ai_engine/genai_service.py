import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file


class GenAIService:
    def __init__(self):
        self.api_key  = (os.environ.get("GROQ_API_KEY") or "").strip()
        self.use_mock = not bool(self.api_key)

        if not self.use_mock:
            self.client = Groq(api_key=self.api_key)

    def generate_marketing_message(self, customer_data, nbo_result, financial_analysis=None):
        """Phase 7: GenAI Personalization — uses real financial context when available."""

        first_name = customer_data.get("first_name", "Customer")
        product    = nbo_result["specific_product"]
        reasons    = nbo_result.get("reasons", [])

        # Build rich financial context block for the prompt
        financial_context = self._build_financial_context(financial_analysis)

        prompt = f"""You are a world-class banking marketing copywriter working for a premium Indian bank.
Write a highly personalised, empathetic, and persuasive email for the customer below.

CUSTOMER FINANCIAL PROFILE:
{financial_context}

RECOMMENDED PRODUCT: {product}

WHY WE ARE RECOMMENDING THIS:
{chr(10).join(['- ' + r for r in reasons])}

WRITING INSTRUCTIONS:
1. Start with: Subject: [catchy, personalised subject line]
2. Address the customer as {first_name} — be warm, not salesy.
3. Reference their ACTUAL financial situation (use the real numbers from the profile above).
4. Explain how {product} directly solves their specific gap.
5. Keep the email body under 160 words. Use short paragraphs.
6. End with a single, clear call-to-action.
7. Do NOT invent product features. Be honest and direct.
8. Tone: professional, friendly, empathetic — like a trusted financial advisor."""

        if self.use_mock:
            return self._mock_llm_call(customer_data, nbo_result, financial_analysis).replace("\r", "")
        else:
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a world-class marketing copywriter for a premium Indian bank. You write personalised, data-driven, empathetic emails.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.65,
                    max_tokens=400,
                )
                return response.choices[0].message.content.strip().replace("\r", "")
            except Exception as e:
                fallback = self._mock_llm_call(customer_data, nbo_result, financial_analysis)
                return (f"[Groq API Error] {str(e)}\n\nFallback Message:\n" + fallback).replace("\r", "")

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _build_financial_context(self, analysis):
        """Convert financial analysis dict into a readable context string for the LLM."""
        if not analysis:
            return "  (No detailed financial analysis available)"

        ip  = analysis.get("income_profile", {})
        sp  = analysis.get("spending_profile", {})
        hs  = analysis.get("health_score", {})
        gaps = analysis.get("gaps", [])

        lines = []

        monthly_income = ip.get("monthly_avg_income", 0)
        if monthly_income:
            lines.append(f"  Monthly Income: Rs.{monthly_income:,.0f}")
            lines.append(f"  Annual Income (observed): Rs.{ip.get('annual_income_observed', 0):,.0f}")

        monthly_spend = sp.get("monthly_total_spend", 0)
        savings_rate  = sp.get("savings_rate", 0)
        if monthly_spend:
            lines.append(f"  Monthly Spending: Rs.{monthly_spend:,.0f}")
            lines.append(f"  Monthly Savings: Rs.{sp.get('monthly_savings', 0):,.0f} ({savings_rate*100:.1f}% savings rate)")

        cat = sp.get("category_breakdown", {})
        if cat:
            lines.append("  Category breakdown (monthly average):")
            for c, d in sorted(cat.items(), key=lambda x: x[1]["monthly_avg"], reverse=True):
                lines.append(f"    - {c}: Rs.{d['monthly_avg']:,.0f} ({d['pct_of_income']*100:.1f}% of income)")

        if hs:
            lines.append(f"  Financial Health Score: {hs.get('score', 0)}/100 — {hs.get('grade', 'Unknown')}")

        if gaps:
            lines.append("  Key Financial Gaps Detected:")
            for g in gaps[:3]:
                lines.append(f"    [{g['severity']}/10] {g['title']}")

        return "\n".join(lines) if lines else "  (No detailed financial analysis available)"

    def _mock_llm_call(self, customer_data, nbo_result, financial_analysis=None):
        """Gap-aware mock message when no LLM is available."""
        first_name = customer_data.get("first_name", "there")
        product    = nbo_result["specific_product"]
        gap_code   = nbo_result.get("gap_code", "")

        # Gap-specific mock templates
        templates = {
            "NO_INVESTMENT": lambda: (
                f"Subject: {first_name}, your money is sitting idle — let's change that\n\n"
                f"Hi {first_name},\n\n"
                f"We noticed something important: you have a strong, regular income but your money isn't working for you.\n\n"
                f"A {product} is a simple, low-risk way to start building real wealth — even starting at just Rs.2,000/month can make a significant difference over time.\n\n"
                f"We've pre-selected a plan that matches your income level. Takes less than 5 minutes to get started.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
            "NO_INSURANCE": lambda: (
                f"Subject: {first_name}, are you financially protected if something goes wrong?\n\n"
                f"Hi {first_name},\n\n"
                f"We've noticed you have no active insurance coverage. With the healthcare costs you've already incurred, "
                f"a single medical emergency could significantly impact your finances.\n\n"
                f"Our {product} covers hospitalisation, critical illness, and more — at a premium that fits your budget.\n\n"
                f"Protect yourself and your family today.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
            "TRAVELLER_NO_CARD": lambda: (
                f"Subject: {first_name}, you're spending a lot on travel — are you earning rewards?\n\n"
                f"Hi {first_name},\n\n"
                f"You're clearly a frequent traveller, but your spending isn't earning you anything back.\n\n"
                f"Our {product} gives you air miles on every booking, free lounge access, and travel insurance — "
                f"all on money you're already spending.\n\n"
                f"Apply today and make every trip more rewarding.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
            "CRITICAL_SAVINGS": lambda: (
                f"Subject: {first_name}, a small step today can secure your tomorrow\n\n"
                f"Hi {first_name},\n\n"
                f"We've noticed your monthly savings are lower than they could be. "
                f"A {product} is a simple, safe way to lock in a portion of your income each month — "
                f"so you build a financial cushion without even thinking about it.\n\n"
                f"Guaranteed returns, zero market risk.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
        }

        template_fn = templates.get(gap_code)
        if template_fn:
            return template_fn()

        # Generic fallback
        reasons = nbo_result.get("reasons", ["We think this is the right fit for you."])
        return (
            f"Subject: {first_name}, a personalised offer just for you\n\n"
            f"Hi {first_name},\n\n"
            f"Based on your financial profile, we'd like to recommend our {product}.\n\n"
            f"{reasons[0]}\n\n"
            f"Get in touch with your relationship manager or apply online today.\n\n"
            f"Best regards,\nYour Banking Partner"
        )
