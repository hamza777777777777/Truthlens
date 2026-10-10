"use client";

import * as React from "react";
import { CheckCircle2, AlertTriangle, HelpCircle } from "lucide-react";
import { EvidenceSource as EvidenceSourceType } from "@/types/investigation";

interface EvidenceSourceProps {
  source: EvidenceSourceType;
}

export function EvidenceSourceCard({ source }: EvidenceSourceProps) {
  const getStanceIcon = () => {
    switch (source.stance) {
      case "CONTRADICTS":
        return <AlertTriangle className="h-4 w-4 text-[var(--false)]" />;
      case "CORROBORATES":
        return <CheckCircle2 className="h-4 w-4 text-[var(--verified)]" />;
      case "INSUFFICIENT":
      default:
        return <HelpCircle className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStanceBadge = () => {
    switch (source.stance) {
      case "CONTRADICTS":
        return "text-[var(--false)] bg-[var(--false)]/10 border-[var(--false)]/30";
      case "CORROBORATES":
        return "text-[var(--verified)] bg-[var(--verified)]/10 border-[var(--verified)]/30";
      case "INSUFFICIENT":
      default:
        return "text-slate-400 bg-slate-800/40 border-slate-700/40";
    }
  };

  return (
    <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-4 sm:p-5 space-y-3 font-sans">
      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-[rgba(255,255,255,0.06)] pb-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="text-[var(--primary)] font-semibold">{source.publisher}</span>
            <span className="text-[rgba(255,255,255,0.2)]">•</span>
            <span className="text-[var(--muted-foreground)]">{source.tierLabel}</span>
          </div>
          <h4 className="text-sm font-bold text-[var(--foreground)]">
            {source.title}
          </h4>
        </div>

        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[11px] font-mono font-semibold ${getStanceBadge()}`}>
            {getStanceIcon()}
            <span>{source.stance}</span>
          </span>
        </div>
      </div>

      <div className="space-y-1.5">
        <span className="font-mono text-[10px] uppercase text-[var(--muted-foreground)] block">
          RELEVANT CORROBORATING EXCERPT:
        </span>
        <blockquote className="border-l-2 border-[var(--primary)]/50 pl-3 py-0.5 text-xs text-[var(--muted-foreground)] italic font-sans leading-relaxed bg-[#080B14]/50 rounded-r">
          &ldquo;{source.excerpt}&rdquo;
        </blockquote>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[rgba(255,255,255,0.05)] text-[11px] font-mono text-[var(--muted-foreground)]">
        <div className="flex items-center gap-2">
          {source.publishedDate && <span>Date: {source.publishedDate}</span>}
          <span>•</span>
          <span>Relevance Match: {Math.round(source.confidenceScore * 100)}%</span>
        </div>

        {source.isSimulatedDemo && (
          <span className="text-[10px] font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
            DEMO EVIDENCE &middot; SIMULATED DATA
          </span>
        )}
      </div>
    </div>
  );
}
