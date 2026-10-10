import logging
from typing import Dict, List, Optional, Tuple

from app.schemas.evidence import FailureCategory
from app.schemas.investigation import RiskLevel
from app.schemas.scam_assessment import (
    IndicatorCategory,
    ScamAssessmentResult,
    ScamAssessmentStatus,
    ScamIndicator,
    SignalProvenance,
)

logger = logging.getLogger("truthlens.risk_fusion")

# Centralized category contribution ceilings
CATEGORY_CEILINGS: Dict[IndicatorCategory, int] = {
    IndicatorCategory.CREDENTIAL_THEFT: 35,
    IndicatorCategory.FINANCIAL_REQUEST: 30,
    IndicatorCategory.IMPERSONATION: 25,
    IndicatorCategory.URL_INDICATOR: 25,
    IndicatorCategory.MANIPULATION_PERSUASION: 20,
}

# Score threshold mappings
RISK_THRESHOLDS: List[Tuple[int, int, RiskLevel]] = [
    (0, 19, RiskLevel.LOW),
    (20, 49, RiskLevel.MODERATE),
    (50, 74, RiskLevel.HIGH),
    (75, 100, RiskLevel.CRITICAL),
]

MIN_CONFIDENCE_THRESHOLD = 0.35


def map_score_to_risk_level(score: int) -> RiskLevel:
    """Map a bounded heuristic score (0-100) to an explicit RiskLevel."""
    for low, high, level in RISK_THRESHOLDS:
        if low <= score <= high:
            return level
    return RiskLevel.CRITICAL if score > 100 else RiskLevel.LOW


def generate_recommendations(
    active_categories: List[IndicatorCategory],
    risk_level: RiskLevel,
) -> List[str]:
    """Generate proportional, actionable recommendations based on active threat vectors."""
    recs: List[str] = []

    if IndicatorCategory.CREDENTIAL_THEFT in active_categories:
        recs.append("NEVER disclose passwords, PINs, OTPs, or banking credentials under any circumstance.")

    if IndicatorCategory.FINANCIAL_REQUEST in active_categories:
        recs.append("DO NOT send advance processing fees, registration charges, or wire transfers to claim rewards.")

    if IndicatorCategory.IMPERSONATION in active_categories or IndicatorCategory.URL_INDICATOR in active_categories:
        recs.append("Avoid following links received in unsolicited messages; navigate to the authentic domain manually.")

    if IndicatorCategory.MANIPULATION_PERSUASION in active_categories:
        recs.append("Pause and verify independently. Legitimate organizations do not enforce urgent deadlines or legal threats via SMS/chat.")

    # Always ensure at least baseline advisory
    if not recs:
        recs.append("Exercise standard vigilance when reviewing unsolicited digital communications.")

    recs.append("Confirm any questionable solicitation directly via verified official organizational channels.")
    return recs


