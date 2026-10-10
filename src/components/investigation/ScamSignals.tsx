"use client";

import * as React from "react";
import { ScamSignal, RiskLevel, ScamAssessmentStatus } from "@/types/investigation";


interface ScamSignalsProps {
  signals: ScamSignal[];
  riskScore?: number | null;
  riskLevel?: RiskLevel | null;
  status?: ScamAssessmentStatus;
  failureCategory?: string;
  isSimulatedDemo?: boolean;
}

export function ScamSignals({
  signals,
  riskScore,
  riskLevel,
  status = "ASSESSED",
  failureCategory,
  isSimulatedDemo,
}: ScamSignalsProps) {
  const isFailed = status === "FAILED";
  const isNotAssessed = status === "NOT_ASSESSED" || (riskScore === null && !isFailed);

  return (
    <div className="space-y-4 font-sans">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-3">
        <div>
          <span className="font-mono text-xs text-rose-400 uppercase tracking-wider block font-semibold">
            INVESTIGATE DECEPTION
          </span>
          <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
            Scam Investigation &amp; Deception Signals
          </h2>
        </div>
        <span className="font-mono text-xs text-rose-400">
          {signals.length} ACTIVE SIGNALS
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Signals List (8 cols) */}
        <div className="lg:col-span-8 space-y-3">
          {signals.length === 0 ? (
            <div className="rounded-lg border border-slate-800 bg-[#0E0C16] p-6 text-center text-xs text-[var(--muted-foreground)]">
              No active deception signals detected under current heuristic rules.
            </div>
          ) : (
            signals.map((signal) => (
              <div
                key={signal.id}
                className="rounded-lg border border-red-500/20 bg-[#0E0C16] p-4 flex items-start justify-between gap-4 transition-all hover:border-red-500/40"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-400 shrink-0" />
                    <h4 className="text-sm font-bold text-[var(--foreground)]">
                      {signal.name}
                    </h4>
                    <span className="text-[10px] font-mono text-[var(--muted-foreground)] px-1.5 py-0.2 rounded bg-black/40 border border-[rgba(255,255,255,0.08)]">
                      {signal.category}
                    </span>
                    {signal.provenance && (
                      <span className="text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.2 rounded bg-rose-950/40 text-rose-300 border border-rose-800/30">
                        {signal.provenance.replace(/_/g, " ")}
                      </span>
                    )}
                    {signal.isDirectlyObserved && (
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/30">
                        OBSERVED EXCERPT
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--muted-foreground)] leading-relaxed font-sans">
                    {signal.description}
                  </p>
                  <div className="text-[11px] font-mono text-rose-300/80 pt-0.5">
                    &bull; Trace: {signal.evidence}
                  </div>
                </div>

                <div className="font-mono text-sm font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-1 rounded shrink-0">
                  +{signal.riskPoints} pts
                </div>
              </div>
            ))
          )}
        </div>

        {/* Aggregated Risk Score Breakdown (4 cols) */}
        <div className={`lg:col-span-4 rounded-xl border p-5 sm:p-6 space-y-4 shadow-xl ${
          isFailed
            ? "border-amber-500/30 bg-[#15100B]"
            : isNotAssessed
              ? "border-slate-800 bg-[#0E0C16]"
              : "border-red-500/30 bg-[#120B15]"
        }`}>
          <span className="font-mono text-xs text-[var(--muted-foreground)] uppercase block">
            ACCUMULATED RISK SCORE
          </span>

          <div className="space-y-1">
            <div className="flex items-baseline gap-2 font-mono">
              <span className={`text-4xl sm:text-5xl font-black ${
                isFailed
                  ? "text-amber-400"
                  : isNotAssessed
                    ? "text-slate-400"
                    : "text-rose-400"
              }`}>
                {isFailed || isNotAssessed || riskScore === null || riskScore === undefined ? "--" : riskScore}
              </span>
              <span className="text-base text-[var(--muted-foreground)]">/ 100</span>
            </div>
            <span className={`inline-block text-xs font-mono font-bold px-2 py-0.5 rounded border ${
              isFailed
                ? "bg-amber-950/60 text-amber-300 border-amber-800/40"
                : isNotAssessed
                  ? "bg-slate-800/60 text-slate-300 border-slate-700/40"
                  : "bg-rose-950/60 text-rose-300 border-rose-800/40"
            }`}>
              {isFailed
                ? `ASSESSMENT FAILED${failureCategory ? ` (${failureCategory})` : ""}`
                : isNotAssessed
                  ? "NOT ASSESSED"
                  : `${riskLevel} SEVERITY${isSimulatedDemo ? " [SIMULATED]" : ""}`}
            </span>
          </div>

          <div className="h-2 w-full bg-[#1C1220] rounded-full overflow-hidden">
            <div
              className={`h-full ${
                isFailed
                  ? "bg-amber-500"
                  : isNotAssessed
                    ? "bg-slate-700"
                    : "bg-gradient-to-r from-amber-500 to-rose-500"
              }`}
              style={{ width: `${isFailed || isNotAssessed ? 0 : (riskScore ?? 0)}%` }}
            />
          </div>

          <div className="pt-2 border-t border-[rgba(255,255,255,0.07)] text-xs text-[var(--muted-foreground)] space-y-2">
            <p className="leading-relaxed">
              {isFailed
                ? "Scam risk fusion encountered a processing failure. No risk score or safety verdict was manufactured."
                : isNotAssessed
                  ? "Scam risk assessment was not performed for this case."
                  : isSimulatedDemo
                    ? "Calculated via additive behavioral risk weights [Simulated Demo]."
                    : "Calculated via deterministic behavioral threat rules. Heuristic risk index, not a percentage fraud probability."}
            </p>
            <div className="font-mono text-[11px] text-amber-300/90 font-medium">
              Note: Truth Status &ne; Scam Risk
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
