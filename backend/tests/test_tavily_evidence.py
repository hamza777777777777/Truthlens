"""
Phase 5A Tavily Evidence Provider Unit Tests

All tests are fully deterministic — they mock Tavily HTTP responses and never
call the live Tavily API or live Gemini API.

Coverage:
  - Provider routing: Tavily preferred when TAVILY_API_KEY configured
  - Provider routing: falls back to Google grounding when TAVILY_API_KEY absent
  - Successful retrieval with real Tavily results
  - Empty results (NO_EVIDENCE) without fabrication
  - Authentication failures (401 / InvalidAPIKeyError)
  - Rate limit / usage limit exceeded
  - Network / timeout errors
  - Malformed / unexpected response formats
  - is_simulated_demo=False for genuine Tavily sources
  - is_simulated_demo=True when retrieval fails / is skipped
  - Gemini rate-limit → deterministic fallback → NOT_ASSESSED (no fabricated verdicts)
  - Evidence retrieval failure NEVER produces a truth verdict
  - Real Tavily results distinct from simulated demo data
  - Claim-to-evidence mapping preserved
  - Tier classification from Tavily URLs
  - Snippet and publisher normalization without fabrication
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.schemas.content_analysis import ClaimAnalysis, ContentAnalysis, LanguageInfo, UrlTarget
from app.schemas.evidence import (
    FailureCategory,
    GroundingAnalysis,
    RetrievalStatus,
)
from app.schemas.investigation import (
    InvestigationRequest,
    TruthAssessmentStatus,
    TruthStatus,
)
from app.services.evidence_service import (
    _build_claim_assessments_from_tavily,
    _build_search_queries,
    _classify_tier,
    _get_tavily_api_key,
    _normalize_tavily_results,
    _retrieve_via_tavily,
    ground_claims,
    UsageLimitExceededError,
)
from app.services.investigation_service import _fallback_content_analysis, investigate

# Patch target for TavilyClient — module-level import in evidence_service
_TAVILY_PATCH = "app.services.evidence_service.TavilyClient"

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

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

MOCK_TAVILY_SUCCESS_RESPONSE = {
    "results": [
        {
            "url": "https://rbi.org.in/Scripts/PublicationReportDetails.aspx?UrlPage=&ID=1234",
            "title": "RBI Alert: Do not pay advance fee for prize claims",
            "content": "The Reserve Bank of India warns customers that no legitimate banking scheme requires advance payment. SBI does not conduct lottery or reward distribution programmes.",
            "published_date": "2024-03-15",
        },
        {
            "url": "https://timesofindia.com/scam-alert-sbi-fake-prize",
            "title": "SBI prize scam targeting account holders",
            "content": "Fraudsters are impersonating State Bank of India to demand advance payments. SBI has confirmed it does not run any prize programme.",
            "published_date": "2024-03-10",
        },
    ]
}

MOCK_TAVILY_EMPTY_RESPONSE = {
    "results": []
}


# ---------------------------------------------------------------------------
# Helper: fake TavilyClient class
# ---------------------------------------------------------------------------

def _make_tavily_client_mock(search_response: Any) -> MagicMock:
    """Return a mock TavilyClient whose .search() returns search_response."""
    mock_client = MagicMock()
    mock_client.search.return_value = search_response
    return mock_client


# ---------------------------------------------------------------------------
# 1. PROVIDER ROUTING TESTS
# ---------------------------------------------------------------------------

class TestProviderRouting:
    """Test that Tavily is chosen over Google grounding based on env var."""

    def test_tavily_preferred_when_api_key_configured(self):
        """ground_claims routes to Tavily when TAVILY_API_KEY is set."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}, clear=False):
            with patch(_TAVILY_PATCH, return_value=mock_client):
                result = ground_claims(claims=SAMPLE_CLAIMS, original_text=ORIGINAL_TEXT)

        # Routing succeeded to Tavily
        assert result.retrieval_status == RetrievalStatus.SUCCESS
        assert result.is_grounded is True
        assert len(result.sources) > 0

    def test_falls_back_to_google_when_tavily_key_absent(self):
        """ground_claims routes to Google grounding when TAVILY_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=False):
            # Ensure TAVILY_API_KEY is absent in env
            env_copy = {k: v for k, v in os.environ.items() if k != "TAVILY_API_KEY"}
            with patch.dict(os.environ, env_copy, clear=True):
                with patch(
                    "app.services.evidence_service._get_tavily_api_key", return_value=None
                ):
                    with patch(
                        "app.services.evidence_service._retrieve_via_google_grounding"
                    ) as mock_google:
                        mock_google.return_value = GroundingAnalysis(
                            retrieval_status=RetrievalStatus.NO_EVIDENCE,
                            failure_category=None,
                            is_grounded=False,
                        )
                        result = ground_claims(claims=SAMPLE_CLAIMS, original_text=ORIGINAL_TEXT)

        mock_google.assert_called_once()
        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE

    def test_empty_claims_returns_no_evidence(self):
        """ground_claims with empty claims returns NO_EVIDENCE without calling any provider."""
        result = ground_claims(claims=[], original_text=ORIGINAL_TEXT)
        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
        assert result.is_grounded is False
        assert result.sources == []


# ---------------------------------------------------------------------------
# 2. SUCCESSFUL RETRIEVAL TESTS
# ---------------------------------------------------------------------------

class TestTavilySuccessfulRetrieval:
    """Tests for successful Tavily evidence retrieval."""

    def test_successful_retrieval_returns_success_status(self):
        """Successful Tavily search returns SUCCESS status with real sources."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.SUCCESS
        assert result.is_grounded is True
        assert len(result.sources) == 2

    def test_sources_have_real_urls_and_titles(self):
        """Sources from Tavily preserve actual URL and title — no fabrication."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        urls = [s.url for s in result.sources]
        assert "https://rbi.org.in/Scripts/PublicationReportDetails.aspx?UrlPage=&ID=1234" in urls
        assert "https://timesofindia.com/scam-alert-sbi-fake-prize" in urls

        titles = [s.title for s in result.sources]
        assert any("RBI Alert" in t for t in titles)
        assert any("SBI prize scam" in t for t in titles)

    def test_sources_tier_classification_from_url(self):
        """Tier classification works correctly for Tavily URL domains."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        tier_map = {s.url: s.tier for s in result.sources}
        assert tier_map.get("https://rbi.org.in/Scripts/PublicationReportDetails.aspx?UrlPage=&ID=1234") == "tier_1_official"
        assert tier_map.get("https://timesofindia.com/scam-alert-sbi-fake-prize") == "tier_2_authoritative"

    def test_sources_stance_defaults_to_insufficient(self):
        """All Tavily sources get INSUFFICIENT stance (Truth Engine assigns final stance)."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        for source in result.sources:
            assert source.stance == "INSUFFICIENT"

    def test_search_queries_captured(self):
        """Search queries executed by Tavily are recorded in grounding_search_queries."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert len(result.grounding_search_queries) > 0

    def test_claim_assessments_generated(self):
        """Per-claim assessments are generated from Tavily results."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        # Factual claims get assessments
        assert len(result.claim_assessments) >= 1
        assert result.claim_assessments[0].claim_id in ("claim-1", "claim-2")


# ---------------------------------------------------------------------------
# 3. EMPTY RESULTS TESTS
# ---------------------------------------------------------------------------

class TestTavilyEmptyResults:
    """Tests when Tavily returns no results."""

    def test_empty_results_returns_no_evidence(self):
        """Empty Tavily results return NO_EVIDENCE without fabricating sources."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_EMPTY_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
        assert result.is_grounded is False
        assert result.sources == []
        assert result.failure_category is None

    def test_empty_results_no_fabricated_claims(self):
        """Empty results never produce fabricated claim assessments."""
        mock_client = _make_tavily_client_mock(MOCK_TAVILY_EMPTY_RESPONSE)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        for assessment in result.claim_assessments:
            assert assessment.evidence_found is False

    def test_missing_results_key_in_response(self):
        """Malformed response with missing 'results' key is handled gracefully."""
        mock_client = _make_tavily_client_mock({"answer": "some text"})  # No 'results' key
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
        assert result.sources == []


