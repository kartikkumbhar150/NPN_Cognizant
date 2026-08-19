"""
NPN Bank — Marketing Templates
==============================
Provides:
  - pick_marketing_image(product)  → filename from /app/marketing_images/
  - build_html_email(...)          → gorgeous HTML email with embedded image
  - build_sms_body(...)            → punchy 160-char SMS
  - PRODUCT_FACTS dict             → short product info bullets for each category
"""

import os
import re
import base64
from pathlib import Path

# ── Image directory (inside Docker container) ─────────────────────────────────
MARKETING_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "marketing images")

# ── Product → image mapping ───────────────────────────────────────────────────
_IMAGE_MAP = {
    # Credit Cards
    "credit card":        "credit_card.jpeg",
    "regalia":            "credit_card.jpeg",
    "millennia":          "credit_card.jpeg",
    "moneyback":          "credit_card.jpeg",
    "cashback":           "credit_card.jpeg",
    "freedom":            "credit_card.jpeg",
    "travel card":        "travel_credit_card.jpeg",
    "travel credit":      "travel_credit_card.jpeg",
    "diners":             "travel_credit_card.jpeg",
    "infinia":            "travel_credit_card.jpeg",
    "business card":      "credit_card.jpeg",
    # Loans
    "personal loan":      "loan.jpeg",
    "personal":           "loan.jpeg",
    "home loan":          "home_loan.jpeg",
    "home":               "home_loan.jpeg",
    "housing":            "home_loan2.jpeg",
    "car loan":           "car_loan2.jpeg",
    "auto loan":          "car_loan2.jpeg",
    "vehicle loan":       "car_loan2.jpeg",
    "education loan":     "loan.jpeg",
    "loan against":       "loan.jpeg",
    "gold loan":          "loan.jpeg",
    "business loan":      "loan.jpeg",
    # Investments
    "mutual fund":        "mutual_funds.jpeg",
    "mutual funds":       "mutual_funds.jpeg",
    "sip":                "mutual_funds.jpeg",
    "fixed deposit":      "mutual_funds.jpeg",
    "fd":                 "mutual_funds.jpeg",
    "recurring deposit":  "mutual_funds.jpeg",
    "rd":                 "mutual_funds.jpeg",
    "savings":            "mutual_funds.jpeg",
    "investment":         "mutual_funds.jpeg",
    # Insurance
    "insurance":          "loan.jpeg",
    "life insurance":     "loan.jpeg",
    "health insurance":   "loan.jpeg",
    "term insurance":     "loan.jpeg",
}


def pick_marketing_image(product: str) -> str:
    """Return the best-matching image filename for the given product name."""
    product_lower = product.lower()
    for keyword, filename in _IMAGE_MAP.items():
        if keyword in product_lower:
            return filename
    # Default fallback
    return "loan.jpeg"


def _image_to_data_uri(filename: str) -> str:
    """Encode an image file as a base64 data URI for inline embedding in emails."""
    path = os.path.join(MARKETING_IMAGES_DIR, filename)
    if not os.path.exists(path):
        return ""
    ext = Path(filename).suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{mime};base64,{data}"


