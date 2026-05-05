# Spec: graph.json as Structured Index for /bedrock:ask

> Generated via /vibeflow:gen-spec on 2026-05-05
> PRD: .vibeflow/prds/ask-graph-index.md
> Budget: ≤ 4 files (from .vibeflow/index.md)

---

## Objective

Replace glob/grep-first with graph.json-first in Phase 2 of `/bedrock:ask`, making the cumulative knowledge graph the primary entity index for all vault queries.

---

## Context

### What exists today

`skills/ask/SKILL.md` has this Phase 2 flow:
1. Glob entity directories for filenames matching search terms
2. Grep for aliases and frontmatter names
3. Read up to 15 matching `.md` files
4. Follow wikilinks 1 level deep

`graph.json` is only consulted in Phase 3-G, after the LLM self-assesses vault content as insufficient. This triggers a live `/graphify` invocation — which re-extracts what is already indexed in the cumulative `graphify-out/graph.json`.

### What already works (no changes needed)

`/bedrock:preserve` Phase 0.2 already implements a Python-based atomic merge of incoming `graph.json` into `<VAULT_PATH>/graphify-out/graph.json` on every `/bedrock:teach` run. Deduplication is by `id` for nodes and `source+target+relation` for edges. This is correct and complete — the graph IS updated on every teach run.

**Conclusion:** The staleness problem stated in the PRD does not exist in the current architecture. The sole change needed is in `skills/ask/SKILL.md`.

### Why this matters now

The vault's `graph.json` contains structured nodes from ALL sources ever taught (code, Confluence, Google Docs, PDFs, papers). Nodes include `file_type`, `source_file`, `community`, and `is_god_node`. This index is ignored in Phase 2, which means:
- Cross-document connections are invisible to grep
- God-nodes (high-centrality entities bridging multiple topics) are never prioritized
- Mature vaults with large `graph.json` files still incur full directory scans

---

## Definition of Done

1. **[ ] Phase 2 reads `graph.json` before any glob/grep** — the first step of Phase 2 is `check graph.json availability`; glob/grep only runs as fallback
2. **[ ] LLM scoring instruction covers all three signals** — Phase 2 instructs the LLM to rank nodes by: label match to search terms > community resonance > god-node proximity (`is_god_node: true`)
3. **[ ] Fallback path is explicit** — Phase 2 specifies: "grep entity directories only for search terms that produced no matching graph nodes"
4. **[ ] Phase 3-G escalation condition checks graph coverage, not just file existence** — before invoking `/graphify` live, Phase 3-G assesses whether `graph.json` already covers the query domain (has nodes matching the identified entities/domains); only escalates if coverage is insufficient
5. **[ ] Nodes without `.md` counterparts are handled** — Phase 2 documents: "for nodes with no corresponding vault `.md` file, use graph metadata alone (label, community, edges) in the response"
6. **[ ] Critical Rules table is updated** — the Phase 2 read strategy change is reflected in the Critical Rules table (new rule: "Graph-first in Phase 2")
7. **[ ] No violations of conventions.md Don'ts** — no path-qualified wikilinks introduced, no flat tags, skill structure follows skill-architecture pattern (phases sequential, Critical Rules table at end)

---

## Scope

**File:** `skills/ask/SKILL.md` only.

**Changes:**

### Phase 2 — New header: "2.0 Check graph.json"

Insert a new sub-phase 2.0 before the current 2.1:

```
### 2.0 Check graph.json availability

Before glob/grep, check if the cumulative knowledge graph is available:

```bash
if [ -f "<VAULT_PATH>/graphify-out/graph.json" ] && [ -s "<VAULT_PATH>/graphify-out/graph.json" ]; then
    echo "graph_available"
else
    echo "graph_not_available"
fi
```

**If `graph_available`:**
1. Read `<VAULT_PATH>/graphify-out/graph.json` (nodes array only — skip edges to avoid context explosion on large graphs)
2. From the nodes array, extract: `id`, `label`, `file_type`, `source_file`, `community`, `is_god_node`
3. Score nodes by relevance to the search terms from Phase 1:
   - **Primary signal:** label contains or closely matches any search term
   - **Secondary signal:** node belongs to a community that contains other high-scoring nodes (community resonance)
   - **Boost:** `is_god_node: true` nodes get elevated priority when their label is even loosely relevant
4. Select top N nodes (N ≤ 15, same limit as the current entity read budget)
5. For each selected node with a non-null `source_file`:
   - Resolve the vault `.md` file: search for `<source_file basename>` in entity directories
   - If found: read the full entity file (replaces steps 2.1–2.4 for this entity)
   - If not found: record graph metadata only (label, community, edges to other nodes — use in Phase 5 response)
6. For search terms that produced zero matching graph nodes → proceed to grep (steps 2.1–2.4) for those terms only

**If `graph_not_available`:**
Skip to existing 2.1 (glob/grep). No warning needed — this is the normal path for fresh vaults.
```

