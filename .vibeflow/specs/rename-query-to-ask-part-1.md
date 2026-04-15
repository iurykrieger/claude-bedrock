# Spec: /bedrock:ask — Orchestrated Vault Reader (Part 1: Core Skill Rewrite)

> Generated from: `.vibeflow/prds/rename-query-to-ask.md`
> Date: 2026-04-15

## Objective

Replace the single-pass `/bedrock:query` with `/bedrock:ask` — an orchestrator that decomposes questions into sub-queries, executes multiple `/graphify` calls, and blends graph results with vault reads for richer answers.

## Context

`skills/query/SKILL.md` (486 lines) currently has two modes: (a) a single `/graphify` delegation or (b) sequential Glob/Grep fallback. Complex questions that span multiple entities or domains require the user to invoke the skill repeatedly and mentally merge results. The graphify delegation (added in the `query-graphify-engine` spec) already works — this spec builds on it by allowing multiple graphify calls per question.

The config system (`.bedrock/config.json`) already supports structured fields (`git.strategy`). A new `query.max_graphify_calls` field follows the same convention.

## Definition of Done

1. `skills/ask/SKILL.md` exists with frontmatter `name: ask`, updated `description`, and updated trigger phrases (`"bedrock ask"`, `"bedrock-ask"`, `"/bedrock:ask"`)
2. Phase 2 implements question decomposition: the skill analyzes the question and produces 1–N sub-queries (each with a graphify mode: `query`, `explain`, or `path`), then executes them sequentially up to the configured max
3. The skill reads `query.max_graphify_calls` from `.bedrock/config.json` at invocation (Phase 0), defaulting to `3` when the config file or field is absent
4. When `graphify-out/graph.json` is missing or empty, the skill displays a `> [!warning]` callout warning the user the graph is compromised, names which command to run to rebuild it, and then proceeds with the sequential fallback (Phase 2-S)
5. `CLAUDE.md` skills table references `/bedrock:ask` instead of `/bedrock:query`; `skills/query/` directory is deleted
6. Skill structure follows the skill-architecture pattern: Plugin Paths section, phased execution, agent type declaration, Critical Rules table at the end

## Scope

### In
- Create `skills/ask/SKILL.md` — full rewrite of the skill with orchestration logic
- Delete `skills/query/` directory
- Update `CLAUDE.md` skills table (1 line: `/bedrock:query` → `/bedrock:ask`)
- **Phase 0** — Read `.bedrock/config.json` for `query.max_graphify_calls` (default 3); git pull for read-only freshness is optional
- **Phase 1** (Analyze) — Keep existing question classification logic (1.1, 1.2, 1.3). Add **1.4 Decompose into sub-queries**: based on info_type, search_terms, and explicit_entities, produce a plan of 1–N graphify invocations (each with mode + prompt). Rules:
  - Single entity, simple question → 1 `explain` call
  - Two entities, relationship question → 1 `path` call
  - Broad domain question → 1 `query` call
  - Complex question spanning multiple entities/domains → decompose into 2–3 calls (e.g., `explain` entity A + `query` relationship context + `path` A→B)
  - Never exceed `max_graphify_calls`
- **Phase 2** (Orchestrated Search) — Two paths:
  - **2-G (graph available):** Execute sub-queries sequentially. For each: invoke `/graphify` via Skill tool, parse JSON response, accumulate nodes/edges. Deduplicate nodes across calls by `id`. If a call fails (parse error, timeout), log warning and continue with remaining calls.
  - **2-S (graph unavailable):** Display `> [!warning]` callout with: "The knowledge graph is not available (`graphify-out/graph.json` missing or empty). Results will be limited to sequential vault search. Run `/graphify build` to rebuild the graph." Then execute existing sequential search logic (Glob/Grep by filename, alias, name, content).
- **Phase 2.5** (Blend) — Merge all graphify results into a unified node/edge set. Resolve nodes to vault `.md` files. Supplement with people/teams via Glob/Grep. Community exploration for broad questions. Limit: 15 entities total.
- **Phases 3–6** — Keep existing logic (wikilink cross-reference, recency prioritization, external fetch, response composition). These phases consume the richer input from Phase 2.5.
- **Critical Rules table** — Update to reflect new orchestration rules (max graphify calls, decomposition, fallback warning)

### Out (anti-scope)
- No changes to `/graphify` — consumed as-is
- No changes to other Bedrock skills (preserve, teach, compress, sync, setup)
- No graphify result caching between invocations
- No automatic graph rebuilds
- No changes to `README.md`, `index.html`, `skills/setup/SKILL.md`, or `skills/teach/SKILL.md` — those are Part 2

## Technical Decisions

### 1. Sequential sub-query execution (not parallel)

Each `/graphify` call is a Skill tool invocation. Running them sequentially allows later sub-queries to be informed by earlier results (e.g., if the first `explain` call reveals an unexpected relationship, the orchestrator could adjust). Parallel execution would be faster but would prevent this adaptive behavior.

**Trade-off:** Slower for multi-call questions (2-3x latency). Acceptable because the alternative (multiple manual `/bedrock:query` calls) is even slower and requires user effort.

### 2. Config field as `query.max_graphify_calls` (not `ask.max_graphify_calls`)

The field name uses `query` as the semantic namespace (querying the vault) rather than `ask` (the skill name). This keeps the config stable if the skill is ever renamed again.

**Trade-off:** Slight naming asymmetry (skill is `ask`, config is `query.*`). Acceptable — config keys should be semantic, not coupled to skill names.

### 3. Decomposition in Phase 1 (not Phase 2)

The sub-query plan is produced during question analysis, before any vault reads. This keeps Phase 2 focused on execution. The decomposition logic is heuristic (rule table in Phase 1.4), not LLM-driven — keeping it deterministic and fast.

**Trade-off:** Cannot adapt the plan based on intermediate results (e.g., first graphify call reveals something that changes the strategy). Acceptable for v0 — adaptive replanning is anti-scope.

## Applicable Patterns

- **skill-architecture.md** — YAML frontmatter, Plugin Paths section, phased execution, Critical Rules table. The new Phase 0 (config read) is a variation of the existing Phase 0 (git pull) pattern.
- **skill-delegation.md** — Graphify is invoked exclusively via the Skill tool. Multiple invocations follow the same contract (structured JSON output instruction appended to the prompt).
- **vault-writing-rules.md** — The skill is read-only. The warning callout for missing graph follows the vault callout conventions (`> [!warning]`).

## Risks

| Risk | Mitigation |
|---|---|
| Graphify calls are slow — 3 sequential calls could take 30+ seconds | Default max is 3; configurable down to 1. Simple questions naturally decompose into 1 call. |
| Sub-query decomposition produces redundant calls (same nodes returned twice) | Phase 2.5 deduplicates nodes by `id` before resolving to .md files |
| `.bedrock/config.json` doesn't exist in most vaults yet | Default to 3 when file or field is absent — zero config required |
| Old references to `/bedrock:query` confuse users during the transition between Part 1 and Part 2 | Part 2 should be implemented immediately after Part 1. CLAUDE.md (updated in Part 1) is the canonical reference agents read. |

## Dependencies

None — this is Part 1 (no prior spec required).
