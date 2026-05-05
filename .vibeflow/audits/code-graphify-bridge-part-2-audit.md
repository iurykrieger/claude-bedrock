# Audit Report: code-graphify-bridge — Part 2 (Classification rewrite)

**Verdict: PASS**

> Audited: 2026-05-05
> Spec: `.vibeflow/specs/code-graphify-bridge-part-2.md`
> Files in scope: `skills/preserve/SKILL.md`, `skills/teach/SKILL.md`
> Implementation merged via PR #27 (commit `ba6ff21`).

## DoD Checklist

- [x] **1. `actor_context` in input protocol; `file_type=document/paper` → `code` with `node_type ∈ {concept, decision}`** —
  - `skills/preserve/SKILL.md:318` adds `actor_context: <actor-name>` as an optional top-level header in Phase 1.1's structured input format. Backward compat for callers without the field at line 341 ("If the input is a bare list (no `entities:` key, no `actor_context`), accept it as a list of entities with `actor_context = null`").
  - `skills/preserve/SKILL.md:385` documents `actor_context` in the Phase 1.3 graphify-output input shape.
  - `skills/preserve/SKILL.md:425-430` Phase 1.3 step 6 splits classification into the `actor_context` present branch (file_type=document/paper → `code` with `node_type ∈ {concept, decision}`, heuristic from `rationale_for` edges or label markers ADR/RFC/etc.) vs absent branch (corpus-agnostic).

- [x] **2. Semantic grouping BEFORE filtering** — `skills/preserve/SKILL.md:413` Phase 1.3 step 5 explicitly titled "Group nodes by semantic similarity (BEFORE filtering and classification)". Union-find clustering by `semantically_similar_to ≥ code.cluster_threshold` (line 415) OR community co-membership guarded by god-node/edge_count (line 416). Fallback when `.graphify_analysis.json` absent or stale: similarity-only (line 417). Cluster's `member_node_ids[]` becomes the `graphify_node_ids` array of the resulting `code` entity (line 419). Defensive hard cap of 50 per cluster (line 420).

- [x] **3. Config keys with documented defaults; per-actor cap; no global cap** —
  - `skills/preserve/SKILL.md:408-411` Phase 1.3 step 4 reads `<VAULT_PATH>/.bedrock/config.json: code.max_per_actor` (default 200) and `code.cluster_threshold` (default 0.85). Silent default fallback when config missing.
  - `skills/preserve/SKILL.md:446` Phase 1.3 step 7 applies the cap **per actor**, not globally. Critical Rule 25 reaffirms: "There is NO absolute global cap on the number of `code` entities in the vault."

- [x] **4. New relevance filter; ranking order; English keyword regex removed** —
  - `skills/preserve/SKILL.md:441-446` Phase 1.3 step 7 inclusion predicate: `confidence ∈ {EXTRACTED, INFERRED}` AND (`is_god_node` OR `degree > community_average_degree` OR `edge_count ≥ 2`). Ranking inside cap: `is_god_node` (true first) > `degree` > `edge_count`.
  - English keyword regex (`Service|Controller|Client|Factory|Handler|Mapper|Gateway|Provider`) verified REMOVED from runtime logic. Grep confirmed only 1 occurrence in the entire skill — that single occurrence is in Critical Rule 27 documenting the removal: "the previous label allowlist (`Service|Controller|Client|Factory|Handler|Mapper|Gateway|Provider`) is REMOVED."
  - Trivial label exclusion (Test/Mock/Builder/Stub/Fixture) preserved per spec (line 444).

- [x] **5. Read both schemas; always write array** —
  - Phase 2.1 read (`skills/preserve/SKILL.md:535`): "accept both the new array form and the legacy singular `graphify_node_id` string; normalize to a set of ids per entity".
  - Phase 2.2 match rule 5 (`skills/preserve/SKILL.md:547`): set intersection across both forms.
  - Phase 4.1.2 write (`skills/preserve/SKILL.md:677-678`): "Fill `graphify_node_ids` (array — always written as a list, even of size 1) ... if the input still carries the legacy singular `graphify_node_id` (string), normalize it to `graphify_node_ids: [<id>]` before writing. Never persist the singular form."
  - Critical Rule 26 enforces: "`graphify_node_ids` is always written as an array — even when the cluster has a single member."
  - Phase 6.5 (Part 3 territory but cross-cuts here) at `skills/preserve/SKILL.md:835-838` also reads both forms.

