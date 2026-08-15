"""
groq_service.py — Groq LLM integration for personalised marketing messages
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqService:
    def __init__(self):
        self.api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
        self.use_mock = not bool(self.api_key)
        if not self.use_mock:
            self.client = Groq(api_key=self.api_key)

    def generate_message(self, analysis: dict) -> str:
        """Generate a personalised banking marketing message using Groq LLM."""
        first_name = analysis.get("first_name", "Customer")
        nbo        = analysis.get("next_best_offer", {})
        product    = nbo.get("product", "our recommended product")
        reasons    = nbo.get("reasons", [])
        gaps       = analysis.get("gaps", [])
        ip         = analysis.get("income_profile", {})
        hs         = analysis.get("health_score", {})

        financial_context = self._build_context(ip, hs, gaps)

        prompt = f"""You are a world-class banking marketing copywriter for a premium Indian bank.
Write a personalised, empathetic, and persuasive SHORT email for this customer.

CUSTOMER: {first_name}
FINANCIAL PROFILE:
{financial_context}
RECOMMENDED PRODUCT: {product}
WHY WE RECOMMEND THIS:
{chr(10).join('- ' + r for r in reasons[:2])}

INSTRUCTIONS:
1. Start with: Subject: [catchy personalised subject line]
2. Address the customer as {first_name} — warm, not salesy
3. Reference their actual financial situation using the real numbers above
4. Explain how {product} solves their specific gap
5. Under 150 words. Short paragraphs.
6. End with one clear call-to-action
7. Tone: trusted financial advisor, professional, friendly"""

        if self.use_mock:
            return self._mock_message(first_name, product, nbo.get("gap_code", ""))

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a world-class marketing copywriter for a premium Indian bank."},
                    {"role": "user",   "content": prompt},
                ],
                model="llama-3.1-8b-instant",
                temperature=0.65,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[AI Error: {str(e)}]\n\n" + self._mock_message(first_name, product, nbo.get("gap_code", ""))

    def _build_context(self, ip, hs, gaps):
        lines = []
        if ip.get("monthly_avg_income"):
            lines.append(f"  Monthly Income: Rs.{ip['monthly_avg_income']:,.0f}")
            lines.append(f"  Monthly Savings: Rs.{ip.get('monthly_avg_savings', 0):,.0f} ({ip.get('savings_rate_pct', 0):.1f}%)")
        if hs:
            lines.append(f"  Financial Health: {hs.get('score', 0)}/100 — {hs.get('grade', '')}")
        if gaps:
            lines.append("  Key Gaps:")
            for g in gaps[:2]:
                lines.append(f"    [{g['severity']}/10] {g['title']}")
        return "\n".join(lines)

    def _mock_message(self, first_name, product, gap_code):
        templates = {
            "NO_INVESTMENT": (
                f"Subject: {first_name}, your money deserves to work harder\n\n"
                f"Hi {first_name},\n\n"
                f"Your income is strong, but your investments are not keeping pace. "
                f"Our {product} is a simple, proven way to grow your wealth — "
                f"even starting with Rs.2,000/month makes a real difference over time.\n\n"
                f"Start investing today. It takes less than 5 minutes.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
            "NO_INSURANCE": (
                f"Subject: {first_name}, are you financially protected?\n\n"
                f"Hi {first_name},\n\n"
                f"We noticed you have no active insurance coverage. A single medical emergency "
                f"can significantly impact even strong finances.\n\n"
                f"Our {product} covers hospitalisation and critical illness at a premium that fits your budget.\n\n"
                f"Protect yourself and your family today.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
            "TRAVELLER_NO_CARD": (
                f"Subject: {first_name}, your travel spend should earn you rewards\n\n"
                f"Hi {first_name},\n\n"
                f"You travel frequently — but are you earning anything back? "
                f"Our {product} gives you air miles, free lounge access, and travel insurance "
                f"on every trip you already take.\n\n"
                f"Apply today and make every journey more rewarding.\n\n"
                f"Best regards,\nYour Banking Partner"
            ),
        }
        return templates.get(gap_code, (
            f"Subject: {first_name}, a personalised offer just for you\n\n"
            f"Hi {first_name},\n\n"
            f"Based on your financial profile, we recommend our {product}.\n\n"
            f"Get in touch with your relationship manager or apply online today.\n\n"
            f"Best regards,\nYour Banking Partner"
        ))
