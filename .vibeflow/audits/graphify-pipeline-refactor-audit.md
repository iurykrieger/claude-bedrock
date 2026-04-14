# Audit Report: graphify-pipeline-refactor

> Audited on 2026-04-14
> Spec: `.vibeflow/specs/graphify-pipeline-refactor.md`

**Verdict: PASS**

## DoD Checklist

- [x] **Check 1 — `/teach` invokes `/graphify` via Skill tool, zero Python API calls remain.**
  Evidence: `skills/teach/SKILL.md:165-168` uses Skill tool invocation (`/graphify $TEACH_TMP --mode deep --obsidian --obsidian-dir <vault_path>`). Grep for `graphify.(detect|build|extract|cluster|analyze|export|cache)` returns only the Critical Rules table (line 296) which says "NEVER call" — a negative instruction. Grep for `import graphify` / `from graphify` / `.graphify_python` returns 0 matches. Grep for `graphify-out/src/` returns 0 matches.

- [x] **Check 2 — `/teach` fetches all remote content to `/tmp/bedrock-teach-<ts>/`.**
  Evidence: `skills/teach/SKILL.md:67-77` creates tmp directory. Six fetch strategies documented (lines 83-148): GitHub clone (1.3.1), Confluence (1.3.2), Google Docs (1.3.3), remote URL (1.3.4), local file (1.3.5), local directory (1.3.6). All target `$TEACH_TMP/`.

- [x] **Check 3 — `/preserve` accepts graphify output as third input mode.**
  Evidence: `skills/preserve/SKILL.md:111-176` — Phase 1.3 "Graphify output input" with 8 processing steps. Reads `graph.json` (step 1), obsidian files (step 2), analysis (step 3). Description (line 4-7) and Overview (line 31) updated to mention graphify output.

- [x] **Check 4 — `/preserve` owns entity classification for graphify input.**
  Evidence: `skills/preserve/SKILL.md:141-148` — step 4 "Classify graphify nodes into vault entity types — /preserve owns this classification" with full classification rules (code → knowledge-node, document → entity definitions, paper → topic/fleeting, god nodes → actor/topic, Zettelkasten fallback → fleeting). `/teach` has zero classification logic — confirmed via grep: only negative instructions ("does NOT classify") at lines 219-220, 298.

- [x] **Check 5 — `/setup` declares graphify as required dependency.**
  Evidence: `skills/setup/SKILL.md:99` — "**Required.** Extraction engine for all `/bedrock:teach` ingestion." Missing message (lines 117-122): "This is REQUIRED for /bedrock:teach to work." Other dependencies remain optional.

- [x] **Check 6 — `/teach` cleans up `/tmp` after /preserve confirms.**
  Evidence: `skills/teach/SKILL.md:240-251` — Phase 4.1 "After `/bedrock:preserve` confirms completion, remove the temporary directory". Critical Rules table (line 300): "Remove only after /preserve confirms completion, not after graphify finishes."

- [x] **Check 7 — No violations of conventions.md Don'ts.**
  Evidence: See Pattern Compliance below.

## Pattern Compliance

- [x] **Skill Architecture** — Both skills follow the pattern correctly.
  - `/teach`: YAML frontmatter (lines 1-12), Plugin Paths (16-25), Overview with agent type declaration "fetcher and orchestrator agent" (29-44), 4 numbered phases (48, 161, 207, 238), Critical Rules table (292-305).
  - `/preserve`: YAML frontmatter (1-11), Plugin Paths (15-24), Overview (28-36), Phase 0 + 7 numbered phases, Critical Rules table (584-602). New Phase 1.3 follows decimal sub-phase convention.
  - `/setup`: Structure unchanged.

- [x] **Skill Delegation** — Delegation contract preserved and simplified.
  - `/teach` delegates to `/preserve` via Skill tool (line 224). Never writes entities.
  - Contract: graphify output path + source_url + source_type (lines 213-216).
  - `/preserve` receives and processes via Phase 1.3, converts to internal structured format, proceeds to existing Phases 2-7.
  - Provenance flow: source_url/source_type passed from teach → preserve → entity `sources` field (Phase 4.3).

- [x] **Vault Writing Rules** — All rules preserved as-is.
  - No changes to frontmatter conventions, wikilink rules, tag hierarchy, update rules, git workflow, or callout conventions in /preserve Phases 4-7.
  - Knowledge-node specific rules preserved in Phase 4.1.2.
  - Bidirectional linking graph unchanged in Phase 5.

## Convention Violations

None found. All conventions from `.vibeflow/conventions.md` are respected:
- File organization: skills in `skills/<name>/SKILL.md` — preserved.
- Skill structure: frontmatter → Plugin Paths → Overview → Phases → Critical Rules — followed in all 3 files.
- Don'ts: no flat tags, no path-qualified wikilinks, no direct entity writes from detection skills, no subagents for MCP calls, no blocking on external sources — all respected.

## Tests

No test runner detected (markdown-only Claude Code plugin — no package.json, pyproject.toml, Cargo.toml, go.mod, or equivalent). Manual verification required.

## Stats

| File | Before | After | Change |
|---|---|---|---|
| `skills/teach/SKILL.md` | 654 lines | 305 lines | -53% (349 lines removed) |
| `skills/preserve/SKILL.md` | 535 lines | 603 lines | +13% (68 lines added) |
| `skills/setup/SKILL.md` | 1052 lines | 1059 lines | +0.7% (7 lines changed) |
| **Total** | — | — | 253 insertions, 525 deletions |

## Summary

The refactoring cleanly separates concerns:
- **/teach** is now a thin fetcher + orchestrator (305 lines, down from 654). No graphify internals, no entity classification, no vault writes.
- **/preserve** gains a third input mode (Phase 1.3) that reads graphify output, classifies nodes, and converts to the existing internal format. All downstream phases (matching, proposal, execution, linking, publishing, reporting) are untouched.
- **/setup** marks graphify as required, with clear messaging when missing.
