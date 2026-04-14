# Spec: /bedrock:query delegates graph traversal to /graphify query engine

> Generated from: `.vibeflow/prds/query-graphify-engine.md`
> Date: 2026-04-14
> Budget: ≤ 4 files (actual: 1 file)

## Objective

Replace `/bedrock:query`'s inline graph traversal (Phase 1.5 + Phase 2-G) with a delegation to `/graphify query` via the Skill tool, so the graphify engine handles all graph operations and `/bedrock:query` focuses exclusively on vault-specific post-processing.

## Context

`/bedrock:query` currently contains ~130 lines of inline graph traversal code (Phase 1.5 checking graph.json, Phase 2-G with raw networkx BFS/DFS, Phase 2.5 with direct community exploration). This duplicates what `/graphify query` already does with better capabilities (token budgets, ranked output, explain mode, path mode, save-result feedback loop).

`/bedrock:teach` was already refactored to delegate extraction to `/graphify` — it invokes via the Skill tool and receives structured output. This spec applies the same delegation pattern to the read path: graphify is the knowledge graph engine, bedrock is the vault management layer.

Reference implementation: `skills/teach/SKILL.md` Phase 2 (lines 161-203) — invokes `/graphify` via Skill tool, verifies output, passes result to next phase.

## Definition of Done

1. **No inline graph traversal code** — query SKILL.md contains zero raw networkx code, zero direct `graph.json` loading, zero BFS/DFS implementations. All graph operations are delegated to `/graphify`.
2. **Delegation via Skill tool** — Phase 2 invokes `/graphify query` (or `/graphify path`, `/graphify explain`) via the Skill tool with a structured output instruction, and parses the returned JSON.
3. **Question type routing** — Phase 1 classification maps to the correct graphify mode:
   - Relationship/status/overview → `/graphify query "<question>"` (BFS)
   - Path-finding ("how does X connect to Y") → `/graphify path "<nodeA>" "<nodeB>"`
   - Single-entity deep dive → `/graphify explain "<entity>"`
   - Broad domain questions → `/graphify query "<question>"` (BFS, then use community data from response)
4. **Sequential fallback preserved** — Phase 2-S (Glob/Grep search) still activates when `graphify-out/graph.json` doesn't exist, unchanged from current implementation.
5. **Vault post-processing preserved** — All vault-specific logic survives in Phase 2.5: node-to-.md resolution, people/teams supplement via Glob/Grep, community exploration using graphify response data. Phases 3-6 unchanged.
6. **Follows skill-architecture pattern** — Phased execution, Plugin Paths section, Critical Rules table. No structural regressions from current skill format.

## Scope

### Files to modify

1. `skills/query/SKILL.md` — the only file modified

### Changes

**Remove:**
- Phase 1.5 (Check Knowledge Graph) — the graph availability check moves into Phase 2 as a pre-condition for delegation
- Phase 2-G (Graphify Search) — all inline traversal code (2-G.1 formulate query, 2-G.2 execute graphify query with raw networkx, 2-G.3 resolve nodes, 2-G.4 supplement)
- Phase 2.5 (Explore Communities) — the inline community exploration with direct graph.json access

**Add — Phase 2 — Delegate to graphify query engine:**

Phase 2 becomes the single entry point that branches into graphify delegation (2-G) or sequential fallback (2-S).

**Phase 2.0 — Check graph availability:**
```bash
if [ -f "graphify-out/graph.json" ] && [ -s "graphify-out/graph.json" ]; then
    echo "graph_available"
else
    echo "graph_not_available"
fi
```
- If available → Phase 2-G (graphify delegation)
- If not available → Phase 2-S (sequential search, unchanged)

**Phase 2-G — Graphify Delegation (when graph available):**

2-G.1 — Route question type to graphify mode:

| Phase 1 info_type | Graphify invocation |
|---|---|
| Relationship, status, overview, history, deprecation | `/graphify query "<original_question>"` |
| Path-finding ("how does X connect to Y", with 2 explicit entities) | `/graphify path "<entityA>" "<entityB>"` |
| Single-entity deep dive ("what is X?", "explain X", 1 explicit entity) | `/graphify explain "<entity>"` |
| Broad domain ("tell me about payments domain") | `/graphify query "<question>"` |

2-G.2 — Invoke via Skill tool:

Invoke the selected graphify command via the Skill tool. In the invocation prompt, append the instruction:

```
Return ONLY a JSON object with this structure (no prose, no markdown fences):
{
  "mode": "query|path|explain",
  "start_nodes": ["node_id1", "node_id2"],
  "nodes": [
    {"id": "...", "label": "...", "source_file": "...", "community": 0, "source_location": "..."}
  ],
  "edges": [
    {"source": "...", "target": "...", "relation": "...", "confidence": "EXTRACTED|INFERRED|AMBIGUOUS", "confidence_score": 0.9}
  ],
  "communities": {
    "0": {"label": "Community Name", "node_ids": ["id1", "id2"]},
    ...
  },
  "traversal": {"mode": "bfs|dfs", "depth": 3, "budget_used": 1200}
}
```

