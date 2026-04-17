"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { SectionHeader } from "@/components/section-header";
import { skills } from "@/data/skills";

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);
  const active = skills[activeStep];

  return (
    <section id="how-it-works" className="py-24 border-t border-border">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeader
          label="How It Works"
          title="Six skills, one workflow"
          subtitle="Set up your vault, ingest knowledge from any source, and let Bedrock keep it organized."
        />

        {/* Stepper */}
        <div className="mt-14 overflow-x-auto pb-2 -mx-6 px-6">
          <div className="flex items-center gap-0 min-w-max">
            {skills.map((skill, i) => (
              <div key={skill.id} className="flex items-center">
                <button
                  onClick={() => setActiveStep(i)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setActiveStep(i);
                    }
                  }}
                  className={cn(
                    "flex flex-col items-center text-center px-5 py-3 rounded-xl transition-all duration-200 min-w-[120px]",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base",
                    i === activeStep
                      ? "bg-purple-500/10 border border-purple-500/25 text-purple-400"
                      : "border border-transparent text-text-muted hover:text-text-secondary hover:bg-bg-elevated"
                  )}
                >
                  <span className="text-xl mb-1.5">{skill.icon}</span>
                  <span className="text-xs font-mono font-medium">
                    {skill.name}
                  </span>
                </button>
                {i < skills.length - 1 && (
                  <span className="text-text-muted/30 mx-1 text-sm select-none">
                    &rarr;
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Panel */}
        <div className="mt-6 rounded-xl border border-border bg-bg-card p-6 md:p-8">
          <div className="flex items-start gap-4">
            <span className="text-2xl flex-shrink-0 mt-0.5">{active.icon}</span>
            <div>
              <h3 className="text-lg font-semibold mb-2">{active.shortDescription}</h3>
              <p className="text-text-secondary text-sm leading-relaxed mb-4">
                {active.description}
              </p>
              <code className="inline-block px-3 py-1.5 rounded-md bg-bg-base border border-border text-purple-400 text-sm font-mono">
                {active.command}
              </code>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
