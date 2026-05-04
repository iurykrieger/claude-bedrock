# Spec: code-graphify-bridge — Part 3 (Bridge propagation)

> Generated via /vibeflow:gen-spec on 2026-05-04
> Source PRD: `.vibeflow/prds/code-graphify-bridge.md`

## Objective

Add Phase 6.5 to `/bedrock:preserve` that propagates `vault_entity_path` to the corresponding nodes in `<VAULT_PATH>/graphify-out/graph.json`, closing the bidirectional bridge between each `code` entity and the graphify nodes it materializes.

## Context

Today the `code` ↔ `graph.json` bridge is unidirectional: the entity frontmatter carries `graphify_node_id` (vault → graph), but the node in `graph.json` has no field pointing back to the entity path. `/compress` and `/healthcheck` that need to know "does this node already have an entity?" must scan `actors/*/nodes/*.md` collecting `graphify_node_id` from all of them — costly and outside the contract.

The PRD's solution adds an optional `vault_entity_path` field on the `graph.json` node (documented in Part 1, written here in Part 3). Every `/preserve` execution that touches `code` entities updates the corresponding nodes in the graph. Atomicity follows the pattern already used by Phase 0.2 (`.staging` + `mv`). Best-effort: vaults without `graphify-out/` keep working.

This part depends on Part 1 (documented schema) and ideally Part 2 (`graphify_node_ids` array). On legacy vaults where Part 2 has not been exercised yet, this phase operates on the singular `graphify_node_id`, treating it as an array of size 1.

## Definition of Done

1. `skills/preserve/SKILL.md` has a new Phase 6.5 ("Sync graph back-pointers") inserted between Phase 5 (Bidirectional Linking) and Phase 6 (Publish).
2. Phase 6.5 iterates over every `code` entity created/updated in this run; for each one, it reads `graphify_node_ids` from frontmatter (also accepting legacy singular `graphify_node_id`), locates corresponding nodes in `<VAULT_PATH>/graphify-out/graph.json` by `id`, and writes `vault_entity_path: <path relative to VAULT_PATH>` on each.
3. Mutation of `graph.json` is atomic: writes to `graph.json.staging`, validates JSON, `mv` replaces the original. If any step fails, the original `graph.json` stays intact.
4. Phase 6.5 is best-effort: if `<VAULT_PATH>/graphify-out/graph.json` does not exist, is empty, is invalid, or no node matches the run's `graphify_node_ids`, log a warning in the report (Phase 7) and proceed to Phase 6 without failing.
5. Idempotency: running `/preserve` twice in a row over the same entities does not duplicate `vault_entity_path` (always overwrite with the current path) and does not introduce duplicates in any field of the node.
6. `<VAULT_PATH>/graphify-out/graph.json` is included in Phase 6's `git add` (Publish), so the back-pointer change lands in the same commit as the touched entities.
7. **Quality gate:** Phase 6.5 strictly follows the atomic pattern of Phase 0.2 (staging file + mv); the `/preserve` Critical Rules table gains explicit entries for Phase 6.5 (atomicity, best-effort, idempotency) following `patterns/skill-architecture.md`; no write to `graph.json` happens outside Phase 0.2 and Phase 6.5 — `patterns/skill-delegation.md` is not violated.

## Scope

- `skills/preserve/SKILL.md`:
  - Insert Phase 6.5 between Phase 5 and Phase 6.
  - Logic to read `graph.json`, locate nodes by the run's `graphify_node_ids`, atomic write via staging + mv.
  - Logic to include the modified `graph.json` in the Phase 6 `git add`.
  - Update Phase 7 (Report) to show how many nodes received a back-pointer and how many had no match.
  - Update the Critical Rules table with 3 new entries (atomicity, best-effort, idempotency for Phase 6.5).
  - Update Overview / Phase index to reflect Phase 6.5.

## Anti-scope

- **DO NOT** implement `action: merge` for `/compress` Cap 5 (out of v0 — v0.1 includes additional mutation in Phase 6.5: the `merged_into` field).
- **DO NOT** implement recompute of `.graphify_analysis.json` when stale (out of v0 — v0.1).
- **DO NOT** propagate back-pointer to non-`code` entities (concept, topic, etc.) — only `code` participates in the explicit bidirectional bridge. Other entities stay for a future iteration if demand emerges.
- **DO NOT** validate / clean orphan `vault_entity_path` (entity was deleted but the back-pointer lingered on the node) — Bedrock does not delete entities; orphan handling is a future migration problem.
- **DO NOT** create a one-shot command to populate back-pointers in existing vaults (`/bedrock:compress --rebuild-back-pointers` is v0.2 per the PRD).
- **DO NOT** modify Phase 0.2 — incoming graphify-out merge stays the same; Phase 6.5 is independent.
- **DO NOT** optimize reading of `graph.json` for large graphs (if it becomes an issue, optimize in a future iteration).

## Technical Decisions

### 1. Phase 6.5 between 5 and 6, not after 6

