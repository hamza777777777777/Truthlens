"use client";

import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { InvestigationResult, TruthStatus } from "@/types/investigation";


interface VerdictSummaryProps {
  result: InvestigationResult;
}

export function VerdictSummary({ result }: VerdictSummaryProps) {
  const isAssessmentFailed = result.truthAssessmentStatus === "FAILED";
  const isNotAssessed = result.truthAssessmentStatus === "NOT_ASSESSED" || (!result.truthStatus && !isAssessmentFailed);
  const isRetrievalFailed = result.evidenceRetrievalStatus === "FAILED";
  const isRetrievalSkipped = result.evidenceRetrievalStatus === "SKIPPED";

  const getTruthBadgeVariant = (status?: TruthStatus | null) => {
    if (!status) return "outline";
    switch (status) {
      case "VERIFIED":
        return "verified";
      case "FALSE":
        return "falseClaim";
      case "PARTIALLY SUPPORTED":
        return "partial";
      case "OUTDATED":
        return "outdated";
      case "CANNOT CONFIRM":
      default:
        return "cannotConfirm";
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch font-sans">
      {/* Left / Main: Dual Verdict Summary (8 cols) */}
      <div className="lg:col-span-8 rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] p-6 sm:p-7 space-y-6 flex flex-col justify-between shadow-xl">
        <div className="space-y-4">
          <div className="flex items-center justify-between font-mono text-xs text-[var(--muted-foreground)]">
            <span className="text-[var(--primary)] font-semibold uppercase">EXECUTIVE VERDICT SYNTHESIS</span>
            <span>CORE FINDINGS</span>
          </div>

          {/* Dual Verdict Readouts: Truth Status vs Scam Risk */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Metric 1: Epistemic Truth Status */}
            <div className={`rounded-lg border p-5 space-y-2 ${
              isAssessmentFailed
                ? "border-amber-500/40 bg-[#080B14]"
                : isNotAssessed
                  ? (isRetrievalFailed || isRetrievalSkipped)
                    ? "border-amber-500/30 bg-[#080B14]"
                    : "border-slate-700/40 bg-[#080B14]"
                  : result.truthStatus === "CANNOT CONFIRM"
                    ? "border-[var(--cannot-confirm)]/30 bg-[#080B14]"
                    : result.truthStatus === "VERIFIED"
                      ? "border-[var(--verified)]/30 bg-[#080B14]"
                      : "border-[var(--false)]/30 bg-[#080B14]"
            }`}>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                  EPISTEMIC TRUTH STATUS
                </span>
                <Badge
                  variant={isAssessmentFailed || isNotAssessed ? "outline" : getTruthBadgeVariant(result.truthStatus)}
                  className={`font-mono text-xs ${
                    isAssessmentFailed
                      ? "text-amber-400 border-amber-500/40 bg-amber-500/10"
                      : isNotAssessed
                        ? (isRetrievalFailed || isRetrievalSkipped)
                          ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
                          : "text-slate-400 border-slate-700/50 bg-slate-800/30"
                        : ""
                  }`}
                >
                  {isAssessmentFailed
                    ? `ASSESSMENT FAILED${result.truthAssessmentFailureCategory ? ` (${result.truthAssessmentFailureCategory})` : ""}`
                    : isNotAssessed
                      ? isRetrievalSkipped
                        ? "RETRIEVAL SKIPPED"
                        : isRetrievalFailed
                        ? "RETRIEVAL FAILED"
                        : "NOT ASSESSED"
                      : (result.truthStatus ?? "NOT ASSESSED")}
                </Badge>
              </div>
              <div className={`text-2xl sm:text-3xl font-black ${
                isAssessmentFailed
                  ? "text-amber-400"
                  : isNotAssessed
                    ? (isRetrievalFailed || isRetrievalSkipped)
                      ? "text-amber-400"
                      : "text-slate-300"
                    : result.truthStatus === "CANNOT CONFIRM"
                      ? "text-[var(--cannot-confirm)]"
                      : result.truthStatus === "VERIFIED"
                        ? "text-[var(--verified)]"
                        : "text-[var(--false)]"
              }`}>
                {isAssessmentFailed
                  ? "ASSESSMENT FAILED"
                  : isNotAssessed
                    ? (isRetrievalFailed || isRetrievalSkipped)
                      ? "ASSESSMENT PENDING"
                      : "NOT ASSESSED"
                    : (result.truthStatus ?? "NOT ASSESSED")}
              </div>
              <p className="text-xs text-[var(--muted-foreground)] font-sans leading-relaxed">
                {isAssessmentFailed
                  ? `External evidence retrieved, but Truth Engine encountered an assessment failure (${result.truthAssessmentFailureCategory || "PROVIDER_ERROR"}). No verdict has been fabricated.`
                  : isNotAssessed
                    ? isRetrievalSkipped
                      ? `External evidence retrieval was not attempted due to upstream processing limits (${result.contentAnalysisFailureCategory || "RATE_LIMIT"}). The Truth Engine has not evaluated these claims.`
                      : isRetrievalFailed
                      ? "External evidence retrieval failed before truth assessment. The Truth Engine has not evaluated these claims."
                      : "Atomic claims isolated and grounded; deterministic truth assessment executes in subsequent phase."
                    : result.truthStatus === "CANNOT CONFIRM"
                      ? "Assessment performed; available external evidence is insufficient to confirm or refute."
                      : result.truthStatus === "VERIFIED"
                        ? "Primary assertions corroborated by official authoritative sources."
                        : "Primary assertions directly refuted by regulatory advisories and authentic bank bulletins."}
              </p>
            </div>

            {/* Metric 2: Scam Risk Threat Index */}
            {result.scamAssessmentStatus === "FAILED" ? (
              <div className="rounded-lg border border-amber-500/30 bg-[#080B14] p-5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                    DECEPTIVE SCAM RISK
                  </span>
                  <span className="text-xs font-mono font-bold text-amber-400">
                    ASSESSMENT FAILED
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5 font-mono">
                  <span className="text-3xl font-black text-amber-400">--</span>
                  <span className="text-sm text-[var(--muted-foreground)]">/ 100</span>
                </div>
                <div className="h-1.5 w-full bg-[#18101E] rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500/50" style={{ width: "0%" }} />
                </div>
                <p className="text-[11px] text-[var(--muted-foreground)] font-sans">
                  {result.scamAssessmentFailureCategory
                    ? `Scam risk evaluation failed (${result.scamAssessmentFailureCategory}). No score fabricated.`
                    : "Scam risk evaluation failed. No score fabricated."}
                </p>
              </div>
            ) : result.scamRiskScore !== null && result.scamRiskScore !== undefined ? (
              <div className="rounded-lg border border-red-500/30 bg-[#080B14] p-5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                    DECEPTIVE SCAM RISK
                  </span>
                  <span className="text-xs font-mono font-bold text-rose-400">
                    {result.riskLevel} {result.developmentMode ? "[SIMULATED]" : ""}
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5 font-mono">
                  <span className="text-3xl font-black text-rose-400">
                    {result.scamRiskScore}
                  </span>
                  <span className="text-sm text-[var(--muted-foreground)]">/ 100</span>
                </div>
                {/* Progress gauge */}
                <div className="h-1.5 w-full bg-[#18101E] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-rose-500"
                    style={{ width: `${result.scamRiskScore}%` }}
                  />
                </div>
                <p className="text-[11px] text-[var(--muted-foreground)] font-sans">
                  {result.developmentMode ? "Demo baseline score [Simulated Data]." : "Accumulated behavioral deception threat index."}
                </p>
              </div>
            ) : (
              <div className="rounded-lg border border-slate-700/40 bg-[#080B14] p-5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                    DECEPTIVE SCAM RISK
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-400">
                    NOT ASSESSED
                  </span>
                </div>
                <div className="flex items-baseline gap-1.5 font-mono">
                  <span className="text-3xl font-black text-slate-400">
                    --
                  </span>
                  <span className="text-sm text-[var(--muted-foreground)]">/ 100</span>
                </div>
                {/* Empty progress gauge */}
                <div className="h-1.5 w-full bg-[#18101E] rounded-full overflow-hidden">
                  <div className="h-full bg-slate-700" style={{ width: "0%" }} />
                </div>
                <p className="text-[11px] text-[var(--muted-foreground)] font-sans">
                  Scam risk assessment was not performed for this case.
                </p>
              </div>
            )}
          </div>

          {/* Explanation */}
          <div className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#070A12] p-4.5 space-y-1.5">
            <span className="font-mono text-xs text-[var(--primary)] font-semibold block">
              FORENSIC SUMMARY:
            </span>
            <p className="text-sm text-[var(--foreground)] leading-relaxed">
              {result.summaryExplanation}
            </p>
          </div>
        </div>

        {/* Fundamental Principle Distinction Alert */}
        <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] flex items-center justify-between text-xs font-mono text-[var(--muted-foreground)]">
          <span className="text-amber-300/90 font-semibold">PRINCIPLE:</span>
          <span>Truth Status (Epistemic Fact) &ne; Scam Risk (Behavioral Threat)</span>
        </div>
      </div>

      {/* Right / Sidebar: Case Information Rail (4 cols) */}
      <div className="lg:col-span-4 rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] p-6 space-y-5 shadow-xl flex flex-col justify-between">
        <div className="space-y-4">
          <div className="font-mono text-xs text-[var(--muted-foreground)] border-b border-[rgba(255,255,255,0.07)] pb-2 flex items-center justify-between">
            <span className="text-[var(--primary)] font-semibold">CASE METADATA</span>
            <span>AUDIT TRAIL</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Input Channel:</span>
              <span className="text-[var(--foreground)] font-semibold uppercase">{result.inputMode}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Extraction Mode:</span>
              <span className={`font-semibold ${result.contentExtractionMode === "DETERMINISTIC_FALLBACK" ? "text-amber-400" : "text-[var(--foreground)]"}`}>
                {result.contentExtractionMode === "DETERMINISTIC_FALLBACK" ? "Heuristic Fallback" : "Gemini 2.5 Flash"}
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Claims Detected:</span>
              <span className="text-[var(--foreground)] font-semibold">{result.metrics.claimsDetected} Atomic</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Sources Analyzed:</span>
              <span className="text-[var(--foreground)] font-semibold">{result.metrics.sourcesCorroborated} Registries</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Threat Signals:</span>
              <span className="text-rose-400 font-semibold">{result.metrics.threatSignalsFound} Active</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.05)]">
              <span className="text-[var(--muted-foreground)]">Execution Time:</span>
              <span className="text-[var(--foreground)] font-semibold">
                {result.metrics.investigationDurationMs >= 1000
                  ? `${(result.metrics.investigationDurationMs / 1000).toFixed(1)} s`
                  : `${result.metrics.investigationDurationMs} ms`}
              </span>
            </div>
          </div>
        </div>

        {/* Raw payload snippet */}
        <div className="rounded border border-[rgba(255,255,255,0.06)] bg-[#070A12] p-3 space-y-1 font-mono text-xs">
          <span className="text-[10px] text-[var(--muted-foreground)] uppercase">INGESTED PAYLOAD</span>
          <p className="text-[11px] text-[var(--muted-foreground)] line-clamp-3">
            &ldquo;{result.rawInput}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}
