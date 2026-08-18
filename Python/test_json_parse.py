import json
import re
from ai_engine.genai_service import GenAIService

svc = GenAIService()
client = svc.client

prompt = '''You are a world-class banking marketing copywriter who writes like Zomato \u2014 witty, warm, hyper-personalised.
Write a email message for the customer below.

CUSTOMER NAME: Kartik
RECOMMENDED PRODUCT: Freedom Credit Card

CUSTOMER PORTFOLIO:
Portfolio data not available.

TIME & CONTEXT (use this to make the message feel timely and alive):
Time of day: afternoon (13:00)
Day: Tuesday (Weekday)
Contextual hook: A quick afternoon check-in on your finances.
Day hook: Happy Tuesday!
Greeting to use: "Good afternoon, Kartik"

WHY WE ARE RECOMMENDING THIS (use these exact reasons, do not invent new ones):
- You have good income

STRICT INSTRUCTIONS:
1. Open with the time-aware greeting above \u2014 make it feel like a push notification that arrived at exactly the right moment.
2. Reference the customer's actual portfolio (cards, loans, investments) to make the message feel genuinely personal.
3. Do NOT invent product features, interest rates, or eligibility claims.
4. Tone: witty, warm, conversational \u2014 like a smart friend at a bank (Zomato-style).
5. Max words: 150
6. Format: 1 compelling subject line, 1 personalised greeting using the exact time-of-day, 2 short paragraphs, 1 clear CTA button label.

OUTPUT FORMAT: Return ONLY valid JSON matching this exact schema:
{
  "subject": "Catchy subject line or notification title",
  "body": "The main message body text"
}
'''
try:
    response = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': 'You are a banking marketing API that writes personalised messages. Always respond with valid JSON only.'},
            {'role': 'user', 'content': prompt},
        ],
        model='qwen/qwen3.6-27b',
        temperature=0.7,
        max_tokens=400,
    )
    content = response.choices[0].message.content.strip()
    safe_content = content.encode('ascii', errors='replace').decode('ascii')
    print('RAW OUTPUT:')
    print(safe_content)

    content2 = re.sub(r'^```(?:json)?\s*', '', content, flags=re.MULTILINE)
    content2 = re.sub(r'```\s*$', '', content2, flags=re.MULTILINE).strip()
    safe_content2 = content2.encode('ascii', errors='replace').decode('ascii')
    print('\nSTRIPPED:')
    print(safe_content2)
except Exception as e:
    print('Error:', e)