**Decision:** position the propagation BEFORE `git add`/`commit` so that the `graph.json` change lands in the same commit as the entities.
**Trade-off:** the alternative would be post-Phase 6 with a separate commit (`vault: sync graph back-pointers`). Rejected because (a) the visual split between "entity created" and "back-pointer applied" in history is noise without value, (b) a single commit is atomic from git's perspective — pull/push never sees an intermediate state, (c) reduces history turbulence.

### 2. Atomicity via staging + mv (same pattern as Phase 0.2)

**Decision:** write to `<VAULT_PATH>/graphify-out/graph.json.staging`, validate JSON parse, `mv` to replace the original. If the Python block fails, `mv` does not run, the original stays intact.
**Trade-off:** the alternative would be direct write with try/except in Python and explicit backup. Rejected because the atomic pattern is already established (Phase 0.2) — internal consistency matters, and `mv` on the same filesystem is atomic at the filesystem level.

### 3. Best-effort: missing `graph.json` is a warning, not an error

**Decision:** a vault without `graphify-out/graph.json` is a valid scenario (vault that never ran `/teach` or `/graphify`). Phase 6.5 detects and silently skips, with a warning in the report.
**Trade-off:** the alternative would be requiring graph.json and aborting `/preserve` if absent. Rejected — breaks legitimate flows (entity created manually, with no graphify origin). Best-effort preserves backward compat.

### 4. Backward compat reads singular `graphify_node_id` as an array

**Decision:** Phase 6.5 normalizes at parse time: `ids = entity.frontmatter.get('graphify_node_ids') or [entity.frontmatter['graphify_node_id']]` when present.
**Trade-off:** the alternative would be requiring Part 2 to be implemented first (every entity has the array). Rejected because Parts 1, 2, 3 can ship independently; Phase 6.5 works on a legacy vault where Part 2 has not yet been exercised.

### 5. Idempotency by overwrite, not skip

**Decision:** Phase 6.5 always writes `vault_entity_path` on the node (overwrite), even if it already exists. Does not check if the value changed.
**Trade-off:** the alternative would be skip if the value is already equal. Rejected for simplicity — overwrite is deterministic and covers the case where the entity was renamed (path changed). The extra cost is negligible.

### 6. Missing match does not block

**Decision:** if `graphify_node_ids` cannot find a corresponding node in `graph.json` (e.g. graphify was re-run and the old id disappeared), warn in the report and proceed. Do not fail `/preserve`.
**Trade-off:** the alternative would be aborting to force reconciliation. Rejected — `/preserve` must be robust to divergence; the symptom is visible in the report and the user decides the next step (`/compress` or re-`/teach`).

### 7. Include `graph.json` in Phase 6's `git add`

**Decision:** Phase 6 extends its staging path list with `graphify-out/graph.json`.
**Trade-off:** the alternative would be a separate stage in Phase 6.5 (`git add graphify-out/graph.json` before the commit). Rejected because Phase 6 already enumerates directories; keep a single staging point in the skill.

## Applicable Patterns

- **`patterns/skill-architecture.md`** (mandatory): new Phase 6.5 follows decimal sub-phase numbering, updates the Critical Rules table.
- **`patterns/skill-delegation.md`** (mandatory): every mutation of `graph.json` keeps being a monopoly of `/preserve` (Phase 0.2 and Phase 6.5). `/compress` and other skills DO NOT write directly.
- **`patterns/vault-writing-rules.md`** (mandatory): atomicity via staging file follows the pattern established by Phase 0.2.

## Risks

| Risk | Mitigation |
|---|---|
| Very large `graph.json` (10k+ nodes) makes read/write slow | Accepted for v0 — optimize only if it becomes observable; document the empirical limit in the `/healthcheck` report (out of scope for this spec). |
| Concurrency: two simultaneous `/preserve` runs overwrite each other | Mitigated by `git pull --rebase` in Phase 0.1 + atomic commit in Phase 6. Vaults with parallel agents need the `commit-push-pr` strategy (already supported). |
| A failure in the Python block leaves an orphan `.staging` in the vault | Defensive cleanup at the start of Phase 6.5: `rm -f <VAULT_PATH>/graphify-out/graph.json.staging` before any write. |
| `vault_entity_path` points to a deleted file (entity removed manually) | Out of scope — Bedrock does not delete entities. If the user deletes manually, `/healthcheck` should detect (future). |
| Phase 6.5 silently breaks on a vault with no `graph.json` (best-effort hides a real bug) | DoD #4 requires an EXPLICIT warning in the report (Phase 7); the user always sees when Phase 6.5 skipped. |
| `graphify_node_ids` array vs singular generates inconsistent diffs in a vault in transition | Backward compat (DoD of Part 2 + decision #4 of this spec) ensures uniform read; full consistency is achieved progressively. |

## Dependencies

- `.vibeflow/specs/code-graphify-bridge-part-1.md` — `vault_entity_path` must be documented in `entities/code.md` before being implemented.
- (Soft) `.vibeflow/specs/code-graphify-bridge-part-2.md` — backward compat in this spec works with the legacy singular form, but the final shape (array) only materializes once Part 2 is exercised. This spec can ship before or after Part 2.

