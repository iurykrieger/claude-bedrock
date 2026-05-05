# Spec: compress-graph-broken-backlinks

> Generated via /vibeflow:gen-spec on 2026-05-04
> Source PRD: `.vibeflow/prds/compress-graph-broken-backlinks.md`
> Revised on 2026-05-04: total-binding rule (no relevance filter at /compress time).

## Objective

Extend `/compress` Capability 1 (Broken backlinks) to enforce a total-binding invariant — every node in `<VAULT_PATH>/graphify-out/graph.json` ends up with `vault_entity_path` set — by detecting unbound nodes, classifying them into three shapes (back-pointer drift, absorbable orphan, isolated orphan), and delegating every fix to `/preserve`.

## Context

Today `/compress` Cap 1 inspects only markdown wikilinks. After Parts 1-3 of `code-graphify-bridge`, the bridge between `code` entities and `graph.json` exists but is not total: nodes filtered out at `/teach` time (relevance filter, trivial labels, AMBIGUOUS confidence) remain in `graph.json` indefinitely without `vault_entity_path`.

The user requirement is unconditional: **every output graphify produces must point to a vault entity OR turn into one.** No subset is acceptable as unbound. `/compress` Cap 1 is the natural home — unbound nodes are the bidirectional-link breakage on the graph layer, exactly what Cap 1 already addresses on the markdown layer.

Three shapes of unbound nodes need binding (priority order — try them top-down per node):

- **Scenario A — back-pointer drift.** A `code` entity carries N's id (in `graphify_node_ids` array or legacy singular `graphify_node_id`); graph node N has no `vault_entity_path`. Mechanical fix: re-trigger Phase 6.5 propagation via no-op `update` on the entity.
- **Scenario A-extended — orphan absorbable into existing entity.** Orphan N is semantically similar to a node already bound to a `code` entity E (above `code.cluster_threshold`, or community co-membership when god-node/edge_count guard applies). Mechanical fix: extend E's `graphify_node_ids` array to include N. The similarity above threshold makes the merge unambiguous.
- **Scenario B — isolated orphan.** N has no candidate to merge into. Cluster N with other Scenario-B-classified orphans via Part 2 grouping; resolve `actor_context` via (b) `source_file` root match + (c) interactive/queued fallback; create a new `code` entity per cluster.

Trivial labels (`Test|Mock|Builder|Stub|Fixture`) and AMBIGUOUS-only nodes are NOT skipped at `/compress` time. They are bound via the same three mechanisms — typically absorbed by Scenario A-extended into the related production class entity. Vault size is controlled by the cluster threshold, not by exclusion lists.

`/preserve` already exposes every write primitive needed:
- `entities/code.md` schema with `graphify_node_ids` array (Part 1).
- Phase 1.3 step 5 semantic grouping algorithm and `code.cluster_threshold` config key (Part 2).
- Phase 6.5 atomic back-pointer propagation (Part 3).

This spec adds the **detection + delegation** logic in `/compress` Cap 1 — no new write primitives.

## Definition of Done

