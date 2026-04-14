# PRD: /bedrock:query delegates graph traversal to /graphify query engine

> Generated via /vibeflow:discover on 2026-04-14

## Problem

`/bedrock:query` currently reimplements graph traversal logic inline (Phase 1.5 + Phase 2-G): it loads `graphify-out/graph.json` with raw networkx, does BFS/DFS node matching, and builds a subgraph — all of which `/graphify query` already does better, with token budgets, ranked output, and feedback loops (`save-result`).

This creates two problems:
1. **Duplication** — the same traversal logic exists in two places (graphify SKILL.md and bedrock query SKILL.md), diverging over time as graphify evolves.
2. **Missed capabilities** — `/graphify query` has features that the inline implementation doesn't use: `explain` for single-node deep dives, `path` for shortest-path between concepts, DFS depth-limiting, and the `save-result` feedback loop that improves future queries.

`/bedrock:teach` was already refactored to delegate extraction to `/graphify`. Applying the same delegation pattern to `/query` completes the symmetry: graphify is the knowledge graph engine, bedrock is the vault management layer.

## Target Audience

AI agents running `/bedrock:query` inside Claude Code sessions. The end users are humans asking questions about their vault — they see better answers because graphify's traversal is more capable than the inline reimplementation.

## Proposed Solution

Replace Phase 1.5 and Phase 2-G of `/bedrock:query` with a delegation to `/graphify query` via the Skill tool. The graphify query returns structured JSON/YAML output (not a human-facing answer) that `/bedrock:query` parses and feeds into its existing vault-specific post-processing phases.

The flow becomes:

1. **Phase 1 — Analyze the question** (unchanged)
2. **Phase 2 — Delegate to graphify query engine** (new)
   - Invoke `/graphify query "<question>"` via Skill tool, requesting structured output (nodes, edges, communities, traversal metadata)
   - Parse the structured response
   - If graphify is not available (no graph.json), fall back to Phase 2-S (sequential Glob/Grep search) — unchanged
3. **Phase 2.5 — Vault-specific post-processing** (restructured from current 2-G.3, 2-G.4, 2.5)
   - Resolve graphify nodes to vault `.md` files
   - Supplement with Glob/Grep for people/teams not in the graph
   - Community exploration for broad questions (using graphify community data from the structured response)
4. **Phases 3–6** — unchanged (wikilink cross-ref, recency, external fetch, response composition)

## Success Criteria

- `/bedrock:query` produces answers of equal or better quality compared to the current inline implementation
- Graph traversal logic is fully removed from query SKILL.md — no raw networkx code, no direct graph.json loading
- The sequential fallback (Phase 2-S) still works when graphify-out/graph.json doesn't exist
- `/graphify query` returns a documented structured format that `/bedrock:query` can reliably parse
- The `explain` and `path` graphify modes are usable from `/bedrock:query` when the question type matches

## Scope v0

1. Define the structured output contract (JSON schema) that `/graphify query` returns when invoked by another skill
2. Rewrite Phase 1.5 + Phase 2-G in `/bedrock:query` to invoke `/graphify query` via Skill tool
3. Rewrite Phase 2.5 (community exploration) to use community data from the graphify response instead of loading graph.json directly
4. Map question types from Phase 1 to graphify query modes:
   - Relationship/status/overview → `/graphify query` (BFS)
   - Path-finding ("how does X connect to Y") → `/graphify path`
   - Single-entity deep dive → `/graphify explain`
   - Broad domain questions → `/graphify query` + community data from response
5. Keep Phase 2-S (sequential search) as fallback — no changes
6. Keep Phases 3–6 (wikilink cross-ref, recency, external fetch, response) — only adjust input to consume graphify's structured output instead of inline traversal output

## Anti-scope

- **No changes to `/graphify query` Python library code** — the structured output is achieved by prompt-level instruction to graphify, not by modifying the graphify Python package
- **No changes to Phases 3–6 logic** — only their input source changes (from inline traversal to graphify response)
- **No changes to Phase 2-S** (sequential search fallback)
- **No new entity types or templates**
- **No changes to `/bedrock:preserve`** or any write-path skill
- **No graphify installation or version management changes**
- **No `save-result` feedback loop integration** in v0 — this is a future enhancement after the delegation pattern is proven

## Technical Context

### Existing patterns to follow
- **Skill delegation pattern** (`.vibeflow/patterns/skill-delegation.md`): all vault writes delegate to `/bedrock:preserve`. This PRD applies the same principle to reads: graph traversal delegates to `/graphify query`.
- **Skill architecture pattern** (`.vibeflow/patterns/skill-architecture.md`): phased execution, Plugin Paths section, Critical Rules table.
- **`/bedrock:teach` → `/graphify` delegation**: the teach skill already invokes `/graphify` via Skill tool for extraction. The query delegation follows the same mechanism.

### Key files
- `skills/query/SKILL.md` — the skill to modify (486 lines currently)
- `~/.claude/skills/graphify/SKILL.md` — the graphify skill (query section starts at line 917)
- `.vibeflow/patterns/skill-delegation.md` — delegation pattern reference

### Constraints
- `/graphify query` today outputs human-readable traversal text. The structured JSON output needs to be requested via the Skill tool invocation prompt (telling graphify to return JSON instead of prose).
- The graphify query engine uses networkx under the hood — the structured output should expose: matched nodes (with labels, source_file, community), edges (with relation, confidence), and traversal metadata (mode, start nodes, budget used).
- People and teams are vault-only entities not present in graphify's graph — the Glob/Grep supplement step is essential and must remain.

## Open Questions

None.
