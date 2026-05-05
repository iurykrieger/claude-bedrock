# PRD: Total binding of graphify nodes to vault entities (extends /compress Cap 1)

> Generated via /vibeflow:discover on 2026-05-04
> Revised on 2026-05-04: total-binding rule (no relevance filter at /compress time).

## Problem

After the `code-graphify-bridge` work (Parts 1-3), every `/preserve` run writes `vault_entity_path` on the corresponding `graph.json` nodes for `code` entities it touches. But the bridge is not total: graphify produces nodes that never end up bound, and there is currently no skill that enforces the contract.

The user-facing rule is simple:

> **Every output that graphify makes NEEDS to POINT to some vault entity OR TURN INTO some vault entity.**

In schema terms: after a complete maintenance pass, every node in `<VAULT_PATH>/graphify-out/graph.json` MUST have `vault_entity_path` set. There is no acceptable subset that stays unbound.

Why this isn't true today:

1. **`/teach` Phase 1.3 step 7 applies a relevance filter** (`confidence ∈ {EXTRACTED, INFERRED}` AND (`is_god_node` OR `degree > community average` OR `edge_count ≥ 2`)) and a trivial-label exclusion (`Test|Mock|Builder|Stub|Fixture`). Nodes filtered out at /teach time stay in `graph.json` indefinitely without `vault_entity_path` — invisible to the vault.
2. **`/preserve` Phase 6.5 only propagates back-pointers for the entities it touches** in the current run. Pre-existing entities (created before Phase 6.5 existed) and entities whose `graphify_node_ids` were extended after the fact accumulate broken back-pointers.
3. **Trivial nodes and AMBIGUOUS-confidence nodes** are intentionally not materialized at /teach time, but they exist in the graph and currently bind to nothing.

Three concrete shapes of unbound nodes that all need to be resolved:

- **Scenario A — back-pointer drift.** Some `code` entity has `graphify_node_ids: [a, b]` (or legacy singular `graphify_node_id: "a"`); graph node `a` exists but lacks `vault_entity_path`. Mechanical fix: re-run Phase 6.5.
- **Scenario A-extended — orphan absorbable into existing entity.** Graph node `d` is semantically similar (above `code.cluster_threshold`) to a node already bound to a `code` entity E, but `d` itself has no entity. Mechanical-ish fix: extend E's `graphify_node_ids` to include `d`. The semantic similarity makes the merge unambiguous.
- **Scenario B — orphan with no nearby entity.** Graph node `c` exists, no entity carries `c`, no other bound node is similar to `c`. Semantic fix: cluster with other unbound nodes and materialize as a new `code` entity. Requires `actor_context` resolution.

`/compress` Cap 1 today only inspects markdown wikilinks. It is the natural home to enforce the total-binding invariant — the user already framed it as "broken backlinks", since unbound nodes are exactly the bidirectional-link breakage on the graph layer.

## Target Audience

Maintainers of Bedrock vaults integrated with graphify (via `/teach` or direct `/graphify` runs), especially:

- Operators of vaults seeded before Parts 1-3 landed (entities exist with `graphify_node_id` legacy schema; no Phase 6.5 propagation has ever run).
- Maintainers running `/compress` in cron mode that expect mechanical broken-backlink fixes to converge the vault toward consistency without manual intervention.
- Any vault where graphify produced nodes that fell below `/teach`'s relevance filter and now sit unbound — these are the silent majority of the orphan population.

## Proposed Solution

Extend `/compress` Capability 1 (Broken backlinks) so it enforces a **total-binding invariant**: after the maintenance pass completes, every node in `<VAULT_PATH>/graphify-out/graph.json` has `vault_entity_path` set.

### Core rule

For every node N in `graph.json` that lacks `vault_entity_path`:

1. **Try Scenario A first** — if N's id is in some `code` entity's `graphify_node_ids` (accept legacy singular too), register `back_pointer_missing`. Mechanical fix: invoke `/preserve update` with empty body so Phase 6.5 re-propagates.
2. **Try Scenario A-extended next** — if N is semantically similar to a node already bound to a `code` entity E (above `code.cluster_threshold`, or co-member of the same community when god-node/edge_count guard applies), register `extend_existing`. Mechanical fix: invoke `/preserve update` on E with extended `graphify_node_ids`.
3. **Otherwise Scenario B** — cluster N with other unbound nodes using the Part 2 semantic grouping algorithm; resolve `actor_context` via (b) `source_file` root match + (c) interactive/queued fallback; invoke `/preserve create` per cluster.

### Trivial labels and AMBIGUOUS confidence

Trivials (`Test|Mock|Builder|Stub|Fixture`) and AMBIGUOUS-only nodes are NOT excluded at `/compress` time. They are bound through the same three mechanisms:

- A trivial getter is typically semantically similar to its containing class → absorbed via Scenario A-extended into the class's `code` entity. The vault sees one entity (the class) carrying multiple `graphify_node_ids` (class + getters + setters).
- A standalone trivial that's NOT similar to any bound node → becomes its own (small) `code` entity via Scenario B.
- The vault grows in proportion to how aggressively graphify clusters; tunable via `code.cluster_threshold`.

This pushes the entity-vs-noise judgment from `/compress` (which lacks corpus context) onto the cluster threshold (which is empirical and configurable).

### Cap behavior

`code.max_per_actor` is a `/teach`-time hint, not a `/compress`-time limit. When Scenario B fixes push an actor above the cap, the proposals proceed with an explicit warning row in the report. The maintainer always sees the overrun before confirming (interactive) or before the proposal lands in the queue (cron).

## Success Criteria

