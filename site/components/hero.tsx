"use client";

import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { GraphCanvas } from "@/components/graph-canvas";
import { TerminalBlock } from "@/components/terminal-block";

const INSTALL_LINES = [
  { command: "/plugin marketplace add", args: "iurykrieger/claude-bedrock" },
  { command: "/plugin install", args: "bedrock@claude-bedrock" },
  { command: "/bedrock:setup" },
];

const COPY_TEXT = `/plugin marketplace add iurykrieger/claude-bedrock
/plugin install bedrock@claude-bedrock
/bedrock:setup`;

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <GraphCanvas />

      <div className="relative z-10 text-center px-6 max-w-[740px]">
        {/* Badges */}
        <div className="flex items-center justify-center gap-3 mb-10 flex-wrap">
          <Badge>
            <svg viewBox="0 0 65 100" fill="currentColor" className="w-3 h-4.5">
              <path d="M0 71.4L18.1 0l28.1 12.2L65 53.5 37.3 100z" />
              <path d="M18.1 0L46.2 12.2 37.3 100 12.4 82.1z" fillOpacity="0.6" />
            </svg>
            Built for Obsidian
          </Badge>
          <Badge variant="secondary">
            Claude Code Plugin
          </Badge>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-[-0.04em] mb-6">
          <span
            className="bg-clip-text text-transparent"
            style={{ backgroundImage: "var(--gradient-hero)" }}
          >
            Bedrock
          </span>
        </h1>

        {/* Tagline */}
        <p className="text-lg md:text-xl text-text-secondary mb-3 leading-relaxed max-w-lg mx-auto">
          Turn any Obsidian vault into a structured Second Brain.
          <br />
          <span className="text-text-muted">
            7 entity types. 6 skills. Zero config.
          </span>
        </p>

        {/* Requires */}
        <p className="text-sm text-text-muted mb-10">
          Requires{" "}
          <a
            href="https://obsidian.md"
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-400 hover:text-purple-300 transition-colors"
          >
            Obsidian
          </a>{" "}
          and{" "}
          <a
            href="https://docs.anthropic.com/en/docs/claude-code"
            target="_blank"
            rel="noopener noreferrer"
            className="text-purple-400 hover:text-purple-300 transition-colors"
          >
            Claude Code
          </a>
        </p>

        {/* Terminal */}
        <TerminalBlock
          lines={INSTALL_LINES}
          copyText={COPY_TEXT}
          className="max-w-[540px] mx-auto mb-8"
        />

        {/* CTAs */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <a
            href="#install"
            className="inline-flex items-center gap-2 h-11 px-6 rounded-lg text-sm font-medium text-white transition-all duration-200 shadow-sm hover:shadow-md"
            style={{ backgroundImage: "var(--gradient-hero)" }}
          >
            Get Started
          </a>
          <a
            href="https://github.com/iurykrieger/claude-bedrock"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 h-11 px-6 rounded-lg text-sm font-medium border border-border text-text-secondary hover:border-border-hover hover:text-text-primary hover:bg-bg-elevated transition-colors"
          >
            View on GitHub
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Scroll hint */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-text-muted animate-bounce">
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10 3v14M5 13l5 5 5-5" />
        </svg>
      </div>
    </section>
  );
}
