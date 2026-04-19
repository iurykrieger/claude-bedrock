# Audit Report: teach-docling-integration-part-2

> Date: 2026-04-18
> Spec: `.vibeflow/specs/teach-docling-integration-part-2.md`
> Implementation: `skills/teach/SKILL.md` (Phase 0 auto-install + Phase 1.1 expanded + new Phase 1.5 + Phase 2/3 redirect + Phase 4 report + Critical Rules); `skills/setup/SKILL.md` (§1.2 dep table + new §1.2.1.1 docling auto-install + §1.2.2 report rows)
> Dependency satisfied: Part 1 audit PASS (`teach-docling-integration-part-1-audit.md`)

**Verdict: PASS**

## Scope of Audit

Spec: `/teach` accepts any docling-supported file format, converts to markdown before extraction, routes graphify output to a per-run temp dir, and delegates the merge to `/preserve` (Part 1). Auto-install on first use; `/setup` installs docling alongside graphify. Budget: ≤ 4 files. Anti-scope: no `/preserve`, `/graphify`, `/sync`, `/compress`, `/ask` changes; no extracted fetcher skill; no docs refresh (Part 3).

## Tests

No test runner in the project — plugin is markdown-only per `.vibeflow/index.md` ("No build system. No runtime"). Warn and continue per the audit skill's fallback rule.

## DoD Checklist

- [x] **1. Classification expansion** — `skills/teach/SKILL.md:144-154` — Phase 1.1 table replaces `Local path ending in .csv`, `.md/.txt/.pdf`, and explicit-binary rows with a single `Local file path (any existing file)` row and a `URL starting with http(s)` → `remote-binary` row. URL routing (Confluence/GDoc/GitHub) preserved. Prompt text updated to say "any file type — docling will convert it to markdown if supported". **PASS**.

- [x] **2. Docling conversion step (new Phase 1.5)** — `skills/teach/SKILL.md:261-332` — new top-level `## Phase 1.5 — Docling Conversion` section sits between Phase 1 and Phase 2; `docling` invoked via Bash at line 306. GitHub repos excluded at the phase intro and explicitly in Phase 1.5.2 ("excluding files inside `<repo-name>/` subdirectories of a `github-repo` source"). Confluence/GDoc outputs are already `.md` and thus fall into Phase 1.5.2 rule 1 (text-native skip). **PASS**.

- [x] **3. Routing + failure rules literally** — `skills/teach/SKILL.md:286-320` — rule 1 skips `.md/.txt/.csv` (text-native); rule 2 passes through docling-unsupported extensions with an explanatory note; rule 3 invokes docling and replaces the source file with converted markdown; rule 4's branch structure matches the spec exactly — raw passthrough for text-native failures (defensive; in practice text-native never reaches rule 4 because of rule 1), abort-with-cleanup for any other extension. **PASS**.

- [x] **4. Graphify target redirection + delegation update** — `skills/teach/SKILL.md:344` invokes `/graphify` with `--obsidian-dir $TEACH_TMP`; `:351` stores `GRAPHIFY_OUT_NEW="$TEACH_TMP/graphify-out"`. `:397` passes that variable to `/preserve` as `graphify_output_path`. Phase 3 IMPORTANT block at `:402-407` explicitly documents that `/teach` does not merge — `/preserve`'s Phase 0.2 owns that write. **PASS**.

- [x] **5. Auto-install** — `skills/teach/SKILL.md:97-132` — new `## Phase 0 — Ensure docling is installed` with pipx → pip fallback, one-line status on success/failure, `exit 1` on final failure with message pointing to `/bedrock:setup`. No user confirmation prompt (explicit "No user prompt" note at line 132). `skills/setup/SKILL.md:113` adds docling row to the dependency table; `:162-192` adds new §1.2.1.1 auto-install chain mirroring graphify's §1.2.1 precedent; `:220` and `:238-247` add the status row and user-facing install guidance. **PASS**.

- [x] **6. Report enrichment** — `skills/teach/SKILL.md:544-566` — Phase 4.2 report now includes a "Docling conversion (Phase 1.5)" table with per-file status (`converted` / `passed-through` / `failed-fallback`) plus a "Graphify merge (via /bedrock:preserve Phase 0.2)" block with `nodes_added` / `nodes_merged` / `edges_added` / `stale_flag_set` surfaced verbatim from `/preserve`'s `graphify_merge` return block. Explicit omission rule for GitHub repos documented. **PASS**.

- [x] **7. Craftsmanship gate** — `/teach` remains a pure fetcher/orchestrator; all writes (including the merge) flow through `/preserve` — enforced in Overview (`:89-91`) and Critical Rules row "/teach does NOT merge graphify output into the vault" (`skills/teach/SKILL.md:586`). Critical Rules table extended with 5 new rows covering the no-merge rule, silent auto-install, GitHub bypass, routing rule, failure fallback. No `conventions.md` Don'ts violations (see Convention section below). **PASS**.

## Pattern Compliance

