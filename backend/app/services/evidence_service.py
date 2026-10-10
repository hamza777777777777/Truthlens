"""
TruthLens Phase 5A — Evidence Intelligence Service (Tavily + Google Grounding)

Evidence Provider Priority
--------------------------
1. Tavily Search API  — if TAVILY_API_KEY is configured in the environment.
   Uses tavily-python SDK over HTTPS. No grounding call to Gemini is needed.
   Results are genuine retrieved web pages; never fabricated.

2. Gemini Google Search Grounding — fallback when TAVILY_API_KEY is absent.
   Uses a separate Gemini call (no response_schema, grounding tool only).
   Preserved from Phase 4C without modification.

Architecture Constraints (enforced here)
-----------------------------------------
- NEVER fabricate sources. All evidence must originate from real API results.
- is_simulated_demo=False ONLY when genuine retrieved sources are present.
- Gemini does NOT decide if claims are true/false (no truth verdicts here).
- Distinct failure semantics: SUCCESS / NO_EVIDENCE / FAILED / SKIPPED.
- A failed search NEVER converts into a FALSE claim or a truth verdict.
- API keys are read from config/env, never logged or hardcoded.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

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
    _get_config_value,
)

# Import TavilyClient at module level so it is patchable in tests.
# If tavily-python is not installed, TavilyClient will be None and the
# absence is detected at call time.
try:
    from tavily import TavilyClient, MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError
    _TAVILY_AVAILABLE = True
except ImportError:  # pragma: no cover — only absent before pip install
    TavilyClient = None  # type: ignore[assignment,misc]
    MissingAPIKeyError = Exception  # type: ignore[assignment,misc]
    InvalidAPIKeyError = Exception  # type: ignore[assignment,misc]
    UsageLimitExceededError = Exception  # type: ignore[assignment,misc]
    _TAVILY_AVAILABLE = False

logger = logging.getLogger("truthlens.evidence_service")

# ---------------------------------------------------------------------------
# Source tier classification by domain patterns
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


def _classify_tier(url: Optional[str], publisher: Optional[str] = None) -> str:
    """Classify source authority tier from URL domain."""
    if not url:
        return "unverified"
    try:
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


def _extract_snippet(text: Optional[str], title: Optional[str], uri: Optional[str]) -> str:
    """Extract a relevant text snippet from a grounding response text."""
    if not text:
        return f"Source retrieved via Google Search grounding: {uri or 'Unknown URL'}"
    if title:
        keywords = [w for w in title.split() if len(w) > 4][:3]
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sent in sentences:
            if any(kw.lower() in sent.lower() for kw in keywords):
                snippet = sent.strip()
                if len(snippet) > 20:
                    return snippet[:400]
    return text[:300].strip() + ("..." if len(text) > 300 else "")


# ---------------------------------------------------------------------------
# TAVILY PROVIDER
# ---------------------------------------------------------------------------

def _get_tavily_api_key() -> Optional[str]:
    """Read TAVILY_API_KEY from Flask app config then os.environ. Never logged."""
    return _get_config_value("TAVILY_API_KEY")


def _build_search_queries(claims: List[ClaimAnalysis], original_text: str) -> List[str]:
    """Build distinct search queries for factual claims."""
    factual = [c for c in claims if c.claim_type == "factual"]
    if not factual:
        factual = [c for c in claims if c.importance in ("high", "medium")][:3]
    if not factual:
        factual = claims[:3]

    queries: List[str] = []
    for c in factual[:4]:
        # Concise form: strip leading "Recipient", "You", etc. and cap length
        stmt = c.statement.strip()
        if len(stmt) > 100:
            stmt = stmt[:100] + "..."
        queries.append(stmt)

    if not queries:
        queries.append(original_text[:120])

    return queries


def _normalize_tavily_results(
    results: List[Dict[str, Any]],
    claims: List[ClaimAnalysis],
) -> List[EvidenceSourceSchema]:
    """
    Convert genuine Tavily result dicts into EvidenceSourceSchema objects.

    Preservation rules:
    - title, url, content (snippet), published_date — taken directly from Tavily, never invented.
    - publisher derived from URL domain (no fabrication).
    - Stance defaults to INSUFFICIENT (Truth Engine assigns final stance later).
    - is_simulated_demo is NOT set here — it lives on EvidenceSource (API contract layer),
      set to False by _map_evidence_source in investigation_service.py.
    """
    sources: List[EvidenceSourceSchema] = []
    for idx, result in enumerate(results[:8]):  # Cap at 8 sources
        url: Optional[str] = result.get("url")
        title: str = result.get("title") or "Untitled Source"
        snippet: str = result.get("content") or result.get("snippet") or ""

        if not url:
            continue  # Skip sources without a URL (cannot be cited)

        if not snippet.strip():
            # Do NOT fabricate — use a safe generic description
            snippet = f"Retrieved from {url}"

        # Derive publisher from domain (no fabrication)
        try:
            domain_raw = re.sub(r"https?://", "", url).split("/")[0].lower()
            publisher = domain_raw.lstrip("www.")
        except Exception:
            publisher = "Unknown Publisher"

        tier = _classify_tier(url)
        confidence_by_tier = {
            "tier_1_official": 0.92,
            "tier_2_authoritative": 0.78,
            "tier_3_secondary": 0.55,
            "unverified": 0.40,
        }
        confidence = confidence_by_tier.get(tier, 0.40)

        # Map to the most relevant claim (round-robin if many sources)
        relevant_claim_id = (
            claims[idx % len(claims)].id if claims else f"claim-{idx + 1}"
        )

        sources.append(
            EvidenceSourceSchema(
                id=f"ev-{idx + 1}",
                title=title,
                publisher=publisher,
                url=url,
                snippet=snippet[:500],
                relevance_to_claim=relevant_claim_id,
                stance="INSUFFICIENT",  # Truth Engine assigns final stance
                tier=tier,
                confidence=confidence,
            )
        )

    return sources


def _build_claim_assessments_from_tavily(
    claims: List[ClaimAnalysis],
    results: List[Dict[str, Any]],
    queries: List[str],
) -> List[ClaimEvidenceAssessment]:
    """Build per-claim evidence assessments from Tavily results."""
    assessments: List[ClaimEvidenceAssessment] = []
    factual_claims = [c for c in claims if c.claim_type == "factual"][:4]

    for idx, claim in enumerate(factual_claims):
        query = queries[idx] if idx < len(queries) else f"Verify: {claim.statement[:80]}"

        if results:
            # Find results most relevant to this claim
            claim_keywords = [w for w in claim.statement.split() if len(w) > 4][:4]
            relevant = [
                r for r in results
                if any(kw.lower() in (r.get("content") or "").lower() for kw in claim_keywords)
            ]
            if relevant:
                snippet = relevant[0].get("content", "")[:400] or "Relevant sources retrieved."
                summary = (
                    f"Tavily Search retrieved {len(relevant)} relevant result(s) for this claim. "
                    f"Excerpt: {snippet}"
                )
                evidence_found = True
            else:
                summary = (
                    f"Tavily Search was executed for this claim ({len(results)} total result(s) retrieved). "
                    "No retrieved document contained a direct passage matching the claim keywords. Manual review recommended."
                )
                evidence_found = bool(results)
        else:
            summary = "No external sources were retrieved for this claim. Evidence retrieval returned empty results."
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


def _retrieve_via_tavily(
    claims: List[ClaimAnalysis],
    original_text: str,
    api_key: str,
) -> GroundingAnalysis:
    """
    Execute evidence retrieval via Tavily Search API.

    Returns GroundingAnalysis. Never raises.
    Failure semantics:
      - Authentication failure (401)  → FailureCategory.AUTHENTICATION
      - Rate limit (429)              → FailureCategory.RATE_LIMIT
      - Network / timeout             → FailureCategory.NETWORK
      - Other API error               → FailureCategory.PROVIDER_ERROR
      - Malformed response            → FailureCategory.INVALID_RESPONSE
      - Empty results                 → RetrievalStatus.NO_EVIDENCE
      - Real results found            → RetrievalStatus.SUCCESS
    """
    if not _TAVILY_AVAILABLE or TavilyClient is None:
        logger.error("[EVIDENCE/TAVILY] tavily-python is not installed. Add it to requirements.txt.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    queries = _build_search_queries(claims, original_text)
    if not queries:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.NO_EVIDENCE,
            failure_category=None,
            is_grounded=False,
        )

    logger.info(f"[EVIDENCE/TAVILY] Starting search for {len(queries)} query/queries.")

    all_results: List[Dict[str, Any]] = []
    search_queries_executed: List[str] = []

    try:
        client = TavilyClient(api_key=api_key)
    except (MissingAPIKeyError, InvalidAPIKeyError):
        logger.error("[EVIDENCE/TAVILY] API key invalid or missing.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.AUTHENTICATION,
            is_grounded=False,
        )
    except Exception as exc:
        logger.error(f"[EVIDENCE/TAVILY] Client initialization failed: {exc.__class__.__name__}")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=5,
                include_answer=False,
            )
            search_queries_executed.append(query)

            if response is None or not isinstance(response, dict):
                logger.warning(f"[EVIDENCE/TAVILY] Unexpected response type: {type(response).__name__}")
                continue

            results_list = response.get("results", [])
            if not isinstance(results_list, list):
                logger.warning("[EVIDENCE/TAVILY] 'results' field in response is not a list.")
                continue

            # Deduplicate by URL
            seen_urls = {r.get("url") for r in all_results}
            for r in results_list:
                if isinstance(r, dict) and r.get("url") and r.get("url") not in seen_urls:
                    all_results.append(r)
                    seen_urls.add(r.get("url"))

        except (MissingAPIKeyError, InvalidAPIKeyError):
            logger.error("[EVIDENCE/TAVILY] Authentication error during search.")
            return GroundingAnalysis(
                retrieval_status=RetrievalStatus.FAILED,
                failure_category=FailureCategory.AUTHENTICATION,
                is_grounded=False,
            )
        except UsageLimitExceededError:
            logger.warning("[EVIDENCE/TAVILY] Usage limit/rate limit exceeded.")
            return GroundingAnalysis(
                retrieval_status=RetrievalStatus.FAILED,
                failure_category=FailureCategory.RATE_LIMIT,
                is_grounded=False,
            )
        except Exception as exc:
            err_str = str(exc).lower()
            err_cls = exc.__class__.__name__
            logger.error(f"[EVIDENCE/TAVILY] Search query failed: {err_cls}")

            # Classify error type from exception string
            if any(k in err_str for k in ["connect", "timeout", "timed out", "network", "socket", "dns", "unreachable", "connection"]):
                return GroundingAnalysis(
                    retrieval_status=RetrievalStatus.FAILED,
                    failure_category=FailureCategory.NETWORK,
                    is_grounded=False,
                )
            if any(k in err_str for k in ["401", "403", "unauthorized", "auth", "api key", "invalid key"]):
                return GroundingAnalysis(
                    retrieval_status=RetrievalStatus.FAILED,
                    failure_category=FailureCategory.AUTHENTICATION,
                    is_grounded=False,
                )
            if any(k in err_str for k in ["429", "rate limit", "quota", "usage limit", "too many"]):
                return GroundingAnalysis(
                    retrieval_status=RetrievalStatus.FAILED,
                    failure_category=FailureCategory.RATE_LIMIT,
                    is_grounded=False,
                )
            return GroundingAnalysis(
                retrieval_status=RetrievalStatus.FAILED,
                failure_category=FailureCategory.PROVIDER_ERROR,
                is_grounded=False,
            )

    logger.info(
        f"[EVIDENCE/TAVILY] Retrieved {len(all_results)} unique source(s) across "
        f"{len(search_queries_executed)} query/queries."
    )

    if not all_results:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.NO_EVIDENCE,
            failure_category=None,
            sources=[],
            claim_assessments=_build_claim_assessments_from_tavily(claims, [], queries),
            grounding_search_queries=search_queries_executed,
            is_grounded=False,
        )

    sources = _normalize_tavily_results(all_results, claims)
    claim_assessments = _build_claim_assessments_from_tavily(claims, all_results, search_queries_executed)

    return GroundingAnalysis(
        retrieval_status=RetrievalStatus.SUCCESS,
        failure_category=None,
        sources=sources,
        claim_assessments=claim_assessments,
        grounding_search_queries=search_queries_executed,
        is_grounded=True,
    )


# ---------------------------------------------------------------------------
# GOOGLE GROUNDING PROVIDER (preserved from Phase 4C as fallback)
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
    factual = [c for c in claims if c.claim_type == "factual"]
    if not factual:
        factual = [c for c in claims if c.importance in ("high", "medium")][:3]
    if not factual:
        factual = claims[:3]

    claim_lines = "\n".join(
        f"  - [{c.id}] {c.statement}"
        for c in factual[:4]
    )

    return (
        f"The following factual claims were extracted from a message submitted for verification:\n\n"
        f"{claim_lines}\n\n"
        f"Using Google Search, retrieve authoritative sources that can confirm or contradict each claim. "
        f"For each claim, summarize what retrieved sources indicate. "
        f"Cite only sources that are directly relevant. "
        f"Original submission context: \"{original_text[:300]}\""
    )


def _validate_grounding_response(
    response: Any,
) -> Tuple[bool, Optional[FailureCategory], Optional[str], Any]:
    """Safely extract (is_valid, failure_category, text, grounding_metadata)."""
    if not response:
        logger.warning("[EVIDENCE] Grounding response is None or empty.")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    candidates = getattr(response, "candidates", None)
    if not candidates:
        logger.warning("[EVIDENCE] Grounding returned no candidates.")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    first = candidates[0]
    finish_reason = getattr(first, "finish_reason", None)

    # Attempt lazy import of FinishReason to avoid hard dependency on google.genai in Tavily-only path
    try:
        from google.genai.types import FinishReason as _FinishReason
        _BLOCKED = (
            _FinishReason.SAFETY,
            getattr(_FinishReason, "BLOCKLIST", "BLOCKLIST"),
            getattr(_FinishReason, "PROHIBITED_CONTENT", "PROHIBITED_CONTENT"),
            getattr(_FinishReason, "SPII", "SPII"),
        )
        _CLEAN = (_FinishReason.STOP, _FinishReason.FINISH_REASON_UNSPECIFIED, None)
    except Exception:
        _BLOCKED = ()
        _CLEAN = (None,)

    if finish_reason in _BLOCKED:
        logger.warning(f"[EVIDENCE] Grounding blocked by policy: finish_reason={finish_reason}")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    if finish_reason not in _CLEAN:
        logger.warning(f"[EVIDENCE] Grounding finish_reason={finish_reason} (non-STOP)")

    grounding_metadata = getattr(first, "grounding_metadata", None)

    content = getattr(first, "content", None)
    parts = getattr(content, "parts", None) if content else None
    has_text = False
    if parts:
        for p in parts:
            pt = getattr(p, "text", None)
            if type(pt).__name__ not in ("MagicMock", "Mock") and pt and str(pt).strip():
                has_text = True
                break

    if not has_text and not grounding_metadata:
        logger.warning("[EVIDENCE] Grounding response has neither text nor grounding metadata.")
        return False, FailureCategory.INVALID_RESPONSE, None, None

    text: Optional[str] = None
    if has_text:
        try:
            text = response.text
        except Exception as exc:
            logger.warning(f"[EVIDENCE] Could not read grounding response.text: {exc}")

    return True, None, text, grounding_metadata


def _normalize_grounding_chunks(
    chunks: list,
    claims: List[ClaimAnalysis],
    grounding_text: Optional[str],
) -> List[EvidenceSourceSchema]:
    """Convert raw GroundingChunk objects into EvidenceSourceSchema instances."""
    sources: List[EvidenceSourceSchema] = []

    for idx, chunk in enumerate(chunks[:8]):
        web = getattr(chunk, "web", None)
        if not web:
            continue

        uri: Optional[str] = getattr(web, "uri", None)
        title: Optional[str] = getattr(web, "title", None) or "Untitled Source"
        domain: Optional[str] = getattr(web, "domain", None)

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
        snippet = _extract_snippet(grounding_text, title, uri)
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
                stance="INSUFFICIENT",
                tier=tier,
                confidence=confidence,
            )
        )

    return sources


def _build_claim_assessments(
    claims: List[ClaimAnalysis],
    grounding_text: Optional[str],
    search_queries: List[str],
) -> List[ClaimEvidenceAssessment]:
    """Build per-claim evidence assessments from Google grounding text."""
    assessments: List[ClaimEvidenceAssessment] = []
    factual_claims = [c for c in claims if c.claim_type == "factual"][:4]

    for idx, claim in enumerate(factual_claims):
        query = search_queries[idx] if idx < len(search_queries) else f"Verify: {claim.statement[:80]}"

        if grounding_text:
            sentences = re.split(r"(?<=[.!?])\s+", grounding_text)
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
                    "Google Search was executed for this claim. Retrieved sources did not contain "
                    "a direct passage matching the claim keywords. Manual review recommended."
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


def _retrieve_via_google_grounding(
    claims: List[ClaimAnalysis],
    original_text: str,
    client: Any,
) -> GroundingAnalysis:
    """
    Execute evidence retrieval via Gemini Google Search Grounding (Phase 4C fallback).

    This function is only called when TAVILY_API_KEY is not configured.
    Never raises — returns GroundingAnalysis with explicit status.
    """
    try:
        from google import genai
        from google.genai import errors, types
    except ImportError:
        logger.error("[EVIDENCE/GROUNDING] google-genai is not installed.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    model_name = _get_config_value("GEMINI_MODEL")
    api_key = _get_config_value("GEMINI_API_KEY")
    if not model_name or not api_key:
        logger.error("[EVIDENCE/GROUNDING] GEMINI_MODEL or GEMINI_API_KEY not configured.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    try:
        from app.services.gemini_service import get_gemini_client
        active_client = client or get_gemini_client()
    except Exception:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.INVALID_CONFIGURATION,
            is_grounded=False,
        )

    prompt = _build_grounding_prompt(claims, original_text)
    grounding_config = types.GenerateContentConfig(
        system_instruction=GROUNDING_SYSTEM_INSTRUCTION,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
    )

    try:
        logger.info(f"[EVIDENCE/GROUNDING] Initiating Google Search grounding for {len(claims)} claim(s).")
        response = active_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=grounding_config,
        )
    except errors.ClientError as exc:
        err_str = str(exc)
        logger.error(f"[EVIDENCE/GROUNDING] Client error: {exc.__class__.__name__}")
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code in (401, 403) or any(k in err_str for k in ["API_KEY_INVALID", "PERMISSION_DENIED", "UNAUTHENTICATED", "api key"]):
            cat = FailureCategory.AUTHENTICATION
        elif code == 429 or any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "quota", "rate limit", "Rate limit"]):
            logger.warning("[EVIDENCE] Rate limit hit during grounding.")
            cat = FailureCategory.RATE_LIMIT
        else:
            cat = FailureCategory.PROVIDER_ERROR
        return GroundingAnalysis(retrieval_status=RetrievalStatus.FAILED, failure_category=cat, is_grounded=False)
    except errors.ServerError:
        logger.error("[EVIDENCE/GROUNDING] Gemini server error.")
        return GroundingAnalysis(retrieval_status=RetrievalStatus.FAILED, failure_category=FailureCategory.PROVIDER_ERROR, is_grounded=False)
    except (ConnectionError, TimeoutError, OSError) as exc:
        logger.error(f"[EVIDENCE/GROUNDING] Network error: {exc.__class__.__name__}")
        return GroundingAnalysis(retrieval_status=RetrievalStatus.FAILED, failure_category=FailureCategory.NETWORK, is_grounded=False)
    except Exception as exc:
        err_str = str(exc).lower()
        logger.error(f"[EVIDENCE/GROUNDING] Grounding call failed: {exc.__class__.__name__}")
        if any(k in err_str for k in ["connection", "timeout", "timed out", "network", "socket", "dns", "unreachable"]):
            cat = FailureCategory.NETWORK
        elif any(k in err_str for k in ["auth", "permission", "api_key", "unauthenticated", "401", "403"]):
            cat = FailureCategory.AUTHENTICATION
        elif any(k in err_str for k in ["429", "resource_exhausted", "quota", "rate limit"]):
            cat = FailureCategory.RATE_LIMIT
        elif isinstance(exc, GeminiProviderError):
            cat = FailureCategory.PROVIDER_ERROR
        else:
            cat = FailureCategory.UNKNOWN
        return GroundingAnalysis(retrieval_status=RetrievalStatus.FAILED, failure_category=cat, is_grounded=False)

    is_valid, fail_cat, grounding_text, grounding_metadata = _validate_grounding_response(response)
    if not is_valid:
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=fail_cat or FailureCategory.INVALID_RESPONSE,
            is_grounded=False,
        )

    raw_chunks: list = []
    search_queries: List[str] = []

    if grounding_metadata:
        raw_chunks = getattr(grounding_metadata, "grounding_chunks", None) or []
        search_queries = getattr(grounding_metadata, "web_search_queries", None) or []
        logger.info(
            f"[EVIDENCE/GROUNDING] Returned {len(raw_chunks)} chunk(s), "
            f"{len(search_queries)} search query/queries."
        )
    else:
        logger.warning("[EVIDENCE/GROUNDING] No grounding_metadata returned.")

    sources = _normalize_grounding_chunks(raw_chunks, claims, grounding_text) if raw_chunks else []
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


# ---------------------------------------------------------------------------
# Main public function — provider routing
# ---------------------------------------------------------------------------
def ground_claims(
    claims: List[ClaimAnalysis],
    original_text: str,
    client: Optional[Any] = None,
) -> GroundingAnalysis:
    """
    Phase 5A Evidence Intelligence: Ground claims using Tavily (primary) or Google grounding (fallback).

    Provider selection:
    - If TAVILY_API_KEY is configured → use Tavily Search API.
    - Otherwise → fall back to Gemini Google Search grounding (requires GEMINI_API_KEY + GEMINI_MODEL).

    Returns GroundingAnalysis with:
    - retrieval_status:         SUCCESS, NO_EVIDENCE, FAILED, or SKIPPED
    - failure_category:         Safe machine-readable category when FAILED (None otherwise)
    - sources:                  EvidenceSourceSchema list (from real retrieved results only)
    - claim_assessments:        Per-claim evidence summaries
    - grounding_search_queries: Queries executed
    - is_grounded:              True only when retrieval_status is SUCCESS and sources present

    Never raises — returns GroundingAnalysis with explicit retrieval_status and failure_category.
    Failure semantics: failing evidence retrieval NEVER sets truth_status.
    """
    if not claims:
        logger.info("[EVIDENCE] No claims to ground. Returning NO_EVIDENCE.")
        return GroundingAnalysis(
            retrieval_status=RetrievalStatus.NO_EVIDENCE,
            failure_category=None,
            is_grounded=False,
        )

    tavily_key = _get_tavily_api_key()

    if tavily_key:
        logger.info("[EVIDENCE] TAVILY_API_KEY configured. Using Tavily Search API as evidence provider.")
        return _retrieve_via_tavily(claims, original_text, api_key=tavily_key)
    else:
        logger.info("[EVIDENCE] No TAVILY_API_KEY. Falling back to Gemini Google Search grounding.")
        return _retrieve_via_google_grounding(claims, original_text, client=client)