# ── Product facts ─────────────────────────────────────────────────────────────
PRODUCT_FACTS = {
    "credit card": [
        "💳 Earn up to 5X reward points on every spend",
        "🎁 Welcome bonus: ₹1,000 worth gift vouchers",
        "✈️ Free airport lounge access (domestic & international)",
        "🛡️ Zero fraud liability — you're always protected",
        "📱 Tap & Pay with NFC — no PIN needed under ₹5,000",
    ],
    "personal loan": [
        "💰 Borrow up to ₹40 Lakhs — no collateral needed",
        "⚡ Instant disbursal in 24 hours post-approval",
        "📅 Flexible tenure: 12 to 60 months",
        "📉 Competitive rates starting at 10.5% p.a.",
        "📄 Minimal documentation — just 2 ID proofs",
    ],
    "home loan": [
        "🏠 Finance up to 90% of property value",
        "📉 Interest rates starting at 8.5% p.a.",
        "📅 Tenure up to 30 years — EMIs that fit your pocket",
        "⚡ Quick approval in 3 working days",
        "📄 Free property valuation & legal check",
    ],
    "car loan": [
        "🚗 Finance 100% of the on-road price",
        "📉 Rates from 7.9% p.a. — lowest in the market",
        "📅 Tenure: 12 to 84 months — you choose",
        "⚡ Approval in 4 hours flat",
        "🎁 Zero processing fee for the first 30 applicants",
    ],
    "mutual fund": [
        "📈 SIPs starting at just ₹500/month",
        "🌱 Power of compounding — start early, retire rich",
        "🔀 Diversified across 200+ hand-picked funds",
        "🛡️ SEBI-regulated — your money is in safe hands",
        "📱 Track & manage in your app — 24×7",
    ],
    "insurance": [
        "🛡️ Cover up to ₹1 Crore at ₹500/month",
        "⚡ Paperless claim settlement in 24 hours",
        "🏥 Cashless treatment at 5,000+ hospitals",
        "👨‍👩‍👧 Family floater plans available",
        "📄 No medical test for cover up to ₹50 Lakhs",
    ],
    "travel card": [
        "✈️ 5X miles on every flight & hotel booking",
        "🛋️ Free access to 300+ airport lounges",
        "🌍 Zero forex markup on international transactions",
        "🛡️ Complimentary travel insurance up to ₹50 Lakhs",
        "🚨 24×7 global concierge & emergency assistance",
    ],
    "fixed deposit": [
        "📈 Up to 8.05% p.a. interest rate",
        "⏰ Tenure from 7 days to 10 years",
        "🛡️ DICGC insured up to ₹5 Lakhs",
        "💸 Monthly interest payout option available",
        "🔒 Loan against FD up to 90% of deposit value",
    ],
}


def _get_product_facts(product: str) -> list[str]:
    """Return the product facts list for the given product name."""
    product_lower = product.lower()
    for key in PRODUCT_FACTS:
        if key in product_lower:
            return PRODUCT_FACTS[key]
    # Guess from keywords
    if any(k in product_lower for k in ("card", "regalia", "millennia", "cashback")):
        return PRODUCT_FACTS["credit card"]
    if any(k in product_lower for k in ("loan",)):
        return PRODUCT_FACTS["personal loan"]
    if any(k in product_lower for k in ("fund", "sip", "invest")):
        return PRODUCT_FACTS["mutual fund"]
    if any(k in product_lower for k in ("insure", "policy", "cover")):
        return PRODUCT_FACTS["insurance"]
    return PRODUCT_FACTS["personal loan"]


# ── Quirky taglines per category ─────────────────────────────────────────────
_TAGLINES = {
    "credit card": [
        "Your wallet called. It said it's embarrassed by your current card. 😬",
        "Still paying with a card that gives NO rewards? Bold. Stupid, but bold.",
        "Spending money is an art. You've been using crayons. Time to upgrade. 🖌️",
    ],
    "personal loan": [
        "Your dreams cost money. Your excuses don't. Time to fix that.",
        "You've been broke long enough. Let's do something about it. 💸",
        "Plot twist: your dreams CAN be funded. We checked. You qualify. 😮",
    ],
    "home loan": [
        "Still paying rent to your landlord's holiday fund? Enough. 🏠",
        "Your current address: someone else's asset. Let's fix that. 🔑",
        "Imagine: YOUR name on the doorbell. We make it possible.",
    ],
    "car loan": [
        "Still Ola-ing everywhere? Your dignity called. It's asking for a car. 🚗",
        "The auto driver knows your face better than your own family. Time for a car.",
        "Public transport builds character. You have enough. Get the car. 🚀",
    ],
    "mutual fund": [
        "Your money is napping in a savings account. Wake it up. 📈",
        "Inflation is eating your savings like it skipped lunch. SIP karo. 🌱",
        "Your money should work harder than you. Currently, it's unemployed.",
    ],
    "insurance": [
        "You insure your phone but not your life? Bold priorities, mate. 🛡️",
        "The universe doesn't send calendar invites for emergencies. Be ready.",
        "Plot twist: the biggest risk is thinking 'nothing will happen to me'. 😅",
    ],
    "travel card": [
        "You travel like a king but your wallet cries at every forex charge. Fix that. ✈️",
        "Paying forex markup is just donating to the airport. Stop it. 🌍",
        "Free lounge access, 5X miles, zero markup. Your current card does WHAT exactly?",
    ],
    "fixed deposit": [
        "Your savings account earns 3%. A FD earns 8%. Pick a side. 📊",
        "Keeping money idle in a savings account is criminal. We have options.",
        "Money that doesn't grow is just money that shrinks slowly. Think about it.",
    ],
}


