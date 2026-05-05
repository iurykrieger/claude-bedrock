# Audit Report: code-graphify-bridge — Part 3 (Bridge propagation)

**Verdict: PASS**

> Audited: 2026-05-05
> Spec: `.vibeflow/specs/code-graphify-bridge-part-3.md`
> Files in scope: `skills/preserve/SKILL.md` (single file)
> Implementation merged via PR #27 (commit `ba6ff21`).

## DoD Checklist

- [x] **1. Phase 6.5 inserted between Phase 5 and Phase 6** — `skills/preserve/SKILL.md:796` "## Phase 6.5 — Sync Graph Back-Pointers". Position verified: §5.3 ends at line 782; Phase 6.5 starts at line 796; "## Phase 6 — Publish" begins at line 913. Six sub-phases present:
  - 6.5.1 Defensive cleanup (line 802)
  - 6.5.2 Best-effort detection (line 812)
  - 6.5.3 Collect target node ids from touched `code` entities (line 828)
  - 6.5.4 Locate and update graph nodes (atomic write) (line 845)
  - 6.5.5 Atomic swap (line 887)
  - 6.5.6 Record stats for Phase 7 (line 897)
  
  The "Phase 6.5 before Phase 6" naming is unusual (decimal usually means later) but is spec-authorized per Part 3 Technical Decision #1: "position the propagation BEFORE `git add`/`commit` so that the `graph.json` change lands in the same commit as the entities."

- [x] **2. Iterates touched `code` entities; locates by ids; writes `vault_entity_path`** —
  - §6.5.3 (`skills/preserve/SKILL.md:828-843`) builds the id-set per touched `code` entity from BOTH `graphify_node_ids` (array, lines 835-836) AND legacy singular `graphify_node_id` (string, lines 837-838). Builds `id → vault_entity_path` map.
  - §6.5.4 (`skills/preserve/SKILL.md:851-878`) Python block iterates `graph["nodes"]`, matches `node["id"] ∈ target_map`, writes `node["vault_entity_path"] = target_map[nid]` (line 867).
  - Path is relative to `<VAULT_PATH>` (line 841: "the path of the entity file relative to `<VAULT_PATH>` (e.g. `actors/billing-api/nodes/process-transaction.md`)").

- [x] **3. Atomic via `.staging` + `mv`** — pattern matches Phase 0.2 verbatim:
  - §6.5.4 line 854: `staging_path = graph_path.with_suffix(".json.staging")`.
  - §6.5.5 line 892: `mv "<VAULT_PATH>/graphify-out/graph.json.staging" "<VAULT_PATH>/graphify-out/graph.json"` runs only after Python block exits 0.
  - Failure handling at line 884 (Python block summary): "If the Python block exits non-zero (parse error, write error, etc.), do NOT run the `mv` — the original `graph.json` stays intact."
  - §6.5.1 cleanup of orphaned staging file before write (line 807): `rm -f "<VAULT_PATH>/graphify-out/graph.json.staging" 2>/dev/null || true` — defensive against prior interrupted runs.
  - Critical Rule 28 codifies: "Same pattern as Phase 0.2 (Rule 21). No write to `graph.json` occurs outside Phase 0.2 and Phase 6.5."

- [x] **4. Best-effort: missing/empty/invalid → warn + proceed** — four explicit skip conditions:
  - §6.5.2 line 822: missing/empty/invalid_json → set `phase_6_5_status = "skipped"`, set reason, skip to Phase 6.
  - §6.5.3 line 843: no `code` entities touched → `phase_6_5_status = "skipped"`, `reason = "no_code_entities"`.
  - §6.5.4 (Python block fail) → `phase_6_5_status = "failed"` with error message; skip to Phase 6 without aborting `/preserve`.
  - All four cases surface as warnings in Phase 7 report (`skills/preserve/SKILL.md:1089-1101` "Graph back-pointers (Phase 6.5)" section). `/preserve` never fails on Phase 6.5 issues.
  - Critical Rule 29 enforces.

- [x] **5. Idempotency by overwrite, not skip** —
  - `skills/preserve/SKILL.md:867` Python block comment: "Idempotency by overwrite: always set, even if already present." The line `node["vault_entity_path"] = target_map[nid]` is unconditional.
  - Other node fields are never touched (only `vault_entity_path` is mutated).
  - Critical Rule 30: "Running `/preserve` twice in a row over the same entities does not duplicate fields nor alter any other node attribute. Unmatched ids (graphify re-run, id changed) surface as a warning but never block."

