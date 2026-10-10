"use client";

import * as React from "react";
import { InvestigationResult, InputMode } from "@/types/investigation";
import { executeInvestigation } from "@/lib/investigation-service";
import { InvestigationInput } from "@/components/investigation/InvestigationInput";
import { InvestigationProgress } from "@/components/investigation/InvestigationProgress";
import { InvestigationHeader } from "@/components/investigation/InvestigationHeader";
import { VerdictSummary } from "@/components/investigation/VerdictSummary";
import { ClaimList } from "@/components/investigation/ClaimList";
import { EvidencePanel } from "@/components/investigation/EvidencePanel";
import { ScamSignals } from "@/components/investigation/ScamSignals";
import { UrlAnalysis } from "@/components/investigation/UrlAnalysis";
import { InvestigationTimeline } from "@/components/investigation/InvestigationTimeline";
import { Recommendation } from "@/components/investigation/Recommendation";
import Link from "next/link";
import { ArrowLeft, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function InvestigatePage() {
  const [viewState, setViewState] = React.useState<"idle" | "analyzing" | "result">("idle");
  const [result, setResult] = React.useState<InvestigationResult | null>(null);

  const handleStart = async ({
    mode,
    text,
    file,
  }: {
    mode: InputMode;
    text: string;
    file?: File | null;
  }) => {
    setViewState("analyzing");
    const investigationData = await executeInvestigation(mode, text, file);
    setResult(investigationData);
  };

  const handleProgressComplete = () => {
    setViewState("result");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleReset = () => {
    setViewState("idle");
    setResult(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#080B12] text-[var(--foreground)] pt-24 pb-24 px-4 sm:px-6 lg:px-8 selection:bg-[var(--primary)]/20 selection:text-[var(--foreground)] font-sans">
      {/* Background ambient forensic wash */}
      <div
        className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_60%_30%_at_50%_0%,rgba(87,214,255,0.06),transparent_70%)]"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl">
        {/* Navigation Breadcrumb */}
        <div className="mb-8 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-mono text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>RETURN TO OVERVIEW</span>
          </Link>

          <span className="font-mono text-xs text-[var(--muted-foreground)]">
            TRUTHLENS WORKSPACE v1.0
          </span>
        </div>

        {/* STATE 1: IDLE / INTAKE FORM */}
        {viewState === "idle" && (
          <div className="space-y-12 animate-in fade-in duration-300">
            <InvestigationInput onStartInvestigation={handleStart} />

            {/* Quick Helper Cards */}
            <div className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs text-[var(--muted-foreground)]">
              <div className="p-4 rounded-lg border border-[rgba(255,255,255,0.06)] bg-[#0C111D] space-y-1">
                <span className="text-[var(--foreground)] font-semibold block">1. Separate the claims</span>
                <p className="text-[11px] font-sans">Messages are broken down into individual assertions.</p>
              </div>
              <div className="p-4 rounded-lg border border-[rgba(255,255,255,0.06)] bg-[#0C111D] space-y-1">
                <span className="text-[var(--foreground)] font-semibold block">2. Check the evidence</span>
                <p className="text-[11px] font-sans">Cross-referenced against public advisories and verifiable sources.</p>
              </div>
              <div className="p-4 rounded-lg border border-[rgba(255,255,255,0.06)] bg-[#0C111D] space-y-1">
                <span className="text-[var(--foreground)] font-semibold block">3. Investigate deception</span>
                <p className="text-[11px] font-sans">Checks for upfront fee demands, artificial urgency, and impersonation.</p>
              </div>
            </div>
          </div>
        )}

        {/* STATE 2: ACTIVE FORENSIC PIPELINE EXECUTION */}
        {viewState === "analyzing" && (
          <div className="py-12 animate-in fade-in zoom-in-95 duration-300">
            <InvestigationProgress onComplete={handleProgressComplete} />
          </div>
        )}

        {/* STATE 3: FULL INVESTIGATION RESULT DOSSIER */}
        {viewState === "result" && result && (
          <div className="space-y-10 animate-in fade-in duration-400">
            {/* Header with Case Metadata */}
            <InvestigationHeader
              result={result}
              onNewInvestigation={handleReset}
            />

            {/* Pipeline Step Trace */}
            <InvestigationTimeline result={result} />

            {/* Top Dual Verdict & Case Metrics */}
            <VerdictSummary result={result} />

            {/* Claim-Level Deconstruction */}
            <ClaimList
              claims={result.claims}
              evidenceList={result.evidence}
            />

            {/* Domain & URL Analysis */}
            {result.urlAnalysis && (
              <UrlAnalysis data={result.urlAnalysis} />
            )}

            {/* Behavioral Scam Signals & Risk Points */}
            <ScamSignals
              signals={result.scamSignals}
              riskScore={result.scamRiskScore}
              riskLevel={result.riskLevel}
              status={result.scamAssessmentStatus}
              failureCategory={result.scamAssessmentFailureCategory}
              isSimulatedDemo={result.developmentMode}
            />

            {/* Evidence Repository Sources */}
            <EvidencePanel evidenceList={result.evidence} />

            {/* Actionable User Recommendations */}
            <Recommendation
              urgentActions={result.recommendations.urgentActions}
              advisoryNote={result.recommendations.advisoryNote}
            />

            {/* Bottom Actions Bar */}
            <div className="pt-8 border-t border-[rgba(255,255,255,0.08)] flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-[var(--muted-foreground)]">
              <span>TRUTHLENS CASE {result.caseRef} • AUDIT STATUS VERIFIED</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleReset}
                className="gap-2"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>INVESTIGATE ANOTHER MESSAGE</span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
