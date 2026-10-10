"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Claim, EvidenceSource } from "@/types/investigation";

interface ClaimCardProps {
  claim: Claim;
  evidenceList: EvidenceSource[];
  isExpandedDefault?: boolean;
}

export function ClaimCard({
  claim,
  evidenceList,
  isExpandedDefault = false,
}: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(isExpandedDefault);

  const getStatusBadgeVariant = (status?: string | null, assessmentStatus?: string) => {
    if (assessmentStatus === "FAILED" || assessmentStatus === "NOT_ASSESSED" || !status) {
      return "outline";
    }
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

  const supportingEvidence = evidenceList.filter((e) =>
    (claim.supportingEvidenceRefIds || []).includes(e.id)
  );
  const contradictingEvidence = evidenceList.filter((e) =>
    (claim.contradictingEvidenceRefIds || []).includes(e.id)
  );
  const otherRelatedEvidence = evidenceList.filter((e) =>
    claim.evidenceRefIds.includes(e.id) &&
    !(claim.supportingEvidenceRefIds || []).includes(e.id) &&
    !(claim.contradictingEvidenceRefIds || []).includes(e.id)
  );

  return (
    <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#0C111D] overflow-hidden transition-all font-sans">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 sm:p-5 text-left flex items-start sm:items-center justify-between gap-4 hover:bg-[var(--surface)] transition-colors"
      >
        <div className="flex items-start sm:items-center gap-3.5 min-w-0">
          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[#080B14] border border-[rgba(255,255,255,0.08)] text-[var(--muted-foreground)] shrink-0">
            CLAIM #{claim.claimNumber}
          </span>
          <p className="text-sm sm:text-base font-medium text-[var(--foreground)] truncate sm:whitespace-normal">
            &ldquo;{claim.statement}&rdquo;
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          {claim.truthAssessmentStatus === "ASSESSED" && claim.confidence !== undefined && (
            <span className="font-mono text-[11px] text-slate-400 hidden sm:inline-block">
              Confidence: {Math.round(claim.confidence * 100)}%
            </span>
          )}
          <Badge
            variant={getStatusBadgeVariant(claim.truthStatus, claim.truthAssessmentStatus)}
            className={`font-mono text-xs ${
              claim.truthAssessmentStatus === "FAILED"
                ? "text-amber-400 border-amber-500/40 bg-amber-500/10"
                : claim.truthAssessmentStatus === "NOT_ASSESSED"
                ? "text-slate-400 border-slate-700/50 bg-slate-800/30"
                : ""
            }`}
          >
            {claim.truthAssessmentStatus === "FAILED"
              ? "ASSESSMENT FAILED"
              : claim.truthAssessmentStatus === "NOT_ASSESSED"
              ? "NOT ASSESSED"
              : (claim.truthStatus ?? "NOT ASSESSED")}
          </Badge>
          <ChevronDown
            className={`h-4 w-4 text-[var(--muted-foreground)] transition-transform duration-200 ${
              isExpanded ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {isExpanded && (
        <div className="px-5 pb-5 pt-2 border-t border-[rgba(255,255,255,0.07)] space-y-4 text-xs bg-[#080B14]/60">
          {/* Explanation rationale */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-[var(--primary)] uppercase font-semibold">
                EPISTEMIC RATIONALE:
              </span>
              {claim.truthAssessmentStatus === "ASSESSED" && (
                <span className="font-mono text-[10px] text-slate-400 italic">
                  Confidence: {Math.round(claim.confidence * 100)}% (Heuristic Agreement Score &bull; Uncalibrated)
                </span>
              )}
            </div>
            <p className="text-sm text-[var(--muted-foreground)] leading-relaxed font-sans">
              {claim.explanation}
            </p>
          </div>

          {/* Limitations and caveats if present */}
          {claim.limitations && (
            <div className="space-y-1.5 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              <span className="font-mono text-[11px] text-amber-400 uppercase font-semibold">
                LIMITATIONS & CAVEATS:
              </span>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed font-sans">
                {claim.limitations}
              </p>
            </div>
          )}

          {/* Supporting Evidence Excerpts */}
          {supportingEvidence.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              <span className="font-mono text-[11px] text-[var(--verified)] uppercase font-semibold flex items-center gap-1.5">
                <span>SUPPORTING EVIDENCE ({supportingEvidence.length})</span>
              </span>
              <div className="space-y-2">
                {supportingEvidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 rounded border border-emerald-500/20 bg-[#0C111D] space-y-1"
                  >
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-[var(--foreground)] font-semibold">{ev.publisher}</span>
                      <span className="text-[var(--verified)] font-bold">{ev.tierLabel}</span>
                    </div>
                    <p className="text-xs text-[var(--muted-foreground)] italic font-sans">
                      &ldquo;{ev.excerpt}&rdquo;
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contradicting Evidence Excerpts */}
          {contradictingEvidence.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              <span className="font-mono text-[11px] text-[var(--false)] uppercase font-semibold flex items-center gap-1.5">
                <span>CONTRADICTING EVIDENCE ({contradictingEvidence.length})</span>
              </span>
              <div className="space-y-2">
                {contradictingEvidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 rounded border border-rose-500/20 bg-[#0C111D] space-y-1"
                  >
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-[var(--foreground)] font-semibold">{ev.publisher}</span>
                      <span className="text-[var(--false)] font-bold">{ev.tierLabel}</span>
                    </div>
                    <p className="text-xs text-[var(--muted-foreground)] italic font-sans">
                      &ldquo;{ev.excerpt}&rdquo;
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Other Linked Evidence (e.g. before full classification or neutral) */}
          {otherRelatedEvidence.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-[rgba(255,255,255,0.06)]">
              <span className="font-mono text-[11px] text-[var(--muted-foreground)] uppercase">
                ADDITIONAL LINKED EVIDENCE ({otherRelatedEvidence.length})
              </span>
              <div className="space-y-2">
                {otherRelatedEvidence.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 rounded border border-[rgba(255,255,255,0.06)] bg-[#0C111D] space-y-1"
                  >
                    <div className="flex items-center justify-between font-mono text-[11px]">
                      <span className="text-[var(--foreground)] font-semibold">{ev.publisher}</span>
                      <span className="text-slate-400 font-mono">{ev.stance}</span>
                    </div>
                    <p className="text-xs text-[var(--muted-foreground)] italic font-sans">
                      &ldquo;{ev.excerpt}&rdquo;
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
