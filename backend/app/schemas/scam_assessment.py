from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import FailureCategory
from app.schemas.investigation import RiskLevel, ScamAssessmentStatus


class SignalProvenance(str, Enum):
    """Traceable origin of an identified indicator."""
    ORIGINAL_MESSAGE = "original_message"
    GEMINI_EXTRACTED_SIGNAL = "gemini_extracted_signal"
    DETERMINISTIC_URL_CHECK = "deterministic_url_check"
    EXTERNAL_FACT_CHECK = "external_fact_check"


class IndicatorCategory(str, Enum):
    """Functional category of behavioral and technical threat indicators."""
    FINANCIAL_REQUEST = "financial_request"
    CREDENTIAL_THEFT = "credential_theft"
    MANIPULATION_PERSUASION = "manipulation_persuasion"
    IMPERSONATION = "impersonation"
    URL_INDICATOR = "url_indicator"


class ScamIndicator(BaseModel):
    """Normalized structured indicator record with provenance and uncalibrated strength."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Stable indicator ID, e.g. 'ind-fin-1'")
    category: IndicatorCategory = Field(description="Indicator category")
    name: str = Field(description="Human-readable title of the indicator")
    severity_weight: int = Field(ge=0, description="Centralized rule base weight")
    effective_points: int = Field(default=0, ge=0, description="Points contributed after fusion calculation")
    provenance: SignalProvenance = Field(description="Traceable origin of this indicator")
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Relevant verbatim message excerpt or exact URL supporting the indicator",
    )
    associated_claim_ids: List[str] = Field(
        default_factory=list,
        description="IDs of extracted claims correlated with this indicator",
    )
    explanation: str = Field(description="Why this rule fired and its behavioral or technical implication")
    confidence: float = Field(ge=0.0, le=1.0, description="Uncalibrated detection strength score")
    is_directly_observed: bool = Field(
        default=False,
        description="True if observed directly in user input; False if inferred/suspected by model pattern",
    )


class ScamAssessmentResult(BaseModel):
    """Result of Scam Investigation and Deterministic Risk Fusion."""
    model_config = ConfigDict(populate_by_name=True)

    status: ScamAssessmentStatus = Field(description="Assessment lifecycle status")
    failure_category: Optional[FailureCategory] = Field(
        default=None,
        description="Safe machine-readable failure reason if status is FAILED",
    )
    risk_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Calculated deterministic threat index (0-100). None if not assessed or failed.",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.NOT_ASSESSED,
        description="Categorical risk tier: LOW, MODERATE, HIGH, CRITICAL, or NOT_ASSESSED",
    )
    indicators: List[ScamIndicator] = Field(
        default_factory=list,
        description="Normalized indicators evaluated by the engine",
    )
    deduplication_notes: List[str] = Field(
        default_factory=list,
        description="Auditing notes regarding grouped or capped correlated indicators",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable user recommendations proportional to observed risk",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Documented forensic limitations of the heuristic evaluation",
    )
    summary_explanation: str = Field(
        default="",
        description="Forensic explanation of risk fusion findings",
    )
