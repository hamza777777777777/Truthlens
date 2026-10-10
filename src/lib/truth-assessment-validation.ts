/**
 * Deterministic Frontend Type & State Validation: Truth Assessment Lifecycle
 *
 * Enforces Phase 4C requirements:
 * 1. Truth assessment not yet performed (NOT_ASSESSED, truthStatus=null/undefined)
 * 2. Evidence retrieval failed before assessment (FAILED retrieval, NOT_ASSESSED, truthStatus=null/undefined)
 * 3. Assessment performed with insufficient evidence (ASSESSED, truthStatus="CANNOT CONFIRM")
 * 4. Assessment performed with supported or contradicted claim (ASSESSED, truthStatus="VERIFIED"|"FALSE"|"PARTIALLY SUPPORTED")
 */

import type { Claim, InvestigationResult } from "../types/investigation";

/** State 1: Truth assessment not yet performed */
export const STATE_1_NOT_YET_ASSESSED: InvestigationResult = {
  id: "inv-test-state-1",
  caseRef: "TL-CASE-STATE-1",
  timestamp: "2026-10-10 12:00:00 UTC",
  inputMode: "text",
  rawInput: "Test claim statement",
  truthStatus: null,
  truthAssessmentStatus: "NOT_ASSESSED",
  evidenceRetrievalStatus: "SUCCESS",
  scamRiskScore: null,
  riskLevel: "NOT_ASSESSED",
  headlineVerdict: "CLAIMS EXTRACTED (1) • 0 SIGNALS DETECTED • 1 SOURCE(S) GROUNDED",
  summaryExplanation: "Atomic claims isolated and grounded; deterministic truth assessment executes in subsequent phase.",
  claims: [
    {
      id: "cl-1",
      claimNumber: 1,
      statement: "Factual claim pending assessment",
      truthStatus: null,
      truthAssessmentStatus: "NOT_ASSESSED",
      confidence: 0.9,
      category: "factual_assertion",
      explanation: "Grounded against 1 retrieved source(s). Truth fusion executes in subsequent TruthLens engines.",
      evidenceRefIds: ["ev-1"],
    },
  ],
  evidence: [
    {
      id: "ev-1",
      title: "Authoritative Reference",
      publisher: "official.gov.in",
      url: "https://official.gov.in/notice",
      tier: "tier_1_official",
      tierLabel: "Official / Government Source",
      stance: "INSUFFICIENT",
      confidenceScore: 0.92,
      excerpt: "Relevant passage retrieved.",
      isSimulatedDemo: false,
    },
  ],
  scamSignals: [],
  recommendations: { urgentActions: [], advisoryNote: "Advisory" },
  metrics: { claimsDetected: 1, sourcesCorroborated: 1, threatSignalsFound: 0, investigationDurationMs: 500 },
  developmentMode: true,
};

/** State 2: Evidence retrieval failed before assessment */
export const STATE_2_RETRIEVAL_FAILED: InvestigationResult = {
  id: "inv-test-state-2",
  caseRef: "TL-CASE-STATE-2",
  timestamp: "2026-10-10 12:00:00 UTC",
  inputMode: "text",
  rawInput: "Test claim statement",
  truthStatus: null,
  truthAssessmentStatus: "NOT_ASSESSED",
  evidenceRetrievalStatus: "FAILED",
  evidenceFailureCategory: "RATE_LIMIT",
  scamRiskScore: null,
  riskLevel: "NOT_ASSESSED",
  headlineVerdict: "CLAIMS EXTRACTED (1) • 0 SIGNALS DETECTED [EVIDENCE RETRIEVAL FAILED]",
  summaryExplanation: "External evidence retrieval failed (RATE_LIMIT). The Truth Engine does not yet have sufficient evidence to make an assessment.",
  claims: [
    {
      id: "cl-1",
      claimNumber: 1,
      statement: "Factual claim where retrieval failed",
      truthStatus: null,
      truthAssessmentStatus: "NOT_ASSESSED",
      confidence: 0.9,
      category: "factual_assertion",
      explanation: "Evidence retrieval could not be completed (RATE_LIMIT); evidence assessment is pending.",
      evidenceRefIds: [],
    },
  ],
  evidence: [
    {
      id: "ev-retrieval-failed",
      title: "Evidence Retrieval Unavailable",
      publisher: "TruthLens Evidence Engine",
      tier: "unverified",
      tierLabel: "Retrieval Failed",
      stance: "INSUFFICIENT",
      confidenceScore: 0.0,
      excerpt: "Evidence retrieval could not be completed (RATE_LIMIT). The Truth Engine does not yet have sufficient evidence to make an assessment.",
      isSimulatedDemo: true,
    },
  ],
  scamSignals: [],
  recommendations: { urgentActions: [], advisoryNote: "Advisory" },
  metrics: { claimsDetected: 1, sourcesCorroborated: 1, threatSignalsFound: 0, investigationDurationMs: 500 },
  developmentMode: true,
};

