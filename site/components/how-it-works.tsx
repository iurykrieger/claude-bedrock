"use client";

import { SectionHeader } from "@/components/section-header";
import { AnimateIn } from "@/components/animate-in";

const NARRATIVE_STEPS = [
  {
    number: "01",
    title: "Teach it your sources",
    description:
      "Point Bedrock at a Confluence page, a GitHub repo, a Google Doc, or a CSV. It reads the source, extracts entities — people, systems, teams, topics — and classifies them automatically.",
    command: "/bedrock:teach",
    videoPath: "/videos/teach.mp4",
    accent: "purple" as const,
  },
  {
    number: "02",
    title: "It preserves the knowledge",
    description:
      "Every entity is written to your vault with structured YAML frontmatter, hierarchical tags, and bidirectional wikilinks. One single write point — no conflicts, no duplicates, no orphans.",
    command: "/bedrock:preserve",
    videoPath: "/videos/preserve.mp4",
    accent: "orange" as const,
  },
  {
    number: "03",
    title: "Compress and maintain",
    description:
      "Over time, knowledge drifts. Compress scans your vault for duplicates, broken links, stale content, and entity misalignment — then heals it. Your Second Brain stays clean.",
    command: "/bedrock:compress",
    videoPath: "/videos/compress.mp4",
    accent: "purple" as const,
  },
  {
    number: "04",
    title: "Ask anything, anytime",
    description:
      "Once your Second Brain is established, query it from any Claude session. Ask about systems, people, decisions, or dependencies — Bedrock searches the graph, cross-references entities, and answers with linked context.",
    command: "/bedrock:ask",
    videoPath: "/videos/ask.mp4",
    accent: "orange" as const,
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 border-t border-border">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeader
          label="How It Works"
          title="Teach, preserve, compress, ask"
          subtitle="Four steps to turn scattered knowledge into a living, queryable graph."
        />

        <div className="mt-16 space-y-20">
          {NARRATIVE_STEPS.map((step, i) => (
            <AnimateIn key={step.number} delay={i * 0.1}>
              <div
                className={`flex flex-col gap-8 ${
                  i % 2 === 1 ? "md:flex-row-reverse" : "md:flex-row"
                } items-center`}
              >
                {/* Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-4">
                    <span
                      className={`text-xs font-mono font-bold tracking-wider ${
                        step.accent === "purple"
                          ? "text-purple-500"
                          : "text-orange-500"
                      }`}
                    >
                      {step.number}
                    </span>
                    <div
                      className={`h-px flex-1 ${
                        step.accent === "purple"
                          ? "bg-purple-500/20"
                          : "bg-orange-500/20"
                      }`}
                    />
                  </div>

                  <h3 className="text-2xl font-bold mb-3">{step.title}</h3>

                  <p className="text-text-secondary leading-relaxed mb-5 max-w-md">
                    {step.description}
                  </p>

                  <code
                    className={`inline-block px-3 py-1.5 rounded-md bg-bg-base border text-sm font-mono ${
                      step.accent === "purple"
                        ? "border-purple-500/20 text-purple-400"
                        : "border-orange-500/20 text-orange-400"
                    }`}
                  >
                    {step.command}
                  </code>
                </div>

                {/* Video */}
                <div className="flex-1 min-w-0 w-full">
                  <div
                    className={`rounded-xl border overflow-hidden ${
                      step.accent === "purple"
                        ? "border-purple-500/15"
                        : "border-orange-500/15"
                    }`}
                  >
                    <video
                      src={step.videoPath}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </AnimateIn>
          ))}
        </div>
      </div>
    </section>
  );
}
