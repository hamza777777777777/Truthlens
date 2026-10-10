"""
TruthLens Phase 4D — Truth Assessment Pydantic Schemas

Defines structured response contracts for Gemini Truth Engine calls.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class SingleClaimAssessment(BaseModel):
    """Structured assessment output for one claim from Gemini Truth Engine."""

    model_config = ConfigDict(populate_by_name=True)

    claim_id: str = Field(description="ID of the claim being evaluated, e.g. 'cl-1'")
    verdict: Literal["VERIFIED", "FALSE", "PARTIALLY SUPPORTED", "OUTDATED", "CANNOT CONFIRM"] = Field(
        description="Truth verdict strictly grounded in provided external evidence."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score from 0.0 to 1.0 reflecting evidence strength, tier authority, and agreement."
    )
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of provided evidence IDs that directly corroborate the claim."
    )
    contradicting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of provided evidence IDs that directly contradict the claim."
    )
    reasoning: str = Field(
        description="Traceable, evidence-grounded explanation explaining why the verdict was reached."
    )
    limitations: str = Field(
        default="",
        description="Key limitations, unresolved ambiguities, temporal gaps, or source credibility caveats."
    )


class TruthEngineBatchResponse(BaseModel):
    """Batch assessment response returned by Gemini structured generation."""

    model_config = ConfigDict(populate_by_name=True)

    assessments: List[SingleClaimAssessment] = Field(
        default_factory=list,
        description="Per-claim assessments for all eligible claims."
    )
    overall_synthesis: str = Field(
        default="",
        description="Forensic synthesis summarizing the epistemic truth findings across all evaluated claims."
    )