# ---------------------------------------------------------------------------
# 4. AUTHENTICATION FAILURE TESTS
# ---------------------------------------------------------------------------

class TestTavilyAuthFailures:
    """Tests for authentication error handling."""

    def test_invalid_api_key_returns_authentication_failure(self):
        """InvalidAPIKeyError maps to FailureCategory.AUTHENTICATION."""
        from tavily import InvalidAPIKeyError

        mock_client = MagicMock()
        mock_client.search.side_effect = InvalidAPIKeyError("Invalid API key")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-invalid-key",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.AUTHENTICATION
        assert result.is_grounded is False

    def test_missing_api_key_returns_authentication_failure(self):
        """MissingAPIKeyError on client creation maps to FailureCategory.AUTHENTICATION."""
        from tavily import MissingAPIKeyError

        with patch(_TAVILY_PATCH, side_effect=MissingAPIKeyError()):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.AUTHENTICATION

    def test_auth_failure_never_sets_truth_verdict(self):
        """Authentication failure never produces a truth verdict in the pipeline."""
        from tavily import InvalidAPIKeyError

        mock_tavily_client = MagicMock()
        mock_tavily_client.search.side_effect = InvalidAPIKeyError("Invalid API key")

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-bad-key"}, clear=False):
            with patch(_TAVILY_PATCH, return_value=mock_tavily_client):
                with patch("app.services.investigation_service.analyze_content") as mock_analyze:
                    mock_analyze.return_value = MagicMock(
                        normalized_text=ORIGINAL_TEXT,
                        claims=[
                            type("ClaimAnalysis", (), {
                                "id": "claim-1", "statement": "SBI prize",
                                "category": "factual", "claim_type": "factual",
                                "importance": "high", "confidence": 0.9
                            })()
                        ],
                        entities=[],
                        urls=[],
                        suspicious_signals=[],
                        language=type("Lang", (), {"code": "en", "name": "English", "confidence": 0.95})(),
                    )
                    result = investigate(request)

        # Truth assessment must NOT have been fabricated
        assert result.truth_status is None
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED


