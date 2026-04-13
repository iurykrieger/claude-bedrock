# Spec: `/bedrock:init` — Vault Initialization Skill

> Generated via /vibeflow:gen-spec on 2026-04-13
> Source PRD: `.vibeflow/prds/bedrock-init-skill.md`

## Objective

New users can run `/bedrock:init` on any folder and get a fully scaffolded, configured Obsidian vault with connected example entities, dependency warnings, and a clear next-steps guide — zero manual setup required.

## Context

The Bedrock plugin currently has no initialization flow. Setup is implicit: skills assume directories exist, templates are in place, and the user understands the entity model. This kills adoption for anyone discovering the plugin via GitHub. The genericization effort removed company-specific references, but without an onboarding path the plugin remains inaccessible to new users.

Existing skills follow a consistent pattern: YAML frontmatter (`name`, `description`, `user_invocable`, `allowed-tools`), a `Plugin Paths` section, a `Visao Geral` overview, and phased execution. The init skill must follow this same structure.

The init skill is the **first thing a new user encounters**, so unlike existing skills (which are in Portuguese), this skill's output must adapt to the user's chosen language. The SKILL.md itself is written in English as the canonical instruction set — Claude adapts its output language based on the config.

## Definition of Done

1. **`skills/init/SKILL.md` exists** with correct frontmatter (`name: init`, `description`, `user_invocable: true`, `allowed-tools`) and follows the phased execution pattern of existing skills (Plugin Paths section, numbered phases, clear agent role statement).

2. **`.bedrock/config.json` is created** when the skill runs, containing at minimum: `version`, `language`, `preset`, `domains`, `initialized_at`, `initialized_by`. Schema is documented in the skill.

3. **All 7 entity directories are scaffolded** (`actors/`, `people/`, `teams/`, `topics/`, `discussions/`, `projects/`, `fleeting/`) with `_template.md` files copied from the plugin's `templates/` directory.

4. **5 connected example entities are generated** (1 team, 2 people, 1 actor, 1 topic, 1 project) with correct bidirectional wikilinks, hierarchical tags, proper frontmatter per template, and content adapted to the chosen preset and language.

5. **Vault-level `CLAUDE.md` is generated** describing the vault's purpose, content language, domain taxonomy, and key conventions — distinct from and non-overlapping with the plugin's `CLAUDE.md`.

6. **Dependencies are checked and reported** (graphify, confluence-to-markdown, gdoc-to-markdown) with warn-and-continue behavior: clear explanation of what each unlocks, install command provided, never blocks initialization.

7. **Idempotency is handled**: if `.bedrock/config.json` already exists, the skill detects it and offers reconfigure/skip options instead of blindly overwriting.

## Scope

- Single deliverable: `skills/init/SKILL.md`
- Interactive flow with 4 phases: language → dependencies → preset → scaffold
- 6 presets with domain mappings and example entity content defined inline
- `.bedrock/config.json` schema definition
- Vault `CLAUDE.md` generation template
- Mini-graph of 5 example entities per preset (names and content vary by preset)
- Next-steps guide printed to user after completion

## Anti-scope

- **Not** modifying existing skills to read `.bedrock/config.json` — that's a separate migration task
- **Not** localizing `_template.md` files — templates are copied as-is from the plugin; section headers remain in their original language. Future work.
- **Not** auto-installing any dependency — warn and provide commands only
- **Not** running `git init` — the user handles their own git setup
- **Not** creating discussion, fleeting, or knowledge-node example entities
- **Not** supporting vault migration from non-Bedrock vaults
- **Not** validating that Obsidian is installed or configured

## Technical Decisions

### TD1: `.bedrock/config.json` schema

```json
{
  "version": "1.0.0",
  "language": "en-US",
  "preset": "engineering",
  "domains": ["backend", "frontend", "infra", "data", "platform", "security"],
  "initialized_at": "2026-04-13",
  "initialized_by": "user@agent"
}
```

**Why `version`:** Future-proofing for schema migrations if config grows. Starts at `1.0.0` matching `plugin.json`.

**Why `domains` as explicit array:** Even when derived from a preset, storing the resolved domains allows custom modifications without losing the preset reference. Skills can read `domains` directly without needing to know preset→domain mappings.

**Trade-off:** Considered YAML (more readable in Obsidian) vs JSON. JSON chosen because it's a config file consumed by code/Claude, not a knowledge entity. Avoids YAML parsing ambiguity. Consistent with `plugin.json`.

### TD2: Template copying strategy

Read each `_template.md` from the plugin's `templates/{type}/` directory and write it to the vault's `{type}/_template.md`. No transformation — templates are copied verbatim.

**Why not translate templates?** Templates contain Dataview queries, frontmatter key patterns, and structural hints that Claude reads as-is. Translating section headers risks breaking downstream skill assumptions. The vault `CLAUDE.md` and `config.json` language setting tell Claude what language to use when _filling_ templates. The template structure itself is language-agnostic.

**Trade-off:** Users will see Portuguese section headers in `_template.md` files if they browse them in Obsidian. Acceptable for v0 — these are reference files, not user-facing content. Template localization is future work.

### TD3: Preset → example entity mapping

Each preset defines a set of example entity names, domains, and content themes. Defined inline in the SKILL.md as a lookup table rather than separate files.

**Why inline?** A single SKILL.md is easier to maintain and review. The preset data is small (6 presets × ~10 fields each). Separate preset files would add complexity without benefit.