1. **Graph-side detection added to Cap 1.** `skills/compress/SKILL.md` Phase 1.2 (or a numbered sub-step under it, e.g. 1.2.2) loads `<VAULT_PATH>/graphify-out/graph.json` and `.graphify_analysis.json` (best-effort: skip silently when `graph.json` is missing, empty, or invalid JSON, and proceed with markdown-only Cap 1 detection unchanged). Markdown-side detection (today's behavior) remains identical when graph-side detection is skipped or in addition to it.

2. **Total-binding scope: every unbound node is in scope.** The graph-side detection iterates EVERY node in `graph.json` that lacks `vault_entity_path`. There is NO relevance filter at `/compress` time — `confidence` level (EXTRACTED / INFERRED / AMBIGUOUS), trivial labels, degree, god-node status, and edge count do not exclude any node from binding. Nodes that already have `vault_entity_path` set are skipped (already bound).

3. **Three binding shapes registered as Cap 1 findings, classified in priority order:**
   - `back_pointer_missing` (Scenario A): N's id is in some `code` entity's `graphify_node_ids` (accept legacy singular `graphify_node_id` too).
   - `extend_existing` (Scenario A-extended): N is semantically similar to a node already bound to a `code` entity, above `code.cluster_threshold` (default 0.85, configurable via `.bedrock/config.json`) — OR community co-member with the bound node when god-node OR edge_count ≥ 2 guard applies.
   - `orphan_graph_node` (Scenario B): N is not absorbed by either of the above. Scenario B candidates are clustered together via the Part 2 grouping algorithm before being registered as findings — one cluster → one proposed `code` entity carrying every cluster member's id in `graphify_node_ids`.
   Classification stops at the first matching shape (Scenario A wins over A-extended; A-extended wins over B).

4. **`actor_context` resolution for Scenario B clusters.** Match the cluster representative's `source_file` root directory against existing actor slugs in `<VAULT_PATH>/actors/`. Single match → set `actor_context`. No match → register the cluster as a `concept` global / `topic` / `fleeting` proposal (corpus-agnostic branch from Part 2). Ambiguous match (2+ candidates) → in `--mode interactive`, prompt the user during Phase 3 confirmation; in `--mode cron`, queue the cluster as a proposal in the `<YYYY-MM-DD>-compress-proposals` fleeting note alongside Cap 2/3/5 queued items.

5. **Cron mode autonomy split honored.** `back_pointer_missing` and `extend_existing` (mechanical) are autonomous in `--mode cron`. `orphan_graph_node` (semantic) is queued as a fleeting note proposal. Interactive mode prompts confirmation for all three with cluster-level granularity for Scenario B.

6. **Single-write-point preserved with cap overrun warning.** Phase 4 of `/compress` invokes `/preserve` for every fix (`update` for A and A-extended, `create` for B). `/compress` performs ZERO direct writes to `graph.json` or to entity files. When Scenario B fixes push an actor above `code.max_per_actor`, the proposals proceed but the report shows a warning row per affected actor; cap overrun never blocks a fix.

7. **Quality gate.** Changes to `skills/compress/SKILL.md` (a) follow `patterns/skill-architecture.md` (preserve phase numbering, update Critical Rules, keep agent type declaration); (b) follow `patterns/skill-delegation.md` (every mutation goes through `/preserve`; no `git add graph.json` from `/compress`); (c) reuse the Part 2 algorithm for semantic grouping verbatim — do not re-implement or fork; (d) honor `/preserve` Critical Rule 28 (no `graph.json` write outside Phase 0.2 and Phase 6.5) — `/compress` triggers the writes but does not perform them.

## Scope

Single file: `skills/compress/SKILL.md`.

Sub-changes:

- **Phase 1.2 (Detect broken backlinks)** — extend with sub-step that:
  - Best-effort loads `<VAULT_PATH>/graphify-out/graph.json` and `.graphify_analysis.json`.
  - Computes the entity-id index (every `graphify_node_id` / `graphify_node_ids` from `code` entities → owning entity path).
  - Walks every node in `graph.json` and classifies each into A / A-extended / B / already-bound. NO relevance filter, NO trivial label exclusion at this layer.
  - Applies Part 2 semantic grouping to Scenario B candidates before registering findings.
- **Phase 1.0 / Phase 1 setup** — add a sub-bullet that loads `code.cluster_threshold` from `<VAULT_PATH>/.bedrock/config.json` (default 0.85). Reuse the read pattern established by Part 2.
- **Phase 2.2 (Capability 1 proposal)** — split the table into three sub-tables (back_pointer_missing, extend_existing, orphan_graph_node) with per-row context. Add cap overrun warning row per affected actor.
- **Phase 3 (Confirmation)** — confirm the autonomous-vs-queued split: A and A-extended autonomous in cron; B queued. Interactive prompts cluster-level confirmation for B.
- **Phase 4.1 (Capability 1 fixes)** — replace the existing single YAML template with three branches (one per shape) using `update` for A and A-extended (with extended `graphify_node_ids` array for the latter), `create` for B. Reference `entities/code.md` for required fields when creating B.
- **Phase 5 (Final Report)** — augment the Cap 1 row with the three counts, plus the cap-overrun warning surface.
- **Critical Rules table** — append rules covering: best-effort graph load, no direct `graph.json` mutation from `/compress`, total-binding scope (no relevance filter), cap overrun is allowed-with-warning.

## Anti-scope

- **No relevance filter at `/compress` time.** Every unbound node is in scope, including trivial labels (Test/Mock/Builder/Stub/Fixture), AMBIGUOUS-confidence nodes, low-degree singletons. The cluster threshold (configurable) is the only knob that influences which nodes get absorbed vs become their own entities.
- **No mutation of `graph.json` from `/compress`** — every `vault_entity_path` write happens via `/preserve` Phase 6.5 triggered by the `update`/`create` actions in Phase 4. Single-write-point preserved.
- **No stale `vault_entity_path` cleanup** (path pointing at a deleted entity). Part 3 anti-scoped this; this spec inherits the boundary.
- **No automatic merging of Scenario B entities** in different clusters that may describe the same real-world thing. Cap 5 (misnamed entities) handles that in a separate run.
- **No `code.max_per_actor` enforcement on orphan binding.** Cap overrun is allowed with warning.
- **No extension of Caps 2, 3, 4, 5 to read `graph.json`** — only Cap 1 gains the extension.
- **No recompute of `.graphify_analysis.json` when `stale: true`.** Belongs to a separate work item; if analysis is missing/stale, fall back to `semantically_similar_to`-only grouping (same fallback Part 2 already uses).
- **No batch migration command** to bind every existing orphan in one shot. Migration happens through normal `/compress` runs.
- **No new entity type, no new frontmatter field.** Reuses `code`, `graphify_node_ids`, `vault_entity_path` exactly as Parts 1-3 defined them.
- **No total-binding enforcement at `/teach` time.** `/teach` keeps its Part 2 relevance filter and trivial exclusion to bound initial extraction noise. `/compress` catches up. Two skills, two jobs.

## Technical Decisions

### 1. Cap 1 extension, not a new Capability

**Decision:** the new graph-side detection lives under Capability 1 (Broken backlinks), not as Capability 6.
**Trade-off:** alternatives were (a) new Cap 6 dedicated to graph evidence, (b) extend Cap 4. Rejected (a) because the user explicitly framed this as broken backlinks and the conceptual model is identical (bidirectional link incomplete — just on the graph layer). Rejected (b) because Cap 4 is purely about markdown mentions; mixing graph evidence in there muddies capability boundaries.

### 2. Three binding shapes ordered by precedence

**Decision:** classify each unbound node by trying Scenario A, then A-extended, then B. Stop at first match.
**Trade-off:** order matters because A is cheapest (just propagate) and most certain (id match). A-extended is also mechanical but requires similarity judgment (configurable threshold). B is the fallback — every node that isn't otherwise bindable goes here. The deterministic order keeps the algorithm predictable across runs.

### 3. Total-binding scope, no relevance filter at `/compress` time

**Decision:** the `/compress` graph-side detection iterates every unbound node — no `confidence` filter, no trivial label exclusion, no degree/god-node gate. Every node gets bound.
**Trade-off:** Part 2's relevance filter at `/teach` time was about "which nodes deserve to be a top-level `code` entity at extraction time". `/compress`'s job is different — enforce the total-binding invariant on the existing graph state. The two filters serve different purposes. Concretely: trivial getters at `/teach` time stay out of the entity list (kept lean); at `/compress` time, those same getters get absorbed via `extend_existing` similarity into the class's entity, where they belong. The vault size grows in proportion to clustering aggressiveness, not in proportion to graphify's raw output. Tunable via `code.cluster_threshold`.

### 4. `actor_context` resolution = (b) mechanical inference + (c) interactive/queued fallback

**Decision:** match `source_file` root directory against vault actor slugs (mechanical). On ambiguity (multiple matches) or no match, defer to user prompt in interactive mode; queue as fleeting proposal in cron mode.
**Trade-off:** path inference is fragile in monorepos (Part 2 rejected it for `/preserve`'s `actor_context` derivation in the structured input protocol). Accepted here because (a) `/compress` operates AFTER `/teach`, when actors should already exist and naming is stable; the match becomes more reliable, (b) the (c) fallback covers ambiguous cases without forcing wrong answers, (c) `/compress`'s purpose IS to surface inconsistencies — pushing an ambiguous case to the user is correct behavior.

### 5. `back_pointer_missing` fix via `update` no-op, not direct write

**Decision:** `/compress` invokes `/preserve` with `action: update` on the existing `code` entity and an empty body change; Phase 6.5 of `/preserve` re-propagates `vault_entity_path` because the entity is in the touched-set.
**Trade-off:** the alternative would be a new `/preserve` action like `action: sync_back_pointer` that runs only Phase 6.5 without any other phase. Rejected because (a) Phase 6.5 is already idempotent (Critical Rule 30), so a no-op `update` produces the right effect with zero new code, (b) reusing the existing protocol keeps the contract between `/compress` and `/preserve` consistent across all three shapes, (c) the extra Phase 4 work (touch frontmatter `updated_at`/`updated_by`) is acceptable cost for the simpler protocol.

### 6. Cap overrun allowed, surfaced as warning

**Decision:** when Scenario B fixes push an actor above `code.max_per_actor`, do NOT prune the proposals; emit a warning row in the proposal and final report.
**Trade-off:** alternatives were (a) hard-block at the cap (require maintainer to raise cap first) or (b) silently exceed. Rejected (a) because cap is a `/teach`-time noise control, not a vault invariant — orphan binding is a deliberate decision and should always succeed under the total-binding rule. Rejected (b) because silent overrun hides the cap question from the maintainer.

### 7. Re-queue duplicate clusters across runs

**Decision:** v0 re-queues a Scenario B cluster every time `/compress` runs in cron mode and the cluster is still orphaned, even if a prior fleeting proposal exists. Deduplication is the maintainer's responsibility when reviewing.
**Trade-off:** PRD open question Q1. Deduplication via a `previously_proposed_at` field would require parsing existing fleeting notes and matching on `member_node_ids` set equality — significant complexity for a noise-mitigation feature. Deferred to a future iteration if noise becomes a real problem.

### 8. Trivial labels and AMBIGUOUS get bound, not excluded

**Decision:** at `/compress` time, no node is filtered by label or confidence. Trivial labels are absorbed via Scenario A-extended into related production entities; truly isolated trivials become their own (small) `code` entities via Scenario B; AMBIGUOUS-only nodes follow the same path.
**Trade-off:** vault might grow more than at `/teach` time. Accepted because (a) the user's rule is explicit and unconditional ("every output must bind"), (b) Scenario A-extended (similarity-based merging) prevents most trivial-as-singleton bloat — a getter doesn't become its own entity if its class is already an entity, (c) the `code.cluster_threshold` knob lets the maintainer trade aggressiveness for vault size, (d) interactive mode lets the maintainer decline any specific proposal.

## Applicable Patterns

- **`patterns/skill-architecture.md`** (mandatory): the change adds sub-steps inside existing phases (1.2, 2.2, 3, 4.1, 5) without breaking numbering. Critical Rules table is appended, not reordered. Agent type declaration unchanged.
- **`patterns/skill-delegation.md`** (mandatory): all writes — entity create/update AND `graph.json` mutation — flow through `/preserve`. `/compress` adds detection logic only; the protocol contract with `/preserve` (structured input list with `action`, `relations`, `metadata`) is unchanged.
- **`patterns/entity-definition.md`** (advisory): when `/compress` constructs a Scenario B `create` proposal, it must populate the `code` entity's required fields per `entities/code.md` ("Required fields" table). The proposal does NOT invent a new schema.

No new pattern is introduced.

## Risks

| Risk | Mitigation |
|---|---|
| Total-binding rule causes vault explosion in repos with many trivial nodes | Aggressive merging via `code.cluster_threshold` absorbs trivials into related production entities. Threshold is configurable; lower threshold → more merging → fewer entities. Document in the report when entity count grew significantly in a single run; the maintainer can re-tune. |
| Scenario A-extended threshold (default 0.85) is too aggressive — wrong nodes get merged into existing entities | In `--mode interactive`, every Scenario A-extended fix prompts confirmation per cluster. In `--mode cron`, mistakes happen autonomously; mitigation is to lower threshold or run interactive periodically. Threshold reuses the existing Part 2 config key for consistency. |
| Loading large `graph.json` (10k+ nodes) slows `/compress` | Anti-scope (`code-graphify-bridge` v0.1 covers optimization). For v0, accept the cost; document in the report when graph load takes >2s. |
| `actor_context` (b) inference yields false positives in monorepo | (c) fallback escalates to user (interactive) or fleeting queue (cron). Never auto-binds to wrong actor. |
| Re-queueing same cluster across runs spams fleeting notes | Accepted v0 behavior; flagged as future work. Maintainer can manually delete stale `compress-proposals` notes. |
| `/preserve` Phase 6.5 silent skip (because `graph.json` was missing for that run) leaves Cap 1 unable to fix back-pointer drift on the same run | After this spec lands, `/compress` Cap 1 picks up the drift on the next run. Convergence is eventual, not immediate. Acceptable for v0. |
| Cap overrun creates thousands of `code` entities, degrading Obsidian UX | Maintainer sees overrun warning before confirming (interactive) or in queued fleeting note (cron). The decision is theirs. |
| Cap 1 markdown-side detection regresses because of the new sub-step | DoD #1 explicitly requires markdown-side detection to remain unchanged. Code review should verify byte equality of the markdown-side detection block where possible. |
| Total-binding invariant is not runtime-enforced — user can decline a proposal in interactive mode and the node stays unbound | Accepted. The rule is a target after all proposals are accepted, not a runtime guarantee. Document in the report which nodes remained unbound after the run. |

## Dependencies

- `.vibeflow/specs/code-graphify-bridge-part-1.md` — `entities/code.md` schema with `graphify_node_ids` array. **Audit verdict: PASS.**
- `.vibeflow/specs/code-graphify-bridge-part-2.md` — Part 2 semantic grouping algorithm and config keys. Implemented; audit pending.
- `.vibeflow/specs/code-graphify-bridge-part-3.md` — `/preserve` Phase 6.5 propagation primitive. Implemented; audit pending.

This spec assumes Parts 2 and 3 will pass audit. If either fails audit and is reworked, this spec may need adjustment to track changes in their algorithm or interface.