### Phase 3-G — Refine escalation trigger

Replace the current "3-G.0 Check graph availability" check (which only tests file existence) with:

```
### 3-G.0 Assess graph coverage

Before escalating to a live /graphify call, assess whether the cumulative graph.json
already covers the query's relevant domain:

- From the nodes read in Phase 2.0 (if graph was available), check if nodes matching
  the identified entities and domains were found
- If the graph produced ≥ 1 relevant node for the gap identified in Phase 3.1 self-assessment
  → read those nodes' edges for structural context instead of invoking live /graphify
  → only invoke live /graphify if edges are also insufficient

This means live /graphify escalation is now a last resort, not a first response to
`needs_graphify`. The condition changes from "graph.json exists" to "graph.json
has insufficient coverage for the specific gap".
```

### Critical Rules table — add one row

```
| Graph-first in Phase 2 | Phase 2.0 always runs before glob/grep. grep is a fallback for terms with no graph representation, not the primary strategy. |
```

---

## Anti-scope

- No changes to `skills/preserve/SKILL.md` — Phase 0.2 already implements the merge correctly
- No changes to `skills/teach/SKILL.md` — already delegates graph merge to preserve
- No changes to the graphify schema, `graph.json` format, or merge logic
- No changes to Phase 1 (question analysis), Phase 4 (recency), or Phase 5 (response)
- No new config keys — `query.max_graphify_calls` is unchanged
- No deterministic scoring algorithm — LLM instruction only
- No changes to vault `.md` formats or frontmatter

---

## Technical Decisions

### Decision 1: Read only `nodes` from `graph.json`, not `edges`

**Context:** On mature vaults, `graph.json` can contain thousands of edges. Loading the full graph into context would exhaust the budget.

**Decision:** Phase 2.0 reads only the `nodes` array for initial scoring. Edges are read selectively in Phase 3-G only when structural gap analysis is needed.

**Trade-off:** We lose edge-based proximity scoring in Phase 2. Accepted — label match + community + god-node covers 90% of relevant queries. Edge traversal is preserved for Phase 3-G's deeper analysis.

### Decision 2: LLM-evaluated scoring, not deterministic

**Context:** The skill executes as an LLM prompt, not as compiled code. A deterministic algorithm (TF-IDF, BM25) written in the SKILL.md as instructions would be brittle — the LLM interprets it loosely.

**Decision:** Score with semantic instructions ("label contains or closely matches", "community resonance", "god-node boost"). This leverages the LLM's natural language understanding rather than fighting it.

**Trade-off:** Non-reproducible scoring. Accepted — consistency matters less than relevance here. The 15-entity budget is a hard constraint that limits worst-case behavior.

### Decision 3: Fallback per-term, not per-query

**Context:** graph.json may not have representation for every entity in the vault (e.g., entities created directly via `/bedrock:preserve` without a preceding `/teach`).

**Decision:** Fallback to grep on a per-search-term basis. If `graph.json` has nodes for "billing-api" but not "squad-payments", grep only for "squad-payments".

**Trade-off:** Slightly more complex Phase 2 logic. Accepted — this is the correct behavior per the PRD's intent and the user's explicit direction.

### Decision 4: No changes to preserve Phase 0.2

**Finding during spec:** `/bedrock:preserve` Phase 0.2 already implements a Python-based atomic merge of incoming `graph.json` into the cumulative `graphify-out/graph.json` on every `/teach` run. The PRD incorrectly identified this as a missing piece.

**Decision:** Scope reduced to `skills/ask/SKILL.md` only. The graph IS kept in sync.

---

## Applicable Patterns

- **`patterns/skill-architecture.md`** — Phase numbering must remain sequential (insert 2.0 before 2.1, not renumber). Critical Rules table is mandatory at the end. Sub-phases use decimal notation.
- **`patterns/skill-delegation.md`** — `/ask` remains read-only. It must NOT write to `graph.json` or any vault file. Graph reads are always via Read/Bash, never via write tools.

---

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `graph.json` is large (thousands of nodes) — reading nodes array exhausts context | Medium | Read only the `nodes` array, not edges. If the array is still too large, read up to the first 500 nodes (graph is ordered by centrality in graphify's output — high-value nodes come first) |
| LLM misreads node `source_file` paths and fails to resolve vault `.md` | Low | Use filename-only matching (basename), not full path. Fallback: grep for the node label if file resolution fails |
| Phase 3-G "coverage assessment" introduces ambiguity — LLM may skip escalation incorrectly | Medium | Preserve the "best-effort escalation" principle: when in doubt about coverage, escalate. The assessment is a soft gate, not a hard gate |
| Fresh vaults (no graph.json yet) regress | None | Phase 2.0 is gated on graph availability; fresh vaults fall through to existing glob/grep unchanged |

---

## Dependencies

None. This is a standalone modification to `skills/ask/SKILL.md`.
