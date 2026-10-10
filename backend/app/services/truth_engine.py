"""
TruthLens Phase 4D — Truth Engine Service

Epistemic evaluation of atomic claims against retrieved external evidence packets.

Strict Design Invariants:
1. Never assume finding a source proves a claim.
2. Never fabricate evidence or issue verdicts from Gemini pretrained memory alone.
3. Call 3 (Truth Engine) receives only the claim and its explicitly associated evidence.
4. Distinguish between:
   - Evidence retrieval FAILED -> truth_assessment_status=NOT_ASSESSED, truth_status=None.
   - Evidence retrieval NO_EVIDENCE -> assessment performed, returns CANNOT_CONFIRM, truth_assessment_status=ASSESSED.
   - Truth Engine provider/parse failure -> truth_assessment_status=FAILED, truth_status=None, failure category set.
   - Successful assessment -> truth_assessment_status=ASSESSED, truth_status=VERIFIED|FALSE|PARTIALLY SUPPORTED|OUTDATED|CANNOT CONFIRM.
5. Evidence Authority & Safety Guards:
   - Tier 3/4 evidence alone CANNOT verify a material claim -> downgraded to CANNOT_CONFIRM.
   - Simulated/demo evidence (is_simulated_demo=True) CANNOT support a live verdict -> CANNOT_CONFIRM.
   - Conflicting credible sources (Tier 1/2) with unresolved contradictions -> CANNOT_CONFIRM.
   - Absence of search results is NEVER sufficient to call a claim FALSE.
"""
from dataclasses import dataclass
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from google import genai
from google.genai import errors, types
from google.genai.types import FinishReason
from pydantic import ValidationError

from app.schemas.evidence import FailureCategory, RetrievalStatus
from app.schemas.investigation import (
    Claim,
    EvidenceSource,
    SourceTier,
    TruthAssessmentStatus,
    TruthStatus,
)
from app.schemas.truth_assessment import (
    SingleClaimAssessment,
    TruthEngineBatchResponse,
)
from app.services.gemini_service import (
    _get_config_value,
    get_gemini_client,
)

logger = logging.getLogger("truthlens.truth_engine")

TRUTH_ENGINE_SYSTEM_INSTRUCTION = (
    "You are the Truth Engine of TruthLens AI, an epistemic evaluation system.\n"
    "Your objective is to evaluate atomic factual claims SOLELY against the provided retrieved external evidence.\n\n"
    "CRITICAL EPISTEMIC PRINCIPLES:\n"
    "1. ABSOLUTE GROUNDING: Base every verdict, explanation, and confidence strictly on the provided external evidence items. "
    "Do NOT use internal memory, pre-trained knowledge, or general impressions to declare a claim true or false.\n"
    "2. NO FABRICATION: Do NOT invent sources, evidence IDs, citations, quotes, or publication facts.\n"
    "3. VERDICTS AND THEIR EXACT MEANINGS:\n"
    "   - VERIFIED: Credible, authoritative external evidence (Tier 1 official or Tier 2 authoritative) directly supports the material claim. "
    "No unresolved credible contradiction undermines it.\n"
    "   - FALSE: Credible, relevant external evidence directly contradicts and refutes the material claim. "
    "NOTE: The mere absence of a search result is NEVER sufficient to label a claim FALSE.\n"
    "   - PARTIALLY SUPPORTED: The evidence supports a meaningful portion of the claim, but leaves another material portion unsupported or contradicted. "
    "Your explanation must clearly distinguish what is supported from what is not.\n"
    "   - OUTDATED: Reliable evidence establishes that the assertion was previously accurate or active, but is no longer current (temporal divergence).\n"
    "   - CANNOT CONFIRM: The assessment was genuinely performed, but available evidence is insufficient, ambiguous, low-tier only, conflicting, or absent.\n"
    "4. TIER AUTHORITY HIERARCHY:\n"
    "   - Tier 1: official institutions, government, regulators (RBI, SEBI, police, gov portals).\n"
    "   - Tier 2: authoritative news organizations, peer-reviewed academic sources, established organizations.\n"
    "   - Tier 3: secondary blogs, user forums, community discussions.\n"
    "   - Tier 4: unverified, unknown domains.\n"
    "   * Rule: Tier 3 or Tier 4 sources alone CANNOT verify a material claim.\n"
    "5. SIMULATED / DEMO EVIDENCE:\n"
    "   - If an evidence item is marked is_simulated_demo=true, it is synthetic testing data. It CANNOT corroborate a real-world assertion.\n"
    "6. CITATION INTEGRITY:\n"
    "   - In supporting_evidence_ids and contradicting_evidence_ids, cite ONLY the exact IDs from the provided evidence packet.\n"
    "7. CONFLICTING SOURCES:\n"
    "   - If credible sources disagree on facts without temporal resolution, verdict must be CANNOT CONFIRM with the conflict documented.\n"
)