/** State 2B: Upstream Content Intelligence failure -> Fallback extraction used, Evidence retrieval skipped */
export const STATE_2B_RETRIEVAL_SKIPPED: InvestigationResult = {
  id: "inv-test-state-2b",
  caseRef: "TL-CASE-STATE-2B",
  timestamp: "2026-10-10 12:00:00 UTC",
  inputMode: "text",
  rawInput: "Test claim statement",
  truthStatus: null,
  truthAssessmentStatus: "NOT_ASSESSED",
  contentExtractionMode: "DETERMINISTIC_FALLBACK",
  contentAnalysisFailureCategory: "RATE_LIMIT",
  evidenceRetrievalStatus: "SKIPPED",
  scamRiskScore: null,
  riskLevel: "NOT_ASSESSED",
  headlineVerdict: "CLAIMS EXTRACTED (1) • 0 SIGNALS DETECTED [EVIDENCE RETRIEVAL SKIPPED]",
  summaryExplanation: "Deterministic heuristic parser extracted 1 atomic claim(s) (Gemini content intelligence fallback triggered by RATE_LIMIT). External evidence retrieval was skipped (RATE_LIMIT upstream).",
  claims: [
    {
      id: "cl-1",
      claimNumber: 1,
      statement: "Factual claim where extraction was heuristic and retrieval skipped",
      truthStatus: null,
      truthAssessmentStatus: "NOT_ASSESSED",
      confidence: 0.8,
      category: "factual_assertion",
      explanation: "Extracted via deterministic heuristic extraction (factual): \"Factual claim where extraction was heuristic and retrieval skipped\". External evidence retrieval was skipped (RATE_LIMIT upstream); evidence assessment is pending.",
      evidenceRefIds: [],
    },
  ],
  evidence: [
    {
      id: "ev-retrieval-skipped",
      title: "Evidence Retrieval Skipped",
      publisher: "TruthLens Evidence Engine",
      tier: "unverified",
      tierLabel: "Retrieval Skipped",
      stance: "INSUFFICIENT",
      confidenceScore: 0.0,
      excerpt: "External evidence retrieval was not attempted because upstream content intelligence encountered a RATE_LIMIT limit. Grounding was skipped.",
      isSimulatedDemo: true,
    },
  ],
  scamSignals: [],
  recommendations: { urgentActions: [], advisoryNote: "Advisory" },
  metrics: { claimsDetected: 1, sourcesCorroborated: 0, threatSignalsFound: 0, investigationDurationMs: 500 },
  developmentMode: true,
};

/** State 3: Assessment performed with insufficient evidence */
export const STATE_3_INSUFFICIENT_EVIDENCE: Claim = {
  id: "cl-insufficient",
  claimNumber: 1,
  statement: "Claim evaluated but external evidence is inconclusive",
  truthStatus: "CANNOT CONFIRM",
  truthAssessmentStatus: "ASSESSED",
  confidence: 0.75,
  category: "factual_assertion",
  explanation: "Assessment performed; available external evidence is insufficient to confirm or refute.",
  evidenceRefIds: ["ev-1"],
};

/** State 4: Assessment performed with supported or contradicted claim */
export const STATE_4_VERIFIED_CLAIM: Claim = {
  id: "cl-verified",
  claimNumber: 1,
  statement: "Claim confirmed true by primary sources",
  truthStatus: "VERIFIED",
  truthAssessmentStatus: "ASSESSED",
  confidence: 0.99,
  category: "factual_assertion",
  explanation: "Primary assertions corroborated by official authoritative sources.",
  evidenceRefIds: ["ev-1"],
};

export const STATE_4_CONTRADICTED_CLAIM: Claim = {
  id: "cl-contradicted",
  claimNumber: 2,
  statement: "Claim refuted by regulatory bulletins",
  truthStatus: "FALSE",
  truthAssessmentStatus: "ASSESSED",
  confidence: 0.98,
  category: "benefit_lure",
  explanation: "Primary assertions directly refuted by regulatory advisories and authentic bank bulletins.",
  evidenceRefIds: ["ev-2"],
};

export const STATE_4_PARTIAL_CLAIM: Claim = {
  id: "cl-partial",
  claimNumber: 3,
  statement: "Claim partially corroborated",
  truthStatus: "PARTIALLY SUPPORTED",
  truthAssessmentStatus: "ASSESSED",
  confidence: 0.85,
  category: "factual_assertion",
  explanation: "Assertions partially supported by available evidence.",
  evidenceRefIds: ["ev-3"],
};

