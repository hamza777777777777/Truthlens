import os, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from google import genai
from google.genai import types
from pydantic import BaseModel


class Ping(BaseModel):
    ok: bool


api_key = os.getenv("GEMINI_API_KEY", "").strip()
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

if not api_key:
    print("[ERROR] No API key found in backend/.env")
    sys.exit(1)

print(f"SDK Version: {getattr(genai, '__version__', 'unknown')}")
print(f"Configured Model: {model_name}")

client = genai.Client(api_key=api_key)

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=Ping,
    temperature=0.0,
)

try:
    resp = client.models.generate_content(
        model=model_name,
        contents='Return {"ok": true}',
        config=config,
    )

    # Inspect structure
    candidates = getattr(resp, "candidates", None)
    count = len(candidates) if candidates else 0
    fr = candidates[0].finish_reason if count else None
    content = candidates[0].content if count else None
    parts = content.parts if content else None
    has_text = any(bool(getattr(p, "text", "") and str(getattr(p, "text", "")).strip()) for p in parts) if parts else False
    feedback = getattr(resp, "prompt_feedback", None)
    block = getattr(feedback, "block_reason", None) if feedback else None

    print(f"Candidate Count: {count}")
    print(f"Finish Reason: {fr}")
    print(f"Block Reason: {block if block else 'None'}")
    print(f"Usable Output Parts Exist: {has_text}")

    # Only access .text after confirming safe
    if has_text:
        print(f"response.text (raw): {resp.text!r}")
        print("Live Structured Verification: PASSED")
    else:
        print("[WARN] No usable text parts — response.text NOT accessed (guard works correctly)")

except Exception as exc:
    err = str(exc)
    if api_key in err:
        err = err.replace(api_key, "[REDACTED]")
    print(f"[ERROR] {exc.__class__.__name__}: {err}")
    sys.exit(1)
