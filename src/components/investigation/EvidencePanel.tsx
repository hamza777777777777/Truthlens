"use client";

import * as React from "react";
import { EvidenceSource as EvidenceSourceType } from "@/types/investigation";
import { EvidenceSourceCard } from "./EvidenceSource";

interface EvidencePanelProps {
  evidenceList: EvidenceSourceType[];
}

export function EvidencePanel({ evidenceList }: EvidencePanelProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-3">
        <div>
          <span className="font-mono text-xs text-[var(--primary)] uppercase tracking-wider block">
            CHECK THE EVIDENCE
          </span>
          <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
            Evidence Sources &amp; Citations
          </h2>
        </div>
        <span className={`font-mono text-xs ${
          evidenceList.some((e) => e.id === "ev-retrieval-failed" || e.id === "ev-retrieval-skipped")
            ? "text-amber-400 font-semibold"
            : "text-[var(--muted-foreground)]"
        }`}>
          {evidenceList.some((e) => e.id === "ev-retrieval-skipped")
            ? "RETRIEVAL SKIPPED • 0 LIVE SOURCES"
            : evidenceList.some((e) => e.id === "ev-retrieval-failed")
            ? "RETRIEVAL FAILED • 0 LIVE SOURCES"
            : evidenceList.some((e) => e.id === "ev-no-sources")
            ? "0 SOURCES FOUND"
            : `${evidenceList.filter((e) => !e.isSimulatedDemo).length} SOURCES CITED`}
        </span>
      </div>

      <div className="space-y-3">
        {evidenceList.map((source) => (
          <EvidenceSourceCard key={source.id} source={source} />
        ))}
      </div>
    </div>
  );
}
