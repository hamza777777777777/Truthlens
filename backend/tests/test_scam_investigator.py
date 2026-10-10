import json
import os
import pytest
from unittest.mock import MagicMock, patch

from app.schemas.content_analysis import (
    ClaimAnalysis,
    ContentAnalysis,
    EntityAnalysis,
    LanguageInfo,
    SuspiciousSignal,
    UrlTarget,
)
from app.schemas.evidence import FailureCategory, RetrievalStatus
from app.schemas.investigation import (
    Claim,
    EvidenceSource,
    InputType,
    InvestigationRequest,
    InvestigationResult,
    RiskLevel,
    ScamAssessmentStatus,
    ScamSignal,
    SourceStance,
    SourceTier,
    TruthAssessmentStatus,
    TruthStatus,
)
from app.schemas.scam_assessment import (
    IndicatorCategory,
    ScamAssessmentResult,
    ScamIndicator,
    SignalProvenance,
)
from app.services.scam_investigator import (
    KNOWN_SHORTENERS,
    KNOWN_TARGET_BRANDS,
    ScamInvestigator,
    analyze_url_heuristics,
)
from app.services.risk_fusion import (
    CATEGORY_CEILINGS,
    DeterministicRiskFusion,
    map_score_to_risk_level,
)
from app.services.investigation_service import investigate


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_base_analysis(
    text: str = "Sample content text.",
    signals=None,
    urls=None,
    entities=None,
    claims=None,
) -> ContentAnalysis:
    return ContentAnalysis(
        normalized_text=text,
        language=LanguageInfo(code="en", name="English", confidence=0.99),
        claims=claims or [
            ClaimAnalysis(
                id="claim-1",
                statement="Statement 1",
                category="factual_assertion",
                claim_type="factual",
                importance="high",
                confidence=0.95,
            )
        ],
        entities=entities or [],
        urls=urls or [],
        suspicious_signals=signals or [],
    )


# ---------------------------------------------------------------------------
# Requirement 1: Advance-payment reward request
# ---------------------------------------------------------------------------
def test_1_advance_payment_reward_request():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="Congratulations! Send an advance fee of ₹499 to claim your gift.",
        signals=[
            SuspiciousSignal(
                type="advance_payment_request",
                description="Upfront fee requested to release prize",
                confidence=0.95,
                evidence="advance fee of ₹499 to claim your gift",
            )
        ],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 1
    assert indicators[0].category == IndicatorCategory.FINANCIAL_REQUEST
    assert indicators[0].severity_weight >= 22
    assert indicators[0].is_directly_observed is True

    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.status == ScamAssessmentStatus.ASSESSED
    assert result.risk_score >= 20
    assert result.risk_level in [RiskLevel.MODERATE, RiskLevel.HIGH]


# ---------------------------------------------------------------------------
# Requirement 2: Credential theft request
# ---------------------------------------------------------------------------
def test_2_credential_theft_request():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="Please enter your 6-digit OTP and bank password to verify.",
        signals=[
            SuspiciousSignal(
                type="credential_request",
                description="Solicitation of OTP and password credentials",
                confidence=0.98,
                evidence="enter your 6-digit OTP and bank password",
            )
        ],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 1
    assert indicators[0].category == IndicatorCategory.CREDENTIAL_THEFT
    assert indicators[0].severity_weight >= 28

    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.risk_score >= 25
    assert any("OTP" in r or "password" in r for r in result.recommendations)


# ---------------------------------------------------------------------------
# Requirement 3: Artificial urgency
# ---------------------------------------------------------------------------
def test_3_artificial_urgency():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="Immediate action needed: Account suspended in 2 hours.",
        signals=[
            SuspiciousSignal(
                type="urgency",
                description="Strict 2-hour deadline imposed to prevent account blockage",
                confidence=0.90,
                evidence="Account suspended in 2 hours",
            )
        ],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 1
    assert indicators[0].category == IndicatorCategory.MANIPULATION_PERSUASION
    assert indicators[0].severity_weight in [10, 12]

    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.risk_score == round(indicators[0].severity_weight * 0.90)
    assert result.risk_level == RiskLevel.LOW  # Standalone urgency is low severity


