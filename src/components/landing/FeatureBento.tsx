"use client";

import * as React from "react";
import { motion } from "motion/react";
import { 
  FileText, 
  Image as ImageIcon, 
  Globe 
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const FEATURES = [
  {
    title: "MULTIMODAL INGESTION",
    tagline: "Text, Screenshots & URL Endpoints",
    desc: "Submit suspicious messages via text paste, image/screenshot upload, or raw web URLs for structured forensic extraction.",
    badge: "MVP READY",
    visual: (
      <div className="flex flex-wrap gap-2 pt-3 font-mono text-xs">
        <span className="px-2.5 py-1 rounded bg-[var(--surface-elevated)] text-[var(--primary)] border border-[var(--primary)]/20 flex items-center gap-1.5">
          <FileText className="h-3 w-3" /> TEXT
        </span>
        <span className="px-2.5 py-1 rounded bg-[var(--surface-elevated)] text-[var(--primary)] border border-[var(--primary)]/20 flex items-center gap-1.5">
          <ImageIcon className="h-3 w-3" /> IMAGE OCR
        </span>
        <span className="px-2.5 py-1 rounded bg-[var(--surface-elevated)] text-[var(--primary)] border border-[var(--primary)]/20 flex items-center gap-1.5">
          <Globe className="h-3 w-3" /> URL
        </span>
        <span className="px-2.5 py-1 rounded bg-black/40 text-[var(--muted-foreground)] border border-[var(--border)] opacity-60">
          PDF (COMING SOON)
        </span>
        <span className="px-2.5 py-1 rounded bg-black/40 text-[var(--muted-foreground)] border border-[var(--border)] opacity-60">
          AUDIO (COMING SOON)
        </span>
      </div>
    ),
    colSpan: "lg:col-span-8",
  },
  {
    title: "CLAIM-LEVEL EVIDENCE",
    tagline: "Granular Traceability",
    desc: "Inspect precisely why each specific claim was assessed as true, false, or unconfirmable with cited sources.",
    badge: "PRECISION",
    visual: (
      <div className="pt-3 font-mono text-xs text-[var(--muted-foreground)] space-y-1.5">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-1">
          <span>CLAIM DECOMPOSITION</span>
          <span className="text-[var(--primary)]">100% AUDITABLE</span>
        </div>
        <div className="text-[11px] text-[var(--foreground)]">Direct citation back to primary repositories.</div>
      </div>
    ),
    colSpan: "lg:col-span-4",
  },
  {
    title: "SOURCE INTELLIGENCE",
    tagline: "Reputational & Regulatory Weighting",
    desc: "Sources are weighted by credibility: official gazettes and bank bulletins carry higher epistemic weight than unverified blogs.",
    badge: "CALIBRATED",
    visual: (
      <div className="pt-3 font-mono text-xs space-y-1">
        <div className="flex items-center justify-between text-emerald-400">
          <span>REGULATORY BULLETINS</span>
          <span>TIER 1 (0.95)</span>
        </div>
        <div className="flex items-center justify-between text-amber-300">
          <span>UNVERIFIED SOCIAL REPOSTS</span>
          <span>TIER 4 (0.15)</span>
        </div>
      </div>
    ),
    colSpan: "lg:col-span-4",
  },
  {
    title: "URL & INFRASTRUCTURE SCAN",
    tagline: "Lookalike & Typosquat Analysis",
    desc: "Scrutinize domains for homograph attacks, suspicious subdomains, newly registered domain anomalies, and spoofed hosting.",
    badge: "DECEPTION SIGNALS",
    visual: (
      <div className="pt-3 font-mono text-xs space-y-1">
        <div className="flex items-center gap-2 text-rose-400">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
          <span>LEVENSHTEIN DISTANCE: HIGH SPOOF RISK</span>
        </div>
        <div className="text-[11px] text-[var(--muted-foreground)]">
          Target matches brand profile with zero official registrar link.
        </div>
      </div>
    ),
    colSpan: "lg:col-span-4",
  },
  {
    title: "PLAIN-LANGUAGE EXPLANATIONS",
    tagline: "Editorial Clarity for Any Reader",
    desc: "Receive clear, straightforward rationales free of impenetrable jargon, explaining exactly what you should understand and do next.",
    badge: "ACTIONABLE",
    visual: (
      <div className="pt-3 font-mono text-xs text-[var(--primary)]">
        &ldquo;Do not transfer money. This message is an impersonation designed to capture upfront fees.&rdquo;
      </div>
    ),
    colSpan: "lg:col-span-4",
  },
];

export function FeatureBento() {
  return (
    <section className="py-24 border-t border-[var(--border)] bg-[#080B12] relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center space-y-4 mb-16">
          <Badge variant="outline" className="font-mono text-xs uppercase tracking-wider border-[var(--primary)]/30 text-[var(--primary)]">
            SYSTEM CAPABILITIES &amp; ARCHITECTURE
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-[var(--foreground)]">
            Forensic Depth by Design.
          </h2>
          <p className="text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
            Every layer of TruthLens is engineered for investigative rigor, high-trust transparency, and zero black-box obscurity.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {FEATURES.map((feat, idx) => (
            <motion.div
              key={feat.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.4, delay: idx * 0.06 }}
              className={feat.colSpan}
            >
              <div className="h-full rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-7 hover:border-[var(--primary)]/40 transition-all flex flex-col justify-between group">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-[var(--primary)] uppercase tracking-wider">
                      {feat.title}
                    </span>
                    <Badge variant="outline" className="font-mono text-[10px] text-[var(--muted-foreground)]">
                      {feat.badge}
                    </Badge>
                  </div>

                  <h3 className="text-lg sm:text-xl font-bold text-[var(--foreground)]">
                    {feat.tagline}
                  </h3>

                  <p className="text-sm text-[var(--muted-foreground)] leading-relaxed">
                    {feat.desc}
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-[var(--border)]">
                  {feat.visual}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