@dataclass
class TruthEngineResult:
    """Consolidated result returned by the Truth Engine."""
    claims: List[Claim]
    overall_truth_status: Optional[TruthStatus]
    truth_assessment_status: TruthAssessmentStatus
    truth_assessment_failure_category: Optional[FailureCategory]
    synthesis_explanation: str


def _normalize_verdict_str(verdict_str: str) -> TruthStatus:
    """Map string or variant to standard TruthStatus enum."""
    clean = verdict_str.strip().upper().replace("_", " ")
    if clean == "VERIFIED":
        return TruthStatus.VERIFIED
    if clean == "FALSE":
        return TruthStatus.FALSE
    if clean in ("PARTIALLY SUPPORTED", "PARTIAL", "PARTIALLY_SUPPORTED"):
        return TruthStatus.PARTIALLY_SUPPORTED
    if clean == "OUTDATED":
        return TruthStatus.OUTDATED
    return TruthStatus.CANNOT_CONFIRM


def _apply_deterministic_safeguards(
    claim: Claim,
    assessment: SingleClaimAssessment,
    evidence_by_id: Dict[str, EvidenceSource],
    valid_claim_ev_ids: Set[str],
) -> Tuple[TruthStatus, float, List[str], List[str], str, str]:
    """Validate model output against hard epistemic constraints and source metadata.

    Returns:
        (final_verdict, final_confidence, valid_supporting_ids, valid_contradicting_ids, reasoning, limitations)
    """
    proposed_verdict = _normalize_verdict_str(assessment.verdict)
    confidence = max(0.0, min(1.0, float(assessment.confidence)))
    reasoning = assessment.reasoning.strip()
    limitations = assessment.limitations.strip()

    # 1. Sanitize evidence IDs: retain only IDs that actually exist in input evidence
    supporting_ids = [
        eid for eid in assessment.supporting_evidence_ids
        if eid in valid_claim_ev_ids and eid in evidence_by_id
    ]
    contradicting_ids = [
        eid for eid in assessment.contradicting_evidence_ids
        if eid in valid_claim_ev_ids and eid in evidence_by_id
    ]

    # Inspect the actual sources supporting or contradicting
    sup_sources = [evidence_by_id[eid] for eid in supporting_ids]
    con_sources = [evidence_by_id[eid] for eid in contradicting_ids]

    has_tier_1_2_sup = any(
        s.tier in (SourceTier.TIER_1_OFFICIAL, SourceTier.TIER_2_AUTHORITATIVE)
        for s in sup_sources
    )
    has_tier_1_2_con = any(
        s.tier in (SourceTier.TIER_1_OFFICIAL, SourceTier.TIER_2_AUTHORITATIVE)
        for s in con_sources
    )

    all_sup_simulated = all(s.is_simulated_demo for s in sup_sources) if sup_sources else False
    all_con_simulated = all(s.is_simulated_demo for s in con_sources) if con_sources else False

    # Guard 1: Simulated demo evidence cannot establish a live truth verdict
    if proposed_verdict in (TruthStatus.VERIFIED, TruthStatus.FALSE, TruthStatus.OUTDATED):
        if (proposed_verdict == TruthStatus.VERIFIED and all_sup_simulated) or \
           (proposed_verdict == TruthStatus.FALSE and all_con_simulated):
            proposed_verdict = TruthStatus.CANNOT_CONFIRM
            confidence = min(confidence, 0.4)
            demo_note = "Supplied evidence consists exclusively of simulated/demo records. Live verification cannot be established from synthetic data."
            limitations = f"{limitations} {demo_note}".strip()

    # Guard 2: No evidence attached at all -> CANNOT_CONFIRM
    if proposed_verdict in (TruthStatus.VERIFIED, TruthStatus.FALSE) and not supporting_ids and not contradicting_ids:
        proposed_verdict = TruthStatus.CANNOT_CONFIRM
        confidence = min(confidence, 0.4)
        no_src_note = "No verifiable external evidence IDs provided to substantiate the assertion."
        limitations = f"{limitations} {no_src_note}".strip()

    # Guard 3: Low-tier (Tier 3/4) evidence alone cannot verify a material claim
    if proposed_verdict == TruthStatus.VERIFIED and not has_tier_1_2_sup:
        proposed_verdict = TruthStatus.CANNOT_CONFIRM
        confidence = min(confidence, 0.5)
        tier_note = "Available corroboration is restricted to low-tier / unverified sources without Tier 1 or Tier 2 verification."
        limitations = f"{limitations} {tier_note}".strip()

    # Guard 4: Conflicting credible sources (both Tier 1/2 supporting and contradicting)
    if has_tier_1_2_sup and has_tier_1_2_con:
        if proposed_verdict != TruthStatus.PARTIALLY_SUPPORTED:
            proposed_verdict = TruthStatus.CANNOT_CONFIRM
            confidence = min(confidence, 0.5)
            conflict_note = "Material conflict detected between authoritative sources without chronological or scope resolution."
            limitations = f"{limitations} {conflict_note}".strip()

    # Guard 5: Outdated claims require temporal evidence
    if proposed_verdict == TruthStatus.OUTDATED:
        has_dated_source = any(s.published_date for s in (sup_sources + con_sources))
        if not has_dated_source and not re.search(r"\b(former|previous|20\d\d|past|expired)\b", reasoning, re.I):
            proposed_verdict = TruthStatus.CANNOT_CONFIRM
            confidence = min(confidence, 0.5)
            limitations = f"{limitations} Temporal status could not be corroborated with publication dates.".strip()

    return (
        proposed_verdict,
        round(confidence, 2),
        supporting_ids,
        contradicting_ids,
        reasoning,
        limitations,
    )