class DeterministicRiskFusion:
    """Deterministic, transparent risk fusion engine.
    
    Principles:
    1. Pure deterministic code — Gemini never calculates or alters the score.
    2. Bounded index: 0 to 100 maximum.
    3. Deduplication: repeated indicators of the same canonical type take max weight, not cumulative sum.
    4. Category caps: prevent single-vector signal inflation.
    5. Provenance validation: signals without traceable origin contribute 0 points.
    6. Low-confidence model noise filtering (confidence < 0.35 discarded).
    7. Independence: Truth status has zero influence on the risk score.
    """

    def fuse(
        self,
        indicators: List[ScamIndicator],
    ) -> ScamAssessmentResult:
        """Execute deterministic risk calculation over normalized indicators."""
        try:
            return self._execute_fusion(indicators)
        except Exception as e:
            logger.exception(f"Unexpected error during risk fusion: {e}")
            return ScamAssessmentResult(
                status=ScamAssessmentStatus.FAILED,
                failure_category=FailureCategory.UNKNOWN,
                risk_score=None,
                risk_level=RiskLevel.NOT_ASSESSED,
                indicators=indicators,
                deduplication_notes=[],
                recommendations=[],
                limitations=["Risk fusion engine encountered an internal failure."],
                summary_explanation="Risk fusion calculation failed. No risk score or safety verdict was manufactured.",
            )

    def _execute_fusion(
        self,
        indicators: List[ScamIndicator],
    ) -> ScamAssessmentResult:
        if not indicators:
            return ScamAssessmentResult(
                status=ScamAssessmentStatus.ASSESSED,
                failure_category=None,
                risk_score=0,
                risk_level=RiskLevel.LOW,
                indicators=[],
                deduplication_notes=["No suspicious indicators detected."],
                recommendations=generate_recommendations([], RiskLevel.LOW),
                limitations=[
                    "Heuristic assessment: Absence of detected indicators does NOT confirm authentic origin or rule out fraud.",
                    "External infrastructure, WHOIS, and DNS records were not inspected.",
                ],
                summary_explanation=(
                    "No behavioral deception indicators or structural URL anomalies were detected under the "
                    "current deterministic rules. Risk is assessed as LOW. This indicates fewer observable threat "
                    "patterns, not guaranteed message safety."
                ),
            )

        # 1. Filter, validate provenance, and compute effective points
        valid_indicators: List[ScamIndicator] = []
        deduplication_notes: List[str] = []

        # Group by canonical deduplication key: (category, normalized_name)
        grouped_by_key: Dict[Tuple[IndicatorCategory, str], List[ScamIndicator]] = {}

        for ind in indicators:
            # Provenance requirement
            if not ind.provenance:
                ind.effective_points = 0
                deduplication_notes.append(
                    f"Indicator '{ind.name}' disregarded: Missing traceable evidence provenance."
                )
                continue

            # Confidence threshold for model-detected signals
            if ind.provenance == SignalProvenance.GEMINI_EXTRACTED_SIGNAL and ind.confidence < MIN_CONFIDENCE_THRESHOLD:
                ind.effective_points = 0
                deduplication_notes.append(
                    f"Indicator '{ind.name}' filtered out: Low extraction confidence ({ind.confidence:.2f} < {MIN_CONFIDENCE_THRESHOLD})."
                )
                continue

            # Calculate individual effective points
            raw_effective = round(ind.severity_weight * ind.confidence)
            ind.effective_points = max(1, raw_effective) if ind.severity_weight > 0 else 0

            group_key = (ind.category, ind.name.lower())
            grouped_by_key.setdefault(group_key, []).append(ind)

        # 2. Deduplicate within canonical groups (prevent duplicate signal inflation)
        # Category accumulators
        category_contributions: Dict[IndicatorCategory, int] = {cat: 0 for cat in IndicatorCategory}
        active_categories: List[IndicatorCategory] = []

        for (cat, name_key), group_items in grouped_by_key.items():
            if len(group_items) > 1:
                # Multiple signals of the same type — take the one with highest effective points
                highest_scoring = max(group_items, key=lambda x: x.effective_points)
                deduplication_notes.append(
                    f"Deduplicated {len(group_items)} instances of '{highest_scoring.name}': "
                    f"counted maximum ({highest_scoring.effective_points} pts), suppressing redundant duplicates."
                )
                for item in group_items:
                    if item is not highest_scoring:
                        item.effective_points = 0
                valid_indicators.extend(group_items)
                category_contributions[cat] += highest_scoring.effective_points
                if cat not in active_categories:
                    active_categories.append(cat)
            else:
                single_item = group_items[0]
                valid_indicators.append(single_item)
                category_contributions[cat] += single_item.effective_points
                if cat not in active_categories:
                    active_categories.append(cat)

        # 3. Apply category ceilings
        final_category_scores: Dict[IndicatorCategory, int] = {}
        for cat, raw_pts in category_contributions.items():
            ceiling = CATEGORY_CEILINGS.get(cat, 25)
            if raw_pts > ceiling:
                final_category_scores[cat] = ceiling
                deduplication_notes.append(
                    f"Category '{cat.value}' capped at ceiling of {ceiling} pts (raw total: {raw_pts} pts)."
                )
            else:
                final_category_scores[cat] = raw_pts

        # 4. Sum and cap total score at 100
        raw_total_score = sum(final_category_scores.values())
        final_score = min(100, max(0, raw_total_score))
        risk_level = map_score_to_risk_level(final_score)

        # 5. Explanations and limitations
        limitations = [
            "Heuristic risk index, NOT a percentage probability of fraud.",
            "URL indicators reflect syntactic and structural heuristics only; WHOIS, DNS, and SSL reputation were not queried.",
            "Independent of epistemic truth verdict: verified factual claims can accompany high deception risk.",
        ]

        active_cat_names = [c.value.replace("_", " ").title() for c in active_categories]
        summary_explanation = (
            f"Deterministic risk fusion evaluated {len(valid_indicators)} indicator(s) across "
            f"{len(active_categories)} threat vector(s) ({', '.join(active_cat_names) if active_cat_names else 'None'}). "
            f"Calculated heuristic risk index is {final_score}/100 ({risk_level.value} RISK)."
        )

        recommendations = generate_recommendations(active_categories, risk_level)

        return ScamAssessmentResult(
            status=ScamAssessmentStatus.ASSESSED,
            failure_category=None,
            risk_score=final_score,
            risk_level=risk_level,
            indicators=valid_indicators,
            deduplication_notes=deduplication_notes,
            recommendations=recommendations,
            limitations=limitations,
            summary_explanation=summary_explanation,
        )
