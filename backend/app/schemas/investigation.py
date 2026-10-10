from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.evidence import FailureCategory, RetrievalStatus


class InputType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    URL = "url"
    PDF = "pdf"
    AUDIO = "audio"


class TruthAssessmentStatus(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    ASSESSED = "ASSESSED"
    FAILED = "FAILED"


class ScamAssessmentStatus(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    ASSESSED = "ASSESSED"
    FAILED = "FAILED"


class TruthStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FALSE = "FALSE"
    PARTIALLY_SUPPORTED = "PARTIALLY SUPPORTED"
    OUTDATED = "OUTDATED"
    CANNOT_CONFIRM = "CANNOT CONFIRM"


class RiskLevel(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceTier(str, Enum):
    TIER_1_OFFICIAL = "tier_1_official"
    TIER_2_AUTHORITATIVE = "tier_2_authoritative"
    TIER_3_SECONDARY = "tier_3_secondary"
    UNVERIFIED = "unverified"


class SourceStance(str, Enum):
    CONTRADICTS = "CONTRADICTS"
    CORROBORATES = "CORROBORATES"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class SslStatus(str, Enum):
    ANOMALOUS = "anomalous"
    VALID_COMMERCIAL = "valid_commercial"
    SELF_SIGNED = "self_signed"
    MISSING = "missing"


# Request Schema
class InvestigationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    input_type: InputType = Field(
        default=InputType.TEXT,
        validation_alias=AliasChoices("input_type", "inputMode", "input_mode"),
        description="Type of input: text, image, or url",
    )
    content: str = Field(
        ...,
        validation_alias=AliasChoices("content", "text", "rawInput", "raw_input"),
        description="Raw message text, URL, or extracted transcription",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Optional image URL or asset reference if analyzing an image",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional supplementary client metadata (e.g. filename, user agent)",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Investigation content cannot be empty.")
        return v.strip()


# Sub-schemas for Result
class Claim(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    claim_number: int = Field(..., alias="claimNumber")
    statement: str
    truth_status: Optional[TruthStatus] = Field(default=None, alias="truthStatus")
    truth_assessment_status: TruthAssessmentStatus = Field(
        default=TruthAssessmentStatus.NOT_ASSESSED,
        alias="truthAssessmentStatus",
        description="Assessment lifecycle status: NOT_ASSESSED, ASSESSED, or FAILED",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: Literal["benefit_lure", "advance_fee", "urgency_coercion", "factual_assertion"] = "factual_assertion"
    explanation: str
    evidence_ref_ids: List[str] = Field(default_factory=list, alias="evidenceRefIds")
    supporting_evidence_ref_ids: List[str] = Field(
        default_factory=list,
        alias="supportingEvidenceRefIds",
        description="IDs of evidence sources that corroborate this claim",
    )
    contradicting_evidence_ref_ids: List[str] = Field(
        default_factory=list,
        alias="contradictingEvidenceRefIds",
        description="IDs of evidence sources that contradict this claim",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="Unresolved conflicts, temporal limits, or source caveats",
    )
    truth_assessment_failure_category: Optional[FailureCategory] = Field(
        default=None,
        alias="truthAssessmentFailureCategory",
        description="Safe machine-readable category if truth assessment failed",
    )


class EvidenceSource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    publisher: str
    url: Optional[str] = None
    published_date: Optional[str] = Field(default=None, alias="publishedDate")
    tier: SourceTier
    tier_label: str = Field(..., alias="tierLabel")
    stance: SourceStance
    confidence_score: float = Field(..., alias="confidenceScore", ge=0.0, le=1.0)
    excerpt: str
    is_simulated_demo: bool = Field(default=True, alias="isSimulatedDemo")


class ScamSignal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    category: str
    description: str
    risk_points: int = Field(..., alias="riskPoints", ge=0)
    evidence: str
    provenance: Optional[str] = Field(default=None, description="Signal origin / provenance")
    is_directly_observed: bool = Field(default=False, alias="isDirectlyObserved")


class UrlInvestigationData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analyzed_url: str = Field(..., alias="analyzedUrl")
    domain: str
    is_typosquat: bool = Field(..., alias="isTyposquat")
    impersonated_brand: Optional[str] = Field(default=None, alias="impersonatedBrand")
    registration_age: str = Field(..., alias="registrationAge")
    ssl_status: SslStatus = Field(..., alias="sslStatus")
    registrar: str
    risk_indicators: List[str] = Field(default_factory=list, alias="riskIndicators")


class Recommendations(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    urgent_actions: List[str] = Field(default_factory=list, alias="urgentActions")
    advisory_note: str = Field(..., alias="advisoryNote")


class Metrics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    claims_detected: int = Field(..., alias="claimsDetected")
    sources_corroborated: int = Field(..., alias="sourcesCorroborated")
    threat_signals_found: int = Field(..., alias="threatSignalsFound")
    investigation_duration_ms: int = Field(..., alias="investigationDurationMs")


# Top-Level Investigation Result
class InvestigationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    case_ref: str = Field(..., alias="caseRef")
    timestamp: str
    input_mode: InputType = Field(..., alias="inputMode")
    raw_input: str = Field(..., alias="rawInput")
    extracted_text: Optional[str] = Field(default=None, alias="extractedText")
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    truth_status: Optional[TruthStatus] = Field(default=None, alias="truthStatus")
    truth_assessment_status: TruthAssessmentStatus = Field(
        default=TruthAssessmentStatus.NOT_ASSESSED,
        alias="truthAssessmentStatus",
        description="Truth assessment lifecycle status: NOT_ASSESSED, ASSESSED, or FAILED",
    )
    truth_assessment_failure_category: Optional[FailureCategory] = Field(
        default=None,
        alias="truthAssessmentFailureCategory",
        description="Safe machine-readable category if truth assessment failed",
    )
    scam_risk_score: Optional[int] = Field(
        default=None,
        alias="scamRiskScore",
        ge=0,
        le=100,
        description="Scam risk score (0-100). None if not assessed or failed.",
    )
    risk_level: Optional[RiskLevel] = Field(
        default=RiskLevel.NOT_ASSESSED,
        alias="riskLevel",
        description="Risk level tier: LOW, MODERATE, HIGH, CRITICAL, or NOT_ASSESSED.",
    )
    scam_assessment_status: ScamAssessmentStatus = Field(
        default=ScamAssessmentStatus.NOT_ASSESSED,
        alias="scamAssessmentStatus",
        description="Scam assessment lifecycle status: NOT_ASSESSED, ASSESSED, or FAILED",
    )
    scam_assessment_failure_category: Optional[FailureCategory] = Field(
        default=None,
        alias="scamAssessmentFailureCategory",
        description="Safe machine-readable category if scam assessment failed",
    )
    headline_verdict: str = Field(..., alias="headlineVerdict")
    summary_explanation: str = Field(..., alias="summaryExplanation")
    claims: List[Claim] = Field(default_factory=list)
    evidence: List[EvidenceSource] = Field(default_factory=list)
    scam_signals: List[ScamSignal] = Field(default_factory=list, alias="scamSignals")

    url_analysis: Optional[UrlInvestigationData] = Field(default=None, alias="urlAnalysis")
    recommendations: Recommendations
    metrics: Metrics
    development_mode: bool = Field(default=True, alias="developmentMode")
    content_extraction_mode: Optional[Literal["GEMINI_LLM", "DETERMINISTIC_FALLBACK"]] = Field(
        default="GEMINI_LLM",
        alias="contentExtractionMode",
        description="Content extraction mechanism: GEMINI_LLM or DETERMINISTIC_FALLBACK",
    )
    content_analysis_failure_category: Optional[FailureCategory] = Field(
        default=None,
        alias="contentAnalysisFailureCategory",
        description="Safe machine-readable category if Gemini content analysis failed (e.g. RATE_LIMIT)",
    )
    evidence_retrieval_status: Optional[RetrievalStatus] = Field(
        default=None,
        alias="evidenceRetrievalStatus",
        description="Explicit status of evidence retrieval: SUCCESS, NO_EVIDENCE, FAILED, or SKIPPED",
    )
    evidence_failure_category: Optional[FailureCategory] = Field(
        default=None,
        alias="evidenceFailureCategory",
        description="Safe machine-readable category if evidence retrieval failed",
    )
