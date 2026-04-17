"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { SkillPanel } from "@/components/skill-panel";
import { SectionHeader } from "@/components/section-header";
import { skills } from "@/data/skills";

export function SkillsShowcase() {
  return (
    <section id="skills" className="py-24 bg-bg-card border-t border-border">
      <div className="max-w-5xl mx-auto px-6">
        <SectionHeader
          label="Skills"
          title="Everything you need to manage knowledge"
          subtitle="Each skill is a specialized agent that reads your vault conventions and acts accordingly."
        />

        <Tabs defaultValue="setup" className="mt-14">
          {/* Sidebar on desktop, horizontal tab bar on mobile */}
          <div className="flex flex-col md:flex-row gap-8">
            {/* Tab list */}
            <TabsList className="flex md:flex-col md:w-56 shrink-0 overflow-x-auto md:overflow-x-visible gap-1 pb-2 md:pb-0">
              {skills.map((skill) => (
                <TabsTrigger
                  key={skill.id}
                  value={skill.id}
                  className="justify-start text-left w-full md:px-4 md:py-3 px-3 py-2"
                >
                  <span className="mr-2.5 text-base">{skill.icon}</span>
                  <span className="font-mono text-xs">
                    <span className="hidden md:inline">{skill.command}</span>
                    <span className="md:hidden">{skill.name}</span>
                  </span>
                </TabsTrigger>
              ))}
            </TabsList>

            {/* Panels */}
            <div className="flex-1 min-w-0">
              {skills.map((skill) => (
                <TabsContent key={skill.id} value={skill.id}>
                  <SkillPanel skill={skill} />
                </TabsContent>
              ))}
            </div>
          </div>
        </Tabs>
      </div>
    </section>
  );
}
