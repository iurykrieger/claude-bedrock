# PRD: graph.json as Structured Index for /bedrock:ask

> Generated via /vibeflow:discover on 2026-05-05

## Problem

`/bedrock:ask` currently uses glob/grep on vault `.md` files as its primary read strategy in Phase 2. The cumulative `graph.json` — already populated by every `/bedrock:teach` run — is only consulted in Phase 3-G, after the LLM self-assesses vault content as insufficient. This triggers live `/graphify` calls that re-extract what is already indexed, making `/ask` slower, less precise, and token-heavy on mature vaults.

The `graph.json` captures nodes and edges from all sources ever taught: code, Confluence pages, Google Docs, PDFs, papers. It includes named concepts, entities, citations, `rationale_for` edges, community clusters, and god-nodes. This structured index is being ignored during the most critical phase of the query flow.

The root cause of staleness — the gap between vault `.md` content and `graph.json` — is a process issue: `/bedrock:teach` does not guarantee that `graph.json` is updated on every run. Fixing the read strategy without fixing the write side would leave `graph.json` perpetually stale.

## Target Audience

Bedrock plugin users with mature vaults (graph.json populated via multiple `/bedrock:teach` runs). The change is transparent to end users — it improves response quality and speed without changing the query interface.

## Proposed Solution

Two coordinated changes:

**1. `/bedrock:ask` Phase 2 — graph.json as primary filter:**
Replace glob/grep-first with graph.json-first. Score graph nodes by relevance to the query using label match + community proximity + god-node boost (LLM-evaluated, not algorithmic). Read only the vault `.md` files corresponding to top-ranked nodes. Fall back to grep only for entities with no graph representation.

**2. `/bedrock:teach` — append to graph.json on every run:**
After extracting entities from any source, `/teach` must merge its graphify output into the cumulative `graphify-out/graph.json`. This guarantees graph.json always reflects the full vault state, making it a reliable primary index.

## Success Criteria

- `/bedrock:ask` reads `graph.json` before any glob/grep in Phase 2
- Responses surface cross-document connections (e.g., a concept taught from a PDF linked to an actor from GitHub) that grep alone would miss
- Live `/graphify` escalations in Phase 3-G decrease on vaults with a populated `graph.json`
- Every `/bedrock:teach` run updates `graph.json` — the vault and the graph stay in sync

## Scope v0

- Modify `skills/ask/SKILL.md`: Phase 2 read strategy — graph.json pre-filter before glob/grep
- Modify `skills/ask/SKILL.md`: Phase 3-G escalation trigger — condition on graph.json age/coverage, not just availability
- Modify `skills/teach/SKILL.md`: append graphify output to cumulative `graphify-out/graph.json` after every teach run
- Scoring in Phase 2: LLM-evaluated semantic scoring (label match + community + god-node boost) — no deterministic algorithm

## Anti-scope

- No changes to `/bedrock:preserve`, `/bedrock:compress`, or `/bedrock:sync`
- No changes to the graphify schema or merge logic
- No UI or CLI changes
- No changes to vault `.md` file formats or frontmatter
- No deterministic/algorithmic scoring implementation — LLM instruction only
- No new config keys (reuse `query.max_graphify_calls`)

## Technical Context

### Current Phase 2 flow (skills/ask/SKILL.md)

Phase 2 runs glob/grep across entity directories (`actors/`, `people/`, `teams/`, `topics/`, `discussions/`, `projects/`, `fleeting/`) using search terms extracted in Phase 1. Up to 15 entities are read, with 1-level wikilink traversal. `graph.json` is not consulted here.

### Current Phase 3-G flow

Phase 3-G checks if `graphify-out/graph.json` exists and is non-empty. If available, it invokes `/graphify` live via the Skill tool (modes: `explain`, `path`, `query`) to fill gaps identified by LLM self-assessment. This is where the graph is first used — but it triggers re-extraction rather than reading the cumulative index.

### Proposed Phase 2 flow

```
1. Check graph.json availability
   - If available: parse nodes array (label, file_type, source_file, community, is_god_node)
   - Score nodes: LLM ranks by query relevance (label match > community resonance > god-node proximity)
   - Select top N nodes (N ≤ 15, same entity limit as today)
   - Read the vault .md files for top-ranked nodes
   - For nodes with no corresponding .md: use graph metadata alone (label, community, edges)
   - Fallback: grep entity directories for terms not covered by any graph node

2. If graph.json not available: run existing glob/grep strategy unchanged
```

### Proposed teach change

After graphify runs during `/teach`, the resulting graph fragment must be merged into `graphify-out/graph.json` (nodes deduplicated by id, edges deduplicated by source+target+relation). This is the same deduplication logic already described in Phase 3-G.3 of the current `/ask` skill — it should be extracted into a shared convention and applied consistently in `/teach`.

### graph.json node shape (reference)

```json
{
  "id": "node_id",
  "label": "Human Readable Name",
  "file_type": "code|document|paper|image",
  "source_file": "relative/path",
  "community": 0,
  "is_god_node": true
}
```

### Key files

- `skills/ask/SKILL.md` — Phase 2 (vault read strategy) and Phase 3-G (escalation trigger condition)
- `skills/teach/SKILL.md` — graphify invocation and cumulative graph merge

## Open Questions

None.
