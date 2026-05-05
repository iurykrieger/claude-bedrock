# Audit Report: compress-graph-broken-backlinks

**Verdict: PASS**

> Audited: 2026-05-04
> Spec: `.vibeflow/specs/compress-graph-broken-backlinks.md`
> Files in scope: `skills/compress/SKILL.md` (single file)
> Audit gap noted: dependencies (Parts 2 & 3) implemented but not yet audited; spec author explicitly accepted this risk.

## DoD Checklist

- [x] **1. Graph-side detection added to Cap 1, best-effort load** — `skills/compress/SKILL.md:167-249` adds §1.2 with two sub-phases:
  - §1.2.1 Markdown-side backlinks (lines 171-179) — preserved verbatim from the prior implementation; output now tagged `kind: "markdown_backlink"` for downstream demultiplexing.
  - §1.2.2 Graph-side back-pointers (lines 181-249) — loads `<VAULT_PATH>/graphify-out/graph.json` via best-effort detection (line 185-190: explicit "skip §1.2.2 silently and proceed with §1.2.1 results only" when missing/empty/invalid). Also loads `.graphify_analysis.json` best-effort with `semantically_similar_to`-only fallback (line 192).

- [x] **2. Total-binding scope: every unbound node in scope, no relevance filter** — `skills/compress/SKILL.md:183` explicit: "every node ... MUST end up with `vault_entity_path` set. There is NO relevance filter at `/compress` time — `confidence` level (EXTRACTED / INFERRED / AMBIGUOUS), trivial labels (Test / Mock / Builder / Stub / Fixture), `degree`, `is_god_node`, `edge_count` do NOT exclude any node from binding." Critical Rule at line 888 reaffirms. The walker loop (line 207) iterates every node in `graph.json`; the only skip condition is "vault_entity_path already set" (line 209). Grep verification: zero occurrences of the legacy filter pattern (`is_god_node OR.*degree.*OR.*edge_count`) in detection logic.

- [x] **3. Three binding shapes registered as Cap 1 findings, priority order** — `skills/compress/SKILL.md:210-221` classifies in strict priority order: Scenario A (id match, line 212) → Scenario A-extended (similarity above `code.cluster_threshold` OR community co-membership guarded by god-node/edge_count, line 214-219) → Scenario B (lines 221-237, clustered via Part 2 algorithm before registration). Output schema documented at line 245-249.

- [x] **4. `actor_context` resolution = (b) + (c)** — `skills/compress/SKILL.md:229-235`:
  - (b) Mechanical inference (line 231): take cluster representative's `source_file` first path segment, match (case-insensitive, kebab-case) against `<VAULT_PATH>/actors/` slugs.
  - Single match → set; no match → `null` (corpus-agnostic branch from Part 2); ambiguous → list of candidates.
  - (c) Phase 3 fallback (line 235): interactive prompt or cron queue.

- [x] **5. Cron mode autonomy split honored** — `skills/compress/SKILL.md:481-501`. Autonomous in cron: §1.2.1, Scenario A (back_pointer_missing), Scenario A-extended (extend_existing), Cap 4. Queued in cron: Caps 2, 3, 5, AND Scenario B (orphan_graph_node) — including clusters with unresolved or ambiguous `actor_context`. The fleeting-note template at line 510-518 includes a new "Orphan Graph Nodes" section for Scenario B.

- [x] **6. Single-write-point preserved with cap overrun warning** — Phase 4.1 (lines 538-696) introduces 4 fix templates:
  - 1A — Markdown backlink → `update`.
  - 1B-A — `back_pointer_missing` → `update` with empty body, triggers `/preserve` Phase 6.5 propagation.
  - 1B-B — `extend_existing` → `update` with full computed `graphify_node_ids` array (union of existing + new id, dedup performed in `/compress` from `vault_data`); standard `/preserve` metadata field, NO new protocol field introduced.
  - 1B-C — `orphan_graph_node` → `create` with cluster's `member_node_ids` as `graphify_node_ids` array.
  All four delegate via standard `/preserve` `update`/`create` actions. Zero direct writes to `graph.json` or entity files (grep confirmed zero occurrences of `graphify_node_ids_add` or other invented protocol keys). Phase 5 (lines 819-823) shows cap overrun warning rows. Critical Rule 887 forbids any `graph.json` mutation from `/compress`.

