"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HeroInvestigation } from "@/components/landing/HeroInvestigation";

export function Hero() {
  return (
    <section className="relative pt-24 pb-16 sm:pt-28 sm:pb-20 overflow-hidden">
      {/* Background Ambience: Subtle coordinate lines and restrained top radial wash */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_40%_at_50%_0%,rgba(87,214,255,0.08),transparent_70%)]"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Editorial Text Content */}
        <div className="mx-auto max-w-4xl text-center space-y-5">
          {/* Eyebrow badge */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="inline-flex items-center gap-2 rounded-full border border-[rgba(255,255,255,0.1)] bg-[var(--surface-elevated)]/80 px-3.5 py-1 text-xs font-mono text-[var(--muted-foreground)]"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--primary)]" />
            <span>AI-POWERED MULTIMODAL FORENSICS</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.06, ease: "easeOut" }}
            className="text-5xl sm:text-7xl lg:text-8xl font-black uppercase tracking-tight text-[var(--foreground)] leading-[0.95]"
          >
            Don&apos;t Just<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--primary)] via-[#A5B4FC] to-[var(--secondary-accent)]">
              Verify.
            </span><br />
            Investigate.
          </motion.h1>

          {/* Supporting Copy */}
          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.12, ease: "easeOut" }}
            className="mx-auto max-w-2xl text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed"
          >
            Understand what a message claims, what the evidence supports, and whether something is trying to deceive you.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.18, ease: "easeOut" }}
            className="flex flex-wrap items-center justify-center gap-4 pt-1"
          >
            <Button asChild size="lg" className="h-11 px-6 text-sm sm:text-base font-semibold shadow-md gap-2">
              <Link href="/investigate">
                Investigate a Message
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="secondary" size="lg" className="h-11 px-6 text-sm sm:text-base">
              <Link href="#how-it-works">
                See How It Works
              </Link>
            </Button>
          </motion.div>
        </div>

        {/* Hero Visual: Direct, cohesive integration closer to the headline */}
        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.24, ease: "easeOut" }}
          className="mt-10 sm:mt-12 mx-auto max-w-5xl"
        >
          <HeroInvestigation />
        </motion.div>
      </div>
    </section>
  );
}
