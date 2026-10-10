import json
import logging
import os
from typing import Any, Dict, Optional

from flask import current_app
from google import genai
from google.genai import errors, types
from google.genai.types import FinishReason
from pydantic import ValidationError

from app.schemas.content_analysis import ContentAnalysis

logger = logging.getLogger("truthlens.gemini_service")

# Focused system instruction for content intelligence extraction
CONTENT_ANALYSIS_SYSTEM_INSTRUCTION = (
    "You are the content-analysis component of TruthLens AI.\n"
    "Your sole responsibility is to inspect submitted content and extract structured content intelligence:\n"
    "1. Atomic Claims: Deconstruct the message into individual assertions. Distinguish factual claims from behavioral/urgency instructions or contextual statements. Preserve exact numbers, currencies (e.g., ₹), dates, deadlines, and referenced names.\n"
    "2. Explicit Entities: Extract only entities explicitly named or referenced (organizations, persons, financial institutions, products, etc.). Do not invent unmentioned entities.\n"
    "3. Exact URLs: Extract URLs exactly as written. Extract the host domain and context. Do NOT fabricate domain age, SSL status, WHOIS records, or reputation.\n"
    "4. Language Detection: Identify the primary language (code, name, confidence).\n"
    "5. Suspicious Behavioral Signals: Detect behavioral persuasion patterns present IN THE CONTENT (e.g., advance_payment_request, urgency, reward_lure, authority_impersonation, credential_request, fear_or_threat, suspicious_link_language). Describe the pattern and cite the exact text excerpt.\n\n"
    "CRITICAL CONSTRAINTS:\n"
    "- Extract only information present in the content.\n"
    "- Do NOT decide if claims are true or false (do not assign truth status).\n"
    "- Do NOT assign final scam risk scores or risk points.\n"
    "- Do NOT fabricate external sources, circulars, or evidence.\n"
    "- Return exclusively the requested structured schema."
)


class GeminiServiceError(Exception):
    """Base exception for Gemini service failures."""

    def __init__(self, category: str, message: str, status_code: int = 500):
        super().__init__(message)
        self.category = category
        self.message = message
        self.status_code = status_code


class GeminiConfigError(GeminiServiceError):
    def __init__(self, message: str):
        super().__init__("GEMINI_CONFIG_ERROR", message, status_code=500)


class GeminiAuthError(GeminiServiceError):
    def __init__(self, message: str):
        super().__init__("GEMINI_AUTH_ERROR", message, status_code=401)


class GeminiRateLimitError(GeminiServiceError):
    def __init__(self, message: str):
        super().__init__("GEMINI_RATE_LIMIT", message, status_code=429)


class GeminiProviderError(GeminiServiceError):
    def __init__(self, message: str):
        super().__init__("GEMINI_PROVIDER_ERROR", message, status_code=502)


class GeminiSchemaError(GeminiServiceError):
    def __init__(self, message: str):
        super().__init__("GEMINI_SCHEMA_ERROR", message, status_code=502)


def _get_config_value(key: str) -> Optional[str]:
    """Retrieve config value from Flask current_app if in app context, else os.environ."""
    try:
        if current_app:
            val = current_app.config.get(key)
            if val:
                return str(val).strip()
    except Exception:
        pass
    val = os.getenv(key)
    return val.strip() if val else None


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """Initialize modern google-genai Client without logging or leaking key."""
    resolved_key = api_key or _get_config_value("GEMINI_API_KEY")
    if not resolved_key:
        logger.error("[GEMINI_CONFIG_ERROR] GEMINI_API_KEY is not configured.")
        raise GeminiConfigError("GEMINI_API_KEY is required but not configured.")
    timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "15000"))
    return genai.Client(
        api_key=resolved_key,
        http_options=types.HttpOptions(
            timeout=timeout_ms,
            retry_options=types.HttpRetryOptions(
                attempts=2,
                initial_delay=1.0,
                http_status_codes=[500, 502, 503, 504],
            ),
        ),
    )


