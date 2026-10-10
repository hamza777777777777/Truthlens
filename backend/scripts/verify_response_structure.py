import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Resolve and load backend/.env
backend_root = Path(__file__).resolve().parent.parent
load_dotenv(backend_root / ".env")

if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from google import genai
from google.genai import types
from app.schemas.content_analysis import ContentAnalysis
from app.services.gemini_service import CONTENT_ANALYSIS_SYSTEM_INSTRUCTION


def run_verification():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    sdk_version = getattr(genai, "__version__", "unknown")

    print(f"SDK Version: {sdk_version}")
    print(f"Configured Model: {model_name}")

    if not api_key:
        print("[ERROR] GEMINI_API_KEY is not set.")
        return False

    client = genai.Client(api_key=api_key)

    # Use the EXACT structured-output configuration currently used by TruthLens
    config = types.GenerateContentConfig(
        system_instruction=CONTENT_ANALYSIS_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=ContentAnalysis,
        temperature=0.1,
    )

    sample_prompt = (
        "Analyze the following submitted content and extract the structured content intelligence:\n\n"
        '"""\n'
        "Urgent: Your SBI account has been suspended. Update KYC at https://sbi-secure.example to restore access.\n"
        '"""'
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=sample_prompt,
            config=config,
        )

        # Inspect response structure
        feedback = getattr(response, "prompt_feedback", None)
        block_reason = getattr(feedback, "block_reason", None) if feedback else None
        candidates = getattr(response, "candidates", None)
        candidate_count = len(candidates) if candidates is not None else 0

        first_candidate = candidates[0] if candidate_count > 0 else None
        finish_reason = getattr(first_candidate, "finish_reason", None) if first_candidate else None

        content = getattr(first_candidate, "content", None) if first_candidate else None
        parts = getattr(content, "parts", None) if content else None
        parts_count = len(parts) if parts is not None else 0

        has_usable_parts = False
        if parts:
            for p in parts:
                txt = getattr(p, "text", None)
                if txt and str(txt).strip():
                    has_usable_parts = True
                    break

        print(f"Candidate Count: {candidate_count}")
        print(f"Finish Reason: {finish_reason}")
        print(f"Block Reason: {block_reason if block_reason else 'None'}")
        print(f"Usable Output Parts Exist: {has_usable_parts} (parts count: {parts_count})")

        # Now test that response.text can be safely read and parsed
        if has_usable_parts:
            raw_text = response.text
            parsed = ContentAnalysis.model_validate_json(raw_text)
            print(f"Structured Parsing Succeeded: True")
            print(f"Extracted Claims Count: {len(parsed.claims)}")
            print(f"Extracted Entities Count: {len(parsed.entities)}")
            print(f"Extracted URLs Count: {len(parsed.urls)}")
            print(f"Extracted Signals Count: {len(parsed.suspicious_signals)}")
        return True

    except Exception as exc:
        err_msg = str(exc)
        if api_key and api_key in err_msg:
            err_msg = err_msg.replace(api_key, "[REDACTED]")
        print(f"[ERROR] Live call failed: {exc.__class__.__name__}: {err_msg}")
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
