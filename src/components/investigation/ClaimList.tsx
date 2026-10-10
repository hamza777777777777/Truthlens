"use client";

import * as React from "react";
import { Claim, EvidenceSource } from "@/types/investigation";
import { ClaimCard } from "./ClaimCard";

interface ClaimListProps {
  claims: Claim[];
  evidenceList: EvidenceSource[];
}

export function ClaimList({ claims, evidenceList }: ClaimListProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-3">
        <div>
          <span className="font-mono text-xs text-[var(--primary)] uppercase tracking-wider block">
            CLAIM-LEVEL DECOMPOSITION
          </span>
          <h2 className="text-xl font-bold tracking-tight text-[var(--foreground)]">
            Atomic Claims Under Review
          </h2>
        </div>
        <span className="font-mono text-xs text-[var(--muted-foreground)]">
          {claims.length} DETECTED
        </span>
      </div>

      <div className="space-y-3">
        {claims.map((claim, idx) => (
          <ClaimCard
            key={claim.id}
            claim={claim}
            evidenceList={evidenceList}
            isExpandedDefault={idx === 0}
          />
        ))}
      </div>
    </div>
  );
}