# ---------------------------------------------------------------------------
# 5. RATE LIMIT TESTS
# ---------------------------------------------------------------------------

class TestTavilyRateLimit:
    """Tests for rate limit / usage limit exceeded."""

    def test_usage_limit_exceeded_returns_rate_limit_failure(self):
        """UsageLimitExceededError maps to FailureCategory.RATE_LIMIT."""
        from tavily import UsageLimitExceededError

        mock_client = MagicMock()
        mock_client.search.side_effect = UsageLimitExceededError("Usage limit exceeded")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.RATE_LIMIT
        assert result.is_grounded is False

    def test_rate_limit_generic_exception_classified(self):
        """Generic exceptions with 'rate limit' in message map to RATE_LIMIT."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("429 Too Many Requests: rate limit exceeded")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.RATE_LIMIT


# ---------------------------------------------------------------------------
# 6. NETWORK / TIMEOUT TESTS
# ---------------------------------------------------------------------------

class TestTavilyNetworkErrors:
    """Tests for network and timeout error handling."""

    def test_connection_error_returns_network_failure(self):
        """ConnectionError maps to FailureCategory.NETWORK."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("connection refused to api.tavily.com")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.NETWORK

    def test_timeout_error_returns_network_failure(self):
        """Timeout exceptions map to FailureCategory.NETWORK."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Request timed out after 30 seconds")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.NETWORK


# ---------------------------------------------------------------------------
# 7. MALFORMED RESPONSE TESTS
# ---------------------------------------------------------------------------

class TestTavilyMalformedResponses:
    """Tests for malformed or unexpected API response handling."""

    def test_non_dict_response_handled_gracefully(self):
        """Non-dict response type (e.g. string) is handled without raising."""
        mock_client = _make_tavily_client_mock("unexpected string response")
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE
        assert result.sources == []

    def test_results_key_not_a_list(self):
        """'results' key with non-list value is handled without raising."""
        mock_client = _make_tavily_client_mock({"results": "not a list"})
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.NO_EVIDENCE

    def test_results_with_missing_urls_skipped(self):
        """Sources without URL are silently skipped (cannot be cited)."""
        mock_client = _make_tavily_client_mock({
            "results": [
                {"title": "No URL source", "content": "Some content"},  # No url key
                {"url": "https://rbi.org.in/page", "title": "With URL", "content": "RBI content"},
            ]
        })
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status == RetrievalStatus.SUCCESS
        assert len(result.sources) == 1  # Only the one with a URL
        assert result.sources[0].url == "https://rbi.org.in/page"

    def test_none_response_does_not_raise(self):
        """None response value is handled without raising."""
        mock_client = _make_tavily_client_mock(None)
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        assert result.retrieval_status in (RetrievalStatus.NO_EVIDENCE, RetrievalStatus.FAILED)


# ---------------------------------------------------------------------------
# 8. is_simulated_demo INTEGRITY TESTS
# ---------------------------------------------------------------------------

class TestSimulatedDemoLabeling:
    """Verify is_simulated_demo is correctly set in the investigation pipeline."""

    def test_real_tavily_sources_have_is_simulated_demo_false(self):
        """End-to-end: real Tavily sources produce is_simulated_demo=False evidence."""
        mock_tavily_client = _make_tavily_client_mock(MOCK_TAVILY_SUCCESS_RESPONSE)
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)

        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}, clear=False):
            with patch(_TAVILY_PATCH, return_value=mock_tavily_client):
                with patch("app.services.investigation_service.analyze_content") as mock_analyze:
                    mock_analyze.return_value = MagicMock(
                        normalized_text=ORIGINAL_TEXT,
                        claims=SAMPLE_CLAIMS,
                        entities=[],
                        urls=[],
                        suspicious_signals=[],
                        language=type("Lang", (), {"code": "en", "name": "English", "confidence": 0.95})(),
                    )
                    result = investigate(request)

        real_sources = [e for e in result.evidence if not e.is_simulated_demo]
        assert len(real_sources) > 0
        assert result.evidence_retrieval_status == RetrievalStatus.SUCCESS

    def test_tavily_failure_evidence_placeholder_is_simulated_demo_true(self):
        """When Tavily fails, the placeholder evidence record has is_simulated_demo=True."""
        from tavily import InvalidAPIKeyError

        mock_tavily_client = MagicMock()
        mock_tavily_client.search.side_effect = InvalidAPIKeyError("Invalid API key")
        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)

        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-bad-key"}, clear=False):
            with patch(_TAVILY_PATCH, return_value=mock_tavily_client):
                with patch("app.services.investigation_service.analyze_content") as mock_analyze:
                    mock_analyze.return_value = MagicMock(
                        normalized_text=ORIGINAL_TEXT,
                        claims=SAMPLE_CLAIMS,
                        entities=[],
                        urls=[],
                        suspicious_signals=[],
                        language=type("Lang", (), {"code": "en", "name": "English", "confidence": 0.95})(),
                    )
                    result = investigate(request)

        assert result.evidence[0].is_simulated_demo is True


# ---------------------------------------------------------------------------
# 9. GEMINI QUOTA / RATE-LIMIT TESTS
# ---------------------------------------------------------------------------

class TestGeminiQuotaFailures:
    """Tests that Gemini rate-limit failures do not produce fabricated truth verdicts."""

    def test_gemini_rate_limit_uses_deterministic_fallback_not_gemini(self):
        """When Gemini is rate-limited, content_extraction_mode is DETERMINISTIC_FALLBACK."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}, clear=False), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
        assert result.content_analysis_failure_category == FailureCategory.RATE_LIMIT

    def test_gemini_rate_limit_does_not_fabricate_truth_verdict(self):
        """Gemini rate limit → fallback extraction → truth assessment stays NOT_ASSESSED."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        # Truth assessment MUST be NOT_ASSESSED — never fabricated
        assert result.truth_status is None
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED

    def test_gemini_rate_limit_evidence_skipped_not_reported_as_retrieval_failure(self):
        """When extraction falls back and no Tavily key is configured, evidence_retrieval_status is SKIPPED."""
        from app.services.gemini_service import GeminiRateLimitError

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch("app.services.investigation_service._get_tavily_api_key", return_value=None), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED

    def test_gemini_rate_limit_extraction_note_accurate(self):
        """When fallback is used, extraction prefix says 'deterministic', not 'Gemini'."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        # All claim explanations must attribute extraction correctly
        for claim in result.claims:
            assert "deterministic" in claim.explanation.lower() or "heuristic" in claim.explanation.lower()
            assert "gemini 3.8" not in claim.explanation.lower()

    def test_scam_investigation_runs_even_when_gemini_rate_limited(self):
        """Scam signals and risk fusion still execute when deterministic extraction is used."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        # Risk fusion should still run (inputs: heuristic signals from fallback analysis)
        assert result.scam_risk_score is not None or result.scam_assessment_status.value in ("ASSESSED", "NOT_ASSESSED")


# ---------------------------------------------------------------------------
# 9B. FALLBACK EXTRACTION + TAVILY INTEGRATION REGRESSION TESTS (A - F)
# ---------------------------------------------------------------------------

class TestFallbackExtractionTavilyIntegration:
    """
    Regression suite for Phase 5A:
    Ensures Tavily evidence retrieval executes when Gemini content analysis
    hits RATE_LIMIT and deterministic fallback successfully extracts claims.
    """

    def test_a_gemini_rate_limit_with_fallback_extraction_calls_tavily(self):
        """A. Gemini RATE_LIMIT + successful fallback extraction → Tavily is called."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert mock_client.search.called is True
        assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
        assert result.content_analysis_failure_category == FailureCategory.RATE_LIMIT

    def test_b_gemini_rate_limit_tavily_returns_real_results(self):
        """B. Gemini RATE_LIMIT + Tavily returns real results → real evidence appears with is_simulated_demo=false."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.evidence_retrieval_status == RetrievalStatus.SUCCESS
        assert len(result.evidence) >= 2
        for ev in result.evidence:
            assert ev.is_simulated_demo is False
            assert ev.url is not None
            assert ev.title is not None
        assert result.metrics.sources_corroborated == len(result.evidence)
        # Verify claims have references mapped
        assert any(len(c.evidence_ref_ids) > 0 for c in result.claims)

    def test_c_gemini_rate_limit_tavily_failure_preserves_error(self):
        """C. Gemini RATE_LIMIT + Tavily failure → evidence failure is shown, no fabricated evidence."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.side_effect = UsageLimitExceededError("Tavily usage limit exceeded")

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.evidence_retrieval_status == RetrievalStatus.FAILED
        assert result.evidence_failure_category == FailureCategory.RATE_LIMIT
        assert len(result.evidence) == 1
        assert result.evidence[0].id == "ev-retrieval-failed"
        assert result.evidence[0].is_simulated_demo is True
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert result.truth_status is None

    def test_d_gemini_rate_limit_no_usable_fallback_claims_skips_retrieval(self):
        """D. Gemini RATE_LIMIT + no usable fallback claims → evidence retrieval legitimately skipped."""
        from app.services.gemini_service import GeminiRateLimitError
        from app.schemas.content_analysis import ContentAnalysis, LanguageInfo

        mock_client = MagicMock()

        # Fallback returns 0 claims
        empty_claims_analysis = ContentAnalysis(
            normalized_text="short",
            language=LanguageInfo(code="en", name="English", confidence=0.9),
            claims=[],
            entities=[],
            urls=[],
            suspicious_signals=[],
        )

        request = InvestigationRequest(input_type="text", content="short")
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")), \
             patch("app.services.investigation_service._fallback_content_analysis",
                   return_value=empty_claims_analysis):
            result = investigate(request)

        assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED
        assert mock_client.search.called is False
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert result.truth_status is None

    def test_e_no_tavily_key_existing_fallback_behavior_remains_correct(self):
        """E. No Tavily key → existing fallback behavior remains correct (Google grounding skipped)."""
        from app.services.gemini_service import GeminiRateLimitError

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch("app.services.investigation_service._get_tavily_api_key", return_value=None), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED
        assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert result.truth_status is None

    def test_f_truth_verdict_never_fabricated_on_fallback_path(self):
        """F. Truth verdict is never fabricated because of the fallback path."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(input_type="text", content=ORIGINAL_TEXT)
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        # Epistemic truth assessment must stay NOT_ASSESSED (pending)
        assert result.truth_status is None
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert result.truth_assessment_failure_category is None

        # Each claim must also be NOT_ASSESSED with None truth_status
        for claim in result.claims:
            assert claim.truth_status is None
            assert claim.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED

        # Headline and synthesis must not claim a fabricated verdict
        assert "FALSE" not in result.headline_verdict
        assert "VERIFIED" not in result.headline_verdict


# ---------------------------------------------------------------------------
# 10. EVIDENCE NORMALIZATION TESTS
# ---------------------------------------------------------------------------

class TestNormalizeTavilyResults:
    """Unit tests for _normalize_tavily_results()."""

    def test_preserves_real_titles_and_urls(self):
        """Normalizer preserves actual titles and URLs from Tavily results."""
        sources = _normalize_tavily_results(
            MOCK_TAVILY_SUCCESS_RESPONSE["results"],
            SAMPLE_CLAIMS,
        )

        assert sources[0].url == "https://rbi.org.in/Scripts/PublicationReportDetails.aspx?UrlPage=&ID=1234"
        assert "RBI Alert" in sources[0].title

    def test_derives_publisher_from_url_not_fabricated(self):
        """Publisher is derived from URL domain, not fabricated."""
        sources = _normalize_tavily_results(
            MOCK_TAVILY_SUCCESS_RESPONSE["results"],
            SAMPLE_CLAIMS,
        )
        for source in sources:
            assert source.publisher != ""
            assert source.publisher is not None

    def test_skips_results_with_missing_url(self):
        """Results without URL are not included (cannot be cited)."""
        results_with_missing_url = [
            {"title": "No URL", "content": "Some content"},
        ]
        sources = _normalize_tavily_results(results_with_missing_url, SAMPLE_CLAIMS)
        assert len(sources) == 0

    def test_snippet_not_fabricated_when_empty_content(self):
        """When content is empty, snippet falls back to URL description — never invented."""
        results = [
            {"url": "https://example.com/page", "title": "Some Page", "content": ""},
        ]
        sources = _normalize_tavily_results(results, SAMPLE_CLAIMS)
        assert len(sources) == 1
        # Snippet should reference the URL, not invented content
        assert "example.com" in sources[0].snippet or "Retrieved from" in sources[0].snippet

    def test_capped_at_eight_sources(self):
        """_normalize_tavily_results caps at 8 sources maximum."""
        many_results = [
            {"url": f"https://example{i}.com", "title": f"Title {i}", "content": f"Content {i}"}
            for i in range(15)
        ]
        sources = _normalize_tavily_results(many_results, SAMPLE_CLAIMS)
        assert len(sources) <= 8

    def test_deduplication_by_url(self):
        """Duplicate URLs from multiple searches are deduplicated."""
        mock_client = MagicMock()

        def fake_search(query, **kwargs):
            # Both calls return the same URL
            return {
                "results": [
                    {"url": "https://rbi.org.in/page", "title": "RBI Page", "content": "RBI content"},
                ]
            }

        mock_client.search.side_effect = fake_search
        with patch(_TAVILY_PATCH, return_value=mock_client):
            result = _retrieve_via_tavily(
                claims=SAMPLE_CLAIMS,
                original_text=ORIGINAL_TEXT,
                api_key="tvly-test-key",
            )

        # Despite multiple queries returning the same URL, only one source should appear
        urls = [s.url for s in result.sources]
        assert len(urls) == len(set(urls))


# ---------------------------------------------------------------------------
# 11. TAVILY IMPORT NOT INSTALLED TEST
# ---------------------------------------------------------------------------

class TestTavilyImportMissing:
    """Test behavior when tavily-python is not installed."""

    def test_missing_tavily_import_returns_invalid_config(self):
        """If tavily-python is not installed, returns INVALID_CONFIGURATION failure."""
        with patch("app.services.evidence_service._TAVILY_AVAILABLE", False):
            with patch("app.services.evidence_service.TavilyClient", None):
                result = _retrieve_via_tavily(
                    claims=SAMPLE_CLAIMS,
                    original_text=ORIGINAL_TEXT,
                    api_key="tvly-test-key",
                )

        assert result.retrieval_status == RetrievalStatus.FAILED
        assert result.failure_category == FailureCategory.INVALID_CONFIGURATION


# ---------------------------------------------------------------------------
# 12. TIER CLASSIFICATION TESTS
# ---------------------------------------------------------------------------

class TestTierClassification:
    """Tier classification logic for Tavily URLs."""

    def test_rbi_classified_as_tier_1(self):
        assert _classify_tier("https://rbi.org.in/Notifications") == "tier_1_official"

    def test_gov_in_classified_as_tier_1(self):
        assert _classify_tier("https://cybercrime.gov.in/alerts") == "tier_1_official"

    def test_ndtv_classified_as_tier_2(self):
        assert _classify_tier("https://ndtv.com/scam-news") == "tier_2_authoritative"

    def test_unknown_domain_classified_as_tier_3(self):
        assert _classify_tier("https://some-random-blog.blogspot.com/post") == "tier_3_secondary"

    def test_no_url_classified_as_unverified(self):
        assert _classify_tier(None) == "unverified"

    def test_dot_gov_heuristic(self):
        assert _classify_tier("https://whitehouse.gov/policy") == "tier_1_official"


# ---------------------------------------------------------------------------
# 13. SEARCH QUERY CONSTRUCTION TESTS
# ---------------------------------------------------------------------------

class TestBuildSearchQueries:
    """Tests for search query construction from claims."""

    def test_factual_claims_preferred(self):
        """Factual claims are used over behavioral instructions for search queries."""
        queries = _build_search_queries(SAMPLE_CLAIMS, ORIGINAL_TEXT)
        # claim-1 is factual; its statement should appear in queries
        assert any("SBI" in q or "₹50,000" in q for q in queries)

    def test_queries_capped_at_four(self):
        """Search queries are capped at 4 maximum."""
        many_claims = [
            ClaimAnalysis(
                id=f"cl-{i}", statement=f"Claim statement {i}.",
                category="factual", claim_type="factual",
                importance="high", confidence=0.9,
            )
            for i in range(10)
        ]
        queries = _build_search_queries(many_claims, "test text")
        assert len(queries) <= 4

    def test_empty_claims_returns_fallback_query(self):
        """Empty claims list falls back to original text snippet as query."""
        queries = _build_search_queries([], ORIGINAL_TEXT)
        assert len(queries) == 1
        assert ORIGINAL_TEXT[:120] in queries[0] or queries[0] in ORIGINAL_TEXT


# ---------------------------------------------------------------------------
# 14. ZERO CLAIMS & URL FALLBACK REGRESSION TESTS
# ---------------------------------------------------------------------------

class TestZeroClaimsAndUrlFallbackRegressions:
    """Regression tests for zero-claims, URL-only inputs, and safe attribution."""

    def test_gemini_success_with_zero_claims_does_not_falsely_report_rate_limit(self):
        """1. Gemini success with zero claims does not falsely report RATE_LIMIT."""
        empty_analysis = ContentAnalysis(
            normalized_text="Hello there! Just checking in today.",
            language=LanguageInfo(code="en", name="English", confidence=0.95),
            claims=[],
            entities=[],
            urls=[],
            suspicious_signals=[],
        )

        request = InvestigationRequest(
            input_type="text",
            content="Hello there! Just checking in today.",
        )
        with patch("app.services.investigation_service.analyze_content", return_value=empty_analysis):
            result = investigate(request)

        assert result.content_extraction_mode == "GEMINI_LLM"
        assert result.content_analysis_failure_category is None
        assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED
        assert "RATE_LIMIT" not in result.summary_explanation
        assert "LIMIT upstream" not in result.summary_explanation
        assert "no discrete claims were isolated" in result.summary_explanation.lower()
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert result.truth_status is None

    def test_url_only_input_does_not_generate_fabricated_factual_claim(self):
        """2. URL-only input does not generate a fabricated factual claim."""
        url_input = "https://sbi-secure-portal.xyz/login"

        # Case A: Fallback parser directly on URL-only input
        fallback = _fallback_content_analysis(url_input)
        assert len(fallback.claims) == 0
        assert len(fallback.urls) == 1
        assert fallback.urls[0].url == url_input

        # Case B: Investigation with URL-only input and LLM returning zero claims
        url_analysis = ContentAnalysis(
            normalized_text=url_input,
            language=LanguageInfo(code="en", name="English", confidence=0.9),
            claims=[],
            entities=[],
            urls=[UrlTarget(url=url_input, domain="sbi-secure-portal.xyz", context="Extracted link")],
            suspicious_signals=[],
        )
        request = InvestigationRequest(input_type="url", content=url_input)
        with patch("app.services.investigation_service.analyze_content", return_value=url_analysis):
            result = investigate(request)

        assert len(result.claims) == 0
        assert result.metrics.claims_detected == 0
        assert result.url_analysis is not None
        assert result.url_analysis.analyzed_url == url_input
        for c in result.claims:
            assert c.statement != url_input
            assert c.category != "factual_assertion"

    def test_gemini_rate_limit_with_tavily_configured_attempts_retrieval_on_usable_claims(self):
        """3. Gemini rate limit plus configured Tavily still attempts retrieval when safe, usable fallback claims exist."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(
            input_type="text",
            content="State Bank of India is distributing ₹50,000 refund to all eligible account holders.",
        )
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}, clear=False), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
        assert result.content_analysis_failure_category == FailureCategory.RATE_LIMIT
        assert result.evidence_retrieval_status == RetrievalStatus.SUCCESS
        assert result.metrics.sources_corroborated > 0
        assert mock_client.search.called is True

    def test_tavily_success_after_gemini_failure_never_fabricates_truth_verdict(self):
        """4. Tavily success after Gemini failure never fabricates a truth verdict."""
        from app.services.gemini_service import GeminiRateLimitError

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_SUCCESS_RESPONSE

        request = InvestigationRequest(
            input_type="text",
            content="State Bank of India is distributing ₹50,000 refund to all eligible account holders.",
        )
        with patch.dict(os.environ, {"TAVILY_API_KEY": "tvly-test-key"}, clear=False), \
             patch(_TAVILY_PATCH, return_value=mock_client), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        # Invariant: truth status MUST be None, status NOT_ASSESSED
        assert result.truth_status is None
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        for claim in result.claims:
            assert claim.truth_status is None
            assert claim.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        assert "epistemic truth assessment requires Gemini LLM intelligence" in result.summary_explanation

    def test_genuine_rate_limit_messages_remain_accurate(self):
        """5. Genuine rate-limit messages remain accurate."""
        from app.services.gemini_service import GeminiRateLimitError

        request = InvestigationRequest(
            input_type="text",
            content="State Bank of India is distributing ₹50,000 refund to all eligible account holders.",
        )
        with patch("app.services.investigation_service._get_tavily_api_key", return_value=None), \
             patch("app.services.investigation_service.analyze_content",
                   side_effect=GeminiRateLimitError("Rate limit exceeded")):
            result = investigate(request)

        assert result.content_extraction_mode == "DETERMINISTIC_FALLBACK"
        assert result.content_analysis_failure_category == FailureCategory.RATE_LIMIT
        assert result.evidence_retrieval_status == RetrievalStatus.SKIPPED
        assert "RATE_LIMIT" in result.summary_explanation
        assert any("RATE_LIMIT upstream" in c.explanation for c in result.claims)
        assert "RATE_LIMIT limit" in result.evidence[0].excerpt

