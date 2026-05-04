# PRD: Reinforce the `code` entity as a bidirectional bridge between graphify and the vault

> Generated via /vibeflow:discover on 2026-05-04

## Problem

The `code` entity is the bridge between nodes extracted by `/graphify` and the Bedrock vault — every `code` entity lives in `actors/<actor>/nodes/<slug>.md` and carries `graphify_node_id` in its frontmatter. Despite that, the current pipeline leaves most graphify nodes orphaned from the vault and never propagates `/compress` decisions back to `graph.json`. The graph and the vault diverge progressively.

Three concrete breakages, all centered on the `code` entity:

1. **Restrictive classification in `/preserve` Phase 1.3.** [skills/preserve/SKILL.md:401](../../skills/preserve/SKILL.md) classifies as `code` only when `file_type=code`, under-covering the `node_type ∈ {concept, decision}` values that [entities/code.md:44](../../entities/code.md) admits. Architectural documentation extracted from an actor's repo gets classified as a global `concept` or `topic` instead of becoming `code` for that actor, losing the `graphify_node_id` link.

2. **Top-50 cap with English label regex.** [skills/preserve/SKILL.md:408](../../skills/preserve/SKILL.md) discards valid nodes whose labels do not match `Service|Controller|Client|Factory|Handler|Mapper|Gateway|Provider`. Domain helpers in Go, pure functions in Python, traits in Rust never become `code`. The hard cap of 50 is hardcoded and ignores repo size.

3. **Unidirectional bridge + missing template + zero propagation.** `graphify_node_id` points vault → graph; there is no reverse field in `graph.json`. The template `actors/_template_node.md` is referenced by [entities/code.md:3](../../entities/code.md) and [skills/preserve/SKILL.md:635](../../skills/preserve/SKILL.md) but does not exist in `templates/actors/` — `/bedrock:setup` doesn't create it, so the first `/teach` against a fresh vault breaks. And no `/compress` decision (Cap 1, 2, 3, 5) ever touches `graph.json`, leaving merges/recategorizations misaligned with the graph.

Who suffers: Bedrock vault maintainers who use `/teach` or `/graphify` for semantic extraction of actors. Observable symptom: the `/healthcheck` report shows `graphify-out/` populated, yet `actors/<actor>/nodes/` only has a handful of files; the remaining nodes stay visible in `graph.json` and unknown to Obsidian.

## Target Audience

**Primary:** human Bedrock vault maintainers who run `/teach` against actor repositories and expect to see the granular code knowledge materialized as navigable `code` entities in Obsidian.

**Secondary:** Claude agents executing `/compress` in cron mode — they need a `graph.json` that faithfully reflects the canonical state of the vault so future detections (broken backlinks, duplicates) can rely on the graph as a trustworthy source.

## Proposed Solution

Reinforce the `code` entity as a bidirectional bridge between `graph.json` and the vault through 4 coordinated moves:

1. **Classification delegated to the caller.** Instead of `/preserve` guessing from `source_file`, the caller (`/teach`, `/graphify`) passes the context. When the input comes from a specific actor repo, every `file_type=document/paper` node in that corpus becomes `code` for that actor with `node_type=concept|decision`. When the input is a generic corpus, docs follow the existing path to global `concept` / `topic` / `fleeting`.

2. **Semantic grouping before the cap.** Graphify nodes connected by `semantically_similar_to` (high `confidence_score`) and/or co-members of the same community get consolidated into a single `code` entity. The entity now carries `graphify_node_ids` (array) instead of `graphify_node_id` (singular). This reduces noise, leverages a signal graphify already produces, and keeps the cap operative.

3. **Cap configurable per actor.** `.bedrock/config.json: code.max_per_actor` (default 200) replaces the global cap of 50. Priority filters within the cap: `confidence ∈ {EXTRACTED, INFERRED}` AND ranking by `is_god_node` > `degree` > `edge_count`. No more English keyword regex.

4. **Bidirectional bridge.** New optional `vault_entity_path` field on the node schema in `graph.json`, written by `/preserve` in a new Phase 6.5 right before publish. For each created/updated `code` entity, `/preserve` locates the corresponding nodes (via `graphify_node_ids`) and writes the entity path. Atomic via `.staging` + `mv`. Best-effort: if `graph.json` is absent, silently skip.

Plus: physically create `templates/actors/_template_node.md` so `/bedrock:setup` can install it in the vault and the first `/teach` doesn't break.

## Success Criteria

1. **Coverage.** After running `/teach` against an actor repo with 500 EXTRACTED/INFERRED nodes, up to `code.max_per_actor` `code` entities are observed in the vault (default 200), with most of those 500 nodes referenced via `graphify_node_ids` (thanks to semantic grouping).
2. **Bidirectional bridge.** After any `/preserve` execution that touches `code` entities, every corresponding node in `<VAULT_PATH>/graphify-out/graph.json` has `vault_entity_path` populated and the path points to an existing file.
3. **Clean setup.** In a fresh vault, `/bedrock:setup` creates `templates/actors/_template_node.md` before any `/teach` is invoked.
4. **Backward compat.** A vault without `graphify-out/` keeps working — every Phase 6.5 is best-effort. Vaults with legacy singular `graphify_node_id` migrate transparently (`/preserve` reads both, always writes the `graphify_node_ids` array).
5. **No UX regression.** Cap per actor prevents monorepos from generating thousands of files in `actors/<actor>/nodes/`.

## Scope v0

1. **Physical template:** create `templates/actors/_template_node.md` with full frontmatter (`type: code`, `graphify_node_ids` (array), `actor`, `node_type`, `source_file`, `confidence`, `aliases`, `tags`, `updated_at`, `updated_by`) and minimal body structure.