- [x] **6. `graph.json` included in Phase 6's `git add`** — `skills/preserve/SKILL.md:945-950`:
  ```bash
  # Stage graphify back-pointer changes when Phase 6.5 ran successfully.
  # Only run when graphify-out/graph.json exists — `git add` of a non-existent path errors out.
  if [ -f "<VAULT_PATH>/graphify-out/graph.json" ]; then
    git -C <VAULT_PATH> add graphify-out/graph.json
  fi
  ```
  The conditional check protects vaults without `graphify-out/` (consistent with Phase 6.5 best-effort behavior). The back-pointer change lands in the same commit as the entity diffs (per Technical Decision #1).

- [x] **7. Quality gate** — see Pattern Compliance section below for full breakdown.

## Pattern Compliance

- [x] **`patterns/skill-architecture.md`** — followed.
  - New phase added with sub-phase decimal numbering (6.5.1–6.5.6).
  - Critical Rules table extended with 3 new rows (28, 29, 30); no reorder. Total 30 rows.
  - Agent type ("execution agent") declaration unchanged.
  - "Phase 6.5 before Phase 6" naming is unusual but spec-authorized (Technical Decision #1). The Overview section at line 75 doesn't enumerate phases (no "phase index" sub-section to update); Phase 6.5 introduces itself via its own header. Spec scope item "Update Overview / Phase index to reflect Phase 6.5" is naturally satisfied.

- [x] **`patterns/skill-delegation.md`** — followed strictly.
  - Verified by grep — `graph.json` is written only inside Phase 0.2 (existing) and Phase 6.5 (new). No `/compress`, `/teach`, `/sync` write paths added.
  - Single-write-point on `graph.json` is preserved; Critical Rule 28 makes this explicit ("No write to `graph.json` occurs outside Phase 0.2 and Phase 6.5").

- [x] **`patterns/vault-writing-rules.md`** — followed.
  - Atomic via staging file mirrors Phase 0.2 line 237 (the canonical reference).
  - Idempotent overwrite without touching other node fields; never deletes existing data (per spec Technical Decision #5).
  - Append-only-equivalent semantics for nodes: only `vault_entity_path` is set or replaced; other attributes preserved verbatim.

## Convention Violations

None detected.

## Tests

**No test runner detected** for this change. Project is markdown-only per `.vibeflow/index.md`. The `hooks/` directory contains Python tests but is unrelated to this spec.

Manual sanity checks performed:
- Phase 6.5 sub-structure intact: 6 sub-phases (6.5.1-6.5.6) covering cleanup, detection, target collection, atomic write, swap, and stats recording.
- Position: §5.3 ends line 782; Phase 6.5 starts line 796; Phase 6 starts line 913. Correct ordering.
- §6.2.1 git add hook: lines 947-949 with conditional `[ -f ... ]` protection. Verified.
- Critical Rules: 30 total in `/preserve` (was 27 after Part 2 + 3 new for Part 3 = 30). Confirmed via `awk '/^## Critical Rules/,/^---$/' | grep -c "^| [0-9]"`.
- Anti-scope check: `merged_into` and `action: merge` strings absent (0 occurrences) — Cap 5 future work not preemptively added.
- Anti-scope check: no recompute of stale `.graphify_analysis.json` added; only the existing reference in Critical Rule 22 (Part 0.2 ownership).
- Phase 0.2 untouched at line 102.

## Anti-scope

All anti-scope items respected:
- `action: merge` for `/compress` Cap 5 not implemented — `grep -c "merged_into\|action: merge"` returned 0 ✓.
- Recompute of `.graphify_analysis.json` stale not added (only the existing Rule 22 mentions it) ✓.
- Non-`code` entity propagation not added — Phase 6.5 §6.5.3 explicitly filters to `type: code` only ✓.
- Orphan `vault_entity_path` validation not added — `unmatched_ids` is a warning (line 875), not a cleanup ✓.
- One-shot rebuild command not added ✓.
- Phase 0.2 untouched ✓.
- Read optimization for large graphs not added — single full read of `graph.json`, accepted for v0 ✓.

## Conclusion

Part 3 is complete and correct. Phase 6.5 cleanly closes the bidirectional bridge: every `code` entity touched by `/preserve` propagates `vault_entity_path` to the corresponding nodes in `<VAULT_PATH>/graphify-out/graph.json`, atomically and idempotently. Best-effort behavior preserves backward compat (vaults without `graphify-out/` continue to work). The change lands in the same commit as the entity diffs because Phase 6.5 runs before Phase 6's `git add`.

The unusual numbering ("Phase 6.5 before Phase 6") is spec-authorized and serves a deliberate purpose (single-commit atomicity). Pattern compliance is strong; no convention violations detected.

**Ready to ship.**
