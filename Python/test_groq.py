import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

prompt = """You are a senior banking marketing strategist at NPN Bank India.

UPCOMING FESTIVALS & EVENTS:
- Dhanteras: 15 days away

Based on these upcoming events, generate exactly 1 campaign suggestion.

OUTPUT: Return only a valid JSON array."""

try:
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a banking marketing API. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        model="qwen/qwen3.6-27b",
        temperature=0.7,
        max_tokens=8000,
    )
    raw = resp.choices[0].message.content
    print("RAW OUTPUT:")
    with open("output.txt", "w", encoding="utf-8") as f: f.write(raw)
except Exception as e:
    print("ERROR:", e)
