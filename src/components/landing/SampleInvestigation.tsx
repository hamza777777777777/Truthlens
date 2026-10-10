"use client";

import * as React from "react";
import { 
  Info, 
  ChevronDown, 
  ArrowRight 
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export function SampleInvestigation() {
  const [expandedClaim, setExpandedClaim] = React.useState<number | null>(0);

  const CLAIMS = [
    {
      id: 0,
      text: "You have won ₹50,000 from an institutional lottery scheme.",
      status: "false" as const,
      statusLabel: "FALSE",
      badgeVariant: "falseClaim" as const,
      confidence: "99% Refutation Confidence",
      evidence: "Primary banking records and official RBI circulars verify that no such institutional lottery program exists. Banks are legally prohibited from running prize draws tied to payment requirements under regulatory guidelines.",
      source: "Banking Advisory Archive [Demo Simulation — Circular 2026/04]",
    },
    {
      id: 1,
      text: "A ₹499 payment is required to release the prize.",
      status: "cannotConfirm" as const,
      statusLabel: "CANNOT CONFIRM",
      badgeVariant: "cannotConfirm" as const,
      confidence: "Unverifiable Payment Channel",
      evidence: "While the message instructs sending ₹499, the destination payment gateway is unhosted or using ephemeral virtual payment addresses. TruthLens marks uncorroborated third-party payment endpoints as CANNOT CONFIRM rather than guessing.",
      source: "Payment Endpoint Gateway [Demo Simulation Trace TL-EP-99]",
    },
    {
      id: 2,
      text: "The sender represents an authorized financial intermediary.",
      status: "cannotConfirm" as const,
      statusLabel: "CANNOT CONFIRM",
      badgeVariant: "cannotConfirm" as const,
      confidence: "Unverified Identity Identity Header",
      evidence: "The sender phone number originated from an unlisted prepaid gateway. Without cryptographic signing or verified business profile authentication, legitimate identity cannot be confirmed.",
      source: "Telecom Sender Header Intelligence [Demo Simulation Trace]",
    },
  ];

  return (
    <section id="sample-investigation" className="py-24 border-t border-[var(--border)] bg-[#0A0E17] relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          <Badge variant="outline" className="font-mono text-xs uppercase tracking-wider border-amber-500/30 text-amber-300">
            <Info className="h-3 w-3 mr-1" />
            DEMO INVESTIGATION &middot; SIMULATED EVIDENCE
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-[var(--foreground)]">
            Anatomy of an Investigation.
          </h2>
          <p className="text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
            See how TruthLens renders a complete investigative breakdown — distinguishing between factual falsehood, behavioral deception, and unverifiable claims.
          </p>
        </div>

        {/* Master Sample Dossier Container */}
        <div className="mx-auto max-w-5xl rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-9 shadow-2xl shadow-black/60 space-y-8">
          {/* Top Dossier Metadata Bar */}
          <div className="flex flex-wrap items-center justify-between border-b border-[var(--border)] pb-5 gap-4">
            <div>
              <span className="font-mono text-xs text-[var(--muted-foreground)]">SAMPLE CASE IDENTIFIER</span>
              <h3 className="font-mono text-base font-bold text-[var(--foreground)]">CASE #TL-EX-50K-SBI</h3>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="falseClaim" className="font-mono text-xs px-2.5 py-1">
                TRUTH STATUS: FALSE
              </Badge>
              <Badge variant="destructive" className="font-mono text-xs px-2.5 py-1">
                SCAM RISK: 91 / 100 [CRITICAL]
              </Badge>
            </div>
          </div>

          {/* Incoming Content Block */}
          <div className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
              INGESTED MESSAGE ARTIFACT
            </span>
            <div className="rounded-lg border border-[var(--border)] bg-[#080B12] p-4 text-sm sm:text-base text-[var(--foreground)] font-mono leading-relaxed">
              &ldquo;Congratulations! You&apos;ve won ₹50,000. Pay ₹499 to claim your reward at https://sbi-reward-claim.example&rdquo;
            </div>
          </div>

          {/* Dual Verdict Breakdown Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg border border-[var(--false)]/30 bg-[var(--surface-elevated)] p-5 space-y-2">
              <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                VERDICT 1: EPISTEMIC TRUTH
              </span>
              <div className="flex items-center gap-2">
                <span className="text-2xl sm:text-3xl font-black text-[var(--false)]">FALSE</span>
                <span className="text-xs font-mono text-[var(--muted-foreground)]">(Primary claim contradicted)</span>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
                The premise that the recipient won an institutional lottery is refuted by official registry records.
              </p>
            </div>

            <div className="rounded-lg border border-red-500/30 bg-[var(--surface-elevated)] p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                  VERDICT 2: DECEPTIVE THREAT RISK
                </span>
                <span className="font-mono text-xs text-rose-400 font-bold">CRITICAL SEVERITY</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl sm:text-3xl font-black text-rose-400">91 / 100</span>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
                Severe scam signals triggered by upfront fee demands, artificial urgency, and financial institution spoofing.
              </p>
            </div>
          </div>

          {/* Granular Claims Breakdown Accordion */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                ATOMIC CLAIM ASSESSMENTS (3 CLAIMS)
              </span>
              <span className="font-mono text-[11px] text-[var(--primary)]">CLICK TO EXPAND EVIDENCE</span>
            </div>

            <div className="space-y-2.5">
              {CLAIMS.map((claim) => {
                const isOpen = expandedClaim === claim.id;
                return (
                  <div
                    key={claim.id}
                    className="rounded-lg border border-[var(--border)] bg-[#080B12] overflow-hidden transition-all"
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedClaim(isOpen ? null : claim.id)}
                      className="w-full p-4 text-left flex items-center justify-between gap-4 hover:bg-[var(--surface)] transition-colors"
                    >
                      <div className="flex items-start sm:items-center gap-3">
                        <span className="font-mono text-xs text-[var(--muted-foreground)] shrink-0 mt-0.5 sm:mt-0">
                          #{claim.id + 1}
                        </span>
                        <span className="text-sm font-medium text-[var(--foreground)]">
                          &ldquo;{claim.text}&rdquo;
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant={claim.badgeVariant}>
                          {claim.statusLabel}
                        </Badge>
                        <ChevronDown className={`h-4 w-4 text-[var(--muted-foreground)] transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
                      </div>
                    </button>

                    {isOpen && (
                      <div className="px-4 pb-4 pt-2 border-t border-[var(--border)] space-y-2.5 text-xs bg-[var(--surface)]/40">
                        <div className="flex items-center justify-between font-mono text-[11px]">
                          <span className="text-[var(--primary)]">{claim.confidence}</span>
                          <span className="text-[var(--muted-foreground)] truncate max-w-[280px]">SOURCE: {claim.source}</span>
                        </div>
                        <p className="text-[var(--muted-foreground)] leading-relaxed">
                          {claim.evidence}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Scam Signals Discovered */}
          <div className="space-y-3 pt-2">
            <span className="font-mono text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
              DECEPTION SIGNALS IDENTIFIED
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 space-y-1">
                <span className="text-rose-300 font-semibold block">PAYMENT REQUEST</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Requires upfront ₹499 transfer to claim supposed ₹50,000 payout.</span>
              </div>
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 space-y-1">
                <span className="text-amber-300 font-semibold block">ARTIFICIAL URGENCY</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Imposes implicit pressure to act before checking with real bank.</span>
              </div>
              <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 space-y-1">
                <span className="text-rose-300 font-semibold block">REWARD BAIT</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Unsolicited lottery notification with disproportionate return lure.</span>
              </div>
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 space-y-1">
                <span className="text-rose-300 font-semibold block">IMPERSONATION</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Unauthorized utilization of reputable banking institution trademark.</span>
              </div>
            </div>
          </div>

          {/* Investigative Conclusion & Action CTA */}
          <div className="pt-4 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-[var(--muted-foreground)]">
              This sample demonstrates TruthLens calm forensic triage. Ready to evaluate your own suspicious content?
            </p>
            <Button asChild size="sm" className="gap-2 shrink-0">
              <Link href="/investigate">
                Start a New Investigation
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
