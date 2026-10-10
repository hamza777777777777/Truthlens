"use client";

import * as React from "react";
import { 
  X, 
  HelpCircle 
} from "lucide-react";

export function CapabilityGrid() {
  return (
    <section id="capabilities" className="py-24 border-t border-[rgba(255,255,255,0.08)] bg-[#080B12] relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Editorial Section Header */}
        <div className="max-w-3xl space-y-3">
          <span className="font-mono text-xs uppercase tracking-widest text-[var(--primary)] block">
            CORE CAPABILITIES
          </span>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-[var(--foreground)]">
            Truth is only the beginning.
          </h2>
          <p className="text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
            TruthLens separates what a message says from what its evidence supports — then investigates the signals that may make it dangerous.
          </p>
        </div>

        {/* Asymmetric Editorial Bento Composition */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* 01: CLAIM INTELLIGENCE (Large Feature - 7 cols) */}
          <div className="lg:col-span-7 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between font-mono text-xs text-[var(--muted-foreground)]">
                <span className="text-[var(--primary)] font-semibold">01 / DECONSTRUCTION</span>
                <span>ATOMIC EXTRACTION</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
                Claim Intelligence
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] leading-relaxed max-w-xl">
                Break content into the individual claims it is actually making rather than judging it as one ambiguous block. Each assertion is isolated for independent verification.
              </p>
            </div>

            {/* In-situ forensic artifact visual */}
            <div className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#070A12] p-4 space-y-3 font-mono text-xs">
              <div className="text-[var(--muted-foreground)] flex items-center justify-between border-b border-[rgba(255,255,255,0.06)] pb-2">
                <span>INPUT: &ldquo;Won ₹50k. Pay ₹499 fee to claim.&rdquo;</span>
                <span className="text-emerald-400">2 CLAIMS ISOLATED</span>
              </div>
              <div className="space-y-2">
                <div className="p-2.5 rounded bg-[var(--surface-elevated)] border border-[rgba(255,255,255,0.06)] flex items-center justify-between">
                  <span className="text-[var(--foreground)]">&ldquo;You have won ₹50,000.&rdquo;</span>
                  <span className="text-amber-300 text-[11px] font-bold">BENEFIT CLAIM</span>
                </div>
                <div className="p-2.5 rounded bg-[var(--surface-elevated)] border border-[rgba(255,255,255,0.06)] flex items-center justify-between">
                  <span className="text-[var(--foreground)]">&ldquo;A ₹499 payment is required.&rdquo;</span>
                  <span className="text-rose-300 text-[11px] font-bold">OBLIGATION CLAIM</span>
                </div>
              </div>
            </div>
          </div>

          {/* 02: EVIDENCE INTELLIGENCE (Medium Feature - 5 cols) */}
          <div className="lg:col-span-5 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between font-mono text-xs text-[var(--muted-foreground)]">
                <span className="text-[var(--primary)] font-semibold">02 / TRIANGULATION</span>
                <span>CHECK THE EVIDENCE</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
                Evidence Intelligence
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
                Connect claims to supporting, contradicting, or insufficient evidence from authoritative sources.
              </p>
            </div>

            {/* Evidence weighting stack */}
            <div className="space-y-2.5 font-mono text-xs">
              <div className="rounded border border-[var(--false)]/30 bg-[var(--false)]/5 p-3 flex items-start gap-2.5">
                <X className="h-4 w-4 text-[var(--false)] shrink-0 mt-0.5" />
                <div>
                  <span className="text-[var(--foreground)] font-medium">Banking Advisory Records [Demo Simulation]</span>
                  <p className="text-[var(--muted-foreground)] text-[11px] font-sans">Official notice refutes any fee-based prize schemes.</p>
                </div>
              </div>
              <div className="rounded border border-[rgba(255,255,255,0.07)] bg-[var(--surface)] p-3 flex items-start gap-2.5 text-[var(--muted-foreground)]">
                <HelpCircle className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[var(--foreground)] font-medium">Registry Verification [Demo Simulation]</span>
                  <p className="text-[var(--muted-foreground)] text-[11px] font-sans">No matching campaign ID registered.</p>
                </div>
              </div>
            </div>
          </div>

          {/* 03: SCAM INVESTIGATION (Large / High-Impact Feature - 7 cols) */}
          <div className="lg:col-span-7 rounded-xl border border-red-500/20 bg-[#0E0C16] p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between font-mono text-xs text-[var(--muted-foreground)]">
                <span className="text-rose-400 font-semibold">03 / THREAT DETECTION</span>
                <span className="text-rose-400">DECEPTION SIGNALS</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
                Scam Investigation
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] leading-relaxed max-w-xl">
                Identify suspicious behavioral and content patterns like upfront advance fee demands, artificial urgency, and lookalike domain abuse.
              </p>
            </div>

            {/* Deception Signals Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
              <div className="p-3 rounded border border-red-500/30 bg-red-500/10 space-y-1">
                <span className="text-rose-400 font-bold block text-[11px]">PAYMENT HOOK</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Upfront fee barrier</span>
              </div>
              <div className="p-3 rounded border border-amber-500/30 bg-amber-500/10 space-y-1">
                <span className="text-amber-300 font-bold block text-[11px]">URGENCY BAIT</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">2-hour pressure</span>
              </div>
              <div className="p-3 rounded border border-rose-500/30 bg-rose-500/10 space-y-1">
                <span className="text-rose-400 font-bold block text-[11px]">REWARD LURE</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Unsolicited windfall</span>
              </div>
              <div className="p-3 rounded border border-red-500/30 bg-red-500/10 space-y-1">
                <span className="text-rose-400 font-bold block text-[11px]">SPOOFED TLD</span>
                <span className="text-[var(--muted-foreground)] text-[11px] font-sans">Typosquat address</span>
              </div>
            </div>
          </div>

          {/* 04: EXPLAINABLE RISK (Supporting Feature - 5 cols) */}
          <div className="lg:col-span-5 rounded-xl border border-[rgba(255,255,255,0.08)] bg-[#0C111D] p-6 sm:p-8 flex flex-col justify-between space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between font-mono text-xs text-[var(--muted-foreground)]">
                <span className="text-[var(--primary)] font-semibold">04 / SYNTHESIS</span>
                <span>DECISIONING</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
                Explainable Risk
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
                Turn scattered signals into an understandable assessment separating epistemic truth from predatory threat.
              </p>
            </div>

            {/* Dual assessment readout */}
            <div className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[#070A12] p-4 space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center">
                <span className="text-[var(--muted-foreground)]">TRUTH STATUS:</span>
                <span className="text-[var(--false)] font-bold">FALSE (Direct Contradiction)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--muted-foreground)]">SCAM RISK:</span>
                <span className="text-rose-400 font-bold">91 / 100 (HIGH RISK)</span>
              </div>
              <div className="pt-2 border-t border-[rgba(255,255,255,0.06)] text-[11px] font-sans text-[var(--muted-foreground)]">
                Action: Do not transact. Block sender and report destination domain.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
