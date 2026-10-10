"use client";

import * as React from "react";
import { 
  HelpCircle, 
  AlertTriangle 
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const STATUS_TAXONOMY = [
  {
    name: "CANNOT CONFIRM",
    variant: "cannotConfirm" as const,
    color: "text-slate-400 border-slate-600/40 bg-slate-900/60",
    desc: "Sufficient corroborated evidence does not exist in authoritative indices. We treat epistemic silence as an honest forensic finding, never hallucinating certainty.",
    featured: true,
  },
  {
    name: "VERIFIED",
    variant: "verified" as const,
    color: "text-[var(--verified)] border-[var(--verified)]/30 bg-[var(--verified)]/10",
    desc: "Rigorous corroboration confirmed across independent, primary, and authenticated repositories.",
    featured: false,
  },
  {
    name: "FALSE",
    variant: "falseClaim" as const,
    color: "text-[var(--false)] border-[var(--false)]/30 bg-[var(--false)]/10",
    desc: "Substantive claims directly contradict official advisories, empirical records, or authenticated proof.",
    featured: false,
  },
  {
    name: "PARTIALLY SUPPORTED",
    variant: "partial" as const,
    color: "text-[var(--partial)] border-[var(--partial)]/30 bg-[var(--partial)]/10",
    desc: "Portions of the premise hold factual accuracy, while critical caveats, dates, or figures are distorted.",
    featured: false,
  },
  {
    name: "OUTDATED",
    variant: "outdated" as const,
    color: "text-[var(--outdated)] border-[var(--outdated)]/30 bg-[var(--outdated)]/10",
    desc: "Information was historically true under prior conditions but has expired, lapsed, or been revoked.",
    featured: false,
  },
];

export function SafetySection() {
  return (
    <section id="safety" className="py-24 border-t border-[var(--border)] bg-[#070A11] relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          <Badge variant="outline" className="font-mono text-xs uppercase tracking-wider border-[var(--cannot-confirm)] text-[var(--cannot-confirm)]">
            EPISTEMIC SAFETY &amp; HUMILITY
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-[var(--foreground)]">
            Uncertainty is a result too.
          </h2>
          <p className="text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
            Not every claim can be confirmed. In forensic intelligence, admitting what cannot be verified is the highest form of integrity.
          </p>
        </div>

        {/* Featured Emphasis Box: CANNOT CONFIRM */}
        <div className="mx-auto max-w-4xl rounded-xl border border-[var(--cannot-confirm)]/30 bg-[#0E1420] p-6 sm:p-8 mb-12 shadow-xl shadow-black/50">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-5 mb-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[var(--cannot-confirm)]/40 bg-[var(--surface-elevated)] text-[var(--cannot-confirm)]">
                <HelpCircle className="h-5 w-5" />
              </div>
              <div>
                <span className="font-mono text-xs text-[var(--muted-foreground)] uppercase">PRIMARY PRINCIPLE</span>
                <h3 className="text-xl font-bold text-[var(--foreground)]">
                  The Principle of Non-Hallucinated Certainty
                </h3>
              </div>
            </div>
            <Badge variant="cannotConfirm" className="font-mono text-xs px-3 py-1">
              STATUS: CANNOT CONFIRM
            </Badge>
          </div>
          <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
            Many disinformation engines force binary True/False judgments on incomplete data. TruthLens explicitly yields <span className="text-[var(--foreground)] font-semibold font-mono">CANNOT CONFIRM</span> when evidence trails run cold, ensuring analysts and everyday users understand the boundary between fact, contradiction, and unknown territory.
          </p>
        </div>

        {/* Complete Forensic Status Taxonomy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {STATUS_TAXONOMY.map((st) => (
            <div
              key={st.name}
              className={`rounded-xl border p-5 space-y-3 transition-all ${
                st.featured
                  ? "border-[var(--cannot-confirm)]/40 bg-[var(--surface-elevated)] ring-1 ring-[var(--cannot-confirm)]/20"
                  : "border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-focus)]"
              }`}
            >
              <div className="flex items-center justify-between">
                <Badge variant={st.variant} className="font-mono text-xs">
                  {st.name}
                </Badge>
                {st.featured && (
                  <span className="font-mono text-[10px] text-[var(--cannot-confirm)] uppercase">
                    RESPONSIBLE RESULT
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed pt-1">
                {st.desc}
              </p>
            </div>
          ))}
        </div>

        {/* High Stakes Warning Notice */}
        <div className="mt-12 rounded-lg border border-amber-500/20 bg-amber-500/5 p-4 sm:p-5 flex items-start gap-4 text-xs text-amber-200/90 leading-relaxed max-w-4xl mx-auto">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-mono font-bold block mb-1 uppercase tracking-wider text-amber-300">
              HIGH-STAKES ASSISTANCE PROTOCOL:
            </span>
            TruthLens assessments are computational intelligence evaluations designed to augment human judgment, not legal indemnities or infallible guarantees. Decisions involving critical financial transfers, physical security, or legal claims should always be cross-corroborated through verified offline authority channels.
          </div>
        </div>
      </div>
    </section>
  );
}