# ---------------------------------------------------------------------------
# Requirement 4: Unrealistic reward
# ---------------------------------------------------------------------------
def test_4_unrealistic_reward():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="You have won 10,000,000 USD in international prize draw without participation.",
        signals=[
            SuspiciousSignal(
                type="reward_lure",
                description="Unsolicited lottery win of $10M",
                confidence=0.92,
                evidence="won 10,000,000 USD",
            )
        ],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 1
    assert indicators[0].category == IndicatorCategory.MANIPULATION_PERSUASION
    assert indicators[0].severity_weight >= 15


# ---------------------------------------------------------------------------
# Requirement 5: Investment or guaranteed-return claim
# ---------------------------------------------------------------------------
def test_5_investment_or_guaranteed_return_claim():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="Guaranteed 300% daily profit in crypto trading with zero risk.",
        signals=[
            SuspiciousSignal(
                type="investment_guarantee",
                description="Zero risk guaranteed 300% daily return promise",
                confidence=0.95,
                evidence="Guaranteed 300% daily profit",
            )
        ],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 1
    assert indicators[0].category == IndicatorCategory.MANIPULATION_PERSUASION

    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.risk_score >= 15


# ---------------------------------------------------------------------------
# Requirement 6: Possible impersonation with a brand-like URL
# ---------------------------------------------------------------------------
def test_6_brand_like_url_impersonation():
    target = UrlTarget(
        url="https://sbi-account-update.fraudulent-portal.xyz/login",
        domain="sbi-account-update.fraudulent-portal.xyz",
        context="bank verification portal",
    )
    indicators = analyze_url_heuristics(
        target,
        detected_entities=[EntityAnalysis(name="SBI", type="financial_institution", context="bank", confidence=0.99)],
    )
    mismatch_indicators = [i for i in indicators if i.category == IndicatorCategory.IMPERSONATION]
    assert len(mismatch_indicators) == 1
    assert "SBI" in mismatch_indicators[0].name
    assert mismatch_indicators[0].provenance == SignalProvenance.DETERMINISTIC_URL_CHECK
    assert mismatch_indicators[0].severity_weight == 18


# ---------------------------------------------------------------------------
# Requirement 7: URL shortener detection
# ---------------------------------------------------------------------------
def test_7_url_shortener_detection():
    target = UrlTarget(
        url="https://bit.ly/3xY9AbZ",
        domain="bit.ly",
        context="shortened prize link",
    )
    indicators = analyze_url_heuristics(target)
    shortener_inds = [i for i in indicators if i.name == "URL Shortener Detected"]
    assert len(shortener_inds) == 1
    assert shortener_inds[0].provenance == SignalProvenance.DETERMINISTIC_URL_CHECK
    assert shortener_inds[0].severity_weight == 12


# ---------------------------------------------------------------------------
# Requirement 8: Raw IP-address hostname
# ---------------------------------------------------------------------------
def test_8_raw_ip_address_hostname():
    target = UrlTarget(
        url="http://192.0.2.145:8080/secure/login",
        domain="192.0.2.145",
        context="direct IP access",
    )
    indicators = analyze_url_heuristics(target)
    ip_inds = [i for i in indicators if "Raw IP" in i.name]
    assert len(ip_inds) == 1
    assert ip_inds[0].severity_weight == 20
    assert ip_inds[0].category == IndicatorCategory.URL_INDICATOR


# ---------------------------------------------------------------------------
# Requirement 9: Punycode/IDN handling
# ---------------------------------------------------------------------------
def test_9_punycode_idn_handling():
    target = UrlTarget(
        url="https://xn--sbi-8ka.com/login",
        domain="xn--sbi-8ka.com",
        context="punycode spoofing domain",
    )
    indicators = analyze_url_heuristics(target)
    punycode_inds = [i for i in indicators if "Punycode" in i.name]
    assert len(punycode_inds) == 1
    assert punycode_inds[0].severity_weight == 15


