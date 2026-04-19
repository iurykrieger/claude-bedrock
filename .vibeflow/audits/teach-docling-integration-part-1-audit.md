# Audit Report: teach-docling-integration-part-1

> Date: 2026-04-18
> Spec: `.vibeflow/specs/teach-docling-integration-part-1.md`
> Implementation: `skills/preserve/SKILL.md` (Phase 0 restructure + merge sub-phase)

**Verdict: PASS**

## Scope of Audit

Spec: add a pre-write merge of incoming graphify output into the vault's `<VAULT_PATH>/graphify-out/`, with append-only semantics, backward-compat for legacy callers, and merge stats threaded through to the skill's return payload. Budget: ≤ 4 files. Anti-scope: no changes to `/teach`, `/graphify`, `/sync`, `/compress`, `/ask`, `/setup`; no new helper skill.

## Tests

No test runner in this project — `.vibeflow/index.md` declares "No build system. No runtime. Just markdown files, AI agents, and your Obsidian vault." No `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, or similar. Per the audit skill's fallback rule for projects without a test runner: **warn and continue with manual verification of DoD evidence**. Audit does not auto-FAIL on missing tests when tests are genuinely non-existent in the project stack.

## DoD Checklist

- [x] **1. Mode detection + backward compat** — `skills/preserve/SKILL.md:106-117` uses `pwd -P` on both paths (after `cd`) and compares resolved absolute paths. When equal, Phase 0.2 is a documented no-op. Second skip path at line 117 covers free-form and structured-entity inputs that don't carry `graphify_output_path`. **PASS**.

- [x] **2. Node metadata merge** — `skills/preserve/SKILL.md:186-204` Python block: `_dedup_sources_by_url` unions by URL (keeps first occurrence per URL); `updated_at` uses lexical comparison (valid for `YYYY-MM-DD` format); `labels` and `tags` unioned via `_union` (dedup by stringified JSON to handle string-or-dict cases); `nodes_merged` counter increments only on collision path. **PASS**.

- [x] **3. Edge dedup by `(source, target, type)`** — `skills/preserve/SKILL.md:207-219`: `_edge_key` tuple accepts either `type` or `relation` field (handling graphify's NetworkX variants); `seen_edges` set starts seeded from the existing graph's edges, so duplicates from incoming are skipped; `edges_added` only increments on new unique edges; final count is strictly non-decreasing. **PASS**.

- [x] **4. Analysis staleness marker** — `skills/preserve/SKILL.md:282-297`: inline Python reads `.graphify_analysis.json`, adds `data["stale"] = True` at the top level, writes back. Other fields preserved (no overwrites beyond that key). File-missing branch skips cleanly (`stale_flag_set=false`). **PASS**.

- [x] **5. Per-file append behavior** — `obsidian/*.md`: `skills/preserve/SKILL.md:247-259` — existing files get `\n\n---\n\n` separator + new content appended; missing files copied. `GRAPH_REPORT.md`: `skills/preserve/SKILL.md:266-278` — existing file gets dated `# Merge on YYYY-MM-DD` section appended; missing file copied. Existing content preserved verbatim in both cases. **PASS**.

- [x] **6. First-ingestion edge case** — `skills/preserve/SKILL.md:133-141`: `if [ ! -d "<VAULT_PATH>/graphify-out" ]` branch does `cp -R` of the incoming directory to the vault location (wholesale promotion), records stats-as-if-all-were-new, skips to Step 7. No re-merge pass triggered. **PASS**.

- [x] **7. Craftsmanship gate** — Phase numbering: `Phase 0` kept with decimal sub-phases `0.1` (vault sync) and `0.2` (merge), which aligns with `.vibeflow/patterns/skill-architecture.md`'s rule "sub-phases use decimal notation". Critical Rules table (`skills/preserve/SKILL.md:737-740`) updated with four new rows (19–22) covering append-only merge, backward compat, atomicity, and the stale-not-recomputed convention. Phase 7 report (`skills/preserve/SKILL.md:696-711`) includes a new "Graphify merge" section and a `graphify_merge:` return-payload block. Single-write-point discipline is not just preserved — it is *strengthened*: writes to `graphify-out/` that previously went through `/graphify` directly now route through `/preserve`. No `conventions.md` Don'ts violated (see Convention section below). **PASS**.

## Pattern Compliance

- [x] **`.vibeflow/patterns/skill-architecture.md`** — follows correctly. Evidence:
  - Phase structure remains sequential (Phase 0 → Phase 1 → ...) per the pattern's rule.
  - Sub-phase decimal notation used: `### 0.1 Vault Sync`, `### 0.2 Merge Incoming Graphify Output`.
  - Numbered inline Steps 1–8 within the sub-phase provide the "step-by-step instructions and expected outputs" structure the pattern requires.
  - Critical Rules table is still a `| # | Rule |` table at the end; four new rows appended rather than reformatting the existing structure.

- [x] **`.vibeflow/patterns/skill-delegation.md`** — follows correctly (and *strengthens* the pattern). Evidence:
  - `/preserve` remains the single write point; the new merge logic is inside `/preserve`, not in a caller.
  - Backward-compat path (`graphify_output_path == <VAULT_PATH>/graphify-out/`) means legacy callers — including `/bedrock:sync` in its current form — continue to work without modification, preserving the pattern's "structured input contract" between skills.
  - Return payload is extended with a new `graphify_merge:` block, keeping the caller-return contract explicit rather than side-effect-based.

- [x] **`.vibeflow/patterns/vault-writing-rules.md`** — follows correctly. Evidence:
  - Append-only semantics uniformly applied across `graph.json` nodes, `graph.json` edges, `obsidian/*.md`, and `GRAPH_REPORT.md`. No deletion branches exist in the merge code.
  - Sources-field semantics (append-only, dedup by URL, most-recent first) applied at the node level via `_dedup_sources_by_url` — matches the entity-level rule for `sources` frontmatter.
  - `updated_at` take-latest rule applied for node metadata, mirroring the entity-level rule.
  - Phase 0.1 preserves the `git pull --rebase origin main` pre-write sync.

## Convention Violations

None. Checked against `.vibeflow/conventions.md` Don'ts list:

- No flat tags introduced — N/A (no new tags in the skill).
- No path-qualified wikilinks introduced — N/A.
- No display-name wikilinks — N/A.
- No deleted content from people/teams/topics — N/A (merge operates on graph state, not entity markdown).
- No removed wikilinks or frontmatter fields — N/A (graph.json is not entity markdown).
- No credentials, tokens, PANs, CVVs committed — verified by reading the changes.
- "Do NOT write entities directly from detection skills" — *strengthened* by this change.
- "Do NOT block workflows for failed external sources" — respected; merge is best-effort only on its own failure paths (abort before `mv` if validation or Python block fails), not for upstream external sources.
- "Do NOT use subagents for MCP calls" — N/A.

## Observations (non-blocking)

1. **Merge-before-user-confirmation semantics.** Phase 0.2 runs before Phase 3 (user confirmation). If the user rejects the entity proposal in Phase 3, the `graphify-out/` has already been mutated. This is consistent with the spec's "Phase 0" placement — the merge is infrastructure, not an entity write — and mirrors Phase 0.1's existing `git pull --rebase` which also mutates before confirmation. Not a DoD failure. Worth surfacing if future UX work wants a confirm-before-merge variant.

2. **Python error-propagation in Step 3.** The atomic swap `mv` on line 237 runs after the heredoc exits regardless of Python's exit code when bash lacks `set -e`. The prose at line 240 ("If the Python block exits non-zero, abort without running the `mv`") is a procedural instruction the executing agent must honor. Since this is a markdown procedural skill (executed by Claude, not a shell script), this is acceptable but a shell-script port would need an explicit `|| exit 1` check.

3. **`stale: true` contract is one-sided until Part 1's downstream consumer lands.** `/bedrock:compress` does not yet read the `stale` field. The spec correctly places that read out of scope (follow-up spec). `.graphify_analysis.json` will accumulate `stale: true` across merges with no observable downstream effect until that follow-up ships. Documented in the spec's Risks section.

## Budget

- Files changed: **1 / ≤ 4** (only `skills/preserve/SKILL.md`). ✓
- Anti-scope respected: no changes to `/teach`, `/graphify`, `/sync`, `/compress`, `/ask`, `/setup`, no new helper skill. ✓

## Verdict Rationale

All 7 DoD checks PASS with direct evidence in `skills/preserve/SKILL.md`. All three applicable patterns followed (one *strengthened*). Zero convention violations. Three non-blocking observations recorded. Budget and anti-scope respected. Tests: project has none by design.

**Ready to ship.** Part 2 (teach docling integration) and Part 3 (docs refresh) are unblocked.

## Next Steps

- Implement Part 2: `/vibeflow:implement .vibeflow/specs/teach-docling-integration-part-2.md`
- Part 3 (docs refresh) waits until Parts 1 & 2 are both in place.
- Consider a follow-up spec for `/bedrock:compress` to read `.graphify_analysis.json`'s `stale: true` flag and trigger recomputation (Observation #3).
