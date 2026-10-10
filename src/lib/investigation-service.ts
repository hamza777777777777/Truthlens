import { 
  InvestigationResult, 
  InvestigationStage, 
  InputMode 
} from "@/types/investigation";

export const SAMPLE_INPUT_TEXT = 
  "Congratulations! You've won ₹50,000. Pay ₹499 to claim your reward within 2 hours at https://sbi-reward-claim.example";

export const INVESTIGATION_STAGES: InvestigationStage[] = [
  { id: 1, code: "INGESTING", label: "Ingesting Payload", detail: "Parsing multimodal input artifact & origin headers" },
  { id: 2, code: "EXTRACTING", label: "Extracting Claims", detail: "Decomposing content into discrete atomic assertions" },
  { id: 3, code: "SEARCHING", label: "Searching Evidence", detail: "Querying regulatory registries & authoritative archives" },
  { id: 4, code: "CHECKING", label: "Checking Sources", detail: "Triangulating source stances & credibility weights" },
  { id: 5, code: "THREATS", label: "Investigating Deception", detail: "Scanning deception signals & spoofed endpoints" },
  { id: 6, code: "SYNTHESIS", label: "Calculating Risk", detail: "Converging epistemic findings into final verdict" },
];

export const MOCK_INVESTIGATION_RESULT: InvestigationResult = {
  id: "inv-2026-9884",
  caseRef: "TL-CASE-9884-SBI",
  timestamp: "2026-10-10 03:35:12 UTC",
  inputMode: "text",
  rawInput: SAMPLE_INPUT_TEXT,
  extractedText: SAMPLE_INPUT_TEXT,
  truthStatus: "FALSE",
  truthAssessmentStatus: "ASSESSED",
  scamAssessmentStatus: "ASSESSED",
  developmentMode: true,
  contentExtractionMode: "GEMINI_LLM",
  evidenceRetrievalStatus: "SUCCESS",
  scamRiskScore: 91,
  riskLevel: "CRITICAL",
  headlineVerdict: "FALSE • HIGH RISK (91 / 100) — LIKELY SCAM [SIMULATED DEMO SCORE]",
  summaryExplanation: 
    "The reward claim is directly contradicted by primary banking regulatory advisories. The message combines an advance-payment demand, artificial coercive urgency, and a lookalike spoofed domain.",
  claims: [
    {
      id: "cl-1",
      claimNumber: 1,
      statement: "Recipient has won a ₹50,000 cash grant from an institutional lottery scheme.",
      truthStatus: "FALSE",
      truthAssessmentStatus: "ASSESSED",
      confidence: 0.98,
      category: "benefit_lure",
      explanation: "No matching lottery or cash distribution scheme exists in official State Bank of India gazettes or regulatory filings. Commercial banks are legally prohibited from executing unadvertised prize lotteries.",
      evidenceRefIds: ["ev-1", "ev-2"],
    },
    {
      id: "cl-2",
      claimNumber: 2,
      statement: "An upfront processing fee of ₹499 is required to disburse the prize money.",
      truthStatus: "CANNOT CONFIRM",
      truthAssessmentStatus: "ASSESSED",
      confidence: 0.92,
      category: "advance_fee",
      explanation: "The payment collection endpoint points to an ephemeral virtual account. TruthLens classifies the mechanism as an Advance Fee Fraud (419 pattern) trigger, with uncorroborated institutional escrow.",
      evidenceRefIds: ["ev-3"],
    },
    {
      id: "cl-3",
      claimNumber: 3,
      statement: "The reward expires within 2 hours if fee is not submitted.",
      truthStatus: "CANNOT CONFIRM",
      truthAssessmentStatus: "ASSESSED",
      confidence: 0.89,
      category: "urgency_coercion",
      explanation: "Artificial temporal constraint designed to prevent the recipient from verifying through official bank branches or customer support hotlines.",
      evidenceRefIds: ["ev-2"],
    },
  ],
  evidence: [
    {
      id: "ev-1",
      title: "Public Banking Advisory Bulletin on Prize Schemes [Demo Simulation]",
      publisher: "Public Banking Consumer Advisory [Demo Simulation]",
      url: "https://bank.example/advisories/lottery-schemes-warning",
      publishedDate: "2026-03-15",
      tier: "tier_1_official",
      tierLabel: "Primary Advisory [Demo Simulation]",
      stance: "CONTRADICTS",
      confidenceScore: 0.99,
      excerpt: "Regulated banks clarify that institutions never conduct online prize lotteries, reward pools, or request advance processing charges from customers under any campaign.",
      isSimulatedDemo: true,
    },
    {
      id: "ev-2",
      title: "Regulatory Warning on Advance-Fee Lottery Baits [Demo Simulation]",
      publisher: "Central Consumer Protection Authority [Demo Simulation]",
      url: "https://regulator.example/notifications/advance-fee-lures",
      publishedDate: "2026-01-22",
      tier: "tier_2_authoritative",
      tierLabel: "Regulatory Bulletin [Demo Simulation]",
      stance: "CONTRADICTS",
      confidenceScore: 0.96,
      excerpt: "Notices alleging unexpected cash prizes accompanied by nominal processing fees (e.g. ₹499–₹999) represent classic advance-fee financial lures. Regulated entities do not impose fee barriers on awards.",
      isSimulatedDemo: true,
    },
    {
      id: "ev-3",
      title: "Telephony Route & Endpoint Verification [Demo Simulation]",
      publisher: "National Anti-Spam Telephony Registry [Demo Simulation]",
      tier: "unverified",
      tierLabel: "Unable to Verify [Demo Simulation]",
      stance: "INSUFFICIENT",
      confidenceScore: 0.45,
      excerpt: "Originating telephony headers match an unregistered prepaid virtual route. Destination payment handle has no valid merchant corporate KYC record.",
      isSimulatedDemo: true,
    },
  ],
  scamSignals: [
    {
      id: "sig-1",
      name: "Advance Payment Request",
      category: "Financial Extraction",
      riskPoints: 25,
      description: "Demands upfront capital transfer (₹499) prior to releasing supposed larger funds.",
      evidence: "Matches standard 419 advance-fee extortion pattern.",
    },
    {
      id: "sig-2",
      name: "Suspicious Lookalike Domain",
      category: "Infrastructure Spoofing",
      riskPoints: 20,
      description: "Domain 'sbi-reward-claim.example' mimics authentic banking hostname.",
      evidence: "Unregistered TLD, newly provisioned host with zero bank linkage.",
    },
    {
      id: "sig-3",
      name: "Unsolicited Reward Bait",
      category: "Social Engineering",
      riskPoints: 15,
      description: "Promises high monetary windfall (₹50,000) with zero preceding user involvement.",
      evidence: "Lure calibrated to impair critical verification faculties.",
    },
    {
      id: "sig-4",
      name: "Brand Impersonation",
      category: "Identity Deception",
      riskPoints: 15,
      description: "Misappropriates State Bank of India brand recognition without authorization.",
      evidence: "Entity claims official banking capacity without valid origin signing.",
    },
    {
      id: "sig-5",
      name: "Artificial Urgency Deadline",
      category: "Behavioral Coercion",
      riskPoints: 16,
      description: "Enforces a strict 2-hour window to induce impulsive payment.",
      evidence: "Classic high-pressure mechanism to bypass bank verification.",
    },
  ],
  urlAnalysis: {
    analyzedUrl: "https://sbi-reward-claim.example",
    domain: "sbi-reward-claim.example",
    isTyposquat: true,
    impersonatedBrand: "State Bank of India (SBI)",
    registrationAge: "Less than 24 hours ago [Simulated Demo]",
    sslStatus: "anomalous",
    registrar: "Privacy Protect Proxy LLC [Simulated Demo]",
    riskIndicators: [
      "Brand name 'sbi' combined with generic high-risk keywords 'reward-claim'",
      "Domain age under 48 hours with privacy proxy masking ownership",
      "No cryptographic association with authentic banking ASN network",
      "Hosted on known shared offshore cloud infrastructure",
    ],
  },
  recommendations: {
    urgentActions: [
      "DO NOT TRANSFER ANY PAYMENT OR PROCESSING FEES.",
      "DO NOT ENTER OTP, PASSWORDS, OR CARD NUMBERS ON THE LINKED URL.",
      "BLOCK SENDER PHONE NUMBER / MESSAGE CHANNEL.",
      "REPORT THE DOMAIN TO OFFICIAL NATIONAL CYBERCRIME REPOSITORIES.",
    ],
    advisoryNote: 
      "If you have already submitted banking details or personal identifiers, immediately contact your bank to freeze impacted accounts and rotate online credentials.",
  },
  metrics: {
    claimsDetected: 3,
    sourcesCorroborated: 3,
    threatSignalsFound: 5,
    investigationDurationMs: 1420,
  },
};

export async function executeInvestigation(
  mode: InputMode, 
  rawText: string, 
  _file?: File | null
): Promise<InvestigationResult> {
  void _file;
  const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";
  const apiUrl = rawApiUrl.replace(/\/+$/, "");

  try {
    const res = await fetch(`${apiUrl}/api/investigate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input_type: mode,
        content: rawText || SAMPLE_INPUT_TEXT,
      }),
    });

    if (res.ok) {
      const data = await res.json();
      return {
        ...data,
        developmentMode: false,
      } as InvestigationResult;
    }
  } catch {
    // If backend is unreachable or offline, preserve seamless mock execution
  }

  // Fallback mock result with dynamic input metadata
  await new Promise((resolve) => setTimeout(resolve, 300));
  return {
    ...MOCK_INVESTIGATION_RESULT,
    inputMode: mode,
    rawInput: rawText || SAMPLE_INPUT_TEXT,
    timestamp: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
    developmentMode: true,
  };
}