# ---------------------------------------------------------------------------
# Requirement 10: Malformed URL handling
# ---------------------------------------------------------------------------
def test_10_malformed_url_handling():
    # Weird ports, spaces, invalid chars must not crash
    malformed_urls = [
        UrlTarget(url="not a valid url at all! ::: %%", domain="", context=""),
        UrlTarget(url="http://[invalid-ipv6:999999/path", domain="", context=""),
        UrlTarget(url="", domain="", context=""),
        UrlTarget(url="http:///", domain="", context=""),
    ]
    for m in malformed_urls:
        indicators = analyze_url_heuristics(m)
        assert isinstance(indicators, list)


# ---------------------------------------------------------------------------
# Requirement 11: Benign message with no suspicious indicators
# ---------------------------------------------------------------------------
def test_11_benign_message_no_suspicious_indicators():
    investigator = ScamInvestigator()
    analysis = _make_base_analysis(
        text="The Reserve Bank of India raised the benchmark repo rate by 25 basis points.",
        signals=[],
        urls=[],
    )
    indicators = investigator.investigate(analysis.normalized_text, analysis)
    assert len(indicators) == 0

    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.status == ScamAssessmentStatus.ASSESSED
    assert result.risk_score == 0
    assert result.risk_level == RiskLevel.LOW
    assert "No behavioral deception indicators" in result.summary_explanation
    # Must clearly state that absence of indicators does NOT prove guaranteed safety
    assert any("does NOT confirm" in lim or "fewer observable" in result.summary_explanation for lim in result.limitations + [result.summary_explanation])


# ---------------------------------------------------------------------------
# Requirement 12: Duplicate signals do not inflate scores
# ---------------------------------------------------------------------------
def test_12_duplicate_signals_do_not_inflate_scores():
    indicators = [
        ScamIndicator(
            id="ind-1",
            category=IndicatorCategory.MANIPULATION_PERSUASION,
            name="Artificial Urgency or Coercive Threat",
            severity_weight=10,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            evidence_excerpt="act now",
            explanation="repeated urgency 1",
            confidence=0.90,
            is_directly_observed=True,
        ),
        ScamIndicator(
            id="ind-2",
            category=IndicatorCategory.MANIPULATION_PERSUASION,
            name="Artificial Urgency or Coercive Threat",
            severity_weight=10,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            evidence_excerpt="hurry immediately",
            explanation="repeated urgency 2",
            confidence=0.95,
            is_directly_observed=True,
        ),
        ScamIndicator(
            id="ind-3",
            category=IndicatorCategory.MANIPULATION_PERSUASION,
            name="Artificial Urgency or Coercive Threat",
            severity_weight=10,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            evidence_excerpt="urgent deadline",
            explanation="repeated urgency 3",
            confidence=0.85,
            is_directly_observed=True,
        ),
    ]
    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)

    # 3 identical urgency indicators of weight 10 should NOT equal 30.
    # Deduplication takes max(effective_points), which is round(10 * 0.95) = 10 pts.
    assert result.risk_score == 10
    assert any("Deduplicated 3 instances" in note for note in result.deduplication_notes)


# ---------------------------------------------------------------------------
# Requirement 13: Multiple correlated signals are handled correctly
# ---------------------------------------------------------------------------
def test_13_correlated_signals_handled_with_category_ceilings():
    # Add multiple distinct signals within the same category to hit ceiling
    indicators = [
        ScamIndicator(
            id="ind-1",
            category=IndicatorCategory.CREDENTIAL_THEFT,
            name="Password Theft",
            severity_weight=30,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            explanation="passwords",
            confidence=1.0,
        ),
        ScamIndicator(
            id="ind-2",
            category=IndicatorCategory.CREDENTIAL_THEFT,
            name="OTP Theft",
            severity_weight=28,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            explanation="otps",
            confidence=1.0,
        ),
    ]
    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    # Sum is 30 + 28 = 58, but CREDENTIAL_THEFT category ceiling is 35!
    assert result.risk_score == CATEGORY_CEILINGS[IndicatorCategory.CREDENTIAL_THEFT]
    assert any("capped at ceiling of 35 pts" in note for note in result.deduplication_notes)


