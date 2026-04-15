# PRD: Rename /bedrock:query to /bedrock:ask — Orchestrated Vault Reader

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The current `/bedrock:query` skill is a thin proxy: it makes a single `/graphify` call (or falls back to sequential Glob/Grep), post-processes the result, and returns it. This produces shallow answers because there is no iterative refinement — the skill cannot decompose a complex question into sub-queries, combine graph structure with vault prose, or recover when the first graphify call misses the mark.

The name `/query` is also non-intuitive. Users think in terms of "asking" a knowledge base, not "querying" it. `/ask` is more semantic and lowers the friction for new users.

## Target Audience

Users of the Bedrock Claude Code plugin who invoke the vault reader skill to get answers from their Second Brain — typically engineers, tech leads, and PMs navigating a team's shared knowledge vault.

## Proposed Solution

1. **Rename** the skill from `/bedrock:query` to `/bedrock:ask` (directory, frontmatter name, all internal references, CLAUDE.md, plugin manifest).

2. **Redesign the skill as an orchestrator.** Instead of a single-pass approach, `/bedrock:ask`:
   - Analyzes the user's question (unchanged Phase 1).
   - Decomposes it into one or more sub-queries, each targeting a different angle (e.g., `explain` for a specific entity, `query` for a broad relationship, `path` for how two things connect).
   - Executes up to N `/graphify` calls (configurable, default 3), collecting structured results from each.
   - Blends graphify results with direct vault reads (frontmatter, wikilinks, body prose) to produce a richer, more contextualized answer.
   - When the graph is unavailable, falls back to sequential search but **warns the user** that the graph is missing/compromised and which skill to run to fix it (e.g., `/bedrock:teach` or `/graphify build`).

3. **Add a `query.max_graphify_calls` config field** to `.bedrock/config.json` (default: `3`). The skill reads this at invocation time.

## Success Criteria

- A complex question that previously required 2-3 manual `/bedrock:query` invocations is answered in a single `/bedrock:ask` call.
- When `graphify-out/graph.json` is missing or empty, the user sees a clear warning with actionable next steps.
- The rename is complete — no references to `/bedrock:query` remain in the codebase (except git history).

## Scope v0

- Rename `skills/query/` directory to `skills/ask/`
- Rewrite SKILL.md frontmatter (name, description, triggers)
- Redesign Phase 2: question decomposition into sub-queries + multi-call graphify orchestration
- Add configurable `query.max_graphify_calls` (read from `.bedrock/config.json`, default 3)
- Add explicit user warning when graph is unavailable (fallback mode), including which skill to run
- Blend graphify results with vault reads before composing the answer
- Update all references: CLAUDE.md, `.claude-plugin/plugin.json`, `.vibeflow/index.md`, `.vibeflow/conventions.md`, any pattern files that mention `query`
- Keep sequential fallback (Phase 2-S) as degraded mode

## Anti-scope

- No changes to `/graphify` itself — the graphify skill is consumed as-is
- No changes to `/bedrock:preserve`, `/bedrock:teach`, `/bedrock:compress`, `/bedrock:sync`, or `/bedrock:setup`
- No new entity types or template changes
- No UI/UX beyond the CLI skill invocation (no Obsidian plugin changes)
- No caching of graphify results between invocations
- No automatic graph rebuilds when graph is missing — only warn and suggest

## Technical Context

**Current skill:** `skills/query/SKILL.md` (486 lines), 6 phases:
1. Analyze question (classify, extract search terms)
2. Local vault search (2-G graphify delegation OR 2-S sequential fallback)
2.5. Vault-specific post-processing (resolve nodes to .md, supplement people/teams)
3. Cross-reference via wikilinks (1 level depth)
4. Prioritize by recency
5. External fetch (Confluence, GDocs, GitHub — max 3 URLs)
6. Respond to user

**What changes:** Phase 2 becomes an orchestration layer. Instead of one graphify call, the skill decomposes the question and makes up to N calls. Phase 2.5 blends results from all calls. Phases 3-6 remain structurally similar but consume richer input.

**Patterns to follow:**
- `patterns/skill-architecture.md` — YAML frontmatter, phased execution, Plugin Paths, Critical Rules table
- `patterns/skill-delegation.md` — graphify is invoked via Skill tool, never directly
- `patterns/vault-writing-rules.md` — read-only skill, never writes

**Config integration:** `.bedrock/config.json` already supports `git.strategy`. The new `query.max_graphify_calls` field follows the same pattern (top-level key with dot-separated namespace).

## Open Questions

None.