2-G.3 — Parse response:
- Extract the JSON from the graphify Skill response
- If parsing fails (graphify returned prose instead of JSON): log warning, fall back to Phase 2-S
- Store parsed result as `graphify_result` for Phase 2.5

**Phase 2.5 — Vault-specific post-processing (restructured, applies to both 2-G and 2-S results):**

2.5.1 — Resolve graphify nodes to vault .md files (same logic as current 2-G.3, but consuming `graphify_result.nodes` instead of inline traversal output):
- For each node: match `source_file` or `label` to entity files via Glob
- Read resolved .md files (frontmatter + body) — limit: 15 entities

2.5.2 — Supplement with people/teams (same logic as current 2-G.4):
- Use Glob/Grep to search `people/` and `teams/` for search terms from Phase 1
- Merge with graphify results, respect 15 entity limit

2.5.3 — Community exploration for broad questions (replaces current Phase 2.5):
- Use `graphify_result.communities` data instead of loading graph.json directly
- For the relevant community: resolve node_ids to vault .md files
- Prioritize nodes that appear in more edges (higher connectivity)
- Limit: 10 nodes per community exploration

**No changes to Phases 3-6** — they consume the resolved `.md` entity list from Phase 2.5, same as before.

## Anti-scope

- No changes to `/graphify` skill or Python library — structured output is achieved by prompt-level instruction in the Skill tool invocation
- No changes to Phases 3-6 (wikilink cross-ref, recency, external fetch, response composition)
- No changes to Phase 2-S (sequential search fallback)
- No changes to allowed-tools in frontmatter (Skill is already listed)
- No `save-result` feedback loop in v0
- No new files created — this is a rewrite of one existing file

## Technical Decisions

### 1. Delegation via Skill tool with structured output instruction (not Python API)

**Chosen:** Invoke `/graphify query` via Skill tool, appending a JSON output instruction to the invocation prompt.

**Alternative rejected:** Call graphify Python functions directly (`from graphify.query import query`). This would be more precise but couples the skill to graphify's Python API surface, which can change. The teach skill already uses Skill tool delegation — consistency wins.

**Trade-off:** The structured output depends on graphify's LLM execution following the JSON instruction. If graphify returns prose instead of JSON, we fall back to Phase 2-S. This is acceptable — best-effort for graphify, graceful degradation to sequential search.

### 2. JSON contract defined in /bedrock:query, not in /graphify

**Chosen:** The JSON schema is defined in the query skill's invocation prompt (telling graphify what to return). Graphify doesn't need to know about the contract.

**Alternative rejected:** Modify graphify to natively support `--format json` output. This would be cleaner but violates the anti-scope (no graphify changes) and adds cross-project coupling.

**Trade-off:** The contract is implicit (prompt-based) rather than explicit (code-based). If graphify's internal output format changes significantly, the JSON instruction may need updating. Low risk — graphify's query output is structurally stable.

### 3. Fallback to Phase 2-S on graphify parse failure

**Chosen:** If graphify returns non-parseable output (prose, error, timeout), fall back to sequential Glob/Grep search instead of failing.

**Alternative rejected:** Hard-fail and ask the user to fix graphify. This would block queries unnecessarily.

**Trade-off:** The user gets a degraded but functional answer instead of nothing. The warning log tells them graphify delegation failed.

## Applicable Patterns

- **skill-delegation.md** — Core pattern. Extended from write-delegation (preserve) to read-delegation (graphify query). The delegation flow: detection → structured invocation → parse response → post-process.
- **skill-architecture.md** — Phase structure, Plugin Paths section, Critical Rules table must be preserved. Phase numbering stays sequential.
- **vault-writing-rules.md** — Not directly applicable (query is read-only), but the response composition in Phase 6 must still follow wikilink formatting and tag conventions.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Graphify returns prose instead of JSON despite instruction | Medium | Low | Phase 2-S fallback activates. Warning logged. User sees slightly degraded answer. |
| Graphify Skill tool invocation is slow (>30s) for large graphs | Low | Medium | Token budget parameter caps graphify traversal. Current inline code has the same latency characteristics. |
| Community data in graphify response is incomplete or differently structured | Low | Medium | Phase 2.5.3 is defensive — if `communities` key is missing/empty, skip community exploration and rely on node-level results. |
| Removing inline code breaks edge cases not covered by graphify | Low | High | Phase 2-S fallback covers all cases. If graphify handles fewer question types, the sequential search compensates. |