- [x] **7. Quality gate** — see Pattern Compliance section below for full breakdown.

## Pattern Compliance

- [x] **`patterns/skill-architecture.md`** — followed.
  - Phase numbering preserved: §1.0 (existing, extended with config read at line 141-146), §1.1 (unchanged), §1.2 (extended with §1.2.1 and §1.2.2 sub-phases — decimal sub-numbering allowed by pattern), §1.3-§1.6 (unchanged), Phase 2.2 (Cap 1 proposal split into 1A/1B-A/1B-B/1B-C sub-tables), Phase 3 (autonomy lists augmented), Phase 4.1 (new fix templates added; existing Cap 2-5 templates preserved verbatim), Phase 5 (Cap 1 row split + cap overrun row added; existing Cap 2-5 rows preserved).
  - Critical Rules table updated: 6 new rows appended (best-effort graph load, no `graph.json` mutation, total-binding scope, cap overrun allowed, reuse Part 2 algorithm, plus existing rows). Total 21 rows (was 15). No reorder.
  - Agent type declaration unchanged ("execution agent" still in Overview).

- [x] **`patterns/skill-delegation.md`** — followed strictly.
  - Single-write-point preserved: every fix flows through `/preserve` `update` or `create`. `/compress` does NOT mutate `graph.json` directly (Critical Rule 887 + zero grep matches for direct write logic).
  - Protocol contract with `/preserve` unchanged: standard `metadata.graphify_node_ids` field used for the array. The earlier draft used a non-standard `graphify_node_ids_add` key, which was caught and removed during implementation; final spec computes the full union in `/compress` from `vault_data` and passes the standard array.
  - `/compress` Cap 1 1B-A leverages `/preserve` Phase 6.5 idempotent re-propagation via no-op `update`, consistent with `/preserve` Critical Rule 28 (no `graph.json` write outside Phase 0.2 and Phase 6.5).

- [x] **`patterns/entity-definition.md`** — followed.
  - Scenario B `create` template (lines 599-628) populates the required fields per `entities/code.md`: `type`, `name`, `actor` (when `actor_context` resolved), `node_type`, `source_file`, `graphify_node_ids` (array), `confidence`. The corpus-agnostic branch (lines 615-628) classifies as `concept` / `topic` / `fleeting` per `/preserve` Phase 1.3 step 6 — using existing entity definitions, not inventing new schemas.

- [x] **Part 2 algorithm reuse (verbatim)** — followed.
  - Semantic grouping in §1.2.2 (lines 223-227) uses the same predicates as `/preserve` Phase 1.3 step 5: `semantically_similar_to.confidence_score ≥ code.cluster_threshold` OR `community_id` equality with god-node/edge_count guard. Same fallback (analysis absent → similarity-only).
  - Same config keys: `code.cluster_threshold` (default 0.85), `code.max_per_actor` (default 200, used only for warnings).
  - Critical Rule 890 affirms the verbatim reuse contract.

## Convention Violations (if any)

- **`skills/compress/SKILL.md:97`** — minor documentation drift, **not blocking**. The Overview section "Five alignment capabilities" table still describes Capability 1 as `Mechanical | Autonomous — fix without confirmation`. After this change, Cap 1 has a mixed nature: 1A markdown + 1B-A back_pointer_missing + 1B-B extend_existing are mechanical/autonomous, but 1B-C orphan_graph_node is semantic and queued in cron. The functional behavior at Phase 3 (lines 481-501) is correct; only the descriptive overview is stale. Similarly the bullet at line 105-106 ("NEVER execute semantic capabilities (2, 3, 5) autonomously in cron mode — always queue") should also include "Cap 1 Scenario B (orphan_graph_node)". Recommended polish in a follow-up — does NOT affect runtime correctness because operators follow Phase 3 logic, not the overview table.