# ---------------------------------------------------------------------------
# Requirement 14: Score remains bounded between 0 and 100
# ---------------------------------------------------------------------------
def test_14_score_remains_between_0_and_100():
    # Stack massive indicators across all categories
    indicators = []
    for cat in IndicatorCategory:
        for idx in range(5):
            indicators.append(
                ScamIndicator(
                    id=f"ind-{cat.value}-{idx}",
                    category=cat,
                    name=f"High threat {idx}",
                    severity_weight=30,
                    provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
                    explanation="severe risk",
                    confidence=1.0,
                )
            )
    fusion = DeterministicRiskFusion()
    result = fusion.fuse(indicators)
    assert result.risk_score <= 100
    assert result.risk_score >= 0
    assert result.risk_level == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# Requirement 15: Every score is reproducible for identical normalized inputs
# ---------------------------------------------------------------------------
def test_15_score_is_strictly_reproducible():
    indicators = [
        ScamIndicator(
            id="ind-1",
            category=IndicatorCategory.FINANCIAL_REQUEST,
            name="Advance Fee or Payment Demand",
            severity_weight=25,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            evidence_excerpt="pay 500",
            explanation="advance payment",
            confidence=0.88,
        ),
        ScamIndicator(
            id="ind-2",
            category=IndicatorCategory.URL_INDICATOR,
            name="URL Shortener Detected",
            severity_weight=12,
            provenance=SignalProvenance.DETERMINISTIC_URL_CHECK,
            evidence_excerpt="https://bit.ly/test",
            explanation="short link",
            confidence=1.0,
        ),
    ]
    fusion = DeterministicRiskFusion()
    scores = [fusion.fuse(indicators).risk_score for _ in range(25)]
    assert len(set(scores)) == 1  # Exactly the same score across all 25 runs


# ---------------------------------------------------------------------------
# Requirement 16: Missing provenance prevents unsupported signal scoring
# ---------------------------------------------------------------------------
def test_16_missing_provenance_prevents_unsupported_signal_scoring():
    # Construct an indicator without valid provenance
    raw_ind = ScamIndicator.model_construct(
        id="ind-unsupported",
        category=IndicatorCategory.CREDENTIAL_THEFT,
        name="Fabricated Signal",
        severity_weight=30,
        provenance=None,  # Missing provenance
        evidence_excerpt=None,
        explanation="Fabricated without basis",
        confidence=1.0,
    )
    fusion = DeterministicRiskFusion()
    result = fusion.fuse([raw_ind])
    assert result.risk_score == 0
    assert any("Missing traceable evidence provenance" in note for note in result.deduplication_notes)


# ---------------------------------------------------------------------------
# Requirement 17: Truth verdict does not determine risk score
# ---------------------------------------------------------------------------
def test_17_truth_verdict_does_not_determine_risk_score():
    fusion = DeterministicRiskFusion()
    # Risk fusion receives only indicators and does not accept or depend on TruthStatus
    indicators = [
        ScamIndicator(
            id="ind-pay",
            category=IndicatorCategory.FINANCIAL_REQUEST,
            name="Advance Fee or Payment Demand",
            severity_weight=25,
            provenance=SignalProvenance.ORIGINAL_MESSAGE,
            explanation="advance payment required",
            confidence=1.0,
        )
    ]
    res1 = fusion.fuse(indicators)
    res2 = fusion.fuse(indicators)
    assert res1.risk_score == res2.risk_score == 25