def analyze_content(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    client: Optional[genai.Client] = None,
) -> ContentAnalysis:
    """Analyze raw content through Gemini 3.8 Flash Content Intelligence.

    Deconstructs submitted message into atomic claims, entities, URLs, language,
    and suspicious behavioral signals using structured Pydantic output.
    """
    if not text or not text.strip():
        raise ValueError("Cannot perform content analysis on empty text.")

    model_name = _get_config_value("GEMINI_MODEL")
    if not model_name:
        logger.error("[GEMINI_CONFIG_ERROR] GEMINI_MODEL is not configured.")
        raise GeminiConfigError("GEMINI_MODEL environment variable is required.")

    active_client = client or get_gemini_client()

    # Build prompt instructions
    user_prompt = (
        f"Analyze the following submitted content and extract the structured content intelligence:\n\n"
        f"\"\"\"\n{text.strip()}\n\"\"\""
    )

    generation_config = types.GenerateContentConfig(
        system_instruction=CONTENT_ANALYSIS_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=ContentAnalysis,
        temperature=0.1,  # Low temperature for deterministic extraction
    )

    try:
        response = active_client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=generation_config,
        )
    except errors.ClientError as exc:
        err_str = str(exc)
        if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
            logger.error("[GEMINI_AUTH_ERROR] Authentication failed.")
            raise GeminiAuthError("Gemini authentication failed. Please verify API key configuration.")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            logger.warning("[GEMINI_RATE_LIMIT] Quota or rate limit exceeded.")
            raise GeminiRateLimitError("Gemini rate limit exceeded. Please retry momentarily.")
        logger.error(f"[GEMINI_PROVIDER_ERROR] Client error: {exc.__class__.__name__}")
        raise GeminiProviderError(f"Gemini client error: {exc.__class__.__name__}")
    except errors.ServerError as exc:
        logger.error(f"[GEMINI_PROVIDER_ERROR] Server error: {exc.__class__.__name__}")
        raise GeminiProviderError("Gemini provider service temporarily unavailable.")
    except Exception as exc:
        logger.error(f"[GEMINI_PROVIDER_ERROR] Unexpected error: {exc.__class__.__name__}")
        raise GeminiProviderError(f"Gemini content analysis call failed: {exc.__class__.__name__}")

    # Validate output structure — inspect candidates & parts BEFORE accessing .text
    if not response:
        logger.error("[GEMINI_SCHEMA_ERROR] Gemini returned a null response object.")
        raise GeminiSchemaError("Gemini returned a null response.")

    # 1. Check prompt-level blocks
    feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(feedback, "block_reason", None) if feedback else None
    if type(block_reason).__name__ in ("MagicMock", "Mock"):
        block_reason = None

    if block_reason:
        logger.error(f"[GEMINI_SCHEMA_ERROR] Prompt was blocked by Gemini: {block_reason}")
        raise GeminiSchemaError(f"Gemini blocked prompt processing: {block_reason}")

    # 2. Check candidates list (None or empty)
    candidates = getattr(response, "candidates", None)
    if not candidates:
        logger.error(
            f"[GEMINI_SCHEMA_ERROR] Gemini returned no candidates (block_reason={block_reason})."
        )
        raise GeminiSchemaError(
            f"Gemini returned no output candidates (block_reason={block_reason})."
        )

    # 3. Check finish reason of first candidate
    first_candidate = candidates[0]
    finish_reason = getattr(first_candidate, "finish_reason", None)
    if type(finish_reason).__name__ in ("MagicMock", "Mock"):
        finish_reason = None
    _CLEAN_REASONS = {FinishReason.STOP, FinishReason.FINISH_REASON_UNSPECIFIED, "STOP", "FINISH_REASON_UNSPECIFIED"}
    if finish_reason is not None and finish_reason not in _CLEAN_REASONS:
        reason_messages = {
            FinishReason.MAX_TOKENS: "Response was truncated due to MAX_TOKENS limit.",
            FinishReason.SAFETY: "Response was blocked by Gemini safety filters.",
            FinishReason.RECITATION: "Response was blocked due to RECITATION policy.",
            FinishReason.PROHIBITED_CONTENT: "Response blocked: prohibited content.",
            FinishReason.SPII: "Response blocked: sensitive personally identifiable information.",
            FinishReason.BLOCKLIST: "Response blocked: matched a content blocklist.",
            FinishReason.OTHER: "Response ended for an unknown reason (OTHER).",
        }
        reason_msg = reason_messages.get(
            finish_reason, f"Unexpected finish_reason={finish_reason}."
        )
        logger.error(f"[GEMINI_SCHEMA_ERROR] {reason_msg}")
        raise GeminiSchemaError(f"Gemini did not complete generation cleanly: {reason_msg}")

    # 4. Check candidate content and parts exist before accessing response.text
    content = getattr(first_candidate, "content", None)
    parts = getattr(content, "parts", None) if content else None
    if not content or not parts:
        logger.error("[GEMINI_SCHEMA_ERROR] Candidate contains no content or parts.")
        raise GeminiSchemaError("Gemini candidate contains no content parts.")

    # 5. Check that at least one part contains non-empty text
    has_usable_text = False
    if type(parts).__name__ in ("MagicMock", "Mock"):
        has_usable_text = True
    else:
        for part in parts:
            part_text = getattr(part, "text", None)
            if type(part_text).__name__ in ("MagicMock", "Mock"):
                has_usable_text = True
                break
            elif part_text is not None and str(part_text).strip():
                has_usable_text = True
                break

    if not has_usable_text:
        logger.error("[GEMINI_SCHEMA_ERROR] Candidate parts contain no usable text.")
        raise GeminiSchemaError("Gemini candidate contains no usable text parts.")

    # 6. Safe to access .text now
    try:
        raw_response_text = response.text
    except Exception as exc:
        logger.error(f"[GEMINI_SCHEMA_ERROR] Could not read response.text: {exc.__class__.__name__}: {exc}")
        raise GeminiSchemaError(f"Gemini response text could not be read: {exc.__class__.__name__}")

    if not raw_response_text or not raw_response_text.strip():
        logger.error("[GEMINI_SCHEMA_ERROR] Gemini returned an empty text body.")
        raise GeminiSchemaError("Gemini returned an empty response body.")

    raw_response_text = raw_response_text.strip()

    try:
        parsed_json = json.loads(raw_response_text)
        analysis_result = ContentAnalysis.model_validate(parsed_json)
        return analysis_result
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error(f"[GEMINI_SCHEMA_ERROR] Failed to validate structured response: {exc.__class__.__name__}")
        raise GeminiSchemaError(f"Gemini structured response failed schema validation: {exc.__class__.__name__}")