def _get_tagline(product: str, first_name: str) -> str:
    """Pick a witty tagline based on product type."""
    product_lower = product.lower()
    for key, lines in _TAGLINES.items():
        if key in product_lower:
            # Rotate based on name hash for variety
            idx = hash(first_name) % len(lines)
            return lines[idx]
    idx = hash(first_name) % len(_TAGLINES["personal loan"])
    return _TAGLINES["personal loan"][idx]


# ── HTML Email template ───────────────────────────────────────────────────────
def build_html_email(
    first_name: str,
    product: str,
    body_text: str,
    age_group: str = "millennial",
    cta_url: str = "https://npnbank.in/apply",
) -> str:
    """Build a full HTML email with inline image, product facts, and quirky tagline."""
    image_file = pick_marketing_image(product)
    image_data_uri = _image_to_data_uri(image_file)
    tagline = _get_tagline(product, first_name)
    facts = _get_product_facts(product)
    facts_html = "\n".join(
        f'<tr><td style="padding:6px 0;font-size:15px;color:#1a1a2e;">{fact}</td></tr>'
        for fact in facts
    )

    # Color scheme based on age group
    if age_group == "genz":
        primary = "#6C63FF"
        accent  = "#FF6584"
        bg      = "#0f0f1a"
        text_c  = "#ffffff"
    elif age_group == "boomer":
        primary = "#003366"
        accent  = "#cc9900"
        bg      = "#f4f4f4"
        text_c  = "#1a1a1a"
    else:  # millennial / genx
        primary = "#1B4F72"
        accent  = "#F39C12"
        bg      = "#f8f9fa"
        text_c  = "#1a1a2e"

    image_section = ""
    if image_data_uri:
        image_section = f"""
        <tr>
          <td align="center" style="padding:0 0 20px 0;">
            <img src="{image_data_uri}"
                 alt="{product} — NPN Bank"
                 style="max-width:100%;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.15);" />
          </td>
        </tr>"""

    # Convert plain body_text paragraphs to HTML paragraphs
    body_html = "".join(
        f'<p style="font-size:16px;line-height:1.7;color:{text_c};margin:0 0 12px 0;">{para.strip()}</p>'
        for para in body_text.strip().split("\n\n") if para.strip()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NPN Bank — {product}</title>
</head>
<body style="margin:0;padding:0;background-color:{bg};font-family:'Segoe UI',Helvetica,Arial,sans-serif;">

  <!-- Outer wrapper -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
         style="background-color:{bg};padding:30px 15px;">
    <tr><td align="center">

      <!-- Card -->
      <table role="presentation" cellpadding="0" cellspacing="0"
             width="600" style="max-width:600px;background:#ffffff;border-radius:20px;
             overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.12);">

        <!-- Header banner -->
        <tr>
          <td style="background:linear-gradient(135deg,{primary} 0%,{accent} 100%);
                     padding:30px 40px;text-align:center;">
            <p style="margin:0 0 6px 0;font-size:13px;font-weight:700;letter-spacing:3px;
                      color:rgba(255,255,255,0.75);text-transform:uppercase;">NPN Bank</p>
            <h1 style="margin:0;font-size:28px;font-weight:800;color:#ffffff;line-height:1.2;">
              {product}
            </h1>
            <p style="margin:10px 0 0 0;font-size:15px;color:rgba(255,255,255,0.9);
                      font-style:italic;">
              {tagline}
            </p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">

              <!-- Greeting -->
              <tr>
                <td style="padding-bottom:20px;">
                  <p style="margin:0;font-size:22px;font-weight:700;color:{primary};">
                    Hey {first_name}! 👋
                  </p>
                </td>
              </tr>

              <!-- Product image -->
              {image_section}

              <!-- Body text -->
              <tr>
                <td style="padding-bottom:24px;">
                  {body_html}
                </td>
              </tr>

              <!-- Divider -->
              <tr>
                <td style="padding-bottom:24px;">
                  <hr style="border:none;border-top:2px solid #f0f0f0;margin:0;">
                </td>
              </tr>

              <!-- Product facts -->
              <tr>
                <td style="padding-bottom:24px;">
                  <p style="margin:0 0 14px 0;font-size:17px;font-weight:700;color:{primary};">
                    ✨ Why {product}?
                  </p>
                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                         style="background:#f8f9fa;border-radius:12px;padding:16px 20px;">
                    {facts_html}
                  </table>
                </td>
              </tr>

              <!-- CTA button -->
              <tr>
                <td align="center" style="padding-bottom:28px;">
                  <a href="{cta_url}"
                     style="display:inline-block;background:linear-gradient(135deg,{primary} 0%,{accent} 100%);
                            color:#ffffff;text-decoration:none;font-size:18px;font-weight:700;
                            padding:16px 44px;border-radius:50px;letter-spacing:0.5px;
                            box-shadow:0 4px 15px rgba(0,0,0,0.2);">
                    Apply Now — Takes 2 mins ⚡
                  </a>
                </td>
              </tr>

              <!-- Disclaimer -->
              <tr>
                <td>
                  <p style="margin:0;font-size:12px;color:#999;text-align:center;line-height:1.5;">
                    This is a personalised offer from NPN Bank for {first_name}.<br>
                    T&amp;C apply. Subject to credit approval.<br>
                    <a href="https://npnbank.in/unsubscribe" style="color:#999;">Unsubscribe</a>
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:{primary};padding:20px 40px;text-align:center;">
            <p style="margin:0 0 4px 0;font-size:14px;color:rgba(255,255,255,0.9);font-weight:600;">
              NPN Bank — Your Financial Ally
            </p>
            <p style="margin:0;font-size:12px;color:rgba(255,255,255,0.6);">
              📞 1800-NPN-BANK &nbsp;|&nbsp; 🌐 npnbank.in &nbsp;|&nbsp; 📍 Pan India
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