2. **`code` entity schema:** update [entities/code.md](../../entities/code.md):
   - `graphify_node_id` (string) → `graphify_node_ids` (array). Document semantic grouping.
   - Document `vault_entity_path` on the `graph.json` node schema (same section).

3. **Setup:** update `/bedrock:setup` to install `_template_node.md` in fresh vaults.

4. **Rewritten classification in `/preserve` Phase 1.3:**
   - Accept `actor_context` field in the structured input (passed by the caller). When present, every node from that corpus becomes `code` for that actor.
   - When absent: existing classification (global concept / topic / fleeting).
   - Node grouping by similarity BEFORE filtering: `semantically_similar_to.confidence_score ≥ 0.85` OR community co-membership. Cluster becomes a single `code` candidate with multiple `graphify_node_ids`.
   - Configurable cap: read `.bedrock/config.json: code.max_per_actor` (default 200), per actor.
   - Relevance filters: `confidence ∈ {EXTRACTED, INFERRED}` AND (`is_god_node` OR `degree > community average` OR `edge_count ≥ 2`).
   - Remove label regex and the absolute cap of 50.

5. **New Phase 6.5 in `/preserve`:** after Phase 5 (linking), before Phase 6 (publish): for each `code` entity touched in this run, locate nodes in `graph.json` via `graphify_node_ids` and write `vault_entity_path`. Atomic via `.staging` + `mv` (same pattern as Phase 0.2). Best-effort.

6. **Update callers:** `/teach` passes `actor_context` when the input is an actor repo.

## Anti-scope

- **v0.1 (next iteration):**
  - `action: merge` in the structured input protocol for `/compress` Cap 5.
  - Recompute of `.graphify_analysis.json` when `stale: true` (fulfillment of Rule 22 in `/preserve`).
- **v0.2 (future):** one-shot command `/bedrock:compress --rebuild-back-pointers` for existing vaults.
- **No changes to `/graphify`** itself. The fix lives entirely in the Bedrock plugin layer.
- **No changes to `/healthcheck`.** It reports `graphify-out`, with no propagation responsibility.
- **No new entity type.** `code` is already the right bridge.
- **No retroactive modification** of `/compress` decisions in `graph.json`. v0 only populates back-pointers for entities touched FROM NOW ON.
- **No automatic migration** of vaults with legacy singular `graphify_node_id` — migration happens in-line as entities are touched.
- **No global cap.** The cap is strictly per actor; no absolute cap across the vault.

## Technical Context

### Existing patterns to follow
- **patterns/skill-architecture.md:** YAML frontmatter, Plugin Paths section, sequential phases, Critical Rules table at the end. Applies to any change in `/preserve` and `/setup`.
- **patterns/skill-delegation.md:** all writes go through `/bedrock:preserve`. The new Phase 6.5 respects this — only `/preserve` touches `graph.json` in the regular flow.
- **patterns/template-structure.md:** the new `_template_node.md` follows the convention with inline comments and bidirectional links section.
- **patterns/vault-writing-rules.md:** atomic writes via `.staging` + `mv` (`/preserve` Phase 0.2 is the canonical reference).

### Known related tech debts
- [.vibeflow/index.md](../index.md) records: "/bedrock:compress writes entities directly in Phase 4 rather than fully delegating to /bedrock:preserve, breaking the single-write-point pattern" — not addressed by this PRD, but the changes here do not make it worse.
- The language inconsistency in `entities/knowledge-node.md` was resolved by the `rename-knowledge-node-to-code` refactor (entity now lives in `entities/code.md` in English). This PRD couples to the `code` entity without reopening that discussion.

### Known constraints
- **Backward compat:** vaults with legacy singular `graphify_node_id` (string) must keep working. `/preserve` accepts both at parse time, always writes the `graphify_node_ids` array.
- **Best-effort for `graph.json`:** vaults without `graphify-out/` or with corrupted `graph.json` — Phase 6.5 silently skips, `/preserve` does not fail.
- **Atomicity:** mutations to `graph.json` ALWAYS via staging file (same pattern as the current Phase 0.2).
- **Idempotency:** running `/preserve` twice in a row does not create duplicates in `graph.json` nor in `graphify_node_ids`.
- **Sensitivity:** Phase 6.5 never writes credentials, tokens, PANs, CVVs — only paths relative to the vault.

### Dependencies
- `/bedrock:preserve` — owner of the main changes (Phase 1.3 and new Phase 6.5).
- `/bedrock:setup` — installs `_template_node.md` in the vault.
- `/bedrock:teach` — passes `actor_context` in the input.
- `entities/code.md` — updated schema.
- `templates/actors/_template_node.md` — new file.

## Open Questions

1. **Semantic grouping threshold.** `semantically_similar_to.confidence_score ≥ 0.85` is a guess. Validate empirically against at least one large repo (e.g. Stone monorepo) before locking it in — may need to become configurable (`.bedrock/config.json: code.cluster_threshold`).
2. **Exact shape of `actor_context`.** How does `/teach` signal which actor the corpus belongs to when invoked with a URL/path? Most likely derived from the repo name or root directory, but the spec needs a concrete decision. Consider whether multiple actors in the same input are out of scope for v0.
3. **Classification conflict `code` vs global `concept`.** When a document describes a cross-actor pattern but lives in a specific actor's repo, the proposed classification (delegated to the caller) would treat it as `code`. A later `/teach` against another actor might try to create the same concept as `code` there too. Decide: can the caller optionally pass `node_type_hint: concept` to force a global concept even in actor context? Or leave it for `/compress` Cap 2 to detect and move later?