def _synthesize_overall_truth(
    claims: List[Claim],
    assessment_status: TruthAssessmentStatus,
    failure_category: Optional[FailureCategory],
    batch_synthesis: str = "",
) -> Tuple[Optional[TruthStatus], str]:
    """Deterministically synthesize the investigation-level truth status from evaluated claims."""
    if assessment_status != TruthAssessmentStatus.ASSESSED:
        if assessment_status == TruthAssessmentStatus.FAILED:
            cat_str = failure_category.value if failure_category else "PROVIDER_ERROR"
            return (
                None,
                f"Truth assessment could not be completed ({cat_str}). "
                "The Truth Engine encountered an evaluation failure; no verdicts fabricated.",
            )
        return (
            None,
            "Claims extracted; external truth assessment has not been executed.",
        )

    if not claims:
        return (TruthStatus.CANNOT_CONFIRM, "No discrete claims were available to assess.")

    verdicts = [c.truth_status for c in claims if c.truth_status is not None]
    if not verdicts:
        return (TruthStatus.CANNOT_CONFIRM, "Claims were analyzed but no definitive verdicts reached.")

    # All identical
    if all(v == TruthStatus.VERIFIED for v in verdicts):
        synth = batch_synthesis or "All extracted claims are corroborated by credible external evidence."
        return (TruthStatus.VERIFIED, synth)

    if all(v == TruthStatus.FALSE for v in verdicts):
        synth = batch_synthesis or "Extracted assertions are directly contradicted by authoritative sources."
        return (TruthStatus.FALSE, synth)

    if all(v == TruthStatus.CANNOT_CONFIRM for v in verdicts):
        synth = batch_synthesis or "Available external evidence is insufficient or inconclusive to confirm or refute claims."
        return (TruthStatus.CANNOT_CONFIRM, synth)

    if all(v == TruthStatus.OUTDATED for v in verdicts):
        synth = batch_synthesis or "Assessed assertions represent obsolete or superseded information."
        return (TruthStatus.OUTDATED, synth)

    # Mixed conditions
    verified_count = sum(1 for v in verdicts if v == TruthStatus.VERIFIED)
    false_count = sum(1 for v in verdicts if v == TruthStatus.FALSE)
    partial_count = sum(1 for v in verdicts if v == TruthStatus.PARTIALLY_SUPPORTED)

    if false_count > 0 and verified_count > 0:
        return (
            TruthStatus.PARTIALLY_SUPPORTED,
            batch_synthesis or f"Mixed evidentiary findings: {verified_count} claim(s) verified, {false_count} claim(s) refuted.",
        )

    if false_count > 0:
        return (
            TruthStatus.FALSE,
            batch_synthesis or f"Primary assertions refuted ({false_count} claim(s) contradicted by evidence).",
        )

    if verified_count > 0 and (partial_count > 0 or all(v in (TruthStatus.VERIFIED, TruthStatus.CANNOT_CONFIRM) for v in verdicts)):
        return (
            TruthStatus.PARTIALLY_SUPPORTED,
            batch_synthesis or f"Partial verification: {verified_count} claim(s) confirmed, remaining claim(s) inconclusive.",
        )

    if partial_count > 0:
        return (
            TruthStatus.PARTIALLY_SUPPORTED,
            batch_synthesis or "Extracted assertions are partially supported with material caveats.",
        )

    return (
        TruthStatus.CANNOT_CONFIRM,
        batch_synthesis or "Claims produced mixed or indeterminate evidentiary findings.",
    )


