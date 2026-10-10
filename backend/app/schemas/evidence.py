from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class RetrievalStatus(str, Enum):
    """Explicit status of external evidence retrieval."""
    SUCCESS = "SUCCESS"
    NO_EVIDENCE = "NO_EVIDENCE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class FailureCategory(str, Enum):
    """Safe, machine-readable category for retrieval failures (no raw provider leaks)."""
    AUTHENTICATION = "AUTHENTICATION"
    RATE_LIMIT = "RATE_LIMIT"
    NETWORK = "NETWORK"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    UNKNOWN = "UNKNOWN"


class EvidenceSourceSchema(BaseModel):
    """A single external source retrieved and evaluated via Gemini grounding."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Unique evidence identifier, e.g. 'ev-1'")
    title: str = Field(description="Title of the source webpage or document")
    publisher: str = Field(description="Publisher or domain name of the source")
    url: Optional[str] = Field(default=None, description="URL of the retrieved source")
    snippet: str = Field(description="Relevant excerpt retrieved from the source")
    relevance_to_claim: str = Field(
        description="ID of the claim this source is most relevant to (e.g. 'claim-1')"
    )
    stance: Literal["CORROBORATES", "CONTRADICTS", "PARTIAL", "INSUFFICIENT"] = Field(
        description="Whether the source supports, contradicts, or is insufficient regarding the claim"
    )
    tier: Literal["tier_1_official", "tier_2_authoritative", "tier_3_secondary", "unverified"] = Field(
        default="unverified",
        description=(
            "Source authority tier: "
            "tier_1_official (government, RBI, SEBI, CERT-In, police), "
            "tier_2_authoritative (major verified news, academic), "
            "tier_3_secondary (blogs, community forums), "
            "unverified (unknown)"
        ),
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that this source is genuinely relevant to the claim (0.0–1.0)"
    )


class ClaimEvidenceAssessment(BaseModel):
    """Assessment of evidence gathered for a single claim."""

    model_config = ConfigDict(populate_by_name=True)

    claim_id: str = Field(description="ID of the claim being assessed, e.g. 'claim-1'")
    search_query_used: str = Field(description="The verification query submitted to Google Search for this claim")
    evidence_found: bool = Field(description="Whether any relevant evidence was retrieved")
    evidence_summary: str = Field(
        description=(
            "A brief factual summary (2–3 sentences) of what the retrieved evidence "
            "collectively says about this claim. Do NOT assert a truth verdict. "
            "Only describe what the sources indicate."
        )
    )


class GroundingAnalysis(BaseModel):
    """Complete evidence intelligence output for all claims in a submission."""

    model_config = ConfigDict(populate_by_name=True)

    retrieval_status: RetrievalStatus = Field(
        default=RetrievalStatus.FAILED,
        description="Explicit retrieval status: SUCCESS, NO_EVIDENCE, or FAILED"
    )
    failure_category: Optional[FailureCategory] = Field(
        default=None,
        description="Safe machine-readable failure category when retrieval_status is FAILED"
    )
    sources: List[EvidenceSourceSchema] = Field(
        default_factory=list,
        description="Retrieved and evaluated evidence sources (from grounding_chunks)"
    )
    claim_assessments: List[ClaimEvidenceAssessment] = Field(
        default_factory=list,
        description="Per-claim evidence assessment summaries"
    )
    grounding_search_queries: List[str] = Field(
        default_factory=list,
        description="All Google Search queries executed during grounding"
    )
    is_grounded: bool = Field(
        default=False,
        description="True if live Google Search grounding was used and sources returned; False otherwise"
    )
