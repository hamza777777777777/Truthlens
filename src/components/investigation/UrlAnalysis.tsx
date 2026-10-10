"use client";

import * as React from "react";
import { UrlInvestigationData } from "@/types/investigation";


interface UrlAnalysisProps {
  data?: UrlInvestigationData;
}

export function UrlAnalysis({ data }: UrlAnalysisProps) {
  if (!data) return null;

  return (
    <div className="space-y-4 font-sans">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-3">
        <div>
          <span className="font-mono text-xs text-[var(--primary)] uppercase tracking-wider block">
            INFRASTRUCTURE INSPECTION
          </span>
          <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
            URL &amp; Domain Intelligence
          </h2>
        </div>
        <span className="font-mono text-xs text-amber-300 font-semibold px-2 py-0.5 rounded border border-amber-500/30 bg-amber-500/10">
          DEMO ANALYSIS &middot; SIMULATED INFRASTRUCTURE
        </span>
      </div>

      <div className="rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-5 sm:p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[rgba(255,255,255,0.06)] pb-4">
          <div className="space-y-1">
            <span className="font-mono text-xs text-[var(--muted-foreground)]">TARGET HOSTNAME</span>
            <div className="font-mono text-base sm:text-lg font-bold text-[var(--primary)] break-all">
              {data.domain}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {data.isTyposquat && (
              <span className="font-mono text-xs font-bold px-2.5 py-1 rounded border border-rose-500/30 bg-rose-500/10 text-rose-300">
                TYPOSQUAT / LOOKALIKE DETECTED
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
          <div className="p-3 rounded border border-[rgba(255,255,255,0.06)] bg-[#080B14] space-y-1">
            <span className="text-[10px] text-[var(--muted-foreground)]">IMPERSONATED BRAND</span>
            <p className="text-[var(--foreground)] font-semibold font-sans">{data.impersonatedBrand || "None"}</p>
          </div>
          <div className="p-3 rounded border border-[rgba(255,255,255,0.06)] bg-[#080B14] space-y-1">
            <span className="text-[10px] text-[var(--muted-foreground)]">DOMAIN REGISTRATION AGE</span>
            <p className="text-rose-400 font-semibold">{data.registrationAge}</p>
          </div>
          <div className="p-3 rounded border border-[rgba(255,255,255,0.06)] bg-[#080B14] space-y-1">
            <span className="text-[10px] text-[var(--muted-foreground)]">SSL / TLS ANOMALY</span>
            <p className="text-amber-300 font-semibold uppercase">{data.sslStatus}</p>
          </div>
        </div>

        {/* Risk Indicators List */}
        <div className="space-y-2 pt-2">
          <span className="font-mono text-[11px] text-[var(--muted-foreground)] uppercase">
            DETECTED INFRASTRUCTURAL ANOMALIES
          </span>
          <div className="space-y-1.5 font-mono text-xs text-rose-300">
            {data.riskIndicators.map((ind, i) => (
              <div key={i} className="flex items-center gap-2 p-2 rounded bg-red-500/5 border border-red-500/15">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400 shrink-0" />
                <span>{ind}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