</body>
</html>"""


# ── SMS template ──────────────────────────────────────────────────────────────
_SMS_TAGLINES = {
    "credit card": [
        "ur card is collecting dust. upgrade?",
        "no rewards = no point. get the right card",
        "FREE lounges. 5X points. ur card does WHAT?",
    ],
    "personal loan": [
        "broke? we fix that.",
        "dreams > bank balance. we bridge the gap",
        "₹40L in 24hrs. no collateral. for real.",
    ],
    "home loan": [
        "paying rent = paying ur landlord's EMI. stop.",
        "ur dream home at 8.5% p.a. apply now.",
        "live in YOUR house. not someone else's.",
    ],
    "car loan": [
        "no more autowala's face. get a car.",
        "7.9% car loan. ur commute called for help.",
        "100% on-road finance. drive home today.",
    ],
    "mutual fund": [
        "savings acc: 3%. our FD/SIP: 8%+. pick one.",
        "SIP ₹500/mo. retire rich. it's maths.",
        "ur money is sleeping. wake it up.",
    ],
    "insurance": [
        "u insure ur phone. not ur life. priorities?",
        "₹500/mo = ₹1Cr cover. genius or nahi?",
        "emergencies don't RSVP. be ready.",
    ],
    "travel card": [
        "forex markup is daylight robbery. we stopped it.",
        "5X miles + free lounges. ur card does zilch.",
        "globe-trotter life. broke-tourist card. fix it.",
    ],
    "fixed deposit": [
        "8.05% p.a. ur savings acc gives 3%. do the math.",
        "FD > sleeping money. always.",
        "safe. guaranteed. 8% returns. apply now.",
    ],
}


def build_sms_body(
    first_name: str,
    product: str,
    body_text: str,
    max_chars: int = 160,
) -> str:
    """
    Build a punchy, witty SMS message (max_chars chars).
    Format: [TAGLINE] [KEY FACT] [CTA]
    """
    product_lower = product.lower()
    taglines = _SMS_TAGLINES.get("credit card", _SMS_TAGLINES["personal loan"])
    for key, lines in _SMS_TAGLINES.items():
        if key in product_lower:
            taglines = lines
            break

    tagline = taglines[hash(first_name) % len(taglines)]
    facts = _get_product_facts(product)
    # Strip emoji for SMS and take first fact
    first_fact = re.sub(r"[^\x00-\x7F]+", "", facts[0]).strip().lstrip("- ")

    cta = "Apply: npnbank.in/apply"

    full = f"{first_name}! {tagline} | {first_fact} | {cta}"
    if len(full) <= max_chars:
        return full

    # Trim fact if too long
    budget = max_chars - len(f"{first_name}! {tagline} | ... | {cta}")
    trimmed_fact = first_fact[:max(10, budget)]
    full = f"{first_name}! {tagline} | {trimmed_fact}... | {cta}"
    return full[:max_chars]
