import type { Skill } from "@/data/skills";

interface SkillPanelProps {
  skill: Skill;
}

export function SkillPanel({ skill }: SkillPanelProps) {
  return (
    <div className="flex flex-col gap-5">
      {/* Skill name */}
      <h3 className="text-lg font-mono font-semibold text-purple-400">
        {skill.command}
      </h3>

      {/* Description */}
      <p className="text-text-secondary text-sm leading-relaxed max-w-lg">
        {skill.description}
      </p>

      {/* Video */}
      <div className="aspect-[16/10] rounded-lg border border-border bg-bg-base overflow-hidden">
        <video
          src={skill.videoPath}
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover"
        />
      </div>

      {/* Command */}
      <div>
        <p className="text-[11px] text-text-muted uppercase tracking-wider mb-2">
          Invoke with
        </p>
        <code className="inline-block px-3 py-1.5 rounded-md bg-bg-base border border-border text-purple-400 text-sm font-mono">
          {skill.command}
        </code>
      </div>
    </div>
  );
}
