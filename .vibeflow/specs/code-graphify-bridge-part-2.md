# Spec: code-graphify-bridge — Part 2 (Classification rewrite)

> Generated via /vibeflow:gen-spec on 2026-05-04
> Source PRD: `.vibeflow/prds/code-graphify-bridge.md`

## Objective

Rewrite the graphify-output classification in `/preserve` Phase 1.3 to delegate context to the caller, group semantically similar nodes before applying the cap, and use a configurable per-actor cap — replacing the hardcoded top-50 filter with English label regex.

## Context

`skills/preserve/SKILL.md:401` classifies as `code` only when `file_type=code`, under-covering the `node_type ∈ {concept, decision}` values that `entities/code.md` admits. `skills/preserve/SKILL.md:408` applies a top-~50 filter with keyword regex (`Service|Controller|Client|Factory|Handler|Mapper|Gateway|Provider`) — discards valid Go/Python/Rust nodes and ignores repo size.

The PRD's solution changes 3 things inside Phase 1.3: (1) the caller passes `actor_context` to indicate the corpus belongs to a specific actor, (2) nodes connected by `semantically_similar_to.confidence_score ≥ threshold` or community co-membership are grouped into a single `code` entity carrying every `graphify_node_ids`, (3) the cap stops being hardcoded global and becomes `code.max_per_actor` in `.bedrock/config.json` (default 200).

This part depends on Part 1 (physical template + entity schema with array). Part 3 (Phase 6.5) depends on this indirectly — it operates on the `graphify_node_ids` array.

## Definition of Done

