"use client";

import * as React from "react";
import { ArrowRight, Upload, Sparkles, Link2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InputMode } from "@/types/investigation";
import { InputModeSelector } from "./InputModeSelector";
import { SAMPLE_INPUT_TEXT } from "@/lib/investigation-service";

interface InvestigationInputProps {
  onStartInvestigation: (payload: { mode: InputMode; text: string; file?: File | null }) => void;
  isLoading?: boolean;
}

export function InvestigationInput({
  onStartInvestigation,
  isLoading = false,
}: InvestigationInputProps) {
  const [mode, setMode] = React.useState<InputMode>("text");
  const [inputText, setInputText] = React.useState("");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [filePreview, setFilePreview] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleSetExample = () => {
    setMode("text");
    setInputText(SAMPLE_INPUT_TEXT);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setError("File size exceeds 10MB limit.");
        return;
      }
      setSelectedFile(file);
      setError(null);
      const reader = new FileReader();
      reader.onload = (event) => {
        setFilePreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "text" && !inputText.trim()) {
      setError("Please enter or paste the message content to investigate.");
      return;
    }
    if (mode === "url" && !inputText.trim()) {
      setError("Please provide a valid web URL to investigate.");
      return;
    }
    if (mode === "image" && !selectedFile && !inputText.trim()) {
      setError("Please attach an image screenshot or enter accompanying text.");
      return;
    }

    setError(null);
    onStartInvestigation({
      mode,
      text: inputText,
      file: selectedFile,
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto rounded-xl border border-[rgba(255,255,255,0.09)] bg-[#0C111D] shadow-2xl shadow-black/70 overflow-hidden">
      {/* Investigation Console Top Header */}
      <div className="border-b border-[rgba(255,255,255,0.07)] bg-[#080B14] px-5 sm:px-7 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-400/80 inline-block" />
            <span className="h-2 w-2 rounded-full bg-amber-400/80 inline-block" />
            <span className="h-2 w-2 rounded-full bg-emerald-400/80 inline-block" />
          </div>
          <span className="h-3.5 w-px bg-[rgba(255,255,255,0.1)]" />
          <div className="font-mono text-xs text-[var(--muted-foreground)]">
            <span className="text-[var(--primary)] font-semibold">TRUTHLENS FORENSIC INTAKE</span>
            <span className="mx-1.5">/</span>
            <span>NEW CASE</span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSetExample}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono text-[var(--primary)] bg-[var(--primary)]/10 border border-[var(--primary)]/20 hover:bg-[var(--primary)]/20 transition-colors"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Try an example</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-5 sm:p-7 space-y-6">
        {/* Title prompt */}
        <div className="space-y-1">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--foreground)]">
            What should we investigate?
          </h1>
          <p className="text-xs sm:text-sm text-[var(--muted-foreground)]">
            TruthLens decomposes claims, searches evidence sources, and uncovers deceptive threat patterns.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <InputModeSelector
            currentMode={mode}
            onSelectMode={(m) => {
              setMode(m);
              setError(null);
            }}
            disabled={isLoading}
          />
          <span className="text-[11px] font-mono text-[var(--muted-foreground)]">
            {mode === "text" && "Ready to investigate"}
            {mode === "image" && "Ready to extract and investigate"}
            {mode === "url" && "Ready to investigate domain"}
          </span>
        </div>

        {/* Input Interface based on mode */}
        <div className="space-y-3">
          {mode === "text" && (
            <div className="relative">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isLoading}
                rows={5}
                placeholder="Paste a suspicious SMS, WhatsApp message, email excerpt, or promotional claim..."
                className="w-full rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#070A12] p-4 text-sm font-mono text-[var(--foreground)] placeholder:text-[var(--muted-foreground)]/60 focus:outline-none focus:ring-1 focus:ring-[var(--primary)] transition-all resize-y min-h-[140px]"
              />
              <div className="flex justify-between items-center text-[11px] font-mono text-[var(--muted-foreground)] mt-1.5 px-1">
                <span>Supports natural language assertions, URLs, and phone handles</span>
                <span>{inputText.length} chars</span>
              </div>
            </div>
          )}

          {mode === "url" && (
            <div className="space-y-3">
              <div className="relative flex items-center">
                <Link2 className="absolute left-3.5 h-4 w-4 text-[var(--primary)]" />
                <input
                  type="url"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={isLoading}
                  placeholder="https://sbi-reward-claim.example or any suspicious link..."
                  className="w-full rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#070A12] pl-10 pr-4 py-3.5 text-sm font-mono text-[var(--foreground)] placeholder:text-[var(--muted-foreground)]/60 focus:outline-none focus:ring-1 focus:ring-[var(--primary)] transition-all"
                />
              </div>
              <p className="text-xs text-[var(--muted-foreground)] font-mono">
                Inspects domain age, typosquat lookalikes, SSL anomalies, and brand impersonation.
              </p>
            </div>
          )}

          {mode === "image" && (
            <div className="space-y-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-[rgba(255,255,255,0.1)] hover:border-[var(--primary)]/40 rounded-lg p-6 sm:p-8 text-center cursor-pointer bg-[#070A12] transition-colors flex flex-col items-center justify-center space-y-2"
              >
                {filePreview ? (
                  <div className="space-y-3">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={filePreview}
                      alt="Uploaded preview"
                      className="max-h-48 rounded border border-[rgba(255,255,255,0.1)] object-contain mx-auto"
                    />
                    <p className="text-xs font-mono text-[var(--primary)]">
                      {selectedFile?.name} (Click to change)
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="p-3 rounded-full bg-[var(--surface-elevated)] text-[var(--primary)] mb-1">
                      <Upload className="h-5 w-5" />
                    </div>
                    <p className="text-sm font-medium text-[var(--foreground)]">
                      Drop screenshot here, or click to browse
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)] font-mono">
                      PNG, JPG, WEBP up to 10MB
                    </p>
                  </>
                )}
              </div>

              {/* Optional supplementary text notes */}
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Optional context note (e.g. Received via Telegram message group)..."
                className="w-full rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#070A12] px-3.5 py-2.5 text-xs font-mono text-[var(--foreground)] placeholder:text-[var(--muted-foreground)]/60 focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
              />
            </div>
          )}
        </div>

        {/* Validation Error banner */}
        {error && (
          <div className="rounded-md border border-[var(--false)]/30 bg-[var(--false)]/10 p-3 flex items-center gap-2.5 text-xs text-[var(--false)] font-mono">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Footer Action Bar */}
        <div className="pt-4 border-t border-[rgba(255,255,255,0.07)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="text-xs font-mono text-[var(--muted-foreground)] flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Ready to investigate &bull; Claims &middot; Evidence &middot; Deception signals</span>
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={isLoading}
            className="w-full sm:w-auto font-semibold gap-2 shadow-md h-11 px-7"
          >
            <span>START INVESTIGATION</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
