"use client";

import * as React from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-[var(--border)] bg-[#05070D] py-14 text-sm text-[var(--muted-foreground)]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          {/* Brand */}
          <div className="space-y-2">
            <Link
              href="/"
              className="flex items-center gap-2.5 text-foreground hover:opacity-90 transition-opacity"
            >
              <div className="flex h-7 w-7 items-center justify-center rounded border border-[var(--primary)]/30 bg-[var(--surface-elevated)] text-[var(--primary)]">
                <ShieldCheck className="h-3.5 w-3.5" />
              </div>
              <span className="font-semibold tracking-tight text-base text-[var(--foreground)]">
                TruthLens<span className="text-[var(--primary)] text-xs font-mono ml-1 uppercase">AI</span>
              </span>
            </Link>
            <p className="text-xs text-[var(--muted-foreground)] max-w-sm">
              Multimodal investigation platform engineered for deep claim verification, evidence intelligence, and scam signal analysis.
            </p>
          </div>

          {/* Navigation Links (only anchors/pages that exist) */}
          <nav className="flex flex-wrap items-center gap-6 sm:gap-8 text-xs font-medium font-mono">
            <Link
              href="#how-it-works"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              How it works
            </Link>
            <Link
              href="#capabilities"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              Capabilities
            </Link>
            <Link
              href="#sample-investigation"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              Sample Investigation
            </Link>
            <Link
              href="#safety"
              className="transition-colors hover:text-[var(--foreground)]"
            >
              Safety &amp; Humility
            </Link>
            <Link
              href="/investigate"
              className="text-[var(--primary)] hover:underline"
            >
              Investigate
            </Link>
          </nav>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[var(--muted-foreground)]">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[var(--verified)]" />
            <span>Forensic Intelligence Pipeline: Active</span>
          </div>
          <div>
            &copy; 2026 TruthLens AI. Calm Forensic Intelligence.
          </div>
        </div>
      </div>
    </footer>
  );
}
