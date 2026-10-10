import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Resolve and load backend/.env
backend_root = Path(__file__).resolve().parent.parent
load_dotenv(backend_root / ".env")

from google import genai
from google.genai import types
from pydantic import BaseModel


class SmokeTestSchema(BaseModel):
    status: str
    model_echo: str


def run_smoke_test():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    sdk_version = getattr(genai, "__version__", "unknown")

    print(f"SDK Version: {sdk_version}")
    print(f"Configured Model: {model_name}")

    if not api_key:
        print("API Call Succeeded: False")
        print("Response Status/Error Category: Authentication / Missing GEMINI_API_KEY in backend/.env")
        print("Structured JSON Generation Supported: Untested (API key required)")
        return False

    try:
        client = genai.Client(api_key=api_key)

        # Minimal generation request testing structured output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SmokeTestSchema,
            temperature=0.0,
        )

        response = client.models.generate_content(
            model=model_name,
            contents="Return a JSON object with status 'ok' and model_echo equal to the model name.",
            config=config,
        )

        print("API Call Succeeded: True")
        print("Response Status/Error Category: 200 OK")
        print(f"Structured JSON Generation Supported: True")
        return True

    except Exception as exc:
        err_type = exc.__class__.__name__
        err_msg = str(exc)
        # Redact any accidental key leakage in error text
        if api_key and api_key in err_msg:
            err_msg = err_msg.replace(api_key, "[REDACTED]")

        print("API Call Succeeded: False")
        print(f"Response Status/Error Category: {err_type}: {err_msg}")
        print("Structured JSON Generation Supported: False")
        return False


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
