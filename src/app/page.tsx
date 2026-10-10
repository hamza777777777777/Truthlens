import * as React from "react";
import { Hero } from "@/components/landing/Hero";
import { CapabilityGrid } from "@/components/landing/CapabilityGrid";
import { InvestigationStory } from "@/components/landing/InvestigationStory";
import { SampleInvestigation } from "@/components/landing/SampleInvestigation";
import { FeatureBento } from "@/components/landing/FeatureBento";
import { SafetySection } from "@/components/landing/SafetySection";
import { FinalCTA } from "@/components/landing/FinalCTA";
import { SiteFooter } from "@/components/landing/SiteFooter";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)] selection:bg-[var(--primary)]/20 selection:text-[var(--foreground)]">
      {/* 01: Hero with Interactive Progressive Investigation Visual */}
      <Hero />

      {/* 02: Core Capabilities Bento Grid */}
      <CapabilityGrid />

      {/* 03: Scroll-Driven Forensic Investigation Story */}
      <InvestigationStory />

      {/* 04: Polished Illustrative Sample Investigation */}
      <SampleInvestigation />

      {/* 05: System Features & Architectural Bento */}
      <FeatureBento />

      {/* 06: Epistemic Safety & Status Taxonomy */}
      <SafetySection />

      {/* 07: Editorial Final Call to Action */}
      <FinalCTA />

      {/* 08: Grounded Footer */}
      <SiteFooter />
    </div>
  );
}