## Tests

**No test runner detected** for this change. Project is markdown-only per `.vibeflow/index.md` ("This is a Claude Code plugin, not a traditional codebase. It consists entirely of markdown files"). The `hooks/` directory contains Python tests but is unrelated to this spec (no Python file was touched).

Manual sanity checks performed during implementation and re-verified in the audit:
- Phase structure intact: 1.2.1 + 1.2.2 sub-phases present, Phase 3 cron-mode block updated, Phase 4.1 has 4 templates (1A, 1B-A, 1B-B, 1B-C), Phase 5 has cap overrun row.
- Keyword presence: `back_pointer_missing` (5), `extend_existing` (6), `orphan_graph_node` (6), `actor_context` (14), `code.cluster_threshold` (5), `code.max_per_actor` (3), `vault_entity_path` (7), `graphify_node_ids` (8).
- Critical Rules: 21 total (15 original + 6 new), no reorder.
- No `graphify_node_ids_add` or other invented `/preserve` protocol keys (0 occurrences).
- `skills/teach/SKILL.md` untouched (`git diff --stat` confirms 0 changes — anti-scope respected).

## Budget

Files changed: **1 / ≤ 4** (`skills/compress/SKILL.md` only). Within budget.

## Anti-scope

All anti-scope items respected:
- No relevance filter at `/compress` time (line 183 explicit; Critical Rule 888).
- No `graph.json` mutation from `/compress` (Critical Rule 887 + grep clean).
- No stale `vault_entity_path` cleanup (no detection or fix logic added for this).
- No automatic merging of Scenario B entities (Cap 5 untouched; no cross-cluster merge logic).
- No `code.max_per_actor` enforcement (only warning surface in Phase 5).
- No extension of Caps 2/3/4/5 (their Phase 1, Phase 2, Phase 4 sections preserved verbatim; only Cap 1 was modified).
- No recompute of `.graphify_analysis.json` when stale (best-effort fallback at line 192 only).
- No batch migration command (no new flag introduced).
- No new entity type / no new frontmatter field (uses existing `code` + `graphify_node_ids` + `vault_entity_path`).
- No `/teach` changes (`git diff --stat skills/teach/SKILL.md` returns no diff).

## Audit gap note (advisory, not blocking)

This spec depends on `code-graphify-bridge-part-2.md` and `code-graphify-bridge-part-3.md`, which are **implemented and merged** (PR #27) but **lack PASS audits**. The spec author explicitly accepted this risk in the Dependencies section: "This spec assumes Parts 2 and 3 will pass audit. If either fails audit and is reworked, this spec may need adjustment to track changes in their algorithm or interface."

Recommend running `/vibeflow:audit` on Parts 2 and 3 before this spec ships to production. None of the algorithm reuse points in this spec (`code.cluster_threshold`, `code.max_per_actor`, `is_god_node`, community guard, `graphify_node_ids` array, Phase 6.5 propagation) appear at risk based on a reading of the implementation in this branch — but a formal audit is the right backstop.

## Conclusion

The implementation is correct, complete, and aligned with the spec. All 7 DoD checks pass. The single-write-point pattern is preserved (`/compress` triggers `graph.json` mutation only via `/preserve` Phase 6.5; never writes directly). Anti-scope items are all respected — most importantly, the total-binding rule has zero relevance-filter exclusions at `/compress` time.

One non-blocking documentation drift in the Overview block (line 97 + 105-106) should be patched in a follow-up: the "Five alignment capabilities" table claims Cap 1 is purely mechanical, but Scenario B (orphan_graph_node) is now a semantic sub-shape that cron mode queues. Functional behavior is correct; only the descriptive summary is stale.

**Ready to ship**, with the recommended follow-ups: (1) patch the overview drift, (2) run formal audits on Parts 2 and 3.
