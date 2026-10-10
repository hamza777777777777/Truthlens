export type InputMode = "text" | "image" | "url" | "pdf" | "audio";

export type TruthStatus = 
  | "VERIFIED" 
  | "FALSE" 
  | "PARTIALLY SUPPORTED" 
  | "OUTDATED" 
  | "CANNOT CONFIRM";

export type RiskLevel = "NOT_ASSESSED" | "MINIMAL" | "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "CRITICAL";

export type SourceTier = "tier_1_official" | "tier_2_authoritative" | "tier_3_secondary" | "unverified";

export type SourceStance = "CONTRADICTS" | "CORROBORATES" | "PARTIAL" | "INSUFFICIENT";

export type TruthAssessmentStatus = "NOT_ASSESSED" | "ASSESSED" | "FAILED";

export interface Claim {
  id: string;
  claimNumber: number;
  statement: string;
  truthStatus?: TruthStatus | null;
  truthAssessmentStatus: TruthAssessmentStatus;
  confidence: number; // 0 to 1
  category: "benefit_lure" | "advance_fee" | "urgency_coercion" | "factual_assertion";
  explanation: string;
  evidenceRefIds: string[];
  supportingEvidenceRefIds?: string[];
  contradictingEvidenceRefIds?: string[];
  limitations?: string;
  truthAssessmentFailureCategory?: FailureCategory;
}

export interface EvidenceSource {
  id: string;
  title: string;
  publisher: string;
  url?: string;
  publishedDate?: string;
  tier: SourceTier;
  tierLabel: string;
  stance: SourceStance;
  confidenceScore: number;
  excerpt: string;
  isSimulatedDemo: boolean;
}

export type ScamAssessmentStatus = "NOT_ASSESSED" | "ASSESSED" | "FAILED";

export interface ScamSignal {
  id: string;
  name: string;
  category: string;
  description: string;
  riskPoints: number;
  evidence: string;
  provenance?: string;
  isDirectlyObserved?: boolean;
}

export interface UrlInvestigationData {
  analyzedUrl: string;
  domain: string;
  isTyposquat: boolean;
  impersonatedBrand?: string;
  registrationAge: string;
  sslStatus: "anomalous" | "valid_commercial" | "self_signed" | "missing";
  registrar: string;
  riskIndicators: string[];
}

export interface InvestigationResult {
  id: string;
  caseRef: string;
  timestamp: string;
  inputMode: InputMode;
  rawInput: string;
  extractedText?: string;
  imageUrl?: string;
  truthStatus?: TruthStatus | null;
  truthAssessmentStatus?: TruthAssessmentStatus;
  truthAssessmentFailureCategory?: FailureCategory;
  scamRiskScore?: number | null;
  riskLevel?: RiskLevel | null;
  scamAssessmentStatus?: ScamAssessmentStatus;
  scamAssessmentFailureCategory?: FailureCategory;
  headlineVerdict: string;
  summaryExplanation: string;
  claims: Claim[];
  evidence: EvidenceSource[];
  scamSignals: ScamSignal[];
  urlAnalysis?: UrlInvestigationData;
  recommendations: {
    urgentActions: string[];
    advisoryNote: string;
  };
  metrics: {
    claimsDetected: number;
    sourcesCorroborated: number;
    threatSignalsFound: number;
    investigationDurationMs: number;
  };
  developmentMode?: boolean;
  contentExtractionMode?: "GEMINI_LLM" | "DETERMINISTIC_FALLBACK";
  contentAnalysisFailureCategory?: FailureCategory;
  evidenceRetrievalStatus?: RetrievalStatus;
  evidenceFailureCategory?: FailureCategory;
}

export type RetrievalStatus = "SUCCESS" | "NO_EVIDENCE" | "FAILED" | "SKIPPED";

export type FailureCategory =
  | "AUTHENTICATION"
  | "RATE_LIMIT"
  | "NETWORK"
  | "INVALID_CONFIGURATION"
  | "PROVIDER_ERROR"
  | "INVALID_RESPONSE"
  | "UNKNOWN";

export interface InvestigationStage {
  id: number;
  code: string;
  label: string;
  detail: string;
}