**Preset definitions:**

| Preset | Team | People | Actor | Topic slug | Project | Domains |
|---|---|---|---|---|---|---|
| Engineering team | platform-team | alice-chen, bob-santos | billing-api | api-migration | platform-modernization | backend, frontend, infra, data, platform, security |
| Product management | product-team | carol-kim, david-mueller | analytics-dashboard | user-research-q1 | product-launch-v2 | product, design, research, analytics, growth |
| Company wiki | operations-team | emma-silva, frank-weber | internal-portal | onboarding-process | knowledge-base-rollout | engineering, product, operations, finance, hr, legal |
| Personal second brain | — (no team) | the-user (1 person) | reading-tracker | learning-rust | side-project-alpha | learning, career, projects, ideas, health, finance |
| Open source project | core-maintainers | alice-chen, bob-santos | my-oss-lib | v2-migration | v2-roadmap | core, docs, community, ci-cd, integrations |
| Custom | user-defined | user-defined | user-defined | user-defined | user-defined | user-defined |

**Personal second brain exception:** Only 1 person entity (the user themselves), no team entity. Adjusted mini-graph: 1 person, 1 actor, 1 topic, 1 project (4 entities instead of 5). The skill must handle this variant.

**Custom preset:** The skill asks the user to provide: vault name/purpose, 3-6 domain names, and optionally example entity names. If the user skips entity names, the skill generates generic ones.

### TD4: Dependency detection method

Use `Glob` to check for skill/plugin presence:

| Dependency | Check path | What it unlocks |
|---|---|---|
| graphify | `~/.claude/skills/graphify/SKILL.md` | Semantic code extraction for GitHub repos via `/bedrock:teach` |
| confluence-to-markdown | Check via Skill tool availability or `~/.claude/skills/confluence-to-markdown/` | Confluence page ingestion via `/bedrock:teach` |
| gdoc-to-markdown | Check via Skill tool availability or `~/.claude/skills/gdoc-to-markdown/` | Google Docs ingestion via `/bedrock:teach` |

**Why Glob over Bash?** Consistent with plugin conventions. If the check location is wrong (e.g., skills installed via plugins not skills directory), the warning is a false positive — acceptable since it's non-blocking.

### TD5: Vault CLAUDE.md content

The generated `CLAUDE.md` includes:
- Vault name and purpose (derived from preset or user input)
- Content language directive (e.g., "All content in this vault is written in English (en-US)")
- Domain taxonomy (the `domain/*` tags this vault uses)
- Entity type summary (quick reference of what each directory contains)
- Writing conventions specific to this vault (language, any custom rules)
- Pointer to Bedrock skills: "This vault is powered by the Bedrock plugin. Use `/bedrock:query` to search, `/bedrock:teach` to ingest, `/bedrock:preserve` to write."

**What it does NOT include:** Writing rules, tag syntax, git workflow, zettelkasten principles — all of that lives in the plugin's `CLAUDE.md` which is auto-loaded by Claude Code when the plugin is active.

### TD6: Idempotency behavior

If `.bedrock/config.json` exists when the skill runs:

1. Read and display current config (language, preset, domains)
2. Ask user: "This vault is already initialized. What would you like to do?"
   - **Reconfigure** — Update config.json and regenerate vault CLAUDE.md. Do NOT recreate directories or templates (they already exist). Do NOT touch example entities (user may have modified them).
   - **Skip** — Exit gracefully with no changes.

**Why no "full reinit" option?** Destructive re-scaffolding risks overwriting user content that evolved from example entities. If they truly want a fresh start, they can delete `.bedrock/` and the entity directories manually.

## Applicable Patterns

No `.vibeflow/patterns/` exist for this project. The following conventions are derived from the existing skills:

1. **SKILL.md frontmatter format:** `name`, `description` (multiline `>`), `user_invocable: true`, `allowed-tools` (comma-separated tool names)
2. **Plugin Paths section:** Must be the first section after the title, with the `<base_dir>` resolution pattern
3. **Phased execution:** Numbered phases (Fase 0, 1, 2...) with clear inputs/outputs per phase
4. **Agent role statement:** Bold declaration of what kind of agent this is ("You are an execution agent", "You are a setup agent")
5. **User confirmation before writes:** All entity creation goes through user confirmation (consistent with preserve skill pattern)
6. **Best-effort external calls:** MCP/tool failures are warned, never blocking (consistent with teach/query pattern)

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Plugin templates path resolution fails at runtime | Scaffold incomplete — no `_template.md` files copied | SKILL.md includes explicit `<base_dir>` resolution pattern + fallback error message with manual copy instructions |
| Example entities have broken wikilinks | Graph view doesn't light up — bad first impression | DoD check #4 explicitly requires bidirectional links; SKILL.md includes a post-scaffold verification step |
| Dependency check paths are wrong (skills installed via different mechanism) | False positive warnings annoy users | Warnings are clearly labeled as "may not be detected if installed differently" + provide manual check command |
| Personal preset has different entity count (4 vs 5) | Skill logic breaks if it assumes 5 entities | TD3 explicitly documents the variant; SKILL.md handles it as a conditional branch |
| User runs init inside an existing vault with content | Example entities could conflict with real entities | Idempotency guard (TD6) prevents re-scaffolding. For first-time init in a non-empty folder, warn but proceed (files are additive, not destructive) |
