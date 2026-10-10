"""
TruthLens Phase 4D — Deterministic Truth Engine Tests

Comprehensive deterministic test suite covering all 17 requirements of Section 9:
1. Directly supported claim (VERIFIED)
2. Directly contradicted claim (FALSE)
3. Partially supported claim (PARTIALLY SUPPORTED)
4. Outdated claim with adequate temporal evidence (OUTDATED)
5. Inconclusive assessment with insufficient evidence (CANNOT CONFIRM)
6. Conflicting credible sources (downgraded to CANNOT CONFIRM / conflict documented)
7. Low-tier evidence that does not adequately establish a material claim (downgraded to CANNOT CONFIRM)
8. Duplicate or non-independent sources
9. Unknown claim IDs and evidence IDs (hallucinated IDs stripped and sanitized)
10. Malformed or invalid structured output (FAILED / INVALID_RESPONSE, not CANNOT CONFIRM)
11. Gemini safety-blocked or empty response (FAILED / INVALID_RESPONSE)
12. Evidence retrieval FAILED (truth_status=None, NOT_ASSESSED)
13. Evidence retrieval NO_EVIDENCE (ASSESSED, CANNOT CONFIRM)
14. Truth Engine provider failure (FAILED, safe failure category, not CANNOT CONFIRM)
15. Preservation of demo/simulated evidence labels (is_simulated_demo=True cannot verify live claims)
16. No assessment or verdict fabricated when upstream operation fails
17. End-to-end investigation pipeline integration with full claim-to-assessment path
"""
import json
import os
from typing import Any, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors, types
from google.genai.types import FinishReason

from app.schemas.evidence import FailureCategory, RetrievalStatus
from app.schemas.investigation import (
    Claim,
    EvidenceSource,
    InvestigationRequest,
    InvestigationResult,
    SourceStance,
    SourceTier,
    TruthAssessmentStatus,
    TruthStatus,
)
from app.schemas.truth_assessment import (
    SingleClaimAssessment,
    TruthEngineBatchResponse,
)
from app.services.investigation_service import investigate
from app.services.truth_engine import (
    TruthEngineResult,
    evaluate_truth,
)

