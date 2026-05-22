import os
import urllib.request
import json

key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    print("ERROR: GEMINI_API_KEY environment variable not set")
    import sys; sys.exit(1)

url = 'https://generativelanguage.googleapis.com/v1beta/models?key=' + key
r = urllib.request.urlopen(url, timeout=15)
data = json.loads(r.read())
[print(m['name']) for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
