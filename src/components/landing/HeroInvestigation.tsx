"use client";

import * as React from "react";
import { motion, AnimatePresence } from "motion/react";
import { 
  Play, 
  RotateCcw,
  X,
  HelpCircle,
  Pause
} from "lucide-react";

type Stage = 0 | 1 | 2 | 3 | 4 | 5;

const STAGE_LABELS = [
  "Raw Message",
  "Fragment Dissection",
  "Check Evidence",
  "Deception Signals",
  "Risk Calculation",
  "Final Verdict",
];

const STAGE_RISK_MAP: Record<Stage, number> = {
  0: 18,
  1: 34,
  2: 52,
  3: 71,
  4: 91,
  5: 91,
};

export function HeroInvestigation() {
  const [stage, setStage] = React.useState<Stage>(0);
  const [isPlaying, setIsPlaying] = React.useState(true);

  // Stepped progression timer
  React.useEffect(() => {
    if (!isPlaying) return;

    const durations = [2400, 2600, 2800, 2600, 2400, 4500];
    const timer = setTimeout(() => {
      setStage((prev) => ((prev + 1) % 6) as Stage);
    }, durations[stage]);

    return () => clearTimeout(timer);
  }, [stage, isPlaying]);

  const riskCounter = STAGE_RISK_MAP[stage];

  return (
    <div className="w-full rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] text-left shadow-2xl shadow-black/80 overflow-hidden font-sans">
      {/* Forensic Intelligence Chrome Top Bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-[rgba(255,255,255,0.07)] px-4 sm:px-6 py-3 bg-[#080B14]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-400/80 inline-block" />
            <span className="h-2 w-2 rounded-full bg-amber-400/80 inline-block" />
            <span className="h-2 w-2 rounded-full bg-emerald-400/80 inline-block" />
          </div>
          <span className="h-3.5 w-px bg-[rgba(255,255,255,0.1)]" />
          <div className="flex items-center gap-2 font-mono text-xs text-[var(--muted-foreground)]">
            <span className="text-[var(--primary)] font-semibold">TRUTHLENS KERNEL</span>
            <span>/</span>
            <span>CASE #DEMO-SBI-50K</span>
          </div>
          <span className="h-3.5 w-px bg-[rgba(255,255,255,0.1)] hidden sm:inline" />
          <span className="text-[10px] font-semibold text-amber-300/90 bg-amber-500/10 border border-amber-500/25 px-2 py-0.5 rounded font-mono hidden sm:inline">
            DEMO INVESTIGATION &middot; SIMULATED EVIDENCE
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--muted-foreground)] hidden sm:inline">
            STAGE {stage + 1} OF 6: <strong className="text-[var(--foreground)]">{STAGE_LABELS[stage]}</strong>
          </span>
          <div className="flex items-center gap-1 ml-2">
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-1.5 rounded border border-[rgba(255,255,255,0.08)] bg-[var(--surface-elevated)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:border-[rgba(255,255,255,0.2)] transition-colors text-xs font-mono flex items-center gap-1"
              title={isPlaying ? "Pause timeline" : "Resume timeline"}
            >
              {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3 text-[var(--primary)]" />}
              <span className="text-[10px] hidden md:inline">{isPlaying ? "PAUSE" : "PLAY"}</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setStage(0);
                setIsPlaying(true);
              }}
              className="p-1.5 rounded border border-[rgba(255,255,255,0.08)] bg-[var(--surface-elevated)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
              title="Replay investigation"
            >
              <RotateCcw className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Forensic Interactive Timeline Rail */}
      <div className="grid grid-cols-6 border-b border-[rgba(255,255,255,0.06)] bg-[#0A0E18] text-[11px] font-mono">
        {STAGE_LABELS.map((label, idx) => {
          const isActive = stage === idx;
          const isPassed = stage > idx;
          return (
            <button
              key={label}
              type="button"
              onClick={() => {
                setStage(idx as Stage);
                setIsPlaying(false);
              }}
              className={`py-2 px-2 text-center transition-all border-b-2 truncate ${
                isActive
                  ? "border-[var(--primary)] bg-[var(--surface-elevated)] text-[var(--primary)] font-semibold"
                  : isPassed
                  ? "border-transparent text-[var(--foreground)] opacity-80"
                  : "border-transparent text-[var(--muted-foreground)] opacity-50 hover:opacity-80"
              }`}
            >
              <span className="hidden md:inline mr-1">{idx + 1}.</span>
              <span>{label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Dynamic Forensic Canvas */}
      <div className="p-5 sm:p-7 sm:min-h-[440px] flex flex-col justify-between">
        {/* Top: The Incoming Message with dynamic highlighted fragments */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--muted-foreground)]">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block" />
              INGESTED TELEPHONY PAYLOAD
            </span>
            <span>ORIGIN: SMS ROUTE (+91-987XX)</span>
          </div>

          <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#070A12] p-4 sm:p-5 text-base sm:text-lg font-medium leading-relaxed transition-all">
            &ldquo;Congratulations! You&apos;ve won{" "}
            <span
              className={`transition-all duration-300 rounded px-1.5 py-0.5 ${
                stage >= 1
                  ? "bg-amber-400/20 text-amber-200 ring-1 ring-amber-400/50"
                  : "text-[var(--foreground)]"
              }`}
            >
              ₹50,000
            </span>
            . Pay{" "}
            <span
              className={`transition-all duration-300 rounded px-1.5 py-0.5 ${
                stage >= 1
                  ? "bg-rose-500/25 text-rose-300 ring-1 ring-rose-500/50"
                  : "text-[var(--foreground)]"
              }`}
            >
              ₹499
            </span>{" "}
            to claim your reward{" "}
            <span
              className={`transition-all duration-300 rounded px-1.5 py-0.5 ${
                stage >= 1
                  ? "bg-orange-500/20 text-orange-200 ring-1 ring-orange-500/50"
                  : "text-[var(--foreground)]"
              }`}
            >
              within 2 hours
            </span>{" "}
            at{" "}
            <span
              className={`font-mono text-sm sm:text-base transition-all duration-300 rounded px-1.5 py-0.5 ${
                stage >= 1
                  ? "bg-sky-500/20 text-[var(--primary)] ring-1 ring-[var(--primary)]/50 underline underline-offset-4"
                  : "text-[var(--foreground)]"
              }`}
            >
              https://sbi-reward-claim.example
            </span>
            &rdquo;
          </div>
        </div>

        {/* Middle: Investigation Stages & Evidence Connectors */}
        <div className="my-6">
          <AnimatePresence mode="wait">
            {/* STAGE 0: DETECTED */}
            {stage === 0 && (
              <motion.div
                key="stage-0"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="rounded-lg border border-[rgba(255,255,255,0.06)] bg-[var(--surface)] p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 font-mono text-xs text-[var(--muted-foreground)]"
              >
                <div className="flex items-center gap-3">
                  <span className="h-2 w-2 rounded-full bg-[var(--primary)] animate-ping" />
                  <span>Scanning payload structure • Initializing multimodal claim parser...</span>
                </div>
                <span className="text-[var(--primary)]">STATE: INGESTION READY</span>
              </motion.div>
            )}

            {/* STAGE 1: FRAGMENTS EXTRACTED */}
            {stage === 1 && (
              <motion.div
                key="stage-1"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs"
              >
                <div className="rounded-lg border border-amber-400/30 bg-amber-400/5 p-3.5 space-y-1">
                  <span className="text-[10px] text-amber-300 uppercase tracking-wider block">CLAIM 1: WINDFALL LURE</span>
                  <p className="text-[var(--foreground)] font-medium font-sans">&ldquo;Recipient won ₹50,000 cash grant.&rdquo;</p>
                </div>
                <div className="rounded-lg border border-rose-400/30 bg-rose-400/5 p-3.5 space-y-1">
                  <span className="text-[10px] text-rose-300 uppercase tracking-wider block">CLAIM 2: ADVANCE FEE</span>
                  <p className="text-[var(--foreground)] font-medium font-sans">&ldquo;₹499 mandatory fee required to disburse.&rdquo;</p>
                </div>
                <div className="rounded-lg border border-sky-400/30 bg-sky-400/5 p-3.5 space-y-1">
                  <span className="text-[10px] text-sky-300 uppercase tracking-wider block">TARGET ENTITY &amp; DOMAIN</span>
                  <p className="text-[var(--foreground)] font-medium font-sans">SBI Impersonated • Unregistered TLD</p>
                </div>
              </motion.div>
            )}

            {/* STAGE 2: EVIDENCE CORROBORATION */}
            {stage === 2 && (
              <motion.div
                key="stage-2"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="space-y-2.5 font-mono text-xs"
              >
                <div className="rounded-lg border border-[var(--false)]/30 bg-[var(--false)]/5 p-3 flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div className="h-5 w-5 rounded bg-[var(--false)]/20 text-[var(--false)] flex items-center justify-center shrink-0 mt-0.5">
                      <X className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--foreground)] font-medium">Banking Advisory Records</span>
                        <span className="text-[10px] text-amber-300 font-mono bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">DEMO SIMULATION</span>
                      </div>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs mt-0.5">
                        Official records confirm: No reward programs require advance payment. Policy strictly refutes lottery claims.
                      </p>
                    </div>
                  </div>
                  <span className="text-[var(--false)] font-bold text-[11px] shrink-0">CONFLICTING</span>
                </div>

                <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[var(--surface)] p-3 flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <div className="h-5 w-5 rounded bg-slate-700/50 text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                      <HelpCircle className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--foreground)] font-medium">Domain Registration &amp; SSL Check</span>
                        <span className="text-[10px] text-amber-300 font-mono bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/20">DEMO SIMULATION</span>
                      </div>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs mt-0.5">
                        Domain registered 18 hours ago via privacy proxy. Zero association with State Bank of India network.
                      </p>
                    </div>
                  </div>
                  <span className="text-slate-400 font-bold text-[11px] shrink-0">UNCERTAIN</span>
                </div>
              </motion.div>
            )}

            {/* STAGE 3: DECEPTION SIGNALS */}
            {stage === 3 && (
              <motion.div
                key="stage-3"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs"
              >
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 space-y-1">
                  <span className="text-rose-400 font-bold text-[11px] block">1. ADVANCE FEE</span>
                  <span className="text-[var(--muted-foreground)] font-sans text-[11px]">Payment required before prize</span>
                </div>
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 space-y-1">
                  <span className="text-amber-300 font-bold text-[11px] block">2. URGENCY</span>
                  <span className="text-[var(--muted-foreground)] font-sans text-[11px]">2-hour coercive deadline</span>
                </div>
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 space-y-1">
                  <span className="text-rose-400 font-bold text-[11px] block">3. REWARD LURE</span>
                  <span className="text-[var(--muted-foreground)] font-sans text-[11px]">₹50,000 unsolicited windfall</span>
                </div>
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 space-y-1">
                  <span className="text-rose-400 font-bold text-[11px] block">4. IMPERSONATION</span>
                  <span className="text-[var(--muted-foreground)] font-sans text-[11px]">Spoofed national bank identity</span>
                </div>
              </motion.div>
            )}

            {/* STAGE 4: RISK CALCULATION */}
            {stage === 4 && (
              <motion.div
                key="stage-4"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="rounded-lg border border-red-500/30 bg-[#120B13] p-5 space-y-3 font-mono"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--muted-foreground)]">INVESTIGATING DECEPTION PATTERNS...</span>
                  <span className="text-rose-400 font-bold">ACCUMULATING THREAT INDEX</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl sm:text-5xl font-black text-rose-400">{riskCounter}</span>
                  <span className="text-lg text-[var(--muted-foreground)]">/ 100</span>
                  <span className="ml-auto text-xs px-2 py-1 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                    CRITICAL SEVERITY
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-[#1F1522] overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-rose-500 transition-all duration-300"
                    style={{ width: `${riskCounter}%` }}
                  />
                </div>
              </motion.div>
            )}

            {/* STAGE 5: FINAL VERDICT RESOLUTION */}
            {stage === 5 && (
              <motion.div
                key="stage-5"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
                className="rounded-xl border border-rose-500/40 bg-[#100B14] p-5 sm:p-6 space-y-4 shadow-xl"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[rgba(255,255,255,0.08)] pb-4">
                  <div>
                    <span className="font-mono text-xs text-[var(--muted-foreground)] uppercase tracking-wider block">
                      INVESTIGATION COMPLETE
                    </span>
                    <div className="flex items-baseline gap-3 mt-1">
                      <span className="text-2xl sm:text-3xl font-black text-[var(--false)]">FALSE</span>
                      <span className="font-mono text-sm text-[var(--muted-foreground)]">•</span>
                      <span className="text-xl sm:text-2xl font-bold text-rose-400">HIGH RISK (91 / 100)</span>
                    </div>
                  </div>
                  <span className="font-mono text-xs px-3 py-1.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold uppercase tracking-wider">
                    LIKELY SCAM
                  </span>
                </div>

                <p className="text-sm text-[var(--muted-foreground)] leading-relaxed font-sans">
                  Target message impersonates the State Bank of India to extract an upfront ₹499 payment using an illusory ₹50,000 prize and artificial urgency. Official institutional advisories directly refute the claim.
                </p>

                <div className="pt-2 flex flex-wrap items-center gap-3 font-mono text-xs text-[var(--muted-foreground)]">
                  <span className="text-rose-400 font-semibold">• Payment request detected</span>
                  <span className="text-rose-400 font-semibold">• Lookalike domain</span>
                  <span className="text-rose-400 font-semibold">• Unsupported prize claim</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom Control Bar */}
        <div className="pt-4 border-t border-[rgba(255,255,255,0.07)] flex flex-wrap items-center justify-between gap-3 font-mono text-xs text-[var(--muted-foreground)]">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <span className="text-amber-300 font-semibold">DEMO INVESTIGATION &middot; SIMULATED EVIDENCE</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setStage((prev) => (prev <= 0 ? 5 : ((prev - 1) as Stage)));
                setIsPlaying(false);
              }}
              className="px-2.5 py-1 rounded border border-[rgba(255,255,255,0.08)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]"
            >
              PREV
            </button>
            <button
              type="button"
              onClick={() => {
                setStage((prev) => (prev >= 5 ? 0 : ((prev + 1) as Stage)));
                setIsPlaying(false);
              }}
              className="px-2.5 py-1 rounded border border-[rgba(255,255,255,0.08)] bg-[var(--surface-elevated)] text-[var(--foreground)] hover:border-[var(--primary)]/50"
            >
              NEXT STAGE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
