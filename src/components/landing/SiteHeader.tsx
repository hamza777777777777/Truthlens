"use client";

import * as React from "react";
import Link from "next/link";
import { ShieldCheck, Menu, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  const [isScrolled, setIsScrolled] = React.useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-[#080B12]/85 backdrop-blur-md border-b border-[var(--border)] shadow-sm shadow-black/40 py-3"
          : "bg-transparent border-b border-transparent py-5"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand / Logo */}
        <Link
          href="/"
          className="group flex items-center gap-3 text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] rounded-md"
        >
          <div className="relative flex h-8 w-8 items-center justify-center rounded-md border border-[var(--primary)]/30 bg-[var(--surface-elevated)] text-[var(--primary)] transition-transform duration-200 group-hover:scale-105 shadow-[0_0_12px_rgba(87,214,255,0.15)]">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold tracking-tight text-base sm:text-lg text-[var(--foreground)]">
              TruthLens
            </span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-[var(--primary)] bg-[var(--primary)]/10 px-1.5 py-0.5 rounded border border-[var(--primary)]/20">
              AI
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--muted-foreground)]">
          <Link
            href="#how-it-works"
            className="transition-colors hover:text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] rounded px-1.5 py-1"
          >
            How it works
          </Link>
          <Link
            href="#capabilities"
            className="transition-colors hover:text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] rounded px-1.5 py-1"
          >
            Capabilities
          </Link>
          <Link
            href="#sample-investigation"
            className="transition-colors hover:text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] rounded px-1.5 py-1"
          >
            Sample
          </Link>
          <Link
            href="#safety"
            className="transition-colors hover:text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--primary)] rounded px-1.5 py-1"
          >
            Safety
          </Link>
        </nav>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-4">
          <Button asChild size="sm" className="font-medium gap-1.5 shadow-[0_0_15px_rgba(87,214,255,0.2)]">
            <Link href="/investigate">
              Investigate
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="inline-flex items-center justify-center rounded-md p-2 text-[var(--muted-foreground)] hover:bg-[var(--surface)] hover:text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)]"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[var(--border)] bg-[#080B12]/95 backdrop-blur-xl px-4 py-4 space-y-3 transition-all animate-in fade-in slide-in-from-top-2 duration-200">
          <nav className="flex flex-col space-y-1 text-sm font-medium">
            <Link
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-md px-3 py-2 text-[var(--muted-foreground)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]"
            >
              How it works
            </Link>
            <Link
              href="#capabilities"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-md px-3 py-2 text-[var(--muted-foreground)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]"
            >
              Capabilities
            </Link>
            <Link
              href="#sample-investigation"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-md px-3 py-2 text-[var(--muted-foreground)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]"
            >
              Sample Investigation
            </Link>
            <Link
              href="#safety"
              onClick={() => setMobileMenuOpen(false)}
              className="rounded-md px-3 py-2 text-[var(--muted-foreground)] hover:bg-[var(--surface)] hover:text-[var(--foreground)]"
            >
              Safety
            </Link>
          </nav>
          <div className="pt-2 border-t border-[var(--border)]">
            <Button asChild className="w-full" size="sm">
              <Link href="/investigate" onClick={() => setMobileMenuOpen(false)}>
                Investigate a Message
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
