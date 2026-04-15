# PRD: Split /compress into /compress + /healthcheck

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The current `/bedrock:compress` skill (456 lines) conflates two fundamentally different responsibilities: **fixing vault misalignments** and **reporting vault health**. This creates three problems:

1. **You can't run diagnostics without risking writes.** Users who just want to understand vault health must invoke a skill that also proposes destructive consolidation.
2. **The alignment capabilities are incomplete.** The current compress only handles duplicate claims within the same entity type. It misses broken backlinks, fragmented concepts, miscategorized entities, undiscovered entities mentioned across files, and misnamed/split entities — all of which degrade vault quality over time.
3. **It can't run unattended.** Because health reporting and vault mutation are coupled, there's no safe way to schedule compress as a cron agent. Splitting the skills enables a tiered autonomy model: mechanical fixes run automatically, semantic fixes get queued for human review.

## Target Audience

Bedrock plugin users who maintain Obsidian vaults — both humans reading in Obsidian and AI agents writing via skills. The primary beneficiary is the vault maintainer (human or scheduled agent) who needs the vault to stay structurally coherent as it grows.

## Proposed Solution

Split `/bedrock:compress` into two independent skills:

### /bedrock:compress (rewritten) — Vault Alignment Engine

An **execution agent** focused exclusively on detecting and fixing structural misalignments in the vault. Five capabilities:

1. **Broken backlinks:** Detect missing bidirectional wikilinks (entity A links to B, but B doesn't link back to A). Fix by adding the missing backlink.
2. **Concept match:** Detect concepts fragmented across multiple files without a unifying entity. Create a `concept` entity and link the referencing files to it.
3. **Entity misalignment:** Detect entities categorized under an entity type that no longer fits (e.g., a fleeting note that should be a topic now that the entity taxonomy has evolved). Recategorize by moving the file and reprocessing via `/bedrock:preserve`.
4. **Duplicated entities:** Detect entities mentioned across many files without a proper entity file. Create the missing entity and establish backlinks.
5. **Misnamed entities:** Detect the same real-world entity referred to by different names across files (e.g., "Iury" in one file, "Iury Krieger" in another). Merge into a single entity, adding variant names as aliases.

**Autonomy model for cron execution:**
- **Autonomous (mechanical):** Capabilities 1 (broken backlinks) and 4 (duplicated entities) — deterministic, low risk. Executed without confirmation when running as a scheduled agent.
- **Queued (semantic):** Capabilities 2 (concept match), 3 (entity misalignment), and 5 (misnamed entities) — require judgment, higher risk. When running as a scheduled agent, these are detected and written as a proposal to a fleeting note for human review. When running interactively, all 5 capabilities prompt for confirmation as usual.

Delegates all writes to `/bedrock:preserve` (fixes the current anti-pattern where compress writes directly).

### /bedrock:healthcheck (new) — Vault Health Report

A **read-only agent** that generates a diagnostic report without modifying the vault. Five checks:

1. **Check graphify-out:** Verify `graphify-out/` folder exists and contains a valid `graph.json` with complete vault content.
2. **Check setup:** Verify all configurations and dependencies are properly set up (entity definitions, templates, plugin manifest, optional dependencies like graphify/confluence-to-markdown).
3. **Check orphans:** Count entities with zero inbound wikilinks from other entities.
4. **Check dangling content:** Count content that exists but has no links, no references, and no role in the knowledge graph.
5. **Check old content:** Flag entities with `updated_at` older than 15 days from the current date.

No writes, no git operations, no confirmation needed. Safe to run at any frequency.

## Success Criteria

1. `/bedrock:compress` detects and fixes all 5 misalignment types in a test vault with known issues.
2. `/bedrock:compress` runs as a scheduled agent via `/schedule`, autonomously fixing mechanical issues and queuing semantic proposals as fleeting notes.
3. `/bedrock:healthcheck` produces a complete diagnostic report without modifying any file in the vault.
4. The two skills share zero code/logic — fully independent invocations.
5. The current compress anti-pattern (direct writes bypassing `/bedrock:preserve`) is eliminated.

## Scope v0

### /bedrock:compress
- All 5 alignment capabilities (broken backlinks, concept match, entity misalignment, duplicated entities, misnamed entities)
- Tiered autonomy model (autonomous mechanical + queued semantic)
- Full delegation to `/bedrock:preserve` for all writes
- Interactive mode (user confirmation) and cron mode (autonomous + queue)
- Git pull before, commit + push after

### /bedrock:healthcheck
- All 5 checks (graphify-out, setup, orphans, dangling content, old content)
- Read-only — no writes, no git mutations
- Summary table output with actionable suggestions
- Can suggest running `/bedrock:compress` when alignment issues are detected

## Anti-scope

- **No migration of existing compress behavior.** The current duplicate-claim consolidation (Phase 2-4 of old compress) is replaced by the 5 new capabilities, not preserved alongside them.
- **No auto-fix from healthcheck.** Healthcheck reports; compress fixes. Healthcheck never writes.
- **No cross-skill orchestration.** Healthcheck does not automatically trigger compress. It may suggest it, but never invoke it.
- **No UI/dashboard.** Reports are markdown in the terminal. No Obsidian plugin views.
- **No graph.json modification.** Compress may delete orphan code entities (git rm), but never mutates graph.json itself.
- **No custom thresholds in v0.** The 15-day staleness window and other thresholds are hardcoded. Configurability is deferred.

## Technical Context

### Existing patterns to follow (from `.vibeflow/`)
- **Skill architecture** (`patterns/skill-architecture.md`): YAML frontmatter, phased execution, Plugin Paths section, critical rules table, agent type declaration.
- **Skill delegation** (`patterns/skill-delegation.md`): All writes go through `/bedrock:preserve`. The structured entity list format is the contract. This fixes the known anti-pattern where current compress writes directly.
- **Vault writing rules** (`patterns/vault-writing-rules.md`): Append-only for people/teams/topics, free merge for actors, never delete wikilinks.

### Known constraints
- Current compress is 456 lines. The rewrite will likely be larger due to the 5 capabilities + autonomy model.
- The `/schedule` skill creates cron-based remote agents. Compress needs a mode flag or detection mechanism to know if it's running interactively or as a scheduled agent.
- Entity definitions live in `entities/` within the plugin directory — compress needs to read these to make correct categorization judgments (capability 3).

### Dependencies
- `/bedrock:preserve` — write delegation target
- `/bedrock:teach` — suggested by healthcheck when graphify-out is missing/stale
- `graphify-out/graph.json` — used by healthcheck check 1
- Entity definitions (`entities/*.md`) — used by compress capabilities 2 and 3

## Open Questions

None.
