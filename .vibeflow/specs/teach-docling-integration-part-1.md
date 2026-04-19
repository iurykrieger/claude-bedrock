# Spec: /bedrock:preserve — graphify-out append merge (Phase 0)

> Part 1 of 3 — Split from `.vibeflow/prds/teach-docling-integration.md`
> Generated via /vibeflow:gen-spec on 2026-04-18

## Objective

Add a pre-write **Phase 0** to `/bedrock:preserve` that merges an incoming graphify output directory into the vault's `<VAULT_PATH>/graphify-out/`, making graph state append-only across multiple ingestion runs while keeping `/preserve` as the single write point for the vault.

## Context

Today `/graphify` writes its output directly to `<VAULT_PATH>/graphify-out/`, so each `/bedrock:teach` invocation overwrites the previous graph. The vault's knowledge graph reflects only the last ingestion instead of accumulating. Per `.vibeflow/patterns/skill-delegation.md`, all vault writes must flow through `/bedrock:preserve` — `graphify-out/` is part of the vault, so its append logic belongs here, not in callers. Landing this change first unblocks Part 2 (teach+docling) and is also useful on its own for any future consumer (e.g. `/bedrock:sync`).

## Definition of Done

1. **Mode detection + backward compat:** `/preserve` accepts `graphify_output_path` as either the vault's own `graphify-out/` (legacy callers) or any other directory (new temp-dir mode). When the resolved absolute path equals the vault's `graphify-out/`, Phase 0 is a no-op and the skill behaves exactly as today.
2. **Node metadata merge:** on `graph.json` node-ID collision, Phase 0 unions `sources` arrays (dedup by URL), takes the most-recent `updated_at`, and unions label/tag sets. No node from the prior graph is lost.
3. **Edge dedup:** on `graph.json` edge collision keyed by `(source, target, type)` tuple, Phase 0 drops the duplicate. Edge count is strictly non-decreasing across merges.
4. **Analysis staleness marker:** `.graphify_analysis.json` receives a top-level `stale: true` boolean field after merge; the rest of the JSON is untouched. `/bedrock:compress` will recompute on its next run (out of scope here).
5. **Per-file append behavior:** `obsidian/*.md` existing files are appended (content preserved, new sections added with a `---` separator); new files are copied; `GRAPH_REPORT.md` receives a new dated section appended to its end.
6. **First-ingestion edge case:** when `<VAULT_PATH>/graphify-out/` does not exist yet, Phase 0 promotes the incoming directory to the vault location without a re-merge pass.
7. **Craftsmanship gate:** `/preserve` retains single-write-point discipline (no vault file writes outside Phase 0 and the existing entity-write phase); Phase 0 follows `skill-architecture.md` (numbered `## Phase N` heading, Critical Rules table still present and updated); no violations from `.vibeflow/conventions.md` Don'ts; merge stats (`nodes_added`, `nodes_merged`, `edges_added`, `stale_flag_set`) included in `/preserve`'s return payload.

## Scope

- `skills/preserve/SKILL.md` — insert new `## Phase 0 — Merge incoming graphify output` ahead of existing Phase 1; update `## Plugin Paths`/`## Overview` only as needed to describe the new input contract; extend the return-payload description; add a row to the Critical Rules table covering backward compat and append semantics.

## Anti-scope

- **No changes to `/graphify`** — it continues to overwrite its own output dir; that output dir is now a per-run temp dir in Part 2.
- **No changes to `/teach`** — Part 2 changes the call sites to point at the temp dir. Until Part 2 ships, `/teach` keeps calling with the vault's `graphify-out/` and Phase 0 is a no-op thanks to backward compat.
- **No changes to `/sync`, `/compress`, `/ask`, `/setup`.**
- **No extracted helper skill** (no `skills/graph-merge/SKILL.md`).
- **No inline recomputation of `.graphify_analysis.json`** — stale flag only.
- **No rollback/versioning/snapshotting** of the cumulative graph.
- **No validation beyond "valid JSON, non-empty graph.json" on the incoming dir** — if it's malformed, fail fast before mutating the vault.

## Technical Decisions

| Decision | Alternatives considered | Rationale |
|---|---|---|
| **Append semantics live in `/preserve` (new Phase 0)** | (a) inside `/teach`; (b) inside `/graphify` | Aligns with `skill-delegation.md` single-write-point rule; the vault's `graphify-out/` is vault state. Caller (`/teach`) stays a pure orchestrator. |
| **Backward-compat mode via absolute-path comparison** | Caller-supplied flag; version sniffing | Zero API break for legacy callers (`/sync`); the comparison is one `realpath` + one `==`. |
| **Node collision → metadata merge (union sources, most-recent `updated_at`)** | Keep-first; overwrite-latest | Matches the vault's append-only philosophy for people/teams/topics (`vault-writing-rules.md`). Preserves provenance. |
| **Edge collision → drop newer duplicate** | Overwrite with newer; keep both | Edges are structural; no per-edge metadata worth merging in current graphify output. |
| **Stale flag → top-level `stale: true` in `.graphify_analysis.json`** | Sidecar `.stale` file; delete analysis | Discoverable by `/compress` with a single JSON read; keeps the file intact for diagnostics. |
| **First-ingestion = atomic rename/copy** | Full merge against empty state | Avoids running the dedup pass against an empty graph; simpler, faster. |
| **Merge operates on a staging copy, then swaps** | In-place mutation | Avoids half-merged vault state on error; merge either fully lands or fully doesn't. |
| **Return payload carries merge stats** | Logging only | `/teach`'s Phase 4 report needs them. Keeps skill interactions explicit. |

## Applicable Patterns

- **`.vibeflow/patterns/skill-architecture.md`** — Phase 0 uses the numbered `## Phase N — <Title>` convention; Critical Rules table must be updated to mention backward compat and append semantics.
- **`.vibeflow/patterns/skill-delegation.md`** — This spec *strengthens* the pattern: now even `graphify-out/` writes route through `/preserve`.
- **`.vibeflow/patterns/vault-writing-rules.md`** — Append-only, `updated_at` take-latest, never remove existing content.

No new patterns introduced.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `graph.json` bloats over many `/teach` runs | Medium | Medium | `/compress` will add graph dedup in a follow-up spec. For v0, documented behavior; users can delete `graphify-out/` to reset. |
| Merge corrupts the vault's graph if source is malformed | Low | High | Validate incoming dir (JSON parses, `graph.json` non-empty) before touching vault; merge on staging copy + atomic swap. |
| Legacy callers break silently | Low | High | Backward-compat path check + a DoD assertion that legacy path is a no-op. |
| Metadata union grows `sources` field unboundedly | Medium | Low | Dedup by URL on merge; no extra mitigation in v0. |
| `stale: true` flag is ignored by `/compress` | Medium | Medium | Out of scope here; flagged as follow-up. `/compress` gains a read in a separate spec. |

## Dependencies

None — this spec is the foundation and must land first.
