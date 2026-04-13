# Project: claude-bedrock
> Analyzed: 2026-04-13
> Stack: Claude Code plugin · Markdown · YAML frontmatter · Obsidian
> Type: library (Claude Code plugin for Obsidian vault automation)
> Suggested budget: ≤ 4 files per task

## Structure
This is a Claude Code plugin, not a traditional codebase. It consists entirely of markdown files: skill definitions (procedural prompts), entity definitions (semantic references), and templates (frontmatter schemas). The plugin automates Obsidian vault management with 7 entity types following adapted Zettelkasten principles.

## Structural Units
- `skills/` — 6 skill definitions (query, teach, preserve, compress, sync, setup) — the behavioral layer
- `entities/` — 9 entity type definitions (actor, person, team, topic, discussion, project, fleeting, knowledge-node, sources-field) — the semantic layer
- `templates/` — 7 entity templates with frontmatter schemas — the structural layer
- `.claude-plugin/` — plugin manifest (plugin.json)

## Pattern Registry

<!-- vibeflow:patterns:start -->
patterns:
  - file: patterns/skill-architecture.md
    tags: [skill, plugin, claude-code, phased-execution, markdown]
    modules: [skills/]
  - file: patterns/entity-definition.md
    tags: [entity, definition, classification, zettelkasten, semantic]
    modules: [entities/]
  - file: patterns/template-structure.md
    tags: [template, frontmatter, obsidian, vault, schema]
    modules: [templates/]
  - file: patterns/skill-delegation.md
    tags: [delegation, preserve, write-point, skill-interaction, workflow]
    modules: [skills/]
  - file: patterns/vault-writing-rules.md
    tags: [vault, writing, frontmatter, wikilinks, tags, git, conventions]
    modules: [entities/, templates/, skills/]
<!-- vibeflow:patterns:end -->

## Pattern Docs Available
- [patterns/skill-architecture.md](patterns/skill-architecture.md) — How skills are structured: YAML frontmatter, phased execution, Plugin Paths, critical rules table
- [patterns/entity-definition.md](patterns/entity-definition.md) — How entity types are defined: What/When/When NOT/Distinguish/Zettelkasten role
- [patterns/template-structure.md](patterns/template-structure.md) — How templates define frontmatter schemas with inline comments and bidirectional link refs
- [patterns/skill-delegation.md](patterns/skill-delegation.md) — Single write point: all skills delegate entity writes to /bedrock:preserve
- [patterns/vault-writing-rules.md](patterns/vault-writing-rules.md) — Comprehensive vault writing conventions: language, wikilinks, tags, update rules, git

## Key Files
- `CLAUDE.md` — Project instructions: writing rules, entity types, tags, git workflow, zettelkasten principles
- `README.md` — Installation guide, plugin overview, vault structure
- `.claude-plugin/plugin.json` — Plugin manifest (name, version, author, keywords)
- `skills/preserve/SKILL.md` — Single write point for all vault modifications (535 lines)
- `skills/teach/SKILL.md` — External source ingestion with graphify integration (654 lines)
- `skills/query/SKILL.md` — Read-only vault search with graphify graph traversal (486 lines)
- `skills/sync/SKILL.md` — Multi-mode re-sync (sources, people, github) (1,056 lines)
- `skills/compress/SKILL.md` — Deduplication, consolidation, and health report (456 lines)
- `skills/setup/SKILL.md` — Interactive vault initialization wizard (913 lines)
- `entities/actor.md` — Actor entity definition (systems/services with repos and deployments)
- `entities/fleeting.md` — Fleeting note definition with promotion criteria pipeline
- `entities/knowledge-node.md` — Granular knowledge unit extracted from actor source code

## Dependencies (critical only)
- **Claude Code** — Runtime environment for skill execution
- **Obsidian** — Target vault consumer (humans read via Obsidian, agents write via skills)
- **graphify** (optional) — Semantic code extraction for GitHub repos; used by teach and query skills
- **confluence-to-markdown** (optional) — Confluence page ingestion for teach/sync skills
- **gdoc-to-markdown** (optional) — Google Docs ingestion for teach/sync skills

## Known Issues / Tech Debt
- `entities/knowledge-node.md` is written in Portuguese while all other entity definitions are in English — inconsistency from the genericization effort
- `skills/sync/SKILL.md` at 1,056 lines combines 3 distinct modes (sources, people, github) that could benefit from modular decomposition
- `/bedrock:compress` writes entities directly in Phase 4 rather than fully delegating to `/bedrock:preserve`, breaking the single-write-point pattern