1. `skills/preserve/SKILL.md` Phase 1.3 accepts the optional field `actor_context: <actor-name>` in the structured input; when present, every `file_type=document/paper` node from that input is classified as `code` for that actor with `node_type ∈ {concept, decision}` (heuristic from label/edges).
2. Phase 1.3 implements semantic grouping BEFORE applying filters: nodes connected by `semantically_similar_to` edges with `confidence_score ≥ <threshold>` or community co-membership (`.graphify_analysis.json`) are consolidated into a single `code` candidate whose `graphify_node_ids` is the union of the cluster's ids.
3. Phase 1.3 reads `<VAULT_PATH>/.bedrock/config.json: code.max_per_actor` (default 200) and `code.cluster_threshold` (default 0.85); the cap is applied per actor; no absolute global cap.
4. Phase 1.3 replaces the old relevance filter with: `confidence ∈ {EXTRACTED, INFERRED}` AND (`is_god_node` OR `degree > community average` OR `edge_count ≥ 2`); ranking inside the cap uses `is_god_node` > `degree` > `edge_count`. The English keyword regex is removed.
5. Phase 1.3 reads both `graphify_node_id` (legacy singular) AND `graphify_node_ids` (array) when matching against the existing vault; always writes the array form to the resulting frontmatter.
6. `skills/teach/SKILL.md` derives `actor_context` from the input when applicable (URL/path of an actor repo) and passes it in its delegation to `/preserve`. When the input contains multiple actors, abort with a clear error instructing the user to split.
7. **Quality gate:** changes to `/preserve` Phase 1.3 and `/teach` follow `patterns/skill-architecture.md` (preserve phase numbering, update each skill's Critical Rules table with the new rules, keep the agent type declaration); the changes do not violate `patterns/skill-delegation.md` (every write keeps going through `/preserve`).

## Scope

- `skills/preserve/SKILL.md` Phase 1.3:
  - Add `actor_context` to the structured input protocol (Phase 1.1 and 1.3).
  - Rewrite the classification steps (5–7 of the current Phase 1.3) to use `actor_context`.
  - Add a semantic grouping step before relevance filtering.
  - Replace the top-50 / regex filter with the confidence + community signal filter.
  - Add reading of `.bedrock/config.json: code.max_per_actor` and `code.cluster_threshold`.
  - Add backward-compat matching logic (singular + array).
  - Update the Critical Rules table to reflect the new rules.
- `skills/teach/SKILL.md`:
  - Derive `actor_context` from the input's repo name / root directory when the input is an actor repo.
  - Pass `actor_context` in the invocation to `/preserve`.
  - Detect multiple actors in a single input → abort with a clear message.

## Anti-scope

- **DO NOT** implement Phase 6.5 (Part 3 — back-pointer propagation).
- **DO NOT** implement `action: merge` in the protocol (out of v0 — moves to v0.1).
- **DO NOT** implement recompute of `.graphify_analysis.json` when stale (out of v0 — v0.1).
- **DO NOT** migrate legacy vaults in batch (touch-by-touch as entities are touched).
- **DO NOT** change Phase 0.2 (merge of incoming graphify-out) — independent of this change.
- **DO NOT** change classification logic for `file_type=code` (stays the same as today; only `file_type=document/paper` gets new treatment via `actor_context`).
- **DO NOT** empirically validate the 0.85 threshold — documented guess, configurable; tuning is for a future iteration.

## Technical Decisions

### 1. `actor_context` in the structured input, not inferred from `source_file`

**Decision:** the caller passes `actor_context: <actor-name>` explicitly; `/preserve` does not try to infer from `source_file` (`source_file.startswith(actor_path)`).
**Trade-off:** path-based inference looks elegant but is fragile in monorepos (every doc shares the root path) and in repos with embedded external libs. The caller already has this information at invocation time — `/teach` knows whether it is running against a specific actor repo or a generic corpus. Pushing the decision to the caller is more robust and eliminates the path heuristic.

### 2. Multi-actor input → error, not automatic partitioning

**Decision:** when `/teach` detects that the input contains multiple actors (e.g. a monorepo with several logical repos), abort with a message instructing the user to invoke separately.
**Trade-off:** the alternative would be for `/teach` to partition and invoke `/preserve` multiple times. Rejected for v0 — adds complexity to the caller, hides the per-actor cap trade-off (200 each × N actors can blow up the vault). A clear error forces a conscious decision.

### 3. Configurable grouping threshold, default 0.85

**Decision:** `.bedrock/config.json: code.cluster_threshold` (default 0.85); uses graphify's `semantically_similar_to.confidence_score`.
**Trade-off:** the 0.85 default is a guess — not empirically validated. Acceptable for v0 because (a) configurable provides an escape hatch without a new deploy, (b) the value can be tuned later without code change, (c) leaving it non-configurable would lock an unvalidated choice into the code. Empirical validation in a real corpus is an open question of the PRD; documented as a TODO.

### 4. Community co-membership as a complementary signal

**Decision:** grouping uses OR between `semantically_similar_to ≥ threshold` AND equal `community_id` from `.graphify_analysis.json` (when available).
**Trade-off:** graphify communities are detected from graph structure, not content — they may group nodes with weak ties. Mitigated by also requiring that both nodes appear in a shared `is_god_node` or have `edge_count ≥ 2` before merging via community. If `.graphify_analysis.json` is absent or stale, fall back to `semantically_similar_to` alone.

### 5. Per-actor cap, no global cap, no per-community cap

**Decision:** `code.max_per_actor` is the only cap. Default 200.
**Trade-off:** a per-community cap would be more "natural" (each cluster = one `code`), but communities can be unbalanced (one with 500 nodes, another with 5). Per-actor cap matches the physical grouping of the vault (`actors/<actor>/nodes/`) and gives the user a direct knob over the folder size in Obsidian.

### 6. No proactive migration of singular `graphify_node_id`

**Decision:** `/preserve` reads both at parse time (singular or array); when writing back, always writes the array. Legacy entities migrate in-line when they are touched.
**Trade-off:** the alternative would be sweeping and migrating everything in one execution. Rejected — the risk of large massive execution, unnecessary complexity. Touch-by-touch is safe and progressive.

## Applicable Patterns

- **`patterns/skill-architecture.md`** (mandatory): the changes preserve sequential phases, the Critical Rules table, and the agent type declaration.
- **`patterns/skill-delegation.md`** (mandatory): no change escapes the single write point — `/teach` keeps delegating 100% of writes to `/preserve`.
- **`patterns/vault-writing-rules.md`** (advisory): backward compat respects "never delete fields" — reading accepts the legacy schema.

## Risks

| Risk | Mitigation |
|---|---|
| The 0.85 threshold produces poor groupings on the first real corpus | Configurable via `.bedrock/config.json`; documented as a TODO for empirical validation; warn in `/preserve`'s report when many size-1 clusters appear (signal that the threshold is too high). |
| A large monorepo generates 200 code × N actors and blows up the vault | The cap applied per actor forces the user to understand the trade-off; document in the `.bedrock/config.json` template that values >200 may degrade Obsidian. |
| The `/teach` caller detects multiple actors and aborts without a clear instruction | DoD #6 requires a clear message with an example command for the split. |
| `file_type=document/paper` nodes in an actor repo that describe cross-actor patterns become `code` in the wrong actor | PRD open question #3 — for v0, this imprecision is accepted; `/compress` Cap 2 detects and moves it later (out of scope for this spec). |
| Backward compat reads the singular but rewrites everything as array, generating a massive diff on the first `/preserve` over a legacy vault | DoD #5: the migration only happens when the entity is touched for another reason (not a migration pass). |
| Stale `.graphify_analysis.json` degrades the quality of community-based grouping | Phase 1.3 uses `.graphify_analysis.json` as a "best-effort" signal; if absent or stale, grouping operates on `semantically_similar_to` alone. |

## Dependencies

- `.vibeflow/specs/code-graphify-bridge-part-1.md` — the `graphify_node_ids` (array) schema and the physical template must exist before this part is implemented.