# ---------------------------------------------------------------------------
# Requirement 18: Verified factual claim can coexist with high scam risk
# ---------------------------------------------------------------------------
def test_18_verified_claim_coexists_with_high_scam_risk():
    # E.g., message quotes real RBI governor statement, but demands an advance fee to claim a grant
    mock_analysis = _make_base_analysis(
        text="RBI announced repo rate is 6.5%. Transfer ₹1000 processing fee immediately.",
        claims=[
            ClaimAnalysis(
                id="claim-1",
                statement="RBI announced repo rate is 6.5%",
                category="factual_assertion",
                claim_type="factual",
                importance="high",
                confidence=0.99,
            )
        ],
        signals=[
            SuspiciousSignal(
                type="advance_payment_request",
                description="Processing fee demand",
                confidence=0.95,
                evidence="Transfer ₹1000 processing fee",
            ),
            SuspiciousSignal(
                type="credential_request",
                description="Banking PIN request",
                confidence=0.95,
                evidence="enter secret PIN",
            ),
        ],
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth") as mock_truth:

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )
        mock_truth.return_value = MagicMock(
            claims=[Claim(
                id="claim-1",
                claim_number=1,
                statement="RBI announced repo rate is 6.5%",
                truth_status=TruthStatus.VERIFIED,
                truth_assessment_status=TruthAssessmentStatus.ASSESSED,
                confidence=0.99,
                explanation="Verified against authentic bulletin.",
            )],
            overall_truth_status=TruthStatus.VERIFIED,
            truth_assessment_status=TruthAssessmentStatus.ASSESSED,
            truth_assessment_failure_category=None,
            synthesis_explanation="Assertion is factual and corroborated.",
        )

        request = InvestigationRequest(
            input_type="text",
            content="RBI announced repo rate is 6.5%. Transfer ₹1000 processing fee immediately.",
        )
        result = investigate(request)

        # Truth status is VERIFIED, but scam risk is HIGH (advance fee + credentials)!
        assert result.truth_status == TruthStatus.VERIFIED
        assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
        assert result.scam_risk_score >= 50
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "VERIFIED" in result.headline_verdict
        assert "SCAM RISK:" in result.headline_verdict


# ---------------------------------------------------------------------------
# Requirement 19: False factual claim does not automatically generate high scam risk
# ---------------------------------------------------------------------------
def test_19_false_factual_claim_does_not_generate_high_scam_risk():
    # Pure false factual assertion without deceptive behavioral patterns (e.g. rumor / myth)
    mock_analysis = _make_base_analysis(
        text="The Eiffel Tower was built in 1492 by Christopher Columbus.",
        claims=[
            ClaimAnalysis(
                id="claim-1",
                statement="The Eiffel Tower was built in 1492",
                category="factual_assertion",
                claim_type="factual",
                importance="high",
                confidence=0.99,
            )
        ],
        signals=[],  # No behavioral scam signals!
        urls=[],
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth") as mock_truth:

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )
        mock_truth.return_value = MagicMock(
            claims=[Claim(
                id="claim-1",
                claim_number=1,
                statement="The Eiffel Tower was built in 1492",
                truth_status=TruthStatus.FALSE,
                truth_assessment_status=TruthAssessmentStatus.ASSESSED,
                confidence=0.99,
                explanation="Directly refuted by historical evidence.",
            )],
            overall_truth_status=TruthStatus.FALSE,
            truth_assessment_status=TruthAssessmentStatus.ASSESSED,
            truth_assessment_failure_category=None,
            synthesis_explanation="Claim is historically false.",
        )

        request = InvestigationRequest(
            input_type="text",
            content="The Eiffel Tower was built in 1492 by Christopher Columbus.",
        )
        result = investigate(request)

        # Truth status is FALSE, but scam risk is LOW (0 pts)!
        assert result.truth_status == TruthStatus.FALSE
        assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
        assert result.scam_risk_score == 0
        assert result.risk_level == RiskLevel.LOW