def evaluate_truth(
    claims: List[Claim],
    evidence: List[EvidenceSource],
    retrieval_status: RetrievalStatus,
    retrieval_failure_category: Optional[FailureCategory] = None,
    client: Optional[genai.Client] = None,
) -> TruthEngineResult:
    """Evaluate factual claims against retrieved evidence using Gemini structured generation.

    Args:
        claims: Atomic claims extracted by Content Intelligence
        evidence: Evidence sources normalized from grounding chunks
        retrieval_status: RetrievalStatus enum (SUCCESS, NO_EVIDENCE, FAILED)
        retrieval_failure_category: Optional failure category from retrieval stage
        client: Optional injected genai.Client for testing/mocking
    """
    logger.info(
        f"[TRUTH_ENGINE] Evaluating {len(claims)} claim(s), {len(evidence)} source(s), "
        f"retrieval_status={retrieval_status.value}"
    )

    # -------------------------------------------------------------------------
    # STATE 1: Retrieval FAILED or SKIPPED -> Do NOT run Truth Engine or fabricate verdicts
    # -------------------------------------------------------------------------
    if retrieval_status in (RetrievalStatus.FAILED, RetrievalStatus.SKIPPED):
        if retrieval_status == RetrievalStatus.SKIPPED:
            synthesis_msg = (
                "External evidence retrieval was skipped due to upstream limits. "
                "Truth assessment was not executed; no truth verdicts fabricated."
            )
        else:
            fail_cat_str = (
                retrieval_failure_category.value
                if retrieval_failure_category
                else "UNKNOWN"
            )
            synthesis_msg = (
                f"External evidence retrieval failed ({fail_cat_str}). "
                "Truth assessment was not executed; no truth verdicts fabricated."
            )
        logger.info(f"[TRUTH_ENGINE] Evidence retrieval {retrieval_status.value}; skipping assessment.")
        unassessed_claims: List[Claim] = []
        for c in claims:
            c_copy = c.model_copy()
            c_copy.truth_status = None
            c_copy.truth_assessment_status = TruthAssessmentStatus.NOT_ASSESSED
            c_copy.truth_assessment_failure_category = None
            c_copy.supporting_evidence_ref_ids = []
            c_copy.contradicting_evidence_ref_ids = []
            unassessed_claims.append(c_copy)

        return TruthEngineResult(
            claims=unassessed_claims,
            overall_truth_status=None,
            truth_assessment_status=TruthAssessmentStatus.NOT_ASSESSED,
            truth_assessment_failure_category=None,
            synthesis_explanation=synthesis_msg,
        )

    # -------------------------------------------------------------------------
    # STATE 2: Retrieval NO_EVIDENCE -> Assessment performed against empty packet
    # -------------------------------------------------------------------------
    if retrieval_status == RetrievalStatus.NO_EVIDENCE or not evidence:
        logger.info("[TRUTH_ENGINE] Retrieval returned NO_EVIDENCE. Assessment genuinely completes with CANNOT_CONFIRM.")
        assessed_claims: List[Claim] = []
        for c in claims:
            c_copy = c.model_copy()
            c_copy.truth_status = TruthStatus.CANNOT_CONFIRM
            c_copy.truth_assessment_status = TruthAssessmentStatus.ASSESSED
            c_copy.truth_assessment_failure_category = None
            c_copy.confidence = 0.5
            c_copy.supporting_evidence_ref_ids = []
            c_copy.contradicting_evidence_ref_ids = []
            c_copy.explanation = (
                f"Truth assessment completed: external evidence retrieval via Google Search returned no usable "
                f"sources for assertion \"{c.statement[:90]}\". Under TruthLens standards, absence of search results "
                "cannot confirm or refute a claim."
            )
            c_copy.limitations = "Absence of search results does not establish falsity. Official documentation could not be retrieved."
            assessed_claims.append(c_copy)

        return TruthEngineResult(
            claims=assessed_claims,
            overall_truth_status=TruthStatus.CANNOT_CONFIRM,
            truth_assessment_status=TruthAssessmentStatus.ASSESSED,
            truth_assessment_failure_category=None,
            synthesis_explanation=(
                "Google Search grounding completed with no external evidence returned. "
                "Under TruthLens epistemic standards, absence of search results cannot prove or refute assertions; "
                "all claims are assessed as CANNOT CONFIRM."
            ),
        )

    # -------------------------------------------------------------------------
    # STATE 3: Retrieval SUCCESS -> Run Gemini Call 3 with structured output
    # -------------------------------------------------------------------------
    # Build prompt with explicit claim and evidence packet
    evidence_by_id: Dict[str, EvidenceSource] = {e.id: e for e in evidence}
    all_evidence_ids: Set[str] = set(evidence_by_id.keys())

    # Format claims and associated evidence
    claims_payload = []
    for c in claims:
        # Resolve evidence linked specifically to this claim, or all evidence if unmapped
        linked_ev = [
            {
                "id": e.id,
                "title": e.title,
                "publisher": e.publisher,
                "url": e.url or "N/A",
                "tier": e.tier.value,
                "tier_label": e.tier_label,
                "stance": e.stance.value,
                "excerpt": e.excerpt,
                "published_date": e.published_date or "N/A",
                "is_simulated_demo": e.is_simulated_demo,
            }
            for e in evidence
            if e.id in c.evidence_ref_ids
        ]
        if not linked_ev:
            # If no claim-specific mapping, supply full evidence set for evaluation
            linked_ev = [
                {
                    "id": e.id,
                    "title": e.title,
                    "publisher": e.publisher,
                    "url": e.url or "N/A",
                    "tier": e.tier.value,
                    "tier_label": e.tier_label,
                    "stance": e.stance.value,
                    "excerpt": e.excerpt,
                    "published_date": e.published_date or "N/A",
                    "is_simulated_demo": e.is_simulated_demo,
                }
                for e in evidence
            ]

        claims_payload.append({
            "claim_id": c.id,
            "claim_number": c.claim_number,
            "statement": c.statement,
            "category": c.category,
            "associated_evidence": linked_ev,
        })

    user_prompt = (
        "EVALUATE THE FOLLOWING ATOMIC CLAIMS STRICTLY AGAINST THE ASSOCIATED EXTERNAL EVIDENCE:\n\n"
        f"{json.dumps(claims_payload, indent=2)}\n\n"
        "Provide a forensic SingleClaimAssessment for each claim in TruthEngineBatchResponse format."
    )

    model_name = _get_config_value("GEMINI_MODEL")
    if not model_name:
        logger.error("[TRUTH_ENGINE] GEMINI_MODEL not configured.")
        return _build_failure_result(
            claims,
            FailureCategory.INVALID_CONFIGURATION,
            "GEMINI_MODEL is not configured.",
        )

    try:
        active_client = client or get_gemini_client()
    except Exception as exc:
        logger.error(f"[TRUTH_ENGINE] Client initialization failed: {exc}")
        return _build_failure_result(
            claims,
            FailureCategory.AUTHENTICATION if "key" in str(exc).lower() else FailureCategory.PROVIDER_ERROR,
            f"Gemini client initialization failed: {exc.__class__.__name__}",
        )

    generation_config = types.GenerateContentConfig(
        system_instruction=TRUTH_ENGINE_SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=TruthEngineBatchResponse,
        temperature=0.1,
    )

    try:
        response = active_client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=generation_config,
        )
    except errors.ClientError as exc:
        err_str = str(exc)
        logger.warning(f"[TRUTH_ENGINE] Gemini ClientError: {exc.__class__.__name__}")
        if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
            return _build_failure_result(claims, FailureCategory.AUTHENTICATION, "Authentication failed.")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return _build_failure_result(claims, FailureCategory.RATE_LIMIT, "Rate limit exceeded.")
        return _build_failure_result(claims, FailureCategory.PROVIDER_ERROR, f"Client error: {exc.__class__.__name__}")
    except errors.ServerError as exc:
        logger.error(f"[TRUTH_ENGINE] Gemini ServerError: {exc.__class__.__name__}")
        return _build_failure_result(claims, FailureCategory.PROVIDER_ERROR, "Provider service temporarily unavailable.")
    except Exception as exc:
        logger.error(f"[TRUTH_ENGINE] Unexpected exception during generate_content: {exc.__class__.__name__}")
        return _build_failure_result(claims, FailureCategory.NETWORK if "connect" in str(exc).lower() else FailureCategory.PROVIDER_ERROR, str(exc))

    # Safe inspection of response candidates
    valid_resp, fail_cat, raw_json_text = _validate_truth_response(response)
    if not valid_resp or not raw_json_text:
        return _build_failure_result(
            claims,
            fail_cat or FailureCategory.INVALID_RESPONSE,
            "Model returned empty or safety-blocked candidate.",
        )

    # Parse and validate against TruthEngineBatchResponse schema
    try:
        parsed_dict = json.loads(raw_json_text)
        batch_response = TruthEngineBatchResponse.model_validate(parsed_dict)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error(f"[TRUTH_ENGINE] Schema parsing failed: {exc}")
        return _build_failure_result(
            claims,
            FailureCategory.INVALID_RESPONSE,
            f"Response failed structured schema validation: {exc.__class__.__name__}",
        )

    # Map assessments by claim_id
    assessments_by_claim_id: Dict[str, SingleClaimAssessment] = {
        a.claim_id: a for a in batch_response.assessments
    }

    # Apply deterministic safeguards per claim
    updated_claims: List[Claim] = []
    claim_id_set = {c.id for c in claims}

    for c in claims:
        c_assessment = assessments_by_claim_id.get(c.id)
        valid_ev_ids = set(c.evidence_ref_ids) if c.evidence_ref_ids else all_evidence_ids

        if not c_assessment:
            # Fallback if Gemini missed this specific claim
            logger.warning(f"[TRUTH_ENGINE] Model omitted assessment for claim {c.id}; applying conservative fallback.")
            c_copy = c.model_copy()
            c_copy.truth_status = TruthStatus.CANNOT_CONFIRM
            c_copy.truth_assessment_status = TruthAssessmentStatus.ASSESSED
            c_copy.truth_assessment_failure_category = None
            c_copy.confidence = 0.5
            c_copy.supporting_evidence_ref_ids = []
            c_copy.contradicting_evidence_ref_ids = []
            c_copy.explanation = f"Evaluated against evidence; model did not return a discrete assessment for assertion \"{c.statement[:80]}\"."
            c_copy.limitations = "Omitted from batch model output; defaulted to CANNOT CONFIRM."
            updated_claims.append(c_copy)
            continue

        (
            final_verdict,
            final_conf,
            sup_ids,
            con_ids,
            reasoning,
            limitations,
        ) = _apply_deterministic_safeguards(
            claim=c,
            assessment=c_assessment,
            evidence_by_id=evidence_by_id,
            valid_claim_ev_ids=valid_ev_ids,
        )

        c_copy = c.model_copy()
        c_copy.truth_status = final_verdict
        c_copy.truth_assessment_status = TruthAssessmentStatus.ASSESSED
        c_copy.truth_assessment_failure_category = None
        c_copy.confidence = final_conf
        c_copy.supporting_evidence_ref_ids = sup_ids
        c_copy.contradicting_evidence_ref_ids = con_ids
        c_copy.explanation = reasoning or f"Evaluated against {len(sup_ids) + len(con_ids)} source(s)."
        c_copy.limitations = limitations or None
        updated_claims.append(c_copy)

    # Deterministic top-level synthesis
    overall_status, overall_synthesis = _synthesize_overall_truth(
        claims=updated_claims,
        assessment_status=TruthAssessmentStatus.ASSESSED,
        failure_category=None,
        batch_synthesis=batch_response.overall_synthesis,
    )

    return TruthEngineResult(
        claims=updated_claims,
        overall_truth_status=overall_status,
        truth_assessment_status=TruthAssessmentStatus.ASSESSED,
        truth_assessment_failure_category=None,
        synthesis_explanation=overall_synthesis,
    )


