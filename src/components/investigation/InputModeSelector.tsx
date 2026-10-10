"use client";

import * as React from "react";
import { FileText, Image as ImageIcon, Globe, FileSpreadsheet, Mic } from "lucide-react";
import { InputMode } from "@/types/investigation";

interface InputModeSelectorProps {
  currentMode: InputMode;
  onSelectMode: (mode: InputMode) => void;
  disabled?: boolean;
}

export function InputModeSelector({
  currentMode,
  onSelectMode,
  disabled = false,
}: InputModeSelectorProps) {
  const modes: { id: InputMode; label: string; icon: React.ElementType; disabled?: boolean; comingSoon?: boolean }[] = [
    { id: "text", label: "Text Message", icon: FileText },
    { id: "image", label: "Image / Screenshot", icon: ImageIcon },
    { id: "url", label: "Web URL", icon: Globe },
    { id: "pdf", label: "Document (PDF)", icon: FileSpreadsheet, disabled: true, comingSoon: true },
    { id: "audio", label: "Voice / Audio", icon: Mic, disabled: true, comingSoon: true },
  ];

  return (
    <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#080B12]">
      {modes.map((m) => {
        const Icon = m.icon;
        const isActive = currentMode === m.id;
        return (
          <button
            key={m.id}
            type="button"
            disabled={disabled || m.disabled}
            onClick={() => onSelectMode(m.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
              isActive
                ? "bg-[var(--surface-elevated)] text-[var(--primary)] font-semibold border border-[rgba(87,214,255,0.3)] shadow-sm"
                : m.disabled
                ? "text-[var(--muted-foreground)] opacity-40 cursor-not-allowed"
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface)]"
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            <span>{m.label}</span>
            {m.comingSoon && (
              <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-black/50 text-[var(--muted-foreground)] border border-[rgba(255,255,255,0.1)]">
                Soon
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