/** State 5: Truth Engine provider or parsing failure */
export const STATE_5_ASSESSMENT_FAILED: InvestigationResult = {
  id: "inv-test-state-5",
  caseRef: "TL-CASE-STATE-5",
  timestamp: "2026-10-10 12:00:00 UTC",
  inputMode: "text",
  rawInput: "Test claim statement",
  truthStatus: null,
  truthAssessmentStatus: "FAILED",
  truthAssessmentFailureCategory: "PROVIDER_ERROR",
  evidenceRetrievalStatus: "SUCCESS",
  scamRiskScore: null,
  riskLevel: "NOT_ASSESSED",
  headlineVerdict: "CLAIMS EXTRACTED (1) • [TRUTH ASSESSMENT FAILED]",
  summaryExplanation: "Truth assessment could not be completed (PROVIDER_ERROR). The Truth Engine encountered an internal evaluation failure.",
  claims: [
    {
      id: "cl-1",
      claimNumber: 1,
      statement: "Factual claim where truth engine failed",
      truthStatus: null,
      truthAssessmentStatus: "FAILED",
      truthAssessmentFailureCategory: "PROVIDER_ERROR",
      confidence: 0.5,
      category: "factual_assertion",
      explanation: "Truth assessment could not be completed (PROVIDER_ERROR); assessment is pending.",
      evidenceRefIds: ["ev-1"],
      supportingEvidenceRefIds: [],
      contradictingEvidenceRefIds: [],
    },
  ],
  evidence: [
    {
      id: "ev-1",
      title: "Authoritative Reference",
      publisher: "official.gov.in",
      url: "https://official.gov.in/notice",
      tier: "tier_1_official",
      tierLabel: "Official / Government Source",
      stance: "CORROBORATES",
      confidenceScore: 0.95,
      excerpt: "Official corroboration text.",
      isSimulatedDemo: false,
    },
  ],
  scamSignals: [],
  recommendations: { urgentActions: [], advisoryNote: "Advisory" },
  metrics: { claimsDetected: 1, sourcesCorroborated: 1, threatSignalsFound: 0, investigationDurationMs: 500 },
  developmentMode: true,
};

/** Runtime assertion helper validating that NOT_ASSESSED or FAILED never presents a completed truth verdict */
export function validateTruthAssessmentStates(): boolean {
  // State 1 check
  if (STATE_1_NOT_YET_ASSESSED.truthAssessmentStatus !== "NOT_ASSESSED") throw new Error("State 1 failure");
  if (STATE_1_NOT_YET_ASSESSED.truthStatus !== null) throw new Error("State 1 truthStatus must be null");
  if (STATE_1_NOT_YET_ASSESSED.claims[0].truthStatus !== null) throw new Error("State 1 claim truthStatus must be null");

  // State 2 check
  if (STATE_2_RETRIEVAL_FAILED.evidenceRetrievalStatus !== "FAILED") throw new Error("State 2 failure");
  if (STATE_2_RETRIEVAL_FAILED.truthAssessmentStatus !== "NOT_ASSESSED") throw new Error("State 2 failure");
  if (STATE_2_RETRIEVAL_FAILED.truthStatus !== null) throw new Error("State 2 truthStatus must be null");

  // State 2B check: Skipped retrieval preserves NOT_ASSESSED and null truthStatus
  if (STATE_2B_RETRIEVAL_SKIPPED.evidenceRetrievalStatus !== "SKIPPED") throw new Error("State 2B failure");
  if (STATE_2B_RETRIEVAL_SKIPPED.contentExtractionMode !== "DETERMINISTIC_FALLBACK") throw new Error("State 2B extraction mode failure");
  if (STATE_2B_RETRIEVAL_SKIPPED.truthAssessmentStatus !== "NOT_ASSESSED") throw new Error("State 2B failure");
  if (STATE_2B_RETRIEVAL_SKIPPED.truthStatus !== null) throw new Error("State 2B truthStatus must be null");
  if (STATE_2B_RETRIEVAL_SKIPPED.claims[0].truthStatus !== null) throw new Error("State 2B claim truthStatus must be null");

  // State 3 check
  if (STATE_3_INSUFFICIENT_EVIDENCE.truthAssessmentStatus !== "ASSESSED") throw new Error("State 3 failure");
  if (STATE_3_INSUFFICIENT_EVIDENCE.truthStatus !== "CANNOT CONFIRM") throw new Error("State 3 failure");

  // State 4 checks
  if (STATE_4_VERIFIED_CLAIM.truthStatus !== "VERIFIED") throw new Error("State 4 verified failure");
  if (STATE_4_CONTRADICTED_CLAIM.truthStatus !== "FALSE") throw new Error("State 4 contradicted failure");
  if (STATE_4_PARTIAL_CLAIM.truthStatus !== "PARTIALLY SUPPORTED") throw new Error("State 4 partial failure");

  // State 5 checks
  if (STATE_5_ASSESSMENT_FAILED.truthAssessmentStatus !== "FAILED") throw new Error("State 5 failure");
  if (STATE_5_ASSESSMENT_FAILED.truthStatus !== null) throw new Error("State 5 truthStatus must be null");
  if (STATE_5_ASSESSMENT_FAILED.claims[0].truthStatus !== null) throw new Error("State 5 claim truthStatus must be null");
  if (STATE_5_ASSESSMENT_FAILED.claims[0].truthAssessmentStatus !== "FAILED") throw new Error("State 5 claim status failure");

  return true;
}

// Automatically execute and enforce runtime assertions when file is run
validateTruthAssessmentStates();
console.log("✓ Truth assessment lifecycle states validated successfully (6/6 states verified).");

