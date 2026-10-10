"use client";

import * as React from "react";
import { Plus, Clock, FileText, Globe, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InvestigationResult } from "@/types/investigation";

interface InvestigationHeaderProps {
  result: InvestigationResult;
  onNewInvestigation: () => void;
}

export function InvestigationHeader({
  result,
  onNewInvestigation,
}: InvestigationHeaderProps) {
  const getModeIcon = () => {
    switch (result.inputMode) {
      case "image":
        return <ImageIcon className="h-3.5 w-3.5" />;
      case "url":
        return <Globe className="h-3.5 w-3.5" />;
      default:
        return <FileText className="h-3.5 w-3.5" />;
    }
  };

  return (
    <div className="w-full flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] pb-5">
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-[var(--primary)] font-bold tracking-wider">
            {result.caseRef}
          </span>
          <span className="text-[rgba(255,255,255,0.2)]">/</span>
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-xs bg-[var(--surface-elevated)] text-[var(--muted-foreground)] border border-[rgba(255,255,255,0.08)]">
            {getModeIcon()}
            <span className="uppercase">{result.inputMode} INPUT</span>
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black uppercase tracking-tight text-[var(--foreground)]">
          Forensic Investigation Dossier
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-[var(--muted-foreground)] pt-1">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span>Executed: {result.timestamp}</span>
          </div>
          <span>&bull;</span>
          {result.evidence.some((e) => !e.isSimulatedDemo) ? (
            <span className="text-[11px] font-semibold text-emerald-300/90 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
              VERIFIED SOURCES &middot; LIVE GROUNDING
            </span>
          ) : result.evidenceRetrievalStatus === "SKIPPED" ? (
            <span className="text-[11px] font-semibold text-zinc-300/90 bg-zinc-500/10 border border-zinc-500/30 px-2 py-0.5 rounded">
              EVIDENCE RETRIEVAL &middot; SKIPPED
            </span>
          ) : result.evidenceRetrievalStatus === "FAILED" ? (
            <span className="text-[11px] font-semibold text-rose-300/90 bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 rounded">
              EVIDENCE RETRIEVAL &middot; UNAVAILABLE
            </span>
          ) : result.evidenceRetrievalStatus === "NO_EVIDENCE" ? (
            <span className="text-[11px] font-semibold text-amber-300/90 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
              EVIDENCE RETRIEVAL &middot; NO SOURCES FOUND
            </span>
          ) : (
            <span className="text-[11px] font-semibold text-amber-300/90 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
              DEMO INVESTIGATION &middot; SIMULATED EVIDENCE
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 self-stretch sm:self-auto">
        <Button
          variant="outline"
          size="sm"
          onClick={onNewInvestigation}
          className="gap-2 font-mono text-xs w-full sm:w-auto"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>NEW INVESTIGATION</span>
        </Button>
      </div>
    </div>
  );
}
