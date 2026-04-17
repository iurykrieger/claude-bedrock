import { ExternalLink } from "lucide-react";
import { SectionHeader } from "@/components/section-header";
import { TerminalBlock } from "@/components/terminal-block";

const INSTALL_LINES = [
  { command: "/plugin marketplace add", args: "iurykrieger/claude-bedrock" },
  { command: "/plugin install", args: "bedrock@claude-bedrock" },
  { command: "/bedrock:setup" },
];

const COPY_TEXT = `/plugin marketplace add iurykrieger/claude-bedrock
/plugin install bedrock@claude-bedrock
/bedrock:setup`;

const PREREQUISITES = [
  { name: "Claude Code", href: "https://docs.anthropic.com/en/docs/claude-code" },
  { name: "Obsidian", href: "https://obsidian.md" },
  { name: "Git", href: "https://git-scm.com" },
];

export function Installation() {
  return (
    <section id="install" className="py-24 border-t border-border">
      <div className="max-w-5xl mx-auto px-6 text-center">
        <SectionHeader
          label="Get Started"
          title="Up and running in seconds"
          subtitle="Three commands. That's it."
          centered
        />

        <div className="mt-14 max-w-[560px] mx-auto">
          <TerminalBlock lines={INSTALL_LINES} copyText={COPY_TEXT} />
        </div>

        {/* Prerequisites */}
        <div className="mt-8 flex items-center justify-center gap-3 flex-wrap">
          {PREREQUISITES.map((prereq) => (
            <a
              key={prereq.name}
              href={prereq.href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-bg-card px-4 py-2 text-xs text-text-secondary hover:border-border-hover hover:text-text-primary transition-colors"
            >
              {prereq.name}
            </a>
          ))}
        </div>

        {/* Docs link */}
        <a
          href="https://github.com/iurykrieger/claude-bedrock#readme"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 mt-6 text-sm text-purple-400 hover:text-purple-300 transition-colors"
        >
          Read the docs
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </section>
  );
}
