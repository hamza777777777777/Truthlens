"""
Phase 4C Evidence Intelligence Unit Tests

All tests are deterministic — they mock the Gemini client and never call the live API.
Tests cover:
  - Successful grounding with real-typed GroundingChunk objects
  - Empty grounding_chunks (no results)
  - Missing grounding_metadata
  - Safety block during grounding call
  - Tier classification logic
  - Snippet extraction
  - Claim↔evidence mapping in investigation pipeline
  - is_simulated_demo=False when grounding succeeds
  - is_simulated_demo=True when grounding unavailable
  - ground_claims never raises (graceful degradation)
"""
import json
import os
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from google.genai import types
from google.genai.types import FinishReason

from app.schemas.content_analysis import ClaimAnalysis, ContentAnalysis
from app.schemas.evidence import (
    EvidenceSourceSchema,
    FailureCategory,
    GroundingAnalysis,
    RetrievalStatus,
)
from app.schemas.investigation import (
    Claim,
    InvestigationRequest,
    InvestigationResult,
    TruthAssessmentStatus,
    TruthStatus,
)
from app.services.evidence_service import (
    _classify_tier,
    _extract_snippet,
    _normalize_grounding_chunks,
    ground_claims,
)
from app.services.investigation_service import investigate

@pytest.fixture(autouse=True)
def disable_tavily_for_google_tests(monkeypatch):
    """Ensure Tavily is not active during Google Search Grounding unit tests."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


SAMPLE_CLAIMS: List[ClaimAnalysis] = [
    ClaimAnalysis(
        id="claim-1",
        statement="SBI is offering a ₹50,000 cash prize to account holders.",
        category="benefit_claim",
        claim_type="factual",
        importance="high",
        confidence=0.95,
    ),
    ClaimAnalysis(
        id="claim-2",
        statement="Recipients must pay ₹499 to claim the prize.",
        category="payment_instruction",
        claim_type="behavioral_instruction",
        importance="high",
        confidence=0.90,
    ),
]

ORIGINAL_TEXT = "Congratulations! SBI is giving you ₹50,000. Pay ₹499 to claim at https://sbi.fake"


def _make_grounding_response(
    chunks: list,
    text: str = "SBI has issued warnings about lottery scams.",
    finish_reason=FinishReason.STOP,
    search_queries: list = None,
):
    """Build a real GenerateContentResponse with grounding_metadata."""
    search_queries = search_queries or ["SBI lottery prize scam warning"]
    grounding_metadata = types.GroundingMetadata(
        grounding_chunks=chunks,
        web_search_queries=search_queries,
    )
    candidate = types.Candidate(
        finish_reason=finish_reason,
        content=types.Content(parts=[types.Part.from_text(text=text)]),
        grounding_metadata=grounding_metadata,
    )
    return types.GenerateContentResponse(candidates=[candidate])


def _make_web_chunk(uri: str, title: str, domain: str = None) -> types.GroundingChunk:
    return types.GroundingChunk(
        web=types.GroundingChunkWeb(uri=uri, title=title, domain=domain)
    )


def _make_mock_content_client(json_body: dict) -> MagicMock:
    """Mock client for analyze_content (Call 1) — structured response."""
    mock = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(json_body)
    mock_resp.candidates = [MagicMock()]
    mock_resp.candidates[0].finish_reason = FinishReason.STOP
    mock_resp.candidates[0].content = MagicMock()
    mock_resp.candidates[0].content.parts = [MagicMock()]
    mock_resp.prompt_feedback = None
    mock.models.generate_content.return_value = mock_resp
    return mock


# Minimal valid ContentAnalysis payload
MOCK_CONTENT_ANALYSIS_OUTPUT = {
    "normalized_text": ORIGINAL_TEXT,
    "language": {"code": "en", "name": "English", "confidence": 0.99},
    "claims": [
        {"id": "claim-1", "statement": "SBI is offering a ₹50,000 cash prize.", "category": "benefit_claim", "claim_type": "factual", "importance": "high", "confidence": 0.95},
        {"id": "claim-2", "statement": "Recipients must pay ₹499.", "category": "payment_instruction", "claim_type": "behavioral_instruction", "importance": "high", "confidence": 0.90},
    ],
    "entities": [{"name": "SBI", "type": "financial_institution", "context": "Mentioned as prize giver", "confidence": 0.98}],
    "urls": [{"url": "https://sbi.fake", "domain": "sbi.fake", "context": "Prize claim link"}],
    "suspicious_signals": [
        {"type": "advance_payment_request", "description": "Requires upfront fee", "confidence": 0.97, "evidence": "Pay ₹499"}
    ],
}


# ---------------------------------------------------------------------------
# Tier Classification Tests
# ---------------------------------------------------------------------------

def test_tier_classification_official():
    assert _classify_tier("https://rbi.org.in/advisory/123", "rbi.org.in") == "tier_1_official"

def test_tier_classification_gov_heuristic():
    assert _classify_tier("https://cybercrime.gov.in/report", None) == "tier_1_official"

def test_tier_classification_authoritative():
    assert _classify_tier("https://timesofindia.com/story", "timesofindia.com") == "tier_2_authoritative"

def test_tier_classification_secondary():
    assert _classify_tier("https://myblog.example.com/post", None) == "tier_3_secondary"

def test_tier_classification_none_url():
    assert _classify_tier(None, None) == "unverified"


# ---------------------------------------------------------------------------
# Snippet Extraction Tests
# ---------------------------------------------------------------------------

def test_extract_snippet_finds_relevant_sentence():
    text = "SBI has warned customers about fraudulent lottery scams. Users should not pay upfront fees."
    snippet = _extract_snippet(text, "SBI lottery warning", "https://rbi.org.in")
    assert "SBI" in snippet or "lottery" in snippet

def test_extract_snippet_no_text():
    snippet = _extract_snippet(None, "SBI", "https://example.com")
    assert "https://example.com" in snippet

def test_extract_snippet_fallback():
    long_text = "A" * 500
    snippet = _extract_snippet(long_text, "UnknownTitle", "https://x.com")
    assert len(snippet) <= 303  # 300 + "..."


# ---------------------------------------------------------------------------
# _normalize_grounding_chunks Tests
# ---------------------------------------------------------------------------

def test_normalize_chunks_rbi_official():
    chunks = [_make_web_chunk("https://rbi.org.in/advisory", "RBI Advisory", "rbi.org.in")]
    sources = _normalize_grounding_chunks(chunks, SAMPLE_CLAIMS, "RBI has warned about lottery fraud.")
    assert len(sources) == 1
    assert sources[0].tier == "tier_1_official"
    assert sources[0].confidence >= 0.90
    assert sources[0].url == "https://rbi.org.in/advisory"
    assert sources[0].publisher == "rbi.org.in"

def test_normalize_chunks_multiple():
    chunks = [
        _make_web_chunk("https://rbi.org.in/advisory", "RBI Advisory", "rbi.org.in"),
        _make_web_chunk("https://timesofindia.com/sbi-scam", "TOI Report", "timesofindia.com"),
        _make_web_chunk("https://someblog.com/warning", "Blog Post", None),
    ]
    sources = _normalize_grounding_chunks(chunks, SAMPLE_CLAIMS, "Evidence text here.")
    assert len(sources) == 3
    tiers = {s.tier for s in sources}
    assert "tier_1_official" in tiers
    assert "tier_2_authoritative" in tiers

def test_normalize_chunks_caps_at_eight():
    chunks = [
        _make_web_chunk(f"https://example{i}.com/page", f"Source {i}")
        for i in range(12)
    ]
    sources = _normalize_grounding_chunks(chunks, SAMPLE_CLAIMS, "text")
    assert len(sources) == 8

def test_normalize_chunks_skips_non_web():
    # Chunk without web sub-field
    empty_chunk = types.GroundingChunk(web=None)
    sources = _normalize_grounding_chunks([empty_chunk], SAMPLE_CLAIMS, "text")
    assert len(sources) == 0

def test_normalize_chunks_is_simulated_demo_false():
    """Real grounding chunks MUST have is_simulated_demo=False."""
    # EvidenceSourceSchema doesn't have is_simulated_demo; that lives on EvidenceSource
    # Verify the mapping in investigation_service instead (see integration test below)
    chunks = [_make_web_chunk("https://rbi.org.in/a", "RBI")]
    sources = _normalize_grounding_chunks(chunks, SAMPLE_CLAIMS, "text")
    assert len(sources) == 1
    # EvidenceSourceSchema is the raw schema; is_simulated_demo is set to False in _map_evidence_source


# ---------------------------------------------------------------------------
# ground_claims() Tests (mocked Gemini client)
# ---------------------------------------------------------------------------

def test_ground_claims_success():
    mock_client = MagicMock()
    grounding_resp = _make_grounding_response(
        chunks=[
            _make_web_chunk("https://rbi.org.in/advisory", "RBI Fraud Advisory", "rbi.org.in"),
            _make_web_chunk("https://timesofindia.com/story", "TOI Story", "timesofindia.com"),
        ],
        text="RBI has warned against SBI lottery scams. Do not pay advance fees.",
        search_queries=["SBI lottery fraud advisory RBI"],
    )
    mock_client.models.generate_content.return_value = grounding_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.SUCCESS
    assert result.failure_category is None
    assert result.is_grounded is True
    assert len(result.sources) == 2
    assert result.sources[0].tier == "tier_1_official"
    assert len(result.grounding_search_queries) == 1


def test_ground_claims_empty_chunks():
    """Grounding call succeeds, but returns 0 chunks -> NO_EVIDENCE (not FAILED)."""
    mock_client = MagicMock()
    grounding_resp = _make_grounding_response(chunks=[], text="Some text but no chunks.")
    mock_client.models.generate_content.return_value = grounding_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
    assert result.failure_category is None
    assert result.is_grounded is False
    assert result.sources == []


def test_ground_claims_no_grounding_metadata():
    """Response with no grounding_metadata returns NO_EVIDENCE, not FAILED."""
    mock_client = MagicMock()
    candidate = types.Candidate(
        finish_reason=FinishReason.STOP,
        content=types.Content(parts=[types.Part.from_text(text="Some text.")]),
        grounding_metadata=None,
    )
    mock_resp = types.GenerateContentResponse(candidates=[candidate])
    mock_client.models.generate_content.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
    assert result.failure_category is None
    assert result.is_grounded is False


def test_ground_claims_safety_block():
    """Safety-blocked grounding response returns FAILED with INVALID_RESPONSE."""
    mock_client = MagicMock()
    candidate = types.Candidate(
        finish_reason=FinishReason.SAFETY,
        content=None,
    )
    mock_resp = types.GenerateContentResponse(candidates=[candidate])
    mock_client.models.generate_content.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.INVALID_RESPONSE
    assert result.is_grounded is False


def test_ground_claims_no_candidates():
    """Empty candidates list returns FAILED with INVALID_RESPONSE."""
    mock_client = MagicMock()
    mock_resp = types.GenerateContentResponse(candidates=[])
    mock_client.models.generate_content.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.INVALID_RESPONSE
    assert result.is_grounded is False


def test_ground_claims_api_exception():
    """ServerError returns FAILED with PROVIDER_ERROR."""
    from google.genai import errors
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = errors.ServerError(503, "Service unavailable", None)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.PROVIDER_ERROR
    assert result.is_grounded is False


def test_ground_claims_auth_error():
    """Authentication 401/403 returns FAILED with AUTHENTICATION."""
    from google.genai import errors
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = errors.ClientError(401, "API_KEY_INVALID", None)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.AUTHENTICATION
    assert result.is_grounded is False


def test_ground_claims_rate_limit_error():
    """Rate limit 429 returns FAILED with RATE_LIMIT."""
    from google.genai import errors
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = errors.ClientError(429, "RESOURCE_EXHAUSTED", None)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.RATE_LIMIT
    assert result.is_grounded is False


def test_ground_claims_network_error():
    """Connection/network error returns FAILED with NETWORK."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = ConnectionError("Failed to establish a new connection")

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.NETWORK
    assert result.is_grounded is False


