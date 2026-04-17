"use client";

import { useState, useCallback } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface TerminalLine {
  prompt?: string;
  command: string;
  args?: string;
  flag?: string;
}

interface TerminalBlockProps {
  title?: string;
  lines: TerminalLine[];
  copyText: string;
  className?: string;
}

export function TerminalBlock({
  title = "claude",
  lines,
  copyText,
  className,
}: TerminalBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(copyText);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = copyText;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [copyText]);

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-bg-base overflow-hidden transition-all duration-300",
        "hover:border-purple-500/25 hover:shadow-[0_0_24px_rgba(168,130,255,0.04)]",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-bg-elevated border-b border-border">
        <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
        <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
        <span className="flex-1 text-center text-[11px] text-text-muted font-mono mr-10">
          {title}
        </span>
      </div>

      {/* Body */}
      <div className="px-5 py-4">
        {lines.map((line, i) => (
          <div key={i} className="flex items-center gap-0 font-mono text-sm leading-8">
            <span className="text-purple-500 select-none mr-2">
              {line.prompt ?? ">"}
            </span>
            <code className="text-text-muted">{line.command}</code>
            {line.args && (
              <code className="text-text-primary ml-1">{line.args}</code>
            )}
            {line.flag && (
              <code className="text-success ml-1">{line.flag}</code>
            )}
          </div>
        ))}
      </div>

      {/* Copy */}
      <div className="flex justify-end px-4 pb-3">
        <button
          onClick={handleCopy}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-[11px] font-mono transition-colors",
            copied
              ? "border-success/30 text-success"
              : "border-border bg-bg-elevated text-text-muted hover:text-purple-400 hover:border-purple-500/30 hover:bg-purple-500/5"
          )}
        >
          {copied ? (
            <Check className="w-3.5 h-3.5" />
          ) : (
            <Copy className="w-3.5 h-3.5" />
          )}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