# ---------------------------------------------------------------------------
# Requirement 20: Evidence retrieval failure does not block local scam analysis
# ---------------------------------------------------------------------------
def test_20_evidence_retrieval_failure_does_not_block_scam_analysis():
    mock_analysis = _make_base_analysis(
        text="Immediate action: verify password at http://192.168.1.1/login",
        signals=[
            SuspiciousSignal(
                type="credential_request",
                description="Password theft",
                confidence=0.95,
                evidence="verify password",
            )
        ],
        urls=[
            UrlTarget(
                url="http://192.168.1.1/login",
                domain="192.168.1.1",
                context="login",
            )
        ],
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground:

        # Grounding completely fails with NETWORK error
        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.FAILED,
            failure_category=FailureCategory.NETWORK,
            sources=[],
            grounding_search_queries=[],
            claim_assessments=[],
        )

        request = InvestigationRequest(
            input_type="text",
            content="Immediate action: verify password at http://192.168.1.1/login",
        )
        result = investigate(request)

        # Evidence retrieval failed and truth was not assessed...
        assert result.evidence_retrieval_status == RetrievalStatus.FAILED
        assert result.truth_assessment_status == TruthAssessmentStatus.NOT_ASSESSED
        # ... BUT Scam Investigation and Risk Fusion ran and completed successfully!
        assert result.scam_assessment_status == ScamAssessmentStatus.ASSESSED
        assert result.scam_risk_score is not None
        assert result.scam_risk_score >= 40
        assert result.risk_level in [RiskLevel.MODERATE, RiskLevel.HIGH]


# ---------------------------------------------------------------------------
# Requirement 21: Truth Engine failure does not invalidate scam assessment
# ---------------------------------------------------------------------------
def test_21_truth_engine_failure_does_not_invalidate_scam_assessment():
    mock_analysis = _make_base_analysis(
        text="Transfer 500 to claim prize",
        signals=[
            SuspiciousSignal(
                type="advance_payment_request",
                description="Fee request",
                confidence=0.90,
                evidence="Transfer 500",
            )
        ],
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth") as mock_truth:

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )
        # Truth Engine fails
        mock_truth.return_value = MagicMock(
            claims=[],
            overall_truth_status=None,
            truth_assessment_status=TruthAssessmentStatus.FAILED,
            truth_assessment_failure_category=FailureCategory.PROVIDER_ERROR,
            synthesis_explanation="Truth Engine encountered provider error.",
        )

        request = InvestigationRequest(
            input_type="text",
            content="Transfer 500 to claim prize",
        )
        result = investigate(request)

        # Truth Engine is FAILED
        assert result.truth_assessment_status == TruthAssessmentStatus.FAILED
        assert result.truth_status is None
        # Scam assessment is ASSESSED with valid score!
        assert result.scam_assessment_status == ScamAssessmentStatus.ASSESSED
        assert result.scam_risk_score is not None
        assert result.scam_risk_score >= 20


# ---------------------------------------------------------------------------
# Requirement 22: Scam assessment failure produces no fabricated score
# ---------------------------------------------------------------------------
def test_22_scam_assessment_failure_produces_no_fabricated_score():
    mock_analysis = _make_base_analysis()

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth"), \
         patch("app.services.investigation_service.ScamInvestigator.investigate", side_effect=RuntimeError("Scam engine failure")):

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )

        request = InvestigationRequest(
            input_type="text",
            content="Test message",
            metadata={"run_truth_assessment": False},
        )
        result = investigate(request)

        # Status must be FAILED and score must be None (never 0!)
        assert result.scam_assessment_status == ScamAssessmentStatus.FAILED
        assert result.scam_risk_score is None
        assert result.risk_level == RiskLevel.NOT_ASSESSED
        assert result.scam_assessment_failure_category is not None


# ---------------------------------------------------------------------------
# Requirement 23: Simulated demo inputs remain explicitly labelled
# ---------------------------------------------------------------------------
def test_23_simulated_demo_inputs_explicitly_labelled():
    request = InvestigationRequest(
        input_type="text",
        content="Sample content",
        metadata={"run_truth_assessment": False},
    )
    mock_analysis = _make_base_analysis()

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth"):

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.NO_EVIDENCE,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )

        result = investigate(request)
        # Development mode flag preserved
        assert result.development_mode is True
        # If simulated evidence placeholder used, flagged as simulated demo
        if result.evidence:
            assert result.evidence[0].is_simulated_demo is True


