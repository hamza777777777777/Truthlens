"use client";

import * as React from "react";
import { AlertOctagon } from "lucide-react";

interface RecommendationProps {
  urgentActions: string[];
  advisoryNote: string;
}

export function Recommendation({
  urgentActions,
  advisoryNote,
}: RecommendationProps) {
  return (
    <div className="rounded-xl border border-rose-500/30 bg-[#120B15] p-6 sm:p-7 space-y-5 font-sans shadow-xl">
      <div className="flex items-center gap-3 border-b border-[rgba(255,255,255,0.08)] pb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-rose-500/40 bg-rose-500/10 text-rose-400 shrink-0">
          <AlertOctagon className="h-5 w-5" />
        </div>
        <div>
          <span className="font-mono text-xs uppercase tracking-wider text-rose-400 font-bold block">
            CRITICAL ADVISORY
          </span>
          <h3 className="text-xl font-bold text-[var(--foreground)]">
            Actionable User Recommendations
          </h3>
        </div>
      </div>

      <div className="space-y-3 font-mono text-xs">
        <span className="text-[11px] uppercase tracking-wider text-[var(--muted-foreground)] block">
          IMMEDIATE DEFENSIVE ACTIONS:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {urgentActions.map((action, i) => (
            <div
              key={i}
              className="p-3 rounded-lg border border-red-500/20 bg-red-500/5 flex items-start gap-2.5 text-rose-200"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-rose-400 shrink-0 mt-1.5" />
              <span className="font-semibold leading-relaxed">{action}</span>
            </div>
          ))}
        </div>
      </div>

      {advisoryNote && (
        <div className="pt-3 border-t border-[rgba(255,255,255,0.06)] text-xs text-[var(--muted-foreground)] leading-relaxed font-sans">
          <strong className="text-[var(--foreground)] font-mono block mb-1">SECONDARY CONTINGENCY:</strong>
          {advisoryNote}
        </div>
      )}
    </div>
  );
}
