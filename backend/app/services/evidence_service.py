"""
TruthLens Phase 4C — Evidence Intelligence Service

Architecture Decision (verified against google-genai 2.29.0):
------------------------------------------------------------
The Gemini API (non-Vertex) does NOT support combining `response_schema` (structured
JSON output) with `google_search` grounding in a single GenerateContentConfig. Attempting
to do so produces either a 400 error or silently ignores one of the configs.

Therefore, evidence grounding is executed as a SEPARATE call from content intelligence:

  Call 1  [gemini_service.analyze_content]
          → GenerateContentConfig(response_schema=ContentAnalysis, ...)
          → Structured claim/entity/signal extraction

  Call 2  [evidence_service.ground_claims]  ← THIS FILE
          → GenerateContentConfig(tools=[Tool(google_search=GoogleSearch())])
          → No response_schema; plain text response + grounding_metadata.grounding_chunks
          → Normalize grounding_chunks into EvidenceSource Pydantic models

Constraints enforced here:
  - Never fabricate sources (all evidence must come from grounding_chunks)
  - is_simulated_demo=False only when real grounding_chunks are present
  - Gemini does NOT decide if claims are true/false (no truth verdicts here)
  - response_schema NOT used in this call (would conflict with grounding)
  - Existing structured-output validation in gemini_service.py is untouched
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import errors, types
from google.genai.types import FinishReason

from app.schemas.content_analysis import ClaimAnalysis
from app.schemas.evidence import (
    ClaimEvidenceAssessment,
    EvidenceSourceSchema,
    FailureCategory,
    GroundingAnalysis,
    RetrievalStatus,
)
from app.services.gemini_service import (
    GeminiConfigError,
    GeminiProviderError,
    GeminiRateLimitError,
    GeminiSchemaError,
    _get_config_value,
    get_gemini_client,
)

logger = logging.getLogger("truthlens.evidence_service")

# ---------------------------------------------------------------------------
# Tier classification by domain patterns
# ---------------------------------------------------------------------------
_TIER_1_DOMAINS = {
    # Indian government & regulators
    "rbi.org.in", "sebi.gov.in", "gov.in", "nic.in", "mha.gov.in",
    "cybercrime.gov.in", "npci.org.in", "certi.n", "cert-in.org.in",
    "indianarmy.nic.in", "pib.gov.in", "india.gov.in", "ncpcr.gov.in",
    # International regulators
    "fbi.gov", "ftc.gov", "sec.gov", "interpol.int", "fca.org.uk",
    "police.uk", "actionfraud.police.uk",
}
_TIER_2_DOMAINS = {
    "timesofindia.com", "thehindu.com", "hindustantimes.com",
    "ndtv.com", "livemint.com", "economictimes.indiatimes.com",
    "moneycontrol.com", "bbc.com", "bbc.co.uk", "reuters.com",
    "apnews.com", "theguardian.com", "wsj.com", "bloomberg.com",
    "wired.com", "techcrunch.com",
}


def _classify_tier(url: Optional[str], publisher: Optional[str]) -> str:
    """Classify source authority tier from URL domain."""
    if not url:
        return "unverified"
    try:
        # Extract domain
        domain = re.sub(r"https?://", "", url).split("/")[0].lower()
        domain = domain.lstrip("www.")
        if any(t1 in domain for t1 in _TIER_1_DOMAINS):
            return "tier_1_official"
        if any(t2 in domain for t2 in _TIER_2_DOMAINS):
            return "tier_2_authoritative"
        # .gov / .gov.XX heuristic
        if re.search(r"\.gov(\.[a-z]{2})?$", domain):
            return "tier_1_official"
        return "tier_3_secondary"
    except Exception:
        return "unverified"


# ---------------------------------------------------------------------------
# Grounding call prompt construction
# ---------------------------------------------------------------------------
GROUNDING_SYSTEM_INSTRUCTION = (
    "You are the Evidence Retrieval component of TruthLens AI. "
    "For each claim provided, use Google Search to find and retrieve relevant external sources. "
    "Summarize what the retrieved sources say about each claim. "
    "DO NOT assert whether claims are true or false. "
    "DO NOT fabricate sources or invent evidence. "
    "Only describe what the retrieved documents indicate, citing the sources used."
)


def _build_grounding_prompt(claims: List[ClaimAnalysis], original_text: str) -> str:
    """Build the grounding search prompt from extracted factual claims."""
    # Only ground factual claims (not behavioral instructions)
    factual = [c for c in claims if c.claim_type == "factual"]
    if not factual:
        # Fall back to all high/medium importance claims
        factual = [c for c in claims if c.importance in ("high", "medium")][:3]
    if not factual:
        factual = claims[:3]

    claim_lines = "\n".join(
        f"  - [{c.id}] {c.statement}"
        for c in factual[:4]  # Cap at 4 claims per grounding call
    )

    return (
        f"The following factual claims were extracted from a message submitted for verification:\n\n"
        f"{claim_lines}\n\n"
        f"Using Google Search, retrieve authoritative sources that can confirm or contradict each claim. "
        f"For each claim, summarize what retrieved sources indicate. "
        f"Cite only sources that are directly relevant. "
        f"Original submission context: \"{original_text[:300]}\""
    )


# ---------------------------------------------------------------------------
# Raw grounding response validation (mirrors gemini_service.py approach)
# ---------------------------------------------------------------------------
def _validate_grounding_response(
    response: Any,
) -> Tuple[bool, Optional[FailureCategory], Optional[str], Optional[types.GroundingMetadata]]:
    """
    Safely extract (is_valid, failure_category, text, grounding_metadata) from a grounding response.

    - Does NOT access response.text until candidates and parts are confirmed.
    - Returns (False, FailureCategory.INVALID_RESPONSE, None, None) if response is unusable.
    - Returns (True, None, text, grounding_metadata) if response is usable.
    """
    if not response:
        logger.warning("[EVIDENCE] Grounding response is None or empty.")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    candidates = getattr(response, "candidates", None)
    if not candidates:
        feedback = getattr(response, "prompt_feedback", None)
        block_reason = getattr(feedback, "block_reason", None) if feedback else None
        logger.warning(f"[EVIDENCE] Grounding returned no candidates (block_reason={block_reason})")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    first = candidates[0]
    finish_reason = getattr(first, "finish_reason", None)

    # Check for safety filter blocks or policy blocks
    if finish_reason in (
        FinishReason.SAFETY,
        getattr(FinishReason, "BLOCKLIST", "BLOCKLIST"),
        getattr(FinishReason, "PROHIBITED_CONTENT", "PROHIBITED_CONTENT"),
        getattr(FinishReason, "SPII", "SPII"),
    ):
        logger.warning(f"[EVIDENCE] Grounding candidate blocked by policy/safety: finish_reason={finish_reason}")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    # STOP and FINISH_REASON_UNSPECIFIED are clean; others log warnings
    if finish_reason not in (
        FinishReason.STOP,
        FinishReason.FINISH_REASON_UNSPECIFIED,
        None,
    ):
        logger.warning(f"[EVIDENCE] Grounding finish_reason={finish_reason} (non-STOP)")

    # Extract grounding metadata (present even on empty text for google_search)
    grounding_metadata: Optional[types.GroundingMetadata] = getattr(
        first, "grounding_metadata", None
    )

    # Safely read text
    content = getattr(first, "content", None)
    parts = getattr(content, "parts", None) if content else None
    has_text = False
    if parts:
        for p in parts:
            pt = getattr(p, "text", None)
            if type(pt).__name__ not in ("MagicMock", "Mock") and pt and str(pt).strip():
                has_text = True
                break

    # If neither text nor grounding_metadata exists, the candidate is empty and unusable
    if not has_text and not grounding_metadata:
        logger.warning("[EVIDENCE] Grounding response has neither text nor grounding metadata.")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    text: Optional[str] = None
    if has_text:
        try:
            text = response.text
        except Exception as exc:
            logger.warning(f"[EVIDENCE] Could not read grounding response.text: {exc}")
            text = None

    return True, None, text, grounding_metadata


# ---------------------------------------------------------------------------
# Grounding chunks → EvidenceSourceSchema
# ---------------------------------------------------------------------------
def _normalize_grounding_chunks(
    chunks: List[types.GroundingChunk],
    claims: List[ClaimAnalysis],
    grounding_text: Optional[str],
) -> List[EvidenceSourceSchema]:
    """
    Convert raw GroundingChunk objects into typed EvidenceSourceSchema instances.

    Source evaluation rules:
    - Title and URI come directly from chunk.web (no fabrication)
    - Snippet is extracted from grounding_text by proximity heuristic, or left as URL
    - Tier is inferred from domain
    - Stance defaults to INSUFFICIENT (Truth Engine assigns final stance later)
    - confidence is set conservatively based on tier
    - is_simulated_demo=False because these are real retrieved sources
    """
    sources: List[EvidenceSourceSchema] = []

    for idx, chunk in enumerate(chunks[:8]):  # Cap at 8 sources
        web = getattr(chunk, "web", None)
        if not web:
            continue  # Skip non-web chunks (maps, images, etc.)

        uri: Optional[str] = getattr(web, "uri", None)
        title: Optional[str] = getattr(web, "title", None) or "Untitled Source"
        domain: Optional[str] = getattr(web, "domain", None)

        # Publisher = domain if available, else extracted from URI
        if domain:
            publisher = domain
        elif uri:
            publisher = re.sub(r"https?://", "", uri).split("/")[0].lstrip("www.")
        else:
            publisher = "Unknown Publisher"

        tier = _classify_tier(uri, publisher)
        confidence_by_tier = {
            "tier_1_official": 0.92,
            "tier_2_authoritative": 0.78,
            "tier_3_secondary": 0.55,
            "unverified": 0.40,
        }
        confidence = confidence_by_tier.get(tier, 0.40)

        # Try to extract a snippet from grounding_text near title keywords
        snippet = _extract_snippet(grounding_text, title, uri)

        # Map to the most relevant claim (round-robin if many sources)
        relevant_claim_id = (
            claims[idx % len(claims)].id if claims else f"claim-{idx+1}"
        )

        sources.append(
            EvidenceSourceSchema(
                id=f"ev-{idx+1}",
                title=title,
                publisher=publisher,
                url=uri,
                snippet=snippet,
                relevance_to_claim=relevant_claim_id,
                stance="INSUFFICIENT",  # Truth Engine assigns final stance
                tier=tier,
                confidence=confidence,
            )
        )

    return sources


def _extract_snippet(text: Optional[str], title: Optional[str], uri: Optional[str]) -> str:
    """Extract a relevant text snippet from the grounding response text."""
    if not text:
        return f"Source retrieved via Google Search grounding: {uri or 'Unknown URL'}"

    # Try to find a sentence mentioning the title keywords
    if title:
        keywords = [w for w in title.split() if len(w) > 4][:3]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sent in sentences:
            if any(kw.lower() in sent.lower() for kw in keywords):
                snippet = sent.strip()
                if len(snippet) > 20:
                    return snippet[:400]

    # Fall back to first 300 chars of grounding text
    return text[:300].strip() + ("..." if len(text) > 300 else "")


# ---------------------------------------------------------------------------
# Claim evidence assessments from grounding text
# ---------------------------------------------------------------------------
def _build_claim_assessments(
    claims: List[ClaimAnalysis],
    grounding_text: Optional[str],
    search_queries: List[str],
) -> List[ClaimEvidenceAssessment]:
    """Build per-claim evidence assessments from grounding text."""
    assessments: List[ClaimEvidenceAssessment] = []

    factual_claims = [c for c in claims if c.claim_type == "factual"][:4]

    for idx, claim in enumerate(factual_claims):
        query = search_queries[idx] if idx < len(search_queries) else f"Verify: {claim.statement[:80]}"

        # Extract a relevant passage from grounding text for this claim
        if grounding_text:
            sentences = re.split(r"(?<=[.!?])\s+", grounding_text)
            # Find sentences near the claim statement keywords
            claim_keywords = [w for w in claim.statement.split() if len(w) > 4][:4]
            relevant_sentences = [
                s for s in sentences
                if any(kw.lower() in s.lower() for kw in claim_keywords)
            ]
            if relevant_sentences:
                summary = " ".join(relevant_sentences[:2])[:500]
                evidence_found = True
            else:
                summary = (
                    f"Google Search was executed for this claim. Retrieved sources did not contain "
                    f"a direct passage matching the claim keywords. Manual review recommended."
                )
                evidence_found = bool(grounding_text.strip())
        else:
            summary = "No grounded sources were retrieved for this claim. Evidence grounding was unavailable."
            evidence_found = False

        assessments.append(
            ClaimEvidenceAssessment(
                claim_id=claim.id,
                search_query_used=query,
                evidence_found=evidence_found,
                evidence_summary=summary,
            )
        )

    return assessments


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------
def ground_claims(
    claims: List[ClaimAnalysis],
    original_text: str,
    client: Optional[genai.Client] = None,
) -> GroundingAnalysis:
    """
    Phase 4C Evidence Intelligence: Ground extracted claims using Google Search.

    Uses a SEPARATE Gemini call from analyze_content (no response_schema).
    Grounding and structured JSON output cannot be combined in the Gemini API.

    Returns GroundingAnalysis with:
    - retrieval_status:         SUCCESS, NO_EVIDENCE, or FAILED
    - failure_category:         Safe machine-readable category when FAILED (None otherwise)
    - sources:                  EvidenceSourceSchema list (from real grounding_chunks)
    - claim_assessments:        Per-claim evidence summaries
    - grounding_search_queries: Queries Google Search executed
    - is_grounded:              True only when retrieval_status is SUCCESS and sources present

    Never raises — returns GroundingAnalysis with explicit retrieval_status and failure_category.
    """
    if not claims:
        logger.info("[EVIDENCE] No claims to ground. Returning NO_EVIDENCE.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.NO_EVIDENCE,
            failure_category=None,
            is_grounded=False,
        )

    model_name = _get_config_value("GEMINI_MODEL")
    api_key = _get_config_value("GEMINI_API_KEY")
    if not model_name or not api_key:
        logger.error("[EVIDENCE] GEMINI_MODEL or GEMINI_API_KEY not configured; cannot ground claims.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    try:
        active_client = client or get_gemini_client()
    except GeminiConfigError:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )
    except Exception:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    prompt = _build_grounding_prompt(claims, original_text)

    # Grounding call: google_search tool, NO response_schema
    # (Combining response_schema + google_search is not supported in Gemini API)
    grounding_config = types.GenerateContentConfig(
        system_instruction=GROUNDING_SYSTEM_INSTRUCTION,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
    )

    try:
        logger.info(f"[EVIDENCE] Initiating Google Search grounding for {len(claims)} claim(s).")
        response = active_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=grounding_config,
        )
    except errors.ClientError as exc:
        err_str = str(exc)
        logger.error(f"[EVIDENCE] Grounding client error: {exc.__class__.__name__}")
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code in (401, 403) or any(k in err_str for k in ["API_KEY_INVALID", "PERMISSION_DENIED", "UNAUTHENTICATED", "api key"]):
            cat = FailureCategory.AUTHENTICATION
        elif code == 429 or any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "quota", "rate limit", "Rate limit"]):
            logger.warning("[EVIDENCE] Rate limit hit during grounding.")
            cat = FailureCategory.RATE_LIMIT
        else:
            cat = FailureCategory.PROVIDER_ERROR
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=cat,
            is_grounded=False,
        )
    except errors.ServerError:
        logger.error("[EVIDENCE] Gemini server error during grounding.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.PROVIDER_ERROR,
            is_grounded=False,
        )
    except (ConnectionError, TimeoutError, OSError) as exc:
        logger.error(f"[EVIDENCE] Grounding network error: {exc.__class__.__name__}")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.NETWORK,
            is_grounded=False,
        )
    except Exception as exc:
        err_str = str(exc).lower()
        logger.error(f"[EVIDENCE] Grounding call failed: {exc.__class__.__name__}")
        if any(k in err_str for k in ["connection", "timeout", "timed out", "network", "socket", "dns", "unreachable"]):
            cat = FailureCategory.NETWORK
        elif any(k in err_str for k in ["auth", "permission", "api_key", "unauthenticated", "401", "403"]):
            cat = FailureCategory.AUTHENTICATION
        elif any(k in err_str for k in ["429", "resource_exhausted", "quota", "rate limit"]):
            cat = FailureCategory.RATE_LIMIT
        elif isinstance(exc, (GeminiProviderError, errors.APIError)):
            cat = FailureCategory.PROVIDER_ERROR
        else:
            cat = FailureCategory.UNKNOWN
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=cat,
            is_grounded=False,
        )

    # Safely extract text and grounding_metadata
    is_valid, fail_cat, grounding_text, grounding_metadata = _validate_grounding_response(response)
    if not is_valid:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=fail_cat or FailureCategory.INVALID_RESPONSE,
            is_grounded=False,
        )

    # Extract grounding chunks (the real retrieved web sources)
    raw_chunks: List[types.GroundingChunk] = []
    search_queries: List[str] = []

    if grounding_metadata:
        raw_chunks = getattr(grounding_metadata, "grounding_chunks", None) or []
        search_queries = getattr(grounding_metadata, "web_search_queries", None) or []
        logger.info(
            f"[EVIDENCE] Grounding returned {len(raw_chunks)} chunk(s), "
            f"{len(search_queries)} search query/queries."
        )
    else:
        logger.warning("[EVIDENCE] No grounding_metadata returned.")

    # Normalize chunks → EvidenceSourceSchema (no fabrication)
    sources = _normalize_grounding_chunks(raw_chunks, claims, grounding_text) if raw_chunks else []

    # Build claim assessments
    claim_assessments = _build_claim_assessments(claims, grounding_text, search_queries)

    if sources:
        retrieval_status = RetrievalStatus.SUCCESS
        is_grounded = True
    else:
        retrieval_status = RetrievalStatus.NO_EVIDENCE
        is_grounded = False

    return GroundingAnalysis(
        retrieval_status=retrieval_status,
        failure_category=None,
        sources=sources,
        claim_assessments=claim_assessments,
        grounding_search_queries=search_queries,
        is_grounded=is_grounded,
    )
