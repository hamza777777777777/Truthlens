"use client";

import * as React from "react";
import { ArrowDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const STORY_STEPS = [
  {
    step: "01",
    phase: "UNDERSTAND",
    title: "Deconstruct Content & Dissect Atomic Signals",
    copy: "First, TruthLens breaks the content into the individual claims and signals hidden inside it — separating factual assertions from emotional rhetoric, extracted entities, and outbound URLs.",
    badge: "SEMANTIC EXTRACTION",
  },
  {
    step: "02",
    phase: "VERIFY",
    title: "Check Evidence Against Authoritative Sources",
    copy: "Each claim is evaluated against authoritative evidence rather than judged as one block. Official registries, gazettes, and bank advisories are cross-referenced with transparent citations.",
    badge: "PRIMARY EVIDENCE",
  },
  {
    step: "03",
    phase: "INVESTIGATE",
    title: "Investigate Deception & Scam Patterns",
    copy: "Truth isn't the whole story. TruthLens also scrutinizes patterns commonly associated with deception: upfront fee requests, artificial urgency, and lookalike domains.",
    badge: "DECEPTION SIGNALS",
  },
  {
    step: "04",
    phase: "CORRELATE",
    title: "Multi-Vector Convergence",
    copy: "Epistemic contradiction, brand impersonation risk, and predatory behavioral tactics are weighted together into an auditable risk calculation rather than a black-box guess.",
    badge: "CROSS-SIGNAL SYNTHESIS",
  },
  {
    step: "05",
    phase: "VERDICT",
    title: "The Explainable Forensic Assessment",
    copy: "The investigation completes with a definitive assessment separating Epistemic Truth from Deceptive Risk, followed by unambiguous instructions for the user.",
    badge: "DECISIVE PAYOFF",
  },
];

export function InvestigationStory() {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const visualRef = React.useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = React.useState(0);

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const isReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const isMobile = window.innerWidth < 1024;

    if (isReducedMotion || isMobile) {
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const container = containerRef.current;
    if (!container) return;

    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: container,
        start: "top top",
        end: "+=320%",
        pin: visualRef.current,
        pinSpacing: true,
        scrub: 0.5,
        onUpdate: (self) => {
          const progress = self.progress;
          if (progress < 0.2) {
            setActiveStep(0);
          } else if (progress < 0.4) {
            setActiveStep(1);
          } else if (progress < 0.6) {
            setActiveStep(2);
          } else if (progress < 0.8) {
            setActiveStep(3);
          } else {
            setActiveStep(4);
          }
        },
      });
    }, container);

    return () => {
      ctx.revert();
    };
  }, []);

  return (
    <section
      id="how-it-works"
      ref={containerRef}
      className="relative bg-[#080B12] border-t border-[rgba(255,255,255,0.08)] py-24 scroll-mt-16"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="mx-auto max-w-3xl text-center space-y-3 mb-20">
          <span className="font-mono text-xs uppercase tracking-widest text-[var(--primary)] block">
            THE INVESTIGATION ARCHITECTURE
          </span>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-[var(--foreground)]">
            How TruthLens Investigates.
          </h2>
          <p className="text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
            From raw input deconstruction to decisive evidence-grounded judgment.
          </p>
        </div>

        {/* Pinned Desktop Layout / Sequential Fallback Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
          {/* Left Column: Narrative Milestones */}
          <div className="lg:col-span-5 space-y-16 lg:space-y-32 lg:py-10">
            {STORY_STEPS.map((s, idx) => {
              const isCurrent = activeStep === idx;
              return (
                <div
                  key={s.step}
                  className={`transition-all duration-300 rounded-xl p-6 sm:p-7 border ${
                    isCurrent
                      ? "border-[var(--primary)]/60 bg-[var(--surface-elevated)] shadow-xl ring-1 ring-[var(--primary)]/20"
                      : "border-[rgba(255,255,255,0.06)] bg-[var(--surface)]/40 opacity-50 hover:opacity-80"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--primary)]/10 text-[var(--primary)] border border-[var(--primary)]/20">
                      STAGE {s.step} • {s.phase}
                    </span>
                    <span className="font-mono text-[10px] text-[var(--muted-foreground)]">
                      {s.badge}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold tracking-tight text-[var(--foreground)] mb-2">
                    {s.title}
                  </h3>

                  <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
                    {s.copy}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Right Column: Pinned Forensic Visual Canvas */}
          <div
            ref={visualRef}
            className="lg:col-span-7 lg:sticky lg:top-28 w-full"
          >
            <div className="rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] p-6 sm:p-8 shadow-2xl shadow-black/80 relative overflow-hidden font-sans">
              {/* Header Bar */}
              <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-4 mb-6">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[var(--primary)] animate-pulse" />
                  <span className="font-mono text-xs text-[var(--primary)] font-semibold uppercase tracking-wider">
                    INVESTIGATION PIPELINE // STAGE {STORY_STEPS[activeStep].step}: {STORY_STEPS[activeStep].phase}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-amber-300 font-semibold px-2 py-0.5 rounded border border-amber-500/30 bg-amber-500/10 hidden sm:inline">
                    DEMO INVESTIGATION &middot; SIMULATED EVIDENCE
                  </span>
                  <span className="font-mono text-[11px] text-[var(--muted-foreground)]">
                    CASE #DEMO-SBI-50K
                  </span>
                </div>
              </div>

              {/* Dynamic State 01: UNDERSTAND */}
              {activeStep === 0 && (
                <div className="space-y-4 animate-in fade-in duration-300">
                  <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#080B14] p-4 space-y-1.5">
                    <span className="font-mono text-[11px] text-[var(--muted-foreground)]">INGESTED TEXT PAYLOAD</span>
                    <p className="text-sm font-mono text-[var(--foreground)] leading-relaxed">
                      &ldquo;Congratulations! You&apos;ve won ₹50,000. Pay ₹499 to claim your reward at https://sbi-reward-claim.example&rdquo;
                    </p>
                  </div>

                  <div className="flex justify-center text-[var(--primary)]">
                    <ArrowDown className="h-4 w-4" />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                    <div className="rounded-lg border border-amber-400/30 bg-amber-400/5 p-3 space-y-1">
                      <span className="text-[10px] text-amber-300">CLAIM 1</span>
                      <p className="text-[var(--foreground)] font-semibold font-sans">₹50,000 lottery win</p>
                    </div>
                    <div className="rounded-lg border border-rose-400/30 bg-rose-400/5 p-3 space-y-1">
                      <span className="text-[10px] text-rose-300">CLAIM 2</span>
                      <p className="text-[var(--foreground)] font-semibold font-sans">₹499 mandatory fee</p>
                    </div>
                    <div className="rounded-lg border border-sky-400/30 bg-sky-400/5 p-3 space-y-1">
                      <span className="text-[10px] text-sky-300">TARGET DOMAIN</span>
                      <p className="text-[var(--foreground)] font-semibold truncate font-sans">sbi-reward-claim.example</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic State 02: VERIFY */}
              {activeStep === 1 && (
                <div className="space-y-3 animate-in fade-in duration-300 font-mono text-xs">
                  <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#080B14] p-3 text-xs">
                    <span className="text-[var(--muted-foreground)]">CLAIM UNDER ACTIVE VERIFICATION:</span>
                    <p className="text-[var(--foreground)] font-semibold mt-1 font-sans">
                      &ldquo;SBI is distributing ₹50,000 monetary rewards through this scheme.&rdquo;
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="rounded-lg border border-[var(--false)]/30 bg-[var(--false)]/5 p-3.5 flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="falseClaim">CONFLICTING</Badge>
                          <span className="text-[var(--muted-foreground)]">Banking Fraud Advisory [Demo Simulation]</span>
                        </div>
                        <p className="text-xs text-[var(--foreground)] font-sans">
                          Direct refutation: Banks do not host lottery reward portals requiring advance processing fees.
                        </p>
                      </div>
                      <span className="text-[var(--false)] font-bold shrink-0">PRIMARY SOURCE</span>
                    </div>

                    <div className="rounded-lg border border-[rgba(255,255,255,0.07)] bg-[var(--surface)] p-3 flex items-start justify-between text-[var(--muted-foreground)]">
                      <div>
                        <span className="text-[11px] text-[var(--foreground)] font-semibold">Public Press &amp; Gazette Archive [Demo Simulation]</span>
                        <p className="text-[11px] font-sans">Zero corroborating releases for this lottery.</p>
                      </div>
                      <span>0 CORROBORATIONS</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic State 03: INVESTIGATE */}
              {activeStep === 2 && (
                <div className="space-y-3.5 animate-in fade-in duration-300 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--muted-foreground)]">INVESTIGATING DECEPTION SIGNALS</span>
                    <span className="text-rose-400 font-bold">4 RISK VECTORS IDENTIFIED</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="rounded-lg border border-red-500/25 bg-red-500/5 p-3 space-y-1">
                      <span className="text-rose-400 font-bold block">1. ADVANCE FEE HOOK</span>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs">
                        Demands ₹499 payment prior to receiving promised payout.
                      </p>
                    </div>

                    <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-3 space-y-1">
                      <span className="text-amber-300 font-bold block">2. ARTIFICIAL URGENCY</span>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs">
                        Coercive deadline designed to bypass verification checks.
                      </p>
                    </div>

                    <div className="rounded-lg border border-rose-500/25 bg-rose-500/5 p-3 space-y-1">
                      <span className="text-rose-400 font-bold block">3. REWARD LURE</span>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs">
                        Unsolicited windfall with zero previous participation.
                      </p>
                    </div>

                    <div className="rounded-lg border border-red-500/25 bg-red-500/5 p-3 space-y-1">
                      <span className="text-rose-400 font-bold block">4. BRAND FORGERY</span>
                      <p className="text-[var(--muted-foreground)] font-sans text-xs">
                        Unregistered .example domain impersonating national bank.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic State 04: CORRELATE */}
              {activeStep === 3 && (
                <div className="space-y-4 animate-in fade-in duration-300 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--muted-foreground)]">MULTI-VECTOR CORRELATION MATRIX</span>
                    <span className="text-rose-400 font-bold">AGGREGATING RISK SCORE</span>
                  </div>

                  <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#080B14] p-4 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[var(--foreground)]">Epistemic Contradiction Weight:</span>
                      <span className="text-rose-400 font-bold">+35 pts</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[var(--foreground)]">Advance Fee Fraud Vector:</span>
                      <span className="text-rose-400 font-bold">+25 pts</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-[var(--foreground)]">Lookalike Domain Impersonation:</span>
                      <span className="text-rose-400 font-bold">+31 pts</span>
                    </div>

                    <div className="pt-2 border-t border-[rgba(255,255,255,0.08)] flex justify-between items-center">
                      <span className="font-bold text-[var(--foreground)]">TOTAL COMPUTED THREAT INDEX:</span>
                      <span className="text-xl font-bold text-rose-400">91 / 100</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Dynamic State 05: VERDICT (CLIMAX OF THE INVESTIGATION) */}
              {activeStep === 4 && (
                <div className="space-y-4 animate-in fade-in duration-300 font-mono">
                  <div className="rounded-xl border border-rose-500/40 bg-[#120B15] p-5 sm:p-6 space-y-4 shadow-xl">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[rgba(255,255,255,0.08)] pb-4">
                      <div>
                        <span className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider block">
                          INVESTIGATION COMPLETE
                        </span>
                        <div className="flex items-baseline gap-3 mt-1">
                          <span className="text-3xl font-black text-[var(--false)]">FALSE</span>
                          <span className="text-sm text-[var(--muted-foreground)]">•</span>
                          <span className="text-2xl font-bold text-rose-400">91 / 100</span>
                        </div>
                      </div>
                      <Badge variant="falseClaim" className="text-xs px-3 py-1 font-bold">
                        HIGH RISK • LIKELY SCAM
                      </Badge>
                    </div>

                    {/* Concise Rationale Highlights */}
                    <div className="space-y-2 text-xs font-sans text-[var(--muted-foreground)]">
                      <p className="font-mono text-xs text-[var(--foreground)] font-semibold">
                        DETECTED THREAT SIGNALS:
                      </p>
                      <ul className="space-y-1.5 font-mono text-[11px] text-rose-300">
                        <li className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          Payment request detected (₹499 advance fee required)
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          Suspicious lookalike domain detected (sbi-reward-claim.example)
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          Lottery reward claim directly refuted by official bank advisory
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                          Coercive artificial urgency detected (&ldquo;within 2 hours&rdquo;)
                        </li>
                      </ul>
                    </div>

                    <div className="pt-3 border-t border-[rgba(255,255,255,0.08)] flex items-center justify-between text-xs">
                      <span className="text-[var(--muted-foreground)]">RECOMMENDED ACTION:</span>
                      <span className="text-[var(--false)] font-bold">DO NOT PAY • BLOCK SENDER</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Bottom Canvas Rail */}
              <div className="mt-6 pt-4 border-t border-[rgba(255,255,255,0.08)] flex items-center justify-between text-xs font-mono text-[var(--muted-foreground)]">
                <span>SCROLL PROGRESS: STAGE {activeStep + 1} OF 5</span>
                <span className="text-[var(--primary)]">CALM FORENSIC INTELLIGENCE</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
