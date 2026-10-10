from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class LanguageInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(description="ISO language code, e.g. 'en', 'hi', 'mr', 'mixed'")
    name: str = Field(description="Language name, e.g. 'English', 'Hindi', 'Hinglish'")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence score from 0.0 to 1.0")


class ClaimAnalysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Unique claim identifier, e.g. 'claim-1'")
    statement: str = Field(description="Precise, atomic statement preserving exact numbers, currency, and names")
    category: str = Field(
        description="Claim categorization (e.g., 'benefit_claim', 'payment_instruction', 'urgency_constraint', 'link_context', 'factual_assertion')"
    )
    claim_type: Literal["factual", "behavioral_instruction", "contextual"] = Field(
        default="factual",
        description="Distinguishes factual assertions from behavioral instructions or context",
    )
    importance: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Importance of this claim to the core meaning of the message",
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score from 0.0 to 1.0")


class EntityAnalysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Entity name as explicitly mentioned, e.g. 'SBI', 'Reserve Bank'")
    type: Literal[
        "organization",
        "person",
        "place",
        "product",
        "financial_institution",
        "government_body",
        "event",
        "other",
    ] = Field(description="Entity category")
    context: str = Field(description="Context of how the entity is referenced in the content")
    confidence: float = Field(ge=0.0, le=1.0, description="Entity extraction confidence from 0.0 to 1.0")


class UrlTarget(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(description="Exact URL as presented in content without alteration")
    domain: str = Field(description="Extracted host/domain name from the URL")
    context: str = Field(description="Context or purpose of the link in the message")


class SuspiciousSignal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        description="Type of suspicious signal (e.g., 'advance_payment_request', 'urgency', 'reward_lure', 'authority_impersonation', 'credential_request', 'fear_or_threat', 'suspicious_link_language')"
    )
    description: str = Field(description="Plain-language description of the observed behavioral pattern")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence that this behavioral pattern is present")
    evidence: str = Field(description="Exact excerpt or phrase from the content exhibiting this signal")


class ContentAnalysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    normalized_text: str = Field(description="Cleaned, normalized text representation while preserving original meaning")
    language: LanguageInfo = Field(description="Language information of the content")
    claims: List[ClaimAnalysis] = Field(default_factory=list, description="Extracted atomic claims")
    entities: List[EntityAnalysis] = Field(default_factory=list, description="Extracted referenced entities")
    urls: List[UrlTarget] = Field(default_factory=list, description="Extracted URLs present in the content")
    suspicious_signals: List[SuspiciousSignal] = Field(
        default_factory=list,
        description="Detected suspicious behavioral patterns and content signals",
    )
