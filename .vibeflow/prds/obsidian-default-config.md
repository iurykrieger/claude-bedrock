# PRD: Default Obsidian Configuration for Vault Setup

> Generated via /vibeflow:discover on 2026-04-13

## Problem
When `/bedrock:setup` initializes a vault, it creates directories, templates, example entities, and a `CLAUDE.md` — but no Obsidian configuration. Users open the vault in Obsidian and get a blank graph view where all 7 entity types look identical (grey dots). The graph view is the primary navigation tool for a Zettelkasten vault, and without color-coded entity types, the graph is nearly useless for orientation. Additionally, Obsidian defaults to Markdown links instead of wikilinks, and ships with many core plugins enabled that add UI noise for a vault managed by AI agents.

Users must manually configure link behavior, disable unnecessary plugins, and painstakingly set up 7+ color groups in the graph view — a tedious process that every single vault user repeats.

## Target Audience
Anyone who runs `/bedrock:setup` to initialize a new Bedrock-powered Obsidian vault. Both technical users (engineers using the Second Brain for service documentation) and less technical users (PMs, knowledge managers) who rely on the visual graph to navigate.

## Proposed Solution
Add a new phase to the `/bedrock:setup` skill that creates a `.obsidian/` directory with 4 opinionated default configuration files:

1. **`app.json`** — Configure wikilink mode (bare `[[name]]` style that matches Bedrock conventions), link behavior, and sensible editor defaults.
2. **`appearance.json`** — Set a clean, visually appealing theme configuration suitable for knowledge management.
3. **`graph.json`** — Preconfigure color groups for each entity type using `tag:type/actor`, `tag:type/person`, etc. with distinct, accessible colors. This is the highest-impact config — users see a colorful, meaningful graph immediately.
4. **`core-plugins.json`** — Disable all core plugins for a minimal, clean starting experience. Users can enable what they need.

Each file is created **only if it does not already exist** — never overwrite user configuration.

## Success Criteria
- A user runs `/bedrock:setup`, opens the vault in Obsidian, navigates to Graph View, and sees example entities color-coded by type without any manual configuration.
- Wikilinks work in bare `[[name]]` format by default (matching Bedrock's writing rules).
- No existing `.obsidian/` configuration is overwritten if the user re-runs setup or already has Obsidian config.

## Scope v0
- Create `.obsidian/` directory during setup (Phase 3, new sub-phase)
- Write `app.json` with wikilink mode and link behavior settings
- Write `appearance.json` with a clean default theme
- Write `graph.json` with 7 color groups (one per entity type: actor, person, team, topic, discussion, project, fleeting) using visually distinct colors
- Write `core-plugins.json` with all plugins disabled
- Idempotency: skip each file individually if it already exists (per-file check, not all-or-nothing)
- Report created/skipped files in the setup summary

## Anti-scope
- Do NOT configure community plugins (Dataview, Templater, etc.) — future enhancement
- Do NOT create `workspace.json` (layout) — too opinionated, depends on screen size
- Do NOT create `hotkeys.json` — personal preference
- Do NOT include a knowledge-node color group (knowledge-nodes live under actors, they inherit the actor color in the graph via folder proximity)
- Do NOT add colors for `status/*` or `domain/*` tags — only `type/*` in v0
- Do NOT modify the setup skill's Phase 1 (language/deps) or Phase 2 (preset) — the Obsidian config is language/preset-agnostic
- Do NOT bundle or install Obsidian themes — only configure the built-in appearance settings

## Technical Context
**Relevant patterns (from `.vibeflow/`):**
- **Skill Architecture** (`patterns/skill-architecture.md`): The setup skill follows phased execution. The new Obsidian config phase should fit between Phase 3.4 (Generate CLAUDE.md) and Phase 3.5 (Create Example Entities), or as a new Phase 3.6 after examples.
- **Vault Writing Rules** (`patterns/vault-writing-rules.md`): Tags are hierarchical (`type/actor`, `type/person`). The graph color groups query these tags directly.
- **Template Structure** (`patterns/template-structure.md`): Every template includes `tags: [type/<type>]` — this is what the graph queries will match.

**Setup skill structure** (`skills/setup/SKILL.md`, 913 lines):
- Phase 0: Idempotency check
- Phase 1: Language and dependencies
- Phase 2: Vault objective (presets)
- Phase 3: Scaffold (3.1 dirs, 3.2 templates, 3.3 config, 3.4 CLAUDE.md, 3.5 examples)
- Phase 4: Next steps guide

The new phase fits naturally as **Phase 3.6** (after examples, before next steps guide) or as a new **Phase 3.3.1** alongside the `.bedrock/config.json` creation.

**Obsidian config format:**
- `.obsidian/app.json` — JSON object with settings like `useMarkdownLinks`, `newLinkFormat`, `strictLineBreaks`
- `.obsidian/appearance.json` — JSON with `baseFontSize`, `accentColor`, `theme` (base theme), `cssTheme`
- `.obsidian/graph.json` — JSON with `colorGroups` array: each entry has `query` (search filter) and `color` (object with `a`, `r`, `g`, `b` floats 0-1)
- `.obsidian/core-plugins.json` — JSON array of enabled plugin IDs (empty array = none enabled)

**Idempotency:** Each file is checked independently. If `.obsidian/graph.json` exists but `.obsidian/app.json` doesn't, only `app.json` is created. This allows partial reconfiguration and respects user customizations.

## Open Questions
None.