# ---------------------------------------------------------------------------
# Requirement 24: Frontend/API contracts remain consistent
# ---------------------------------------------------------------------------
def test_24_frontend_api_contracts_remain_consistent():
    request = InvestigationRequest(
        input_type="text",
        content="Pay fee at https://bit.ly/claim",
        metadata={"run_truth_assessment": False},
    )
    mock_analysis = _make_base_analysis(
        urls=[UrlTarget(url="https://bit.ly/claim", domain="bit.ly", context="claim")]
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth"):

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=[],
            claim_assessments=[],
        )

        result = investigate(request)
        dumped = result.model_dump(by_alias=True)

        # Check required Phase 5 camelCase fields for TypeScript frontend
        assert "scamAssessmentStatus" in dumped
        assert dumped["scamAssessmentStatus"] in ["NOT_ASSESSED", "ASSESSED", "FAILED"]
        assert "scamRiskScore" in dumped
        assert "riskLevel" in dumped
        assert "scamSignals" in dumped
        if dumped["scamSignals"]:
            first_sig = dumped["scamSignals"][0]
            assert "riskPoints" in first_sig
            assert "provenance" in first_sig
            assert "isDirectlyObserved" in first_sig



# ---------------------------------------------------------------------------
# Requirement 25: Regression coverage for existing Phase 4A–4D behavior
# ---------------------------------------------------------------------------
def test_25_regression_coverage_phase_4a_to_4d_behavior():
    request = InvestigationRequest(
        input_type="text",
        content="PM-KISAN provides 6000 rupees annual direct benefit transfer.",
    )
    mock_analysis = _make_base_analysis(
        text="PM-KISAN provides 6000 rupees annual direct benefit transfer.",
        claims=[
            ClaimAnalysis(
                id="claim-1",
                statement="PM-KISAN provides 6000 rupees annual benefit",
                category="benefit_claim",
                claim_type="factual",
                importance="high",
                confidence=0.98,
            )
        ],
    )

    with patch("app.services.investigation_service.analyze_content", return_value=mock_analysis), \
         patch("app.services.investigation_service.ground_claims") as mock_ground, \
         patch("app.services.investigation_service.evaluate_truth") as mock_truth:

        mock_ground.return_value = MagicMock(
            retrieval_status=RetrievalStatus.SUCCESS,
            sources=[],
            failure_category=None,
            grounding_search_queries=["pm-kisan scheme"],
            claim_assessments=[],
        )
        mock_truth.return_value = MagicMock(
            claims=[Claim(
                id="claim-1",
                claim_number=1,
                statement="PM-KISAN provides 6000 rupees annual benefit",
                truth_status=TruthStatus.VERIFIED,
                truth_assessment_status=TruthAssessmentStatus.ASSESSED,
                confidence=0.98,
                explanation="Official PM-KISAN portal corroborates ₹6,000 in 3 installments.",
            )],
            overall_truth_status=TruthStatus.VERIFIED,
            truth_assessment_status=TruthAssessmentStatus.ASSESSED,
            truth_assessment_failure_category=None,
            synthesis_explanation="Official portal corroborates claim.",
        )

        result = investigate(request)

        # Phase 4A-4D contracts preserved
        assert result.truth_status == TruthStatus.VERIFIED
        assert result.truth_assessment_status == TruthAssessmentStatus.ASSESSED
        assert len(result.claims) == 1
        assert result.claims[0].truth_status == TruthStatus.VERIFIED
        # Phase 5 scam assessment ran in tandem
        assert result.scam_assessment_status == ScamAssessmentStatus.ASSESSED
        assert result.scam_risk_score == 0
        assert result.risk_level == RiskLevel.LOW
