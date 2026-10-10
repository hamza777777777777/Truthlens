"use client";

import * as React from "react";
import { motion } from "motion/react";
import { Check, Loader2 } from "lucide-react";
import { INVESTIGATION_STAGES } from "@/lib/investigation-service";

interface InvestigationProgressProps {
  onComplete: () => void;
}

export function InvestigationProgress({ onComplete }: InvestigationProgressProps) {
  const [currentStageIdx, setCurrentStageIdx] = React.useState(0);

  React.useEffect(() => {
    const stageDurations = [450, 500, 550, 500, 450, 400]; // Total ~2.85s
    let currentIndex = 0;

    const runNextStage = () => {
      if (currentIndex < INVESTIGATION_STAGES.length - 1) {
        currentIndex += 1;
        setCurrentStageIdx(currentIndex);
        setTimeout(runNextStage, stageDurations[currentIndex]);
      } else {
        setTimeout(() => {
          onComplete();
        }, 350);
      }
    };

    const firstTimer = setTimeout(runNextStage, stageDurations[0]);
    return () => clearTimeout(firstTimer);
  }, [onComplete]);

  const activeStage = INVESTIGATION_STAGES[currentStageIdx];
  const progressPercent = Math.round(((currentStageIdx + 1) / INVESTIGATION_STAGES.length) * 100);

  return (
    <div className="w-full max-w-3xl mx-auto rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] p-6 sm:p-9 shadow-2xl shadow-black/80 space-y-8 font-sans">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-[rgba(255,255,255,0.07)] pb-4 font-mono text-xs">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 text-[var(--primary)] animate-spin" />
          <span className="text-[var(--primary)] font-semibold uppercase tracking-wider">
            FORENSIC ENGINE ACTIVE // CASE IN PROGRESS
          </span>
        </div>
        <span className="text-[var(--muted-foreground)]">
          {progressPercent}% COMPLETE
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="h-2 w-full rounded-full bg-[#080B14] overflow-hidden border border-[rgba(255,255,255,0.05)]">
          <motion.div
            className="h-full bg-gradient-to-r from-[var(--primary)] to-[var(--secondary-accent)]"
            initial={{ width: "10%" }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          />
        </div>
        <div className="flex justify-between items-center font-mono text-[11px] text-[var(--muted-foreground)]">
          <span>STAGE {activeStage.id} OF 6</span>
          <span className="text-[var(--foreground)] font-medium">{activeStage.label}</span>
        </div>
      </div>

      {/* Stage Checklist */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 font-mono text-xs">
        {INVESTIGATION_STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIdx;
          const isCurrent = idx === currentStageIdx;

          return (
            <div
              key={stage.id}
              className={`p-3.5 rounded-lg border transition-all flex items-start gap-3 ${
                isCurrent
                  ? "border-[var(--primary)]/60 bg-[var(--surface-elevated)] ring-1 ring-[var(--primary)]/30 text-[var(--foreground)] shadow-md"
                  : isDone
                  ? "border-[rgba(255,255,255,0.08)] bg-[#080B14] text-[var(--foreground)] opacity-90"
                  : "border-transparent bg-transparent text-[var(--muted-foreground)] opacity-40"
              }`}
            >
              <div
                className={`h-5 w-5 rounded flex items-center justify-center shrink-0 mt-0.5 text-xs ${
                  isDone
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : isCurrent
                    ? "bg-[var(--primary)]/20 text-[var(--primary)] border border-[var(--primary)]/40"
                    : "bg-[#111927] text-[var(--muted-foreground)] border border-[rgba(255,255,255,0.08)]"
                }`}
              >
                {isDone ? (
                  <Check className="h-3 w-3" />
                ) : isCurrent ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <span>0{stage.id}</span>
                )}
              </div>

              <div className="space-y-0.5 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-xs truncate">
                    0{stage.id} {stage.code}
                  </span>
                  {isCurrent && (
                    <span className="h-1.5 w-1.5 rounded-full bg-[var(--primary)] animate-ping" />
                  )}
                </div>
                <p className="text-[11px] text-[var(--muted-foreground)] font-sans truncate">
                  {stage.detail}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-2 text-center text-xs font-mono text-[var(--muted-foreground)]">
        Correlating regulatory gazettes, domain DNS records, and scam pattern models...
      </div>
    </div>
  );
}