@pytest.fixture(autouse=True)
def disable_tavily_for_truth_tests(monkeypatch):
    """Ensure Tavily is not active during Truth Engine unit tests."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


def _make_claim(
    claim_id: str = "cl-1",
    num: int = 1,
    statement: str = "SBI provides a ₹50,000 cash grant.",
    ev_refs: Optional[List[str]] = None,
) -> Claim:
    return Claim(
        id=claim_id,
        claim_number=num,
        statement=statement,
        truth_status=None,
        truth_assessment_status=TruthAssessmentStatus.NOT_ASSESSED,
        confidence=0.9,
        category="benefit_lure",
        explanation="Extracted atomic claim.",
        evidence_ref_ids=ev_refs or [],
    )


def _make_evidence_source(
    ev_id: str = "ev-1",
    publisher: str = "rbi.org.in",
    tier: SourceTier = SourceTier.TIER_1_OFFICIAL,
    tier_label: str = "Official / Government Source",
    stance: SourceStance = SourceStance.CORROBORATES,
    excerpt: str = "Official bulletin confirms the policy.",
    published_date: Optional[str] = None,
    is_simulated_demo: bool = False,
    url: Optional[str] = "https://rbi.org.in/bulletin",
) -> EvidenceSource:
    return EvidenceSource(
        id=ev_id,
        title=f"Source {ev_id}",
        publisher=publisher,
        url=url,
        published_date=published_date,
        tier=tier,
        tier_label=tier_label,
        stance=stance,
        confidence_score=0.95,
        excerpt=excerpt,
        is_simulated_demo=is_simulated_demo,
    )


def _make_mock_gemini_client(batch_resp: TruthEngineBatchResponse) -> MagicMock:
    """Mock client returning structured TruthEngineBatchResponse."""
    mock = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = batch_resp.model_dump_json()
    mock_resp.candidates = [MagicMock()]
    mock_resp.candidates[0].finish_reason = FinishReason.STOP
    mock_resp.candidates[0].content = MagicMock()
    mock_resp.candidates[0].content.parts = [MagicMock()]
    mock_resp.prompt_feedback = None
    mock.models.generate_content.return_value = mock_resp
    return mock


# ---------------------------------------------------------------------------
# 1. Directly Supported Claim (VERIFIED)
# ---------------------------------------------------------------------------
def test_1_directly_supported_claim():
    claim = _make_claim(statement="RBI regulates commercial banks in India.", ev_refs=["ev-1"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="rbi.org.in",
            tier=SourceTier.TIER_1_OFFICIAL,
            stance=SourceStance.CORROBORATES,
            excerpt="The Reserve Bank of India is the central banking and regulatory authority.",
        )
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="VERIFIED",
                confidence=0.98,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=[],
                reasoning="The official RBI portal explicitly confirms statutory central regulatory authority.",
                limitations="",
            )
        ],
        overall_synthesis="Claim verified by primary regulatory documentation.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert result.overall_truth_status == TruthStatus.VERIFIED
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.VERIFIED
    assert assessed.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert assessed.confidence == 0.98
    assert assessed.supporting_evidence_ref_ids == ["ev-1"]
    assert assessed.contradicting_evidence_ref_ids == []
    assert "RBI" in assessed.explanation


# ---------------------------------------------------------------------------
# 2. Directly Contradicted Claim (FALSE)
# ---------------------------------------------------------------------------
def test_2_directly_contradicted_claim():
    claim = _make_claim(statement="SBI operates an unadvertised online lottery requiring ₹499 upfront fee.", ev_refs=["ev-1"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="sbi.co.in",
            tier=SourceTier.TIER_1_OFFICIAL,
            stance=SourceStance.CONTRADICTS,
            excerpt="State Bank of India clarifies that it never conducts prize lotteries or asks for advance processing charges.",
        )
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="FALSE",
                confidence=0.97,
                supporting_evidence_ids=[],
                contradicting_evidence_ids=["ev-1"],
                reasoning="Directly refuted by authentic State Bank of India security bulletins.",
                limitations="",
            )
        ],
        overall_synthesis="Primary claim refuted by official bank warnings.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.overall_truth_status == TruthStatus.FALSE
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.FALSE
    assert assessed.contradicting_evidence_ref_ids == ["ev-1"]
    assert assessed.supporting_evidence_ref_ids == []


# ---------------------------------------------------------------------------
# 3. Partially Supported Claim (PARTIALLY SUPPORTED)
# ---------------------------------------------------------------------------
def test_3_partially_supported_claim():
    claim = _make_claim(
        statement="Government launched national digital subsidy and requires instant ₹500 verification fee.",
        ev_refs=["ev-1", "ev-2"],
    )
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="pib.gov.in",
            tier=SourceTier.TIER_1_OFFICIAL,
            stance=SourceStance.CORROBORATES,
            excerpt="Government announces Direct Benefit Transfer expansion across digital channels.",
        ),
        _make_evidence_source(
            ev_id="ev-2",
            publisher="cybercrime.gov.in",
            tier=SourceTier.TIER_1_OFFICIAL,
            stance=SourceStance.CONTRADICTS,
            excerpt="No government welfare program requires citizen payments or fee transfers to disburse subsidies.",
        ),
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="PARTIALLY SUPPORTED",
                confidence=0.88,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=["ev-2"],
                reasoning="The DBT welfare initiative is authentic, but the requirement for a ₹500 fee is an advance-fee fraud.",
                limitations="Subsidy authentic; payment demand fraudulent.",
            )
        ],
        overall_synthesis="Welfare program verified; fee condition refuted.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.overall_truth_status == TruthStatus.PARTIALLY_SUPPORTED
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.PARTIALLY_SUPPORTED
    assert assessed.supporting_evidence_ref_ids == ["ev-1"]
    assert assessed.contradicting_evidence_ref_ids == ["ev-2"]
    assert "fraud" in assessed.explanation or "fee" in assessed.explanation


# ---------------------------------------------------------------------------
# 4. Outdated Claim with Adequate Temporal Evidence (OUTDATED)
# ---------------------------------------------------------------------------
def test_4_outdated_claim_temporal_evidence():
    claim = _make_claim(statement="Fixed deposit interest rate is 8.5% at HDFC Bank.", ev_refs=["ev-1"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="livemint.com",
            tier=SourceTier.TIER_2_AUTHORITATIVE,
            published_date="2023-01-15",
            excerpt="In January 2023, senior citizen FD peaked at 8.5%, but rates were revised downward in subsequent quarters.",
        )
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="OUTDATED",
                confidence=0.91,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=[],
                reasoning="Rate was accurate in early 2023 but has since been revised per subsequent regulatory cycles.",
                limitations="Historical rate corroborated by 2023 archival records; superseded in current fiscal schedule.",
            )
        ],
        overall_synthesis="Claim represents superseded historical information.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.overall_truth_status == TruthStatus.OUTDATED
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.OUTDATED
    assert "2023" in assessed.explanation or "revised" in assessed.explanation


# ---------------------------------------------------------------------------
# 5. Inconclusive Assessment with Insufficient Evidence (CANNOT CONFIRM)
# ---------------------------------------------------------------------------
def test_5_inconclusive_insufficient_evidence():
    claim = _make_claim(statement="CEO John Doe attended an unannounced closed-door conference yesterday.", ev_refs=["ev-1"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="techblog.example",
            tier=SourceTier.TIER_3_SECONDARY,
            stance=SourceStance.INSUFFICIENT,
            excerpt="Rumors circulated online that top tech executives may meet this week.",
        )
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="CANNOT CONFIRM",
                confidence=0.45,
                supporting_evidence_ids=[],
                contradicting_evidence_ids=[],
                reasoning="Available secondary source only cites rumors and lacks concrete verification of attendance.",
                limitations="No primary or authoritative records corroborating or refuting meeting participation.",
            )
        ],
        overall_synthesis="Evidence is insufficient to confirm or refute assertion.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.overall_truth_status == TruthStatus.CANNOT_CONFIRM
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.CANNOT_CONFIRM
    assert assessed.confidence <= 0.6


# ---------------------------------------------------------------------------
# 6. Conflicting Credible Sources (Safeguard Downgrade to CANNOT CONFIRM)
# ---------------------------------------------------------------------------
def test_6_conflicting_credible_sources():
    claim = _make_claim(statement="Company X announced a merger with Company Y.", ev_refs=["ev-1", "ev-2"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="reuters.com",
            tier=SourceTier.TIER_2_AUTHORITATIVE,
            stance=SourceStance.CORROBORATES,
            excerpt="Reuters reported sources confirming merger negotiations concluded successfully.",
        ),
        _make_evidence_source(
            ev_id="ev-2",
            publisher="bloomberg.com",
            tier=SourceTier.TIER_2_AUTHORITATIVE,
            stance=SourceStance.CONTRADICTS,
            excerpt="Bloomberg reported official spokespersons denying any signed merger agreement.",
        ),
    ]
    # Model mistakenly proposed VERIFIED despite direct conflict between 2 tier-2 sources
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="VERIFIED",
                confidence=0.90,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=["ev-2"],
                reasoning="Reuters cited confirming sources.",
                limitations="Bloomberg simultaneously reported denial.",
            )
        ],
        overall_synthesis="Conflicting reports from reputable agencies.",
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    # Deterministic safeguard must downgrade VERIFIED with conflicting credible sources to CANNOT CONFIRM
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.CANNOT_CONFIRM
    assert "conflict" in (assessed.limitations or "").lower()


# ---------------------------------------------------------------------------
# 7. Low-Tier Evidence Alone Cannot Verify (Safeguard Downgrade)
# ---------------------------------------------------------------------------
def test_7_low_tier_evidence_cannot_verify():
    claim = _make_claim(statement="Government is distributing ₹100,000 to every citizen next Monday.", ev_refs=["ev-1"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="unverified-blog.xyz",
            tier=SourceTier.TIER_3_SECONDARY,
            stance=SourceStance.CORROBORATES,
            excerpt="Anonymous post alleges massive welfare distribution next week.",
        )
    ]
    # Model tried to mark VERIFIED based only on Tier 3 blog
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="VERIFIED",
                confidence=0.85,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=[],
                reasoning="Blog post mentions the payout.",
                limitations="",
            )
        ]
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    # Low-tier evidence alone cannot verify -> downgraded to CANNOT_CONFIRM
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.CANNOT_CONFIRM
    assert "low-tier" in (assessed.limitations or "").lower() or "unverified" in (assessed.limitations or "").lower()


# ---------------------------------------------------------------------------
# 8. Duplicate or Non-Independent Sources
# ---------------------------------------------------------------------------
def test_8_duplicate_non_independent_sources():
    claim = _make_claim(statement="Crypto platform offering guaranteed 500% monthly yield.", ev_refs=["ev-1", "ev-2"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-1",
            publisher="crypto-promoter1.xyz",
            tier=SourceTier.TIER_3_SECONDARY,
            stance=SourceStance.CORROBORATES,
            excerpt="Join now for guaranteed 500% monthly return.",
        ),
        _make_evidence_source(
            ev_id="ev-2",
            publisher="crypto-promoter2.xyz",
            tier=SourceTier.TIER_3_SECONDARY,
            stance=SourceStance.CORROBORATES,
            excerpt="Join now for guaranteed 500% monthly return.",  # verbatim copied
        ),
    ]
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="CANNOT CONFIRM",
                confidence=0.40,
                supporting_evidence_ids=["ev-1", "ev-2"],
                contradicting_evidence_ids=[],
                reasoning="Identical syndicated promotional blurbs across unverified domains do not establish independent corroboration.",
                limitations="Copied secondary blurbs without financial registry or regulatory registration.",
            )
        ]
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assert result.overall_truth_status == TruthStatus.CANNOT_CONFIRM
    assert result.claims[0].truth_status == TruthStatus.CANNOT_CONFIRM


# ---------------------------------------------------------------------------
# 9. Unknown Claim IDs and Evidence IDs Handled Safely
# ---------------------------------------------------------------------------
def test_9_unknown_claim_ids_and_evidence_ids():
    claim = _make_claim(claim_id="cl-real", statement="Factual claim", ev_refs=["ev-real"])
    evidence = [_make_evidence_source(ev_id="ev-real", publisher="rbi.org.in")]

    # Model returned unknown claim id "cl-hallucinated" and hallucinated evidence "ev-phantom"
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-hallucinated",
                verdict="VERIFIED",
                confidence=0.99,
                supporting_evidence_ids=["ev-phantom"],
                contradicting_evidence_ids=[],
                reasoning="Hallucinated claim reasoning.",
                limitations="",
            ),
            SingleClaimAssessment(
                claim_id="cl-real",
                verdict="VERIFIED",
                confidence=0.95,
                supporting_evidence_ids=["ev-real", "ev-phantom"],  # ev-phantom is fake
                contradicting_evidence_ids=["ev-nonexistent"],      # fake
                reasoning="Legitimate reasoning on real claim.",
                limitations="",
            ),
        ]
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    # cl-real was assessed, cl-hallucinated was discarded
    assert len(result.claims) == 1
    assessed = result.claims[0]
    assert assessed.id == "cl-real"
    # Hallucinated evidence IDs stripped: ev-phantom and ev-nonexistent must be absent
    assert assessed.supporting_evidence_ref_ids == ["ev-real"]
    assert assessed.contradicting_evidence_ref_ids == []


# ---------------------------------------------------------------------------
# 10. Malformed or Invalid Structured Output (FAILED lifecycle)
# ---------------------------------------------------------------------------
def test_10_malformed_invalid_structured_output():
    claim = _make_claim()
    evidence = [_make_evidence_source()]

    mock = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "{ malformed json: not valid ... "
    mock_resp.candidates = [MagicMock()]
    mock_resp.candidates[0].finish_reason = FinishReason.STOP
    mock_resp.candidates[0].content = MagicMock()
    mock_resp.candidates[0].content.parts = [MagicMock()]
    mock_resp.prompt_feedback = None
    mock.models.generate_content.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=mock)

    assert result.truth_assessment_status == TruthAssessmentStatus.FAILED
    assert result.truth_assessment_failure_category == FailureCategory.INVALID_RESPONSE
    assert result.overall_truth_status is None
    assert result.claims[0].truth_status is None
    assert result.claims[0].truth_assessment_status == TruthAssessmentStatus.FAILED


# ---------------------------------------------------------------------------
# 11. Gemini Safety-Blocked or Empty Response
# ---------------------------------------------------------------------------
def test_11_gemini_safety_blocked_response():
    claim = _make_claim()
    evidence = [_make_evidence_source()]

    mock = MagicMock()
    mock_resp = MagicMock()
    mock_resp.candidates = [MagicMock()]
    mock_resp.candidates[0].finish_reason = FinishReason.SAFETY
    mock_resp.candidates[0].content = MagicMock()
    mock_resp.candidates[0].content.parts = [MagicMock()]
    mock_resp.prompt_feedback = None
    mock.models.generate_content.return_value = mock_resp

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=mock)

    assert result.truth_assessment_status == TruthAssessmentStatus.FAILED
    assert result.truth_assessment_failure_category == FailureCategory.INVALID_RESPONSE
    assert result.overall_truth_status is None
    assert result.claims[0].truth_status is None


# ---------------------------------------------------------------------------
# 12. Evidence Retrieval FAILED (Truth Engine does not run)
# ---------------------------------------------------------------------------
def test_12_evidence_retrieval_failed_preserves_not_assessed():
    claim = _make_claim()
    evidence = [_make_evidence_source()]
    client = MagicMock()

    result = evaluate_truth(
        claims=[claim],
        evidence=evidence,
        retrieval_status=RetrievalStatus.FAILED,
        retrieval_failure_category=FailureCategory.NETWORK,
        client=client,
    )

    # Must NOT call Gemini or fabricate a verdict
    client.models.generate_content.assert_not_called()
    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    assert result.overall_truth_status is None
    assert result.claims[0].truth_status is None
    assert result.claims[0].truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED


# ---------------------------------------------------------------------------
# 13. Evidence Retrieval NO_EVIDENCE (Completes with CANNOT CONFIRM)
# ---------------------------------------------------------------------------
def test_13_evidence_retrieval_no_evidence_completes_cannot_confirm():
    claim = _make_claim(statement="Obscure entity launched private promotion.")
    client = MagicMock()

    result = evaluate_truth(
        claims=[claim],
        evidence=[],
        retrieval_status=RetrievalStatus.NO_EVIDENCE,
        client=client,
    )

    # Completed assessment with CANNOT CONFIRM per specification
    client.models.generate_content.assert_not_called()
    assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert result.overall_truth_status == TruthStatus.CANNOT_CONFIRM
    assessed = result.claims[0]
    assert assessed.truth_status == TruthStatus.CANNOT_CONFIRM
    assert assessed.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert "absence of search results" in assessed.explanation.lower() or "no usable" in assessed.explanation.lower()


# ---------------------------------------------------------------------------
# 14. Truth Engine Provider Failure (Safe Failure Category, not CANNOT CONFIRM)
# ---------------------------------------------------------------------------
def test_14_truth_engine_provider_failure():
    claim = _make_claim()
    evidence = [_make_evidence_source()]

    mock = MagicMock()
    mock.models.generate_content.side_effect = errors.ClientError(429, "RESOURCE_EXHAUSTED", None)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=mock)

    assert result.truth_assessment_status == TruthAssessmentStatus.FAILED
    assert result.truth_assessment_failure_category == FailureCategory.RATE_LIMIT
    assert result.overall_truth_status is None
    # Crucial: Provider error must NOT be masked as CANNOT CONFIRM
    assert result.claims[0].truth_status is None
    assert result.claims[0].truth_assessment_status == TruthAssessmentStatus.FAILED


# ---------------------------------------------------------------------------
# 15. Preservation of Demo/Simulated Evidence Labels (Cannot verify live)
# ---------------------------------------------------------------------------
def test_15_demo_simulated_evidence_cannot_verify_live():
    claim = _make_claim(statement="Claim supported only by synthetic test harness.", ev_refs=["ev-sim"])
    evidence = [
        _make_evidence_source(
            ev_id="ev-sim",
            publisher="Simulated Portal",
            tier=SourceTier.TIER_1_OFFICIAL,
            stance=SourceStance.CORROBORATES,
            is_simulated_demo=True,  # Synthetic test data
        )
    ]
    # Model attempted to output VERIFIED based on demo data
    batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="cl-1",
                verdict="VERIFIED",
                confidence=0.99,
                supporting_evidence_ids=["ev-sim"],
                contradicting_evidence_ids=[],
                reasoning="Simulated bulletin says verified.",
                limitations="",
            )
        ]
    )
    client = _make_mock_gemini_client(batch)

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        result = evaluate_truth([claim], evidence, RetrievalStatus.SUCCESS, client=client)

    assessed = result.claims[0]
    # Safeguard downgrade: synthetic demo evidence cannot establish live verification
    assert assessed.truth_status == TruthStatus.CANNOT_CONFIRM
    assert "simulated" in (assessed.limitations or "").lower() or "demo" in (assessed.limitations or "").lower()


# ---------------------------------------------------------------------------
# 16. No Assessment or Verdict Fabricated When Upstream Fails
# ---------------------------------------------------------------------------
def test_16_no_verdict_fabricated_on_upstream_failure():
    claims = [_make_claim(claim_id="c1"), _make_claim(claim_id="c2")]
    evidence = [_make_evidence_source(ev_id="e1")]
    client = MagicMock()

    result = evaluate_truth(
        claims=claims,
        evidence=evidence,
        retrieval_status=RetrievalStatus.FAILED,
        retrieval_failure_category=FailureCategory.AUTHENTICATION,
        client=client,
    )

    client.models.generate_content.assert_not_called()
    assert result.overall_truth_status is None
    assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
    for c in result.claims:
        assert c.truth_status is None
        assert c.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED


# ---------------------------------------------------------------------------
# 17. End-to-End Investigation Pipeline Integration (Full Path)
# ---------------------------------------------------------------------------
def test_17_full_pipeline_claim_to_assessment_integration():
    """Verify entire 3-call investigation pipeline: content -> grounding -> truth engine."""
    # Call 1 payload (Content Analysis)
    content_json = {
        "normalized_text": "RBI is India's central bank.",
        "language": {"code": "en", "name": "English", "confidence": 0.99},
        "claims": [
            {
                "id": "claim-1",
                "statement": "RBI is India's central bank.",
                "category": "factual_assertion",
                "claim_type": "factual",
                "importance": "high",
                "confidence": 0.95,
            }
        ],
        "entities": [{"name": "RBI", "type": "financial_institution", "context": "Central bank", "confidence": 0.99}],
        "urls": [],
        "suspicious_signals": [],
    }
    call1_resp = MagicMock()
    call1_resp.text = json.dumps(content_json)
    call1_resp.candidates = [MagicMock()]
    call1_resp.candidates[0].finish_reason = FinishReason.STOP
    call1_resp.candidates[0].content = MagicMock()
    call1_resp.candidates[0].content.parts = [MagicMock()]
    call1_resp.prompt_feedback = None

    # Call 2 response (Grounding)
    call2_resp = types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                finish_reason=FinishReason.STOP,
                content=types.Content(parts=[types.Part.from_text(text="Official RBI documentation retrieved.")]),
                grounding_metadata=types.GroundingMetadata(
                    grounding_chunks=[
                        types.GroundingChunk(
                            web=types.GroundingChunkWeb(uri="https://rbi.org.in/overview", title="RBI Overview")
                        )
                    ],
                    web_search_queries=["RBI India central bank official"],
                ),
            )
        ]
    )

    # Call 3 response (Truth Engine)
    truth_batch = TruthEngineBatchResponse(
        assessments=[
            SingleClaimAssessment(
                claim_id="claim-1",
                verdict="VERIFIED",
                confidence=0.99,
                supporting_evidence_ids=["ev-1"],
                contradicting_evidence_ids=[],
                reasoning="Corroborated by official Reserve Bank of India institutional registry.",
                limitations="",
            )
        ],
        overall_synthesis="Primary assertion confirmed by central bank documentation.",
    )
    call3_resp = MagicMock()
    call3_resp.text = truth_batch.model_dump_json()
    call3_resp.candidates = [MagicMock()]
    call3_resp.candidates[0].finish_reason = FinishReason.STOP
    call3_resp.candidates[0].content = MagicMock()
    call3_resp.candidates[0].content.parts = [MagicMock()]
    call3_resp.prompt_feedback = None

    # Wire 3-call mock client
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [call1_resp, call2_resp, call3_resp]

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-3.8-flash", "GEMINI_API_KEY": "mock-key"}):
        req = InvestigationRequest(input_type="text", content="RBI is India's central bank.")
        result = investigate(req, gemini_client=mock_client)

    assert isinstance(result, InvestigationResult)
    assert mock_client.models.generate_content.call_count == 3
    assert result.evidence_retrieval_status == RetrievalStatus.SUCCESS
    assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert result.truth_status == TruthStatus.VERIFIED
    assert len(result.claims) == 1
    assessed_claim = result.claims[0]
    assert assessed_claim.truth_status == TruthStatus.VERIFIED
    assert assessed_claim.truth_assessment_status == TruthAssessmentStatus.ASSESSED
    assert assessed_claim.confidence == 0.99
    assert assessed_claim.supporting_evidence_ref_ids == ["ev-1"]
    assert "VERIFIED" in result.headline_verdict
    assert "Truth Engine Synthesis:" in result.summary_explanation