1. **Total binding invariant verifiable.** After running `/compress --mode interactive` against a vault and accepting all proposals, a script that walks `graph.json` finds zero nodes without `vault_entity_path`. (Manual sanity check; not enforced at runtime.)
2. After `/compress --mode interactive` runs against a vault with a populated `graph.json`, every previously-unbound node either has `vault_entity_path` set OR was deliberately declined by the maintainer (proposal rejected during Phase 3 confirmation).
3. The Cap 1 section of the `/compress` report splits findings into the three shapes (`back_pointer_missing`, `extend_existing`, `orphan_graph_node`) so the maintainer sees what's mechanical vs semantic.
4. In `--mode cron`, Scenarios A and A-extended are applied autonomously and reported; Scenario B proposals land in a `<YYYY-MM-DD>-compress-proposals` fleeting note for human review.
5. Per-actor cap overruns are allowed and surfaced as a single warning line per affected actor; they never block.

## Scope v0

- `skills/compress/SKILL.md` Phase 1 (Detect):
  - Add Capability 1 sub-step that loads `<VAULT_PATH>/graphify-out/graph.json` and `.graphify_analysis.json` (best-effort).
  - Walk every node and classify into `back_pointer_missing` / `extend_existing` / `orphan_graph_node` / not-a-finding (only "not-a-finding" = node already has `vault_entity_path`).
  - Apply Part 2 semantic grouping over Scenario B candidates before registering findings.
  - Resolve `actor_context` via (b) inference; on ambiguity, defer to (c) for the proposal stage.
- `skills/compress/SKILL.md` Phase 2 (Build proposal): split Cap 1 stats into the three shapes; show cap overrun warnings per affected actor.
- `skills/compress/SKILL.md` Phase 3 (Confirmation): A and A-extended autonomous in cron; B queued in cron; interactive confirms all three with cluster-level granularity for B.
- `skills/compress/SKILL.md` Phase 4 (Delegate): `update` action for A and A-extended; `create` action for B.
- `skills/compress/SKILL.md` Critical Rules table updated.

## Anti-scope

- **No relevance filter at `/compress` time.** Every unbound node is in scope; trivials and AMBIGUOUS-only nodes are bound through the three mechanisms (typically absorbed via similarity).
- **No mutation of `graph.json` from `/compress`** — every `vault_entity_path` write happens via `/preserve` Phase 6.5 triggered by `update`/`create` actions in Phase 4.
- **No stale `vault_entity_path` cleanup** (path pointing at a deleted entity). Bedrock does not delete entities; orphan-path handling stays out of scope.
- **No automatic merging of Scenario B entities with each other** when they appear in different clusters. Cap 5 (misnamed entities) handles that in a later run.
- **No `code.max_per_actor` enforcement on orphan binding.** Cap overrun is allowed with warning.
- **No extension of Caps 2, 3, 4, 5 to read `graph.json`** — only Cap 1 gains the extension.
- **No recompute of `.graphify_analysis.json` when `stale: true`.** Falls back to `semantically_similar_to`-only grouping (mirrors Part 2).
- **No batch one-shot binding command** (`/bedrock:compress --rebuild-back-pointers` is `code-graphify-bridge` v0.2; this spec ships through normal `/compress` runs).
- **No new entity type, no new frontmatter field.** Reuses `code`, `graphify_node_ids`, `vault_entity_path`.
- **No total-binding enforcement at `/teach` time.** `/teach` keeps the relevance filter to bound initial extraction noise. `/compress` catches up later. The two skills have different jobs.

## Technical Context

### Existing patterns to follow
- **`patterns/skill-architecture.md`** (mandatory): `/compress` follows phased structure; this PRD adds sub-steps inside existing phases without breaking numbering.
- **`patterns/skill-delegation.md`** (mandatory): `/compress` does NOT write entities or `graph.json` directly; everything goes through `/preserve`.
- **`patterns/vault-writing-rules.md`** (advisory): no new write patterns introduced.

### Known constraints
- Vault may not have `graphify-out/graph.json` (fresh vault, no `/teach` ever ran). Cap 1 graph-side detection is best-effort: skip silently when missing/empty/invalid.
- `/preserve` Phase 6.5 is idempotent; triggering it via no-op `update` is safe and cheap.
- The total-binding invariant is verified per run, not enforced as an invariant the runtime guarantees. If the user declines a proposal in interactive mode, that node stays unbound until the next run.

### Dependencies
- `code-graphify-bridge-part-1` (PASS audit) — schema with `graphify_node_ids` array.
- `code-graphify-bridge-part-2` (implemented, audit pending) — semantic grouping logic, config keys.
- `code-graphify-bridge-part-3` (implemented, audit pending) — `/preserve` Phase 6.5 propagation primitive.

## Open Questions

1. **Cluster identity across runs.** If a previous `/compress` run already proposed creating a `code` entity for orphan cluster `[a, b, c]` (queued in a fleeting note), and a later `/compress` run finds the same cluster again, does it re-queue or detect the prior proposal and skip? Suggested for v0: re-queue; deduplication is the maintainer's responsibility when reviewing the fleeting note. Open question to confirm.
2. **AMBIGUOUS confidence in `extend_existing` decision.** When a node has only AMBIGUOUS edges, we still want to bind it. The most likely path is similarity to a stronger node. If similarity also fails (no nearby cluster), the node becomes a Scenario B singleton entity. Is that acceptable, or should AMBIGUOUS singletons be queued as fleeting proposals instead of materialized as `code`? Suggested for v0: materialize as Scenario B same as any other; let the maintainer downgrade in interactive mode if needed.
3. **Interactive mode UX for high orphan counts.** Vaults with thousands of orphans will produce thousands of confirmation prompts. Should `/compress --mode interactive` group the confirmation by actor or by binding shape, or accept-all-by-shape? Out of scope for v0; document in the report and revisit if it becomes a real pain.