- [x] **6. `/teach` derives `actor_context`; multi-actor abort** —
  - `skills/teach/SKILL.md:395-405` Phase 3.1.1 introduces the derivation table per `source_type`: `github-repo` and `local-dir` derive from repo/dir basename when matching an existing actor slug; `confluence`, `gdoc`, `remote-binary`, `local-file`, `manual` leave `actor_context` unset.
  - `skills/teach/SKILL.md:407-411` Multi-actor abort: scan top-level subdirectories of cloned repo; if 2+ match existing actor slugs, abort with explicit guidance and example commands for splitting. Auto-partitioning is explicitly avoided (per spec Technical Decision 2).
  - `skills/teach/SKILL.md:417-423` Phase 3.1.2 includes `actor_context` in the input passed to `/preserve`.
  - Critical Rules 548-549 in `/teach` enforce both behaviors.

- [x] **7. Quality gate** — see Pattern Compliance section below for full breakdown.

## Pattern Compliance

- [x] **`patterns/skill-architecture.md`** — followed.
  - `/preserve`: Phase numbering preserved. Phase 1.3 internal steps re-numbered 1-10 to accommodate new step 4 (config read) and step 5 (semantic grouping), but still nested within Phase 1.3. Critical Rules table extended with 5 new rows (23-27); no reorder. Total 27 → 30 (with Part 3's additions). Agent type ("execution agent") declaration unchanged.
  - `/teach`: Phase 3.1 split into 3.1.1 (derive) + 3.1.2 (build input) — decimal sub-numbering allowed by pattern. Critical Rules table extended with 2 new rows. Agent type unchanged.

- [x] **`patterns/skill-delegation.md`** — followed strictly.
  - Single-write-point preserved: `/teach` continues delegating 100% of writes to `/preserve`. The `actor_context` is a hint passed in the input, not a new write path.
  - Protocol contract additive only: `actor_context` is an optional new input field; existing callers without it continue to work (verified by spec line 341 backward compat clause).

- [x] **`patterns/vault-writing-rules.md`** (advisory) — followed.
  - Backward compat respects "never delete fields": Phase 2.1 reads legacy schema; Phase 4.1.2 writes new schema; legacy singular field is normalized in-line, no batch migration.

## Convention Violations

None detected.

## Tests

**No test runner detected** for this change. Project is markdown-only per `.vibeflow/index.md` ("This is a Claude Code plugin, not a traditional codebase. It consists entirely of markdown files"). The `hooks/` directory contains Python tests but is unrelated to this spec.

Manual sanity checks performed:
- Grep for `actor_context`: 8 occurrences in `/preserve`, 12 in `/teach` — strong presence in both.
- Grep for config keys: `code.max_per_actor` (3), `code.cluster_threshold` (3+) — used in Phase 1.3 step 4, step 5 (cluster), step 7 (cap).
- Grep for `is_god_node`: 7 occurrences — used in grouping guard (community co-membership) AND filter (relevance).
- Grep for English keyword regex pattern: 1 occurrence (only in Critical Rule 27 documenting removal).
- Grep for `Multi-actor`: 2 occurrences in `/teach` (Phase 3.1.1 abort + Critical Rule).
- Grep for `graphify_node_ids` vs singular: array form 11 occurrences in `/preserve`; singular references all in backward-compat contexts (matching, parsing, write-time normalization, Critical Rule 26).

## Anti-scope

All anti-scope items respected:
- Phase 6.5 not implemented in this Part (delivered by Part 3) ✓.
- `action: merge` not added (out of v0) ✓.
- Recompute of `.graphify_analysis.json` stale not added (still v0.1) ✓.
- Phase 0.2 not modified (still at line 102, structurally identical to pre-Part-2 state) ✓.
- `file_type=code` classification unchanged in `actor_context` absent branch (still classifies as `code` with actor inferred from path; only `file_type=document/paper` in actor_context-present branch is new behavior) ✓.
- Threshold 0.85 not empirically validated — documented as configurable (Technical Decision 3) ✓.
- No batch migration: backward compat is in-line at touch-time only (Critical Rule 26 explicit) ✓.

## Conclusion

Part 2 is complete and correct. The classification rewrite at `/preserve` Phase 1.3 successfully removes the hardcoded top-50 + English label regex filter, replacing it with caller-driven `actor_context` + semantic grouping + per-actor configurable cap. `/teach` cleanly derives `actor_context` from input and aborts on multi-actor monorepos with explicit guidance. Backward compat is robust: vaults with legacy `graphify_node_id` singular continue to be read correctly and migrate in-line as entities are touched.

Pattern compliance is strong; no convention violations detected.

**Ready to ship.**
