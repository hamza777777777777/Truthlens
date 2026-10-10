"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function FinalCTA() {
  return (
    <section className="relative py-28 sm:py-36 border-t border-[var(--border)] bg-[#080B12] overflow-hidden text-center">
      {/* Background radial accent */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(87,214,255,0.08),transparent_60%)]"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="space-y-4">
          <p className="font-mono text-xs uppercase tracking-widest text-[var(--muted-foreground)]">
            DECISIVE INTELLIGENCE
          </p>
          <h2 className="text-4xl sm:text-6xl lg:text-7xl font-black uppercase tracking-tight text-[var(--foreground)] leading-[0.98]">
            Before you trust<br />
            the message,<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--primary)] via-[#A5B4FC] to-[var(--secondary-accent)]">
              Investigate it.
            </span>
          </h2>
        </div>

        <p className="mx-auto max-w-xl text-base sm:text-lg text-[var(--muted-foreground)] leading-relaxed">
          Unmask false assertions, detect hidden scam vectors, and ground your decisions in auditable evidence.
        </p>

        <div className="pt-2">
          <Button asChild size="lg" className="h-13 px-8 text-base font-semibold shadow-[0_0_28px_rgba(87,214,255,0.28)] gap-2">
            <Link href="/investigate">
              Start an Investigation
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
