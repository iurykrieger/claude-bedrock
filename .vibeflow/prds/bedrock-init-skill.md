# PRD: `/bedrock:init` — Vault Initialization Skill

> Generated via /vibeflow:discover on 2026-04-13

## Problem

The Bedrock plugin has no guided initialization mechanism. New users must manually create 7 directories, copy template files, understand entity types and their relationships, configure language preferences, and figure out which skill to run first. This creates significant adoption friction — especially for users outside the original context who discover the plugin via GitHub.

Today, setup is entirely implicit: skills assume directories exist, templates are in place, and the user knows the Zettelkasten model. There's no validation of dependencies (graphify, external skills), no configuration file, and no onboarding flow. A user who runs `/bedrock:teach` on a fresh folder gets errors or unexpected behavior instead of a helpful prompt to initialize first.

The genericization effort (completed separately) removed company-specific references, but without an init flow, the plugin still feels like an insider tool rather than a product anyone can adopt.

## Target Audience

Any Obsidian user installing the Bedrock plugin for the first time — engineers, PMs, CTOs, researchers, or personal knowledge workers. They may have zero familiarity with Zettelkasten, entity-based vaults, or the Bedrock skill ecosystem.

## Proposed Solution

An interactive `/bedrock:init` skill that bootstraps any folder into a fully functional Bedrock-powered Obsidian vault through a guided flow:

1. **Language selection** — Choose the vault content language (default: en-US). Stored in `.bedrock/config.json` and reflected in the generated vault CLAUDE.md. All skills read this config to determine output language.

2. **Dependency check** — Scan for required external tools and skills (graphify, confluence-to-markdown, gdoc-to-markdown, etc.). Warn about missing dependencies with clear explanations of what capabilities they unlock. Never block — the vault is usable without them.

3. **Vault objective selection** — Present a list of usage presets that configure the domain taxonomy, suggest relevant entity types, and tailor example content:
   - Engineering team knowledge base
   - Product management
   - Company wiki
   - Personal second brain
   - Open source project
   - Custom (user defines domains and focus)

4. **Scaffold creation** — Create all 7 entity directories with `_template.md` files, plus a connected set of example entities (mini-graph) tailored to the chosen preset. The user opens Obsidian and immediately sees a working graph with real relationships.

5. **Configuration persistence** — Create `.bedrock/config.json` with language, preset, domains, and any other vault-level settings. Create a vault-level `CLAUDE.md` that describes the vault's purpose, language, domains, and conventions.

6. **Next steps guide** — After scaffolding, present a clear walkthrough: how to ingest content (`/bedrock:teach`), how to query (`/bedrock:query`), how to manually create entities (`/bedrock:preserve`), and how to maintain vault health (`/bedrock:compress`).

## Success Criteria

- A user with zero Bedrock experience can run `/bedrock:init` and have a working vault in under 2 minutes
- The Obsidian graph view shows connected entities immediately after init
- All 5 existing skills work correctly on an init-scaffolded vault without errors
- `.bedrock/config.json` is created with language and preset settings
- A vault-level CLAUDE.md is generated that accurately describes the vault's purpose and conventions
- Missing dependencies are warned about with actionable installation instructions
- Example entities use proper bidirectional wikilinks, hierarchical tags, and follow all template conventions

## Scope v0

- [ ] Interactive language selection (default en-US, support pt-BR and other languages)
- [ ] Dependency scanning and warning for graphify and external skills (warn-and-continue, never block)
- [ ] Vault objective preset selection (6 presets: engineering, product, company wiki, personal, open source, custom)
- [ ] Directory scaffolding: create 7 entity directories with `_template.md` files copied from plugin templates
- [ ] `.bedrock/config.json` creation with language, preset, domains, and metadata
- [ ] Vault-level `CLAUDE.md` generation tailored to chosen preset and language
- [ ] Connected example entities (mini-graph): 1 team, 2 people, 1 actor, 1 topic, 1 project — all with bidirectional wikilinks, proper tags, and realistic content adapted to the chosen preset
- [ ] Next steps guide printed after scaffolding (skill-by-skill walkthrough)
- [ ] Idempotency guard: detect if vault is already initialized and offer to reconfigure vs. skip

## Anti-scope

- **Not** changing existing skills to read `.bedrock/config.json` (separate task — skills currently read CLAUDE.md rules)
- **Not** auto-installing dependencies (just warn and provide install commands)
- **Not** creating a web UI or interactive Obsidian plugin panel
- **Not** supporting vault migration (converting an existing non-Bedrock vault)
- **Not** creating discussion, fleeting, or knowledge-node example entities (keep the mini-graph focused)
- **Not** integrating with git init (assume the user handles their own git setup)
- **Not** handling multi-vault configurations or vault linking
- **Not** making other skills language-aware (that's downstream work after config.json exists)

## Technical Context

**Plugin structure (current):**
- `skills/` — 5 skills (query, teach, preserve, compress, sync), each with a `SKILL.md`
- `templates/` — 7 subdirectories (actors, people, teams, topics, discussions, projects, fleeting), each with `_template.md`
- `entities/` — 9 definition files describing entity semantics, classification rules, and disambiguation
- `CLAUDE.md` — Plugin-level instructions (writing rules, tags, git workflow, zettelkasten)
- `plugin.json` — Plugin metadata

**New files this skill creates in the target vault:**
- `.bedrock/config.json` — Vault configuration (language, preset, domains, metadata)
- `CLAUDE.md` — Vault-level purpose and conventions
- `actors/_template.md`, `people/_template.md`, etc. — Copied from plugin templates
- Example entities: `teams/example-team.md`, `people/alice-smith.md`, `people/bob-jones.md`, `actors/example-api.md`, `topics/YYYY-MM-onboarding-example.md`, `projects/example-project.md`

**Dependency detection approach:**
- graphify: Check if `graphify` skill is available (grep installed plugins or check `~/.claude/skills/graphify/`)
- External skills: Check for `confluence-to-markdown`, `gdoc-to-markdown` availability
- Report missing dependencies with `claude plugins add` or equivalent install command

**Preset → domain mapping:**

| Preset | Suggested domains | Entity focus |
|---|---|---|
| Engineering team | backend, frontend, infra, data, platform, security | Actors, teams, knowledge-nodes |
| Product management | product, design, research, analytics, growth | Topics, projects, discussions |
| Company wiki | engineering, product, operations, finance, hr, legal | All entity types evenly |
| Personal second brain | learning, career, projects, ideas, health, finance | Fleeting, topics, projects |
| Open source project | core, docs, community, ci-cd, integrations | Actors, topics, discussions |
| Custom | user-defined | user-defined |

**Example mini-graph structure (engineering preset):**
```
team/platform-team → members: [alice-smith, bob-jones]
people/alice-smith → team: platform-team, focal_points: [example-api]
people/bob-jones → team: platform-team
actors/example-api → team: platform-team
topics/YYYY-MM-onboarding-example → people: [alice-smith], actors: [example-api]
projects/example-project → focal_points: [alice-smith], related_actors: [example-api], related_teams: [platform-team], related_topics: [onboarding-example]
```

## Open Questions

None.