- [x] **`.vibeflow/patterns/skill-architecture.md`** — follows the pattern. Evidence:
  - Phase structure preserved: each phase has an objective, step-by-step instructions, and an expected-outputs block.
  - Sub-phase decimal notation used correctly within Phase 1 (1.1, 1.2, 1.3, 1.4) and within Phase 1.5 (1.5.1, 1.5.2, 1.5.3).
  - Critical Rules table still a `| Rule | Detail |` table at the end; five new rows appended.
  - **Minor deviation — justified:** `## Phase 1.5 — Docling Conversion` renders as a top-level phase with a decimal number, slightly breaking the pattern's "Phase 0, 1, 2..." integer-sequential rule. Deviation is authorized by the spec's Scope section which explicitly names the new phase "Phase 1.5 — Docling Conversion" rather than renumbering the existing Phase 2/3/4 chain. Logical placement is correct (post-fetch, pre-extract), and sub-phases (1.5.1, 1.5.2, 1.5.3) follow the decimal convention cleanly.

- [x] **`.vibeflow/patterns/skill-delegation.md`** — *strengthens* the pattern. Evidence:
  - Overview (`skills/teach/SKILL.md:89-91`) explicitly states "/teach does not write to the vault directly, or merge graph state. All writes (including the graphify-output merge into the vault's cumulative `graphify-out/`) are done by `/bedrock:preserve`."
  - Phase 3.1 IMPORTANT block documents the single-write-point contract twice (entity classification → preserve; graph merge → preserve).
  - `/teach` invokes `/preserve` via the Skill tool (no direct Python API usage).
  - `source_url` and `source_type` still threaded through for provenance tracking.

- [x] **`.vibeflow/patterns/vault-writing-rules.md`** — follows the pattern. Evidence:
  - Cleanup rule preserved: `/tmp` removed after `/preserve` confirms (Phase 4.1, Critical Rules row).
  - Best-effort for *external sources* (Confluence MCP, GDoc API, GitHub MCP, WebFetch) unchanged. The new docling abort-on-failure applies to a *local dependency*, not an external source — distinct categories, no conflict with the "never block on failed external sources" convention.
  - No frontmatter/wikilink/tag writes introduced by this change (teach remains a pure orchestrator).

## Convention Violations

None newly introduced by this change.

**Pre-existing inconsistency noted (not introduced here):** `skills/setup/SKILL.md` Critical Rule #3 says "NEVER auto-install dependencies — only provide instructions", but the existing graphify auto-install (§1.2.1) and the new docling auto-install (§1.2.1.1) both contradict it. This rule is stale and should be updated in a dedicated follow-up (out of scope for Part 2's anti-scope). Not a blocking violation — the spec explicitly authorizes the docling auto-install chain.

## Observations (non-blocking)

1. **`<auto>` placeholder ambiguity.** `skills/teach/SKILL.md:306` uses `docling --from <auto>` with angle brackets. In the skill's placeholder convention `<...>` denotes a runtime-substituted value; the intended meaning here is the literal docling CLI value `auto`. At runtime an executing agent would likely resolve this to `auto` (or omit `--from` since docling auto-detects by default), but the notation is mildly ambiguous. Consider rewriting to `docling --to md --output "$TEACH_TMP" "<relative-file-path>"` (relying on docling's auto-detect) in a future edit. Not a DoD gap.

2. **Hardcoded docling extension list.** `skills/teach/SKILL.md:273-279` embeds the supported-extensions list inline. When docling adds new formats, the list must be updated manually. The spec's technical-decisions table authorized this trade-off (runtime `docling --list-formats` rejected for latency). Documented — no action needed.

3. **Stale Critical Rule in `/setup`.** As noted above, Rule #3 contradicts two existing auto-install sections. Worth a small follow-up edit to align the rule with current behavior.

4. **`auto` install chain never exercised in CI.** Because the project has no test runner, the auto-install chain (pipx → pip → abort) is only verifiable manually. When a user first invokes `/teach` on a system without docling, the chain runs in production. Document the first-run latency in the user-facing docs during Part 3.

## Budget

- Files changed: **2 / ≤ 4** (`skills/teach/SKILL.md`, `skills/setup/SKILL.md`). ✓
- Anti-scope respected: `/preserve`, `/graphify`, `/sync`, `/compress`, `/ask` untouched; no extracted fetcher skill; no OCR/batch/version pinning; no user confirmation prompts; documentation files (README, CLAUDE.md, etc.) left for Part 3. ✓

## Verdict Rationale

All 7 DoD checks PASS with concrete line-level evidence. All 3 applicable patterns followed (skill-delegation *strengthened*; skill-architecture has one minor, spec-authorized deviation on Phase 1.5 numbering). Zero new convention violations; one pre-existing inconsistency flagged for future cleanup. Four non-blocking observations recorded. Budget respected. Anti-scope respected. Dependency on Part 1 satisfied (PASS audit on record).

**Ready to ship.** Part 3 (documentation refresh) is unblocked.

## Next Steps

- Implement Part 3: `/vibeflow:implement .vibeflow/specs/teach-docling-integration-part-3.md`
- Consider a small follow-up spec to: (a) fix the `<auto>` placeholder to literal `auto` or drop `--from`, and (b) update `skills/setup/SKILL.md` Critical Rule #3 to reflect the accepted auto-install pattern.