def test_ground_claims_missing_configuration():
    """Missing GEMINI_MODEL or GEMINI_API_KEY returns FAILED with INVALID_CONFIGURATION."""
    mock_client = MagicMock()

    with patch.dict(os.environ, {"GEMINI_MODEL": "", "GEMINI_API_KEY": ""}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.INVALID_CONFIGURATION
    assert result.is_grounded is False
    mock_client.models.generate_content.assert_not_called()


def test_ground_claims_unknown_exception():
    """Unclassified runtime exception returns FAILED with UNKNOWN."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("Something completely unexpected happened")

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims(SAMPLE_CLAIMS, ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.FAILED
    assert result.failure_category == FailureCategory.UNKNOWN
    assert result.is_grounded is False


def test_ground_claims_empty_claims():
    """Empty claims list returns NO_EVIDENCE, no API call made."""
    mock_client = MagicMock()

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = ground_claims([], ORIGINAL_TEXT, client=mock_client)

    assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
    assert result.failure_category is None
    assert result.is_grounded is False
    mock_client.models.generate_content.assert_not_called()


# ---------------------------------------------------------------------------
# Investigation Pipeline Integration Tests (Phase 4C)
# ---------------------------------------------------------------------------

def _make_two_call_client(
    content_json: dict,
    grounding_resp: types.GenerateContentResponse,
) -> MagicMock:
    """
    Mock client that returns:
      - Call 1 (structured JSON): content_json text response
      - Call 2 (grounding): grounding_resp
    """
    mock = MagicMock()
    # Call 1 response: structured JSON via MagicMock text property
    call1_resp = MagicMock()
    call1_resp.text = json.dumps(content_json)
    call1_resp.candidates = [MagicMock()]
    call1_resp.candidates[0].finish_reason = FinishReason.STOP
    call1_resp.candidates[0].content = MagicMock()
    call1_resp.candidates[0].content.parts = [MagicMock()]
    call1_resp.prompt_feedback = None
    # Call 2 response: real grounding response
    mock.models.generate_content.side_effect = [call1_resp, grounding_resp]
    return mock


def test_investigate_with_real_grounding():
    """End-to-end: real grounding chunks produce is_simulated_demo=False evidence and SUCCESS status."""
    grounding_resp = _make_grounding_response(
        chunks=[
            _make_web_chunk("https://rbi.org.in/advisory/lottery", "RBI Lottery Warning", "rbi.org.in"),
        ],
        text="RBI warns: no legitimate bank runs lottery schemes requiring advance payment.",
        search_queries=["SBI lottery cash prize scam"],
    )
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, grounding_resp)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(
            input_type="text",
            content=ORIGINAL_TEXT,
            metadata={"run_truth_assessment": False},
        )
        result = investigate(request, gemini_client=mock_client)

    assert isinstance(result, InvestigationResult)
    assert result.evidence_retrieval_status == RetrievalStatus.SUCCESS
    assert result.evidence_failure_category is None
    # Should have real grounded evidence
    assert len(result.evidence) == 1
    assert result.evidence[0].is_simulated_demo is False
    assert result.evidence[0].tier.value == "tier_1_official"
    assert "SOURCE(S) GROUNDED" in result.headline_verdict
    # Gemini was called twice: Call 1 = content analysis, Call 2 = grounding
    assert mock_client.models.generate_content.call_count == 2


def test_investigate_grounding_unavailable_placeholder():
    """When grounding fails, a single is_simulated_demo=True placeholder is returned with FAILED status."""
    # Call 2 returns empty candidates (grounding fails)
    failed_grounding = types.GenerateContentResponse(candidates=[])
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, failed_grounding)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        result = investigate(request, gemini_client=mock_client)

    assert isinstance(result, InvestigationResult)
    assert result.evidence_retrieval_status == RetrievalStatus.FAILED
    assert result.evidence_failure_category == FailureCategory.INVALID_RESPONSE
    assert len(result.evidence) == 1
    assert result.evidence[0].is_simulated_demo is True
    assert result.evidence[0].id == "ev-retrieval-failed"
    assert "EVIDENCE RETRIEVAL FAILED" in result.headline_verdict


def test_investigate_no_evidence_state():
    """When grounding succeeds but returns 0 chunks, status is NO_EVIDENCE, distinct from FAILED."""
    empty_grounding = _make_grounding_response(chunks=[], text="No evidence found for these claims.")
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, empty_grounding)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        result = investigate(request, gemini_client=mock_client)

    assert isinstance(result, InvestigationResult)
    assert result.evidence_retrieval_status == RetrievalStatus.NO_EVIDENCE
    assert result.evidence_failure_category is None
    assert len(result.evidence) == 1
    assert result.evidence[0].is_simulated_demo is True
    assert result.evidence[0].id == "ev-no-sources"
    assert "NO SOURCES RETRIEVED" in result.headline_verdict


def test_failed_retrieval_is_not_truth_verdict():
    """
    Critical requirement: Failed evidence retrieval must NOT be converted into:
      - "Cannot Confirm" as a truth verdict conclusion
      - "Insufficient Evidence" as a truth verdict conclusion
      - FALSE
      - or any other truth verdict.
    A failed retrieval means the engine does not yet have sufficient evidence to make an assessment.
    """
    from google.genai import errors
    mock = MagicMock()
    call1_resp = MagicMock()
    call1_resp.text = json.dumps(MOCK_CONTENT_ANALYSIS_OUTPUT)
    call1_resp.candidates = [MagicMock()]
    call1_resp.candidates[0].finish_reason = FinishReason.STOP
    call1_resp.candidates[0].content = MagicMock()
    call1_resp.candidates[0].content.parts = [MagicMock()]
    call1_resp.prompt_feedback = None

    # Call 2 throws 429 Rate limit error
    mock.models.generate_content.side_effect = [
        call1_resp,
        errors.ClientError(429, "RESOURCE_EXHAUSTED", None),
    ]

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        result = investigate(request, gemini_client=mock)

    assert result.evidence_retrieval_status == RetrievalStatus.FAILED
    assert result.evidence_failure_category == FailureCategory.RATE_LIMIT
    # Verify claims do not assert a false truth verdict
    for claim in result.claims:
        assert "evidence assessment is pending" in claim.explanation
    # Verify evidence placeholder explains retrieval failed, not that evidence doesn't exist
    assert result.evidence[0].id == "ev-retrieval-failed"
    assert "does not yet have sufficient evidence to make an assessment" in result.evidence[0].excerpt
    assert "does not yet have sufficient evidence to make an assessment" in result.summary_explanation
    # Headline verdict clearly states retrieval failed, does not assert FALSE
    assert "EVIDENCE RETRIEVAL FAILED" in result.headline_verdict
    assert "FALSE" not in result.headline_verdict


def test_investigate_evidence_claim_mapping():
    """Claims should carry ev-ids that match real grounded sources."""
    grounding_resp = _make_grounding_response(
        chunks=[
            _make_web_chunk("https://rbi.org.in/advisory", "RBI Advisory", "rbi.org.in"),
            _make_web_chunk("https://ndtv.com/story", "NDTV Story", "ndtv.com"),
        ],
        search_queries=["SBI lottery fraud", "advance fee scam India"],
    )
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, grounding_resp)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(
            input_type="text",
            content=ORIGINAL_TEXT,
            metadata={"run_truth_assessment": False},
        )
        result = investigate(request, gemini_client=mock_client)

    # All evidence ref ids should reference actual evidence IDs
    all_ev_ids = {e.id for e in result.evidence}
    for claim in result.claims:
        for ref_id in claim.evidence_ref_ids:
            assert ref_id in all_ev_ids, f"Claim {claim.id} references missing ev id {ref_id}"


def test_no_fabricated_evidence():
    """Evidence sources must only come from grounding_chunks — URL must be real or None."""
    grounding_resp = _make_grounding_response(
        chunks=[_make_web_chunk("https://cert-in.org.in/advisory", "CERT-In Advisory", "cert-in.org.in")],
    )
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, grounding_resp)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(
            input_type="text",
            content=ORIGINAL_TEXT,
            metadata={"run_truth_assessment": False},
        )
        result = investigate(request, gemini_client=mock_client)

    for ev in result.evidence:
        if ev.url:
            # URL must come from real grounding — not a .example fake domain
            assert ".example" not in ev.url, f"Fabricated URL found: {ev.url}"


# ---------------------------------------------------------------------------
# Truth Assessment Lifecycle Tests (Phase 4C Final Review)
# ---------------------------------------------------------------------------

def test_truth_assessment_not_yet_performed():
    """
    State 1: Truth assessment not yet performed.
    - truth_assessment_status is NOT_ASSESSED
    - truth_status is None (NOT 'CANNOT CONFIRM'!)
    - Each claim has truth_assessment_status=NOT_ASSESSED and truth_status=None
    """
    grounding_resp = _make_grounding_response(
        chunks=[_make_web_chunk("https://rbi.org.in/advisory", "RBI Advisory", "rbi.org.in")],
    )
    mock_client = _make_two_call_client(MOCK_CONTENT_ANALYSIS_OUTPUT, grounding_resp)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(
            input_type="text",
            content=ORIGINAL_TEXT,
            metadata={"run_truth_assessment": False},
        )
        result = investigate(request, gemini_client=mock_client)

    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    assert result.truth_status is None
    for claim in result.claims:
        assert claim.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert claim.truth_status is None


def test_evidence_retrieval_failed_before_assessment():
    """
    State 2: Evidence retrieval failed before assessment.
    - evidence_retrieval_status is FAILED
    - truth_assessment_status remains NOT_ASSESSED
    - truth_status is None (failure is NOT converted into a truth verdict!)
    - Operational failure is visible via evidence_retrieval_status and failure_category
    """
    from google.genai import errors
    mock = MagicMock()
    call1_resp = MagicMock()
    call1_resp.text = json.dumps(MOCK_CONTENT_ANALYSIS_OUTPUT)
    call1_resp.candidates = [MagicMock()]
    call1_resp.candidates[0].finish_reason = FinishReason.STOP
    call1_resp.candidates[0].content = MagicMock()
    call1_resp.candidates[0].content.parts = [MagicMock()]
    call1_resp.prompt_feedback = None

    # Call 2 throws 401 Authentication error
    mock.models.generate_content.side_effect = [
        call1_resp,
        errors.ClientError(401, "API_KEY_INVALID", None),
    ]

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        result = investigate(request, gemini_client=mock)

    assert result.evidence_retrieval_status == RetrievalStatus.FAILED
    assert result.evidence_failure_category == FailureCategory.AUTHENTICATION
    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    assert result.truth_status is None
    for claim in result.claims:
        assert claim.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert claim.truth_status is None


def test_assessment_performed_with_insufficient_evidence():
    """
    State 3: Assessment performed with insufficient evidence.
    - Preserves CANNOT CONFIRM as a legitimate future verdict when assessment HAS been performed.
    - truth_assessment_status is ASSESSED
    - truth_status is CANNOT_CONFIRM
    """
    claim = Claim(
        id="cl-1",
        claim_number=1,
        statement="A fee is required to unlock winnings.",
        truth_status=TruthStatus.CANNOT_CONFIRM,
        truth_assessment_status=TruthAssessmentStatus.ASSESSED,
        confidence=0.85,
        category="advance_fee",
        explanation="Assessment performed; available external sources are insufficient to corroborate or refute.",
        evidence_ref_ids=["ev-1"],
    )

    assert claim.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert claim.truth_status == TruthStatus.CANNOT_CONFIRM
    assert claim.truth_status.value == "CANNOT CONFIRM"


def test_assessment_performed_with_supported_or_contradicted_claim():
    """
    State 4: Assessment performed with a supported or contradicted claim.
    - Verifies VERIFIED, FALSE, and PARTIALLY SUPPORTED verdicts when assessment is performed.
    """
    verified_claim = Claim(
        id="cl-1",
        claim_number=1,
        statement="RBI is India's central bank.",
        truth_status=TruthStatus.VERIFIED,
        truth_assessment_status=TruthAssessmentStatus.ASSESSED,
        confidence=0.99,
        category="factual_assertion",
        explanation="Corroborated by official government gazettes.",
        evidence_ref_ids=["ev-1"],
    )
    false_claim = Claim(
        id="cl-2",
        claim_number=2,
        statement="SBI is running an online lottery requiring ₹499 fee.",
        truth_status=TruthStatus.FALSE,
        truth_assessment_status=TruthAssessmentStatus.ASSESSED,
        confidence=0.97,
        category="benefit_lure",
        explanation="Contradicted by official bank bulletins.",
        evidence_ref_ids=["ev-2"],
    )
    partial_claim = Claim(
        id="cl-3",
        claim_number=3,
        statement="Bank interest rates changed recently.",
        truth_status=TruthStatus.PARTIALLY_SUPPORTED,
        truth_assessment_status=TruthAssessmentStatus.ASSESSED,
        confidence=0.80,
        category="factual_assertion",
        explanation="Partially supported; rates changed for select tenors only.",
        evidence_ref_ids=["ev-3"],
    )

    assert verified_claim.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert verified_claim.truth_status == TruthStatus.VERIFIED

    assert false_claim.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert false_claim.truth_status == TruthStatus.FALSE

    assert partial_claim.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert partial_claim.truth_status == TruthStatus.PARTIALLY_SUPPORTED


def test_stage_attribution_content_failure_deterministic_fallback():
    """Verify stage attribution when Content Intelligence encounters RATE_LIMIT:
    1. content_extraction_mode is DETERMINISTIC_FALLBACK
    2. content_analysis_failure_category is RATE_LIMIT
    3. evidence_retrieval_status is SKIPPED (NOT FAILED)
    4. evidence_failure_category is None (retrieval was not attempted)
    5. No claims state Gemini 3.8 Flash performed extraction
    6. Truth status is NOT_ASSESSED
    7. Heuristic scam risk assessment is preserved and succeeds.
    """
    from app.services.gemini_service import GeminiRateLimitError
    from app.schemas.investigation import ScamAssessmentStatus

    mock_client = MagicMock()
    with patch("app.services.investigation_service.analyze_content", side_effect=GeminiRateLimitError("Rate limit")):
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
            request = InvestigationRequest(
                input_type="text",
                content="Congratulations! You won ₹50,000. Pay ₹499 fee within 2 hours.",
            )
            result = investigate(request, gemini_client=mock_client)

    assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
    assert result.content_analysis_failure_category == FailureCategory.RATE_LIMIT
    assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED
    assert result.evidence_failure_category is None
    assert len(result.evidence) == 1
    assert result.evidence[0].id == "ev-retrieval-skipped"
    assert "Evidence Retrieval Skipped" in result.evidence[0].title
    assert "EVIDENCE RETRIEVAL SKIPPED" in result.headline_verdict
    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    assert result.truth_status is None

    # Verify no claims claim Gemini 3.8 Flash extracted it
    assert "Gemini 3.8 Flash decomposed" not in result.summary_explanation
    assert "Deterministic heuristic parser extracted" in result.summary_explanation
    for claim in result.claims:
        assert "Extracted by Gemini 3.8 Flash" not in claim.explanation
        assert "Extracted via deterministic heuristic extraction" in claim.explanation
        assert claim.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert claim.truth_status is None

    # Verify scam risk assessment is preserved and succeeds
    assert result.scam_assessment_status == ScamAssessmentStatus.ASSESSED
    assert result.scam_risk_score is not None
    assert result.scam_risk_score > 0


def test_stage_attribution_evidence_retrieval_failure_distinguished():
    """Verify stage attribution when Content Intelligence SUCCEEDS but Evidence Retrieval FAILS:
    1. content_extraction_mode is GEMINI_LLM
    2. content_analysis_failure_category is None
    3. evidence_retrieval_status is FAILED (not SKIPPED)
    4. evidence_failure_category is RATE_LIMIT
    5. Truth status is NOT_ASSESSED
    """
    from google.genai import errors

    mock = MagicMock()
    call1_resp = MagicMock()
    call1_resp.text = json.dumps(MOCK_CONTENT_ANALYSIS_OUTPUT)
    call1_resp.candidates = [MagicMock()]
    call1_resp.candidates[0].finish_reason = FinishReason.STOP
    call1_resp.candidates[0].content = MagicMock()
    call1_resp.candidates[0].content.parts = [MagicMock()]
    call1_resp.prompt_feedback = None

    # Call 2 throws 429 Rate limit error during grounding
    mock.models.generate_content.side_effect = [
        call1_resp,
        errors.ClientError(429, "RESOURCE_EXHAUSTED", None),
    ]

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        result = investigate(request, gemini_client=mock)

    assert result.content_extraction_mode == "GEMINI_LLM"
    assert result.content_analysis_failure_category is None
    assert result.evidence_retrieval_status == RetrievalStatus.FAILED
    assert result.evidence_failure_category == FailureCategory.RATE_LIMIT
    assert result.evidence[0].id == "ev-retrieval-failed"
    assert "EVIDENCE RETRIEVAL FAILED" in result.headline_verdict
    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    assert result.truth_status is None
    assert "Gemini 3.8 Flash decomposed" in result.summary_explanation

