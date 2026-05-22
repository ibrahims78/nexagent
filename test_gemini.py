import os
from google import genai
from google.genai import types as genai_types
import sys

key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    print("ERROR: GEMINI_API_KEY environment variable not set")
    sys.exit(1)

client = genai.Client(api_key=key)

# List models
print("=== LISTING MODELS ===")
try:
    for m in client.models.list():
        name = getattr(m, 'name', str(m))
        print(name)
except Exception as e:
    print("list error:", e)

# Test candidate models
candidates = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]
print("\n=== TESTING MODELS ===")
for model in candidates:
    try:
        r = client.models.generate_content(model=model, contents="say hi")
        print("OK:", model, "->", r.text[:30])
        break
    except Exception as e:
        print("FAIL:", model, "->", str(e)[:80])
