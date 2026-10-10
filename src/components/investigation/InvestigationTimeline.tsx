"use client";

import * as React from "react";
import { Check, AlertTriangle, Clock, HelpCircle } from "lucide-react";
import { InvestigationResult } from "@/types/investigation";

interface InvestigationTimelineProps {
  result: InvestigationResult;
}

export function InvestigationTimeline({ result }: InvestigationTimelineProps) {
  const liveSourcesCount = result.evidence.filter((e) => !e.isSimulatedDemo).length;
  const isRetrievalFailed = result.evidenceRetrievalStatus === "FAILED";
  const isRetrievalSkipped = result.evidenceRetrievalStatus === "SKIPPED";
  const isFallbackExtraction = result.contentExtractionMode === "DETERMINISTIC_FALLBACK";
  const isTruthNotAssessed = result.truthAssessmentStatus === "NOT_ASSESSED";
  const isTruthFailed = result.truthAssessmentStatus === "FAILED";
  const isScamFailed = result.scamAssessmentStatus === "FAILED";
  const isScamNotAssessed =
    result.scamAssessmentStatus === "NOT_ASSESSED" ||
    result.scamRiskScore === null ||
    result.scamRiskScore === undefined;

  // Step 1: Input Received
  const inputDetail = result.inputMode
    ? `${result.inputMode.toUpperCase()} (${(result.rawInput || "").length} chars)`
    : "Payload parsed";

  // Step 2: Claims Extracted
  const claimsDetail = isFallbackExtraction
    ? `${result.claims.length} assertions (Heuristic)`
    : `${result.claims.length} atomic assertion${result.claims.length === 1 ? "" : "s"}`;

  // Step 3: Evidence Analyzed
  let evidenceDetail: string;
  let evidenceState: "success" | "failed" | "neutral" = "success";
  if (isRetrievalSkipped) {
    const reason = result.contentAnalysisFailureCategory ? ` (${result.contentAnalysisFailureCategory})` : "";
    evidenceDetail = `Skipped${reason}`;
    evidenceState = "neutral";
  } else if (isRetrievalFailed) {
    evidenceDetail = `Retrieval failed (${result.evidenceFailureCategory || "UNAVAILABLE"})`;
    evidenceState = "failed";
  } else if (result.evidenceRetrievalStatus === "NO_EVIDENCE") {
    evidenceDetail = "0 sources found (None)";
    evidenceState = "neutral";
  } else {
    evidenceDetail = `${liveSourcesCount} live source${liveSourcesCount === 1 ? "" : "s"} matched`;
    evidenceState = liveSourcesCount > 0 ? "success" : "neutral";
  }

  // Step 4: Threat Signals
  const signalsDetail = `${result.scamSignals.length} deception indicator${result.scamSignals.length === 1 ? "" : "s"}`;

  // Step 5: Risk Calculated
  let riskDetail: string;
  let riskState: "success" | "failed" | "neutral" = "success";
  if (isScamFailed) {
    riskDetail = "Scam eval failed";
    riskState = "failed";
  } else if (isScamNotAssessed) {
    riskDetail = "Not assessed";
    riskState = "neutral";
  } else {
    riskDetail = `${result.scamRiskScore}/100 weighted`;
    riskState = "success";
  }

  // Step 6: Verdict Rendered
  let truthVerdictSummary: string;
  if (isTruthFailed) {
    truthVerdictSummary = "Truth failed";
  } else if (isTruthNotAssessed) {
    truthVerdictSummary = isRetrievalFailed ? "Truth pending" : "Truth not assessed";
  } else {
    truthVerdictSummary = result.truthStatus || "Truth pending";
  }

  let scamVerdictSummary: string;
  if (isScamFailed) {
    scamVerdictSummary = "Risk failed";
  } else if (isScamNotAssessed) {
    scamVerdictSummary = "Risk not assessed";
  } else {
    scamVerdictSummary = `${result.riskLevel || "Score"} (${result.scamRiskScore}/100)`;
  }

  const verdictDetail = `${truthVerdictSummary} • ${scamVerdictSummary}`;

  const steps = [
    {
      title: "Input Received",
      detail: inputDetail,
      state: "success" as const,
    },
    {
      title: "Claims Extracted",
      detail: claimsDetail,
      state: "success" as const,
    },
    {
      title: "Evidence Analyzed",
      detail: evidenceDetail,
      state: evidenceState,
    },
    {
      title: "Threat Signals",
      detail: signalsDetail,
      state: "success" as const,
    },
    {
      title: "Risk Calculated",
      detail: riskDetail,
      state: riskState,
    },
    {
      title: "Verdict Rendered",
      detail: verdictDetail,
      state: isTruthNotAssessed || isRetrievalFailed || isRetrievalSkipped ? ("pending" as const) : ("success" as const),
    },
  ];

  return (
    <div className="rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-5 sm:p-6 space-y-4 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] pb-3">
        <span className="text-[var(--primary)] font-semibold uppercase">
          FORENSIC PIPELINE TRACE
        </span>
        {isRetrievalSkipped ? (
          <span className="text-amber-400/90 font-semibold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            EVIDENCE RETRIEVAL SKIPPED
          </span>
        ) : isRetrievalFailed ? (
          <span className="text-amber-400 font-semibold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            EVIDENCE RETRIEVAL INCOMPLETE
          </span>
        ) : isTruthNotAssessed ? (
          <span className="text-slate-400 font-semibold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
            TRUTH ASSESSMENT PENDING
          </span>
        ) : (
          <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            ALL STAGES CORRELATED
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {steps.map((st, i) => (
          <div
            key={st.title}
            className={`p-3 rounded-lg border bg-[#080B14] space-y-1 relative ${
              st.state === "failed"
                ? "border-amber-500/30"
                : st.state === "pending"
                ? "border-slate-700/50"
                : "border-[rgba(255,255,255,0.06)]"
            }`}
          >
            <div className="flex items-center justify-between text-[10px] text-[var(--muted-foreground)]">
              <span>0{i + 1}</span>
              {st.state === "failed" ? (
                <AlertTriangle className="h-3 w-3 text-amber-400" />
              ) : st.state === "pending" ? (
                <Clock className="h-3 w-3 text-slate-400" />
              ) : st.state === "neutral" ? (
                <HelpCircle className="h-3 w-3 text-slate-400" />
              ) : (
                <Check className="h-3 w-3 text-emerald-400" />
              )}
            </div>
            <p className="font-bold text-[var(--foreground)] text-xs font-sans">
              {st.title}
            </p>
            <p
              className={`text-[11px] truncate ${
                st.state === "failed"
                  ? "text-amber-400/90 font-medium"
                  : "text-[var(--muted-foreground)]"
              }`}
              title={st.detail}
            >
              {st.detail}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