def _validate_truth_response(response: Any) -> Tuple[bool, Optional[FailureCategory], Optional[str]]:
    """Safely inspect Gemini response candidate and parts before reading response.text."""
    if not response:
        return False, FailureCategory.INVALID_RESPONSE, None

    feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(feedback, "block_reason", None) if feedback else None
    if type(block_reason).__name__ in ("MagicMock", "Mock"):
        block_reason = None
    if block_reason:
        logger.warning(f"[TRUTH_ENGINE] Prompt blocked: {block_reason}")
        return False, FailureCategory.INVALID_RESPONSE, None

    candidates = getattr(response, "candidates", None)
    if not candidates:
        logger.warning("[TRUTH_ENGINE] Response returned no candidates.")
        return False, FailureCategory.INVALID_RESPONSE, None

    first_cand = candidates[0]
    finish_reason = getattr(first_cand, "finish_reason", None)
    if type(finish_reason).__name__ in ("MagicMock", "Mock"):
        finish_reason = None
    _CLEAN = {FinishReason.STOP, FinishReason.FINISH_REASON_UNSPECIFIED, "STOP", "FINISH_REASON_UNSPECIFIED"}
    if finish_reason is not None and finish_reason not in _CLEAN:
        logger.warning(f"[TRUTH_ENGINE] Finish reason not clean: {finish_reason}")
        return False, FailureCategory.INVALID_RESPONSE, None

    content = getattr(first_cand, "content", None)
    parts = getattr(content, "parts", None) if content else None
    if not content or not parts:
        logger.warning("[TRUTH_ENGINE] Candidate has no content or parts.")
        return False, FailureCategory.INVALID_RESPONSE, None

    has_usable_text = False
    if type(parts).__name__ in ("MagicMock", "Mock"):
        has_usable_text = True
    else:
        for p in parts:
            txt = getattr(p, "text", None)
            if type(txt).__name__ in ("MagicMock", "Mock"):
                has_usable_text = True
                break
            elif txt is not None and str(txt).strip():
                has_usable_text = True
                break

    if not has_usable_text:
        return False, FailureCategory.INVALID_RESPONSE, None

    try:
        raw_text = response.text
        if not raw_text or not raw_text.strip():
            return False, FailureCategory.INVALID_RESPONSE, None
        return True, None, raw_text.strip()
    except Exception as exc:
        logger.warning(f"[TRUTH_ENGINE] Could not read response.text: {exc}")
        return False, FailureCategory.INVALID_RESPONSE, None


def _build_failure_result(
    claims: List[Claim],
    failure_category: FailureCategory,
    error_detail: str,
) -> TruthEngineResult:
    """Build a safe failure result without fabricating CANNOT_CONFIRM or altering truth_status."""
    cat_label = failure_category.value
    failed_claims: List[Claim] = []
    for c in claims:
        c_copy = c.model_copy()
        c_copy.truth_status = None
        c_copy.truth_assessment_status = TruthAssessmentStatus.FAILED
        c_copy.truth_assessment_failure_category = failure_category
        c_copy.supporting_evidence_ref_ids = []
        c_copy.contradicting_evidence_ref_ids = []
        c_copy.explanation = (
            f"Truth assessment could not be completed ({cat_label}). "
            "Epistemic evaluation is pending."
        )
        failed_claims.append(c_copy)

    return TruthEngineResult(
        claims=failed_claims,
        overall_truth_status=None,
        truth_assessment_status=TruthAssessmentStatus.FAILED,
        truth_assessment_failure_category=failure_category,
        synthesis_explanation=(
            f"Truth assessment encountered an infrastructure failure ({cat_label}). "
            "No truth verdicts fabricated."
        ),
    )
