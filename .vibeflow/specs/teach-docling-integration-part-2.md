# Spec: /bedrock:teach — docling conversion + append pipeline

> Part 2 of 3 — Split from `.vibeflow/prds/teach-docling-integration.md`
> Generated via /vibeflow:gen-spec on 2026-04-18

## Objective

`/bedrock:teach` accepts any docling-supported file format, converts it to markdown before extraction, routes `/graphify` output to a per-run temp dir, and delegates the merge into the vault to `/bedrock:preserve` (Part 1).

## Context

`/teach` today only supports Confluence, Google Docs, GitHub, remote URL, CSV, Markdown, TXT, and PDF. Users with DOCX reports, PPTX decks, XLSX spreadsheets, HTML archives, EPUB, or text-bearing images must pre-convert manually. Docling (`https://github.com/docling-project/docling`) is a universal file → markdown converter maintained by the docling project. With Part 1 landed (append merge in `/preserve`), `/teach` can safely route any fetched file through docling, hand graphify's output to `/preserve`, and trust that the vault's cumulative graph grows instead of being overwritten.

## Definition of Done

1. **Classification expansion:** `/teach` Phase 1.1 accepts any local file path and any downloadable remote binary. The allowlist gate for local files is removed. URL-based routing (Confluence / GDoc / GitHub / generic HTTP) is unchanged.
2. **Docling conversion step:** between fetch and `/graphify`, `/teach` invokes `docling <file>` via Bash on any fetched file whose type is docling-supported and which is NOT a GitHub repo and NOT already-markdown output from the Confluence/GDoc fetchers. Converted markdown replaces the source file in `$TEACH_TMP`.
3. **Routing and failure rules implemented literally:** (a) docling-supported type → run docling; (b) docling-unsupported type → raw passthrough to graphify; (c) docling invoked and fails → raw passthrough for `.md`/`.txt`/`.csv`, abort with clean error and `$TEACH_TMP` cleanup for all other types.
4. **Graphify target redirection + delegation update:** `/teach` invokes `/graphify` with output target `$TEACH_TMP/graphify-out-new/` (not the vault). `/teach` delegates to `/preserve` passing that temp path as `graphify_output_path` (relies on Part 1's Phase 0 to merge).
5. **Auto-install:** `/teach` installs docling silently (one-line status message, no prompt) if missing, before any fetch. `/bedrock:setup` also installs docling as part of its dependency check phase (analogous to graphify autoinstall). If install fails, `/teach` aborts with an error pointing to `/bedrock:setup`.
6. **Report enrichment:** Phase 4 report includes per-file docling status (`converted` / `passed-through` / `failed-fallback`) and surfaces merge stats (`nodes_added`, `nodes_merged`, `edges_added`, `stale_flag_set`) returned by `/preserve`.
7. **Craftsmanship gate:** `/teach` remains a pure fetcher/orchestrator — no direct vault file writes; all writes still flow through `/preserve`. Follows `skill-architecture.md` (numbered phases, Critical Rules table updated) and `skill-delegation.md`. No violations from `.vibeflow/conventions.md` Don'ts (no subagents for MCP calls, no blocking on failed external sources, best-effort semantics preserved).

## Scope

- `skills/teach/SKILL.md`:
  - Add docling auto-install check at the top (before Phase 1)
  - Phase 1.1: remove local-file allowlist, update classification table, keep URL routing
  - Phase 1.3.5 (local files): retain tmp copy
  - **New Phase 1.5 — Docling Conversion:** conversion loop with routing + failure rules
  - Phase 2.1: change graphify output target to `$TEACH_TMP/graphify-out-new/`
  - Phase 3 (delegation): change `graphify_output_path` argument to the temp dir
  - Phase 4 report: add docling status section + merge stats passthrough
  - Critical Rules table: add docling behavior, temp-dir contract, fallback rules
- `skills/setup/SKILL.md`:
  - Add docling install to the dependency check phase (alongside graphify)

## Anti-scope

- **No changes to `/preserve`** (Part 1's territory).
- **No changes to `/graphify`.**
- **No OCR tuning, table extraction config, or docling pipeline customization** — defaults only.
- **No multi-file batch mode** — `/teach` still takes one source per invocation.
- **No extracted `skills/docling-to-markdown/SKILL.md`** — inline Bash invocation.
- **No new fetcher layers** — Confluence/GDoc fetchers bypass docling entirely.
- **No user confirmation prompt** for the auto-install step.
- **No docling version pinning** — install latest via `pip`/`uvx`.
- **No documentation refresh** — Part 3's territory.
- **No changes to `/sync`, `/compress`, `/ask`.**

## Technical Decisions

| Decision | Alternatives considered | Rationale |
|---|---|---|
| **Docling invoked inline via Bash (`docling <file>`)** | Extracted fetcher-style skill | Only one consumer today. Extraction is premature abstraction. |
| **Auto-install at top of `/teach`, before fetch** | Lazy install on first docling call | Fail-fast: if install will fail, fail before burning time on fetch. |
| **Install mechanism: `pipx install docling` (fallback `pip install --user docling`)** | `uvx docling` (ephemeral per-call) | Persistent install avoids model re-download on every `/teach`. `pipx` isolates deps from system Python. |
| **Docling-supported detection: known extension list, maintained inline** | `docling --list-formats` at runtime | Runtime check adds latency per call; list is small and slow-changing (pdf, docx, pptx, xlsx, html, md, adoc, png, jpg, jpeg, tiff, epub). Revisit if docling grows. |
| **Fallback rule for docling failure: raw passthrough only for text-native types (`.md`/`.txt`/`.csv`)** | Universal passthrough; universal abort | Binary formats without docling output cannot be graphified; passthrough would pollute the graph. Text formats degrade gracefully. |
| **Graphify output target `$TEACH_TMP/graphify-out-new/`** | Write directly into vault with in-process append | Keeps atomicity — if `/preserve` fails, vault is untouched. |
| **Status surfacing per file in the report** | Summary counts only | Users need to see which files converted and which passed through to trust the result. |

## Applicable Patterns

- **`.vibeflow/patterns/skill-architecture.md`** — New phase is `## Phase 1.5 — Docling Conversion`; Critical Rules table updated.
- **`.vibeflow/patterns/skill-delegation.md`** — `/teach` stays a fetcher/orchestrator; all writes delegate to `/preserve`.
- **`.vibeflow/patterns/vault-writing-rules.md`** — Cleanup `/tmp` only after `/preserve` confirms; best-effort for external sources; never block ingestion on best-effort failures.

No new patterns introduced.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| First-run model download takes minutes (>1 GB) | High | Low | One-time cost; report a warning on auto-install; users re-running subsequent `/teach` invocations hit the cache. |
| Docling aborts mid-conversion on a large PDF | Medium | Medium | Timeout handling: treat timeout as a failure per Phase 1.5 rules; abort for non-text types. |
| Docling install fails in restricted environments (no `pipx`, no network) | Medium | Medium | Clear error message pointing to `/bedrock:setup` and docling install docs. |
| Docling output doesn't round-trip through graphify cleanly (tables, images) | Low | Medium | Docling produces standard CommonMark; graphify already handles markdown. If issues emerge, follow-up spec. |
| Edge case: user passes a GitHub URL pointing at a single file (not a repo) | Low | Low | Keep existing URL routing: GitHub → clone-or-error. Non-repo GitHub URLs stay out of scope. |
| Auto-install competes with `/bedrock:setup` install (race / double install) | Low | Low | `pipx install docling` is idempotent; auto-install checks presence first (`command -v docling`). |

## Dependencies

- `.vibeflow/specs/teach-docling-integration-part-1.md` — `/preserve` must accept `graphify_output_path` as a temp dir and run its new Phase 0. Without Part 1, `/teach`'s new temp-dir target would leave the vault's `graphify-out/` untouched.
