import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/landing/SiteHeader";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TruthLens AI — Multimodal Investigation System",
  description:
    "Don't just verify. Investigate. Extract claims, analyze evidence, and detect scam signals with forensic precision.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} dark`}>
      <body className="min-h-screen bg-[var(--background)] text-[var(--foreground)] antialiased flex flex-col font-sans selection:bg-[var(--primary)]/20 selection:text-[var(--foreground)]">
        <SiteHeader />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
