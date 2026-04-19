# PRD: Docling integration in /teach for universal file-type support

> Generated via /vibeflow:discover on 2026-04-18

## Problem

Today, `/bedrock:teach` accepts a narrow set of inputs: Confluence, Google Docs, GitHub repos, remote URLs, CSV, Markdown, TXT, and PDF. Any other format users encounter in the wild — DOCX reports, PPTX decks, XLSX spreadsheets, HTML archives, scanned PDFs, EPUB, images with text — must be manually converted before ingestion. This creates friction for users whose organizational knowledge lives in heterogeneous files and makes `/teach` feel partial as a Second Brain ingestion front door.

A secondary problem compounds the first: `/graphify` currently writes its output to `<VAULT_PATH>/graphify-out/` as a full overwrite. Each `/teach` run replaces the previous graph instead of enriching it. The vault's graph therefore reflects only the last ingestion, not the accumulated knowledge across sessions. Users expect the graph to grow.

## Target Audience

Bedrock vault operators who ingest mixed-format documents into their Second Brain — primarily internal-tools/knowledge-management users with organizational docs in Office formats, and researchers ingesting papers, presentations, and reports. Secondary: automation flows (`/bedrock:sync`) that may re-ingest sources whose canonical format is not markdown.

## Proposed Solution

Insert **docling** (`https://github.com/docling-project/docling`) as a universal file → markdown converter inside `/teach`'s fetch phase, and change the graphify invocation so it appends to the vault's cumulative graph rather than overwriting it.

High-level pipeline (no implementation details):

0. **Classify** — `/teach` accepts any file type (removes the allowlist gate in Phase 1.1 for local files and remote binaries).
1. **Fetch/Extract** — Existing logic unchanged: GitHub → clone; Confluence/GDoc → existing fetchers (MCP → API → browser); other URLs → download binary to `/tmp`.
2. **Convert via docling** — If the fetched content is a non-GitHub, non-already-markdown file, run docling to convert it to markdown in place within `$TEACH_TMP`.
3. **Graphify** — Invoke `/graphify` against `$TEACH_TMP`, directing its output to a per-run temp directory (`$TEACH_TMP/graphify-out-new/`, not the vault).
4. **Delegate to `/bedrock:preserve`** — `/teach` passes `$TEACH_TMP/graphify-out-new/` as input. `/preserve` owns the merge into `<VAULT_PATH>/graphify-out/` (append-only semantics) as a new Phase 0, then continues with its existing entity classification/write flow. The single-write-point rule is preserved — all writes to `graphify-out/` happen inside `/preserve`.
5. **Cleanup** — `/teach` removes `$TEACH_TMP` after `/preserve` returns. The merged `graphify-out/` in the vault is persisted.
6. **Report** — Existing report format, enriched with docling conversion status (from `/teach`) and merge stats + entity writes (from `/preserve`).

Setup-side: `/bedrock:setup` provisions docling on new vaults. Existing vaults that invoke `/teach` without docling installed get an auto-install prompt/execution at first use, following the precedent set by `graphify-setup-autoinstall`.

## Success Criteria

1. A user can run `/bedrock:teach <local-docx-path>` (or `.pptx`, `.xlsx`, `.html`, `.epub`, `.png` with text, or any other docling-supported format) and receive entities in their vault — no manual conversion.
2. After two sequential `/teach` invocations against different sources, `<VAULT_PATH>/graphify-out/graph.json` contains the union of nodes and edges from both runs. On node-ID collision, the merged node's `sources` field is the union of both runs and `updated_at` is the most recent. No node from run 1 is lost by run 2.
3. After a merge (executed inside `/bedrock:preserve`), `.graphify_analysis.json` carries a `stale: true` (or equivalent) marker, and `/bedrock:compress` recomputes it on its next invocation.
4. `/bedrock:setup` on a fresh vault leaves docling installed and callable; re-running `/teach` on a pre-existing vault without docling silently installs it (one-line status, no prompt) and then proceeds.
5. If docling fails on a fallback-eligible file type (`.md`, `.txt`, `.csv`), `/teach` continues with the current raw-passthrough behavior. For other types (e.g. `.docx`), `/teach` aborts with a clear error and cleans up `$TEACH_TMP`.
6. `README.md`, `CLAUDE.md`, and the SKILL.md files listed in Scope v0 consistently describe `/teach`'s input scope as "any docling-supported file format" plus the pre-existing URL fetchers. No documentation still claims the old narrow allowlist.

## Scope v0

### `/teach` changes
- Extend Phase 1.1 classification to accept any local path or downloadable remote binary (remove type allowlist gate for local paths; keep existing URL-type routing for Confluence/GDoc/GitHub).
- Add a **docling conversion step** (between fetch and graphify) that runs inline via `docling <file>` Bash invocation against any fetched file whose type is in docling's supported list. GitHub repos are never routed through docling (they follow the existing clone → graphify flow). Confluence/GDoc outputs are already markdown and bypass docling.
  - **Routing rule:** if docling supports the file type → run docling. If docling does not support the file type → raw passthrough (graphify handles whatever it gets).
  - **Failure fallback:** if docling is invoked and fails → raw passthrough for `.md`/`.txt`/`.csv`, abort with clean error for all other types. On abort, `$TEACH_TMP` is cleaned up.
- Change `/graphify` invocation to output to `$TEACH_TMP/graphify-out-new/` instead of `<VAULT_PATH>/graphify-out/`.
- Change the delegation to `/bedrock:preserve`: pass `$TEACH_TMP/graphify-out-new/` as the `graphify_output_path` argument (instead of the vault's `graphify-out/`). `/preserve` owns the merge.
- Add **auto-install check** at the top of `/teach` that installs docling silently if missing, emitting a one-line status message before proceeding. No user confirmation prompt.
- Update Phase 4 report to include docling conversion status per file; pull merge stats from `/preserve`'s return payload.

### `/preserve` changes
- Add a new **Phase 0 — Merge incoming graphify output** that runs before the existing classification/write flow:
  - Input: `graphify_output_path` pointing to a temp dir (`$TEACH_TMP/graphify-out-new/`).
  - Merge into `<VAULT_PATH>/graphify-out/`:
    - `graph.json`: union of nodes and edges. On node-ID collision, **merge metadata** — union `sources` arrays, take most-recent `updated_at`, union tag/label sets. On edge `(source, target, type)` collision, dedupe (drop the newer duplicate).
    - `obsidian/*.md`: per-file append; if a file already exists, preserve existing content and append new sections with a separator.
    - `.graphify_analysis.json`: **mark stale** (set a `stale: true` flag or equivalent). No inline recomputation.
    - `GRAPH_REPORT.md`: append a new dated section.
  - After merge, subsequent phases read from the merged `<VAULT_PATH>/graphify-out/` for entity classification (as today).
- Handle the first-ever ingestion edge case: if `<VAULT_PATH>/graphify-out/` does not exist yet, the "merge" is effectively a rename/copy of the incoming temp output.
- Include merge stats (nodes added, nodes merged, edges added, analysis staleness flag set) in `/preserve`'s return payload so `/teach` can surface them in the report.
- Single git commit continues to cover both the merged graph and the entity changes.
- **Backward compatibility:** if `graphify_output_path` already points at `<VAULT_PATH>/graphify-out/` (legacy call sites), skip Phase 0 and proceed as today.

### `/bedrock:setup` changes
- Add **docling install** (new phase or extend an existing dependency phase), analogous to the graphify autoinstall precedent.

### Documentation refresh
- Update user-facing references to the `/teach` supported-source list, in all of:
  - `README.md` (lines 27 and 101 specifically mention the narrow type list)
  - `CLAUDE.md` (plugin root)
  - `skills/teach/SKILL.md` — frontmatter `description` field and Phase 1.1 classification table
  - `skills/setup/SKILL.md` — dependency check section (add docling alongside graphify)
  - `skills/ask/SKILL.md` — any mention of teach's input scope
  - `docs/` assets if any text enumerates formats
- Consistent new wording: "any file format supported by docling" plus existing URL fetchers (Confluence, Google Docs, GitHub).
- **Update documentation** to reflect the expanded format support. All user-facing references to "supported source types" must be consistent:
  - `README.md` — lines 27 (Features) and 101 (Day-to-day loops) mention the narrow type list; broaden to "any file format docling supports" with representative examples.
  - `CLAUDE.md` (plugin root and user-facing docs) — skill table description of `/bedrock:teach` if it enumerates types.
  - `skills/teach/SKILL.md` — frontmatter `description` field and the Phase 1.1 classification table.
  - `skills/setup/SKILL.md` — dependency check section (add docling alongside graphify).
  - `skills/ask/SKILL.md` — any mention of teach's input scope.
  - `docs/` assets referenced from README, if any text mentions formats.

## Anti-scope

- **No modifications to `/graphify`.** Append semantics live entirely inside `/bedrock:preserve` as a pre-write merge. `/graphify` itself continues to overwrite its own output directory (now a per-run temp dir).
- **No extracted `skills/graph-merge/SKILL.md` helper.** Merge logic lives inline in `/preserve`'s new Phase 0. Can be extracted later if/when a second consumer (e.g. `/bedrock:sync`) needs it.
- **No inline recomputation of `.graphify_analysis.json`.** `/preserve` marks it stale; `/bedrock:compress` owns the recomputation.
- **No extracted `skills/docling-to-markdown/SKILL.md` fetcher-style skill.** Docling runs inline via Bash inside `/teach`. (Can be extracted later if/when `/bedrock:sync` also needs it.)
- **No OCR tuning, table extraction config, or docling pipeline customization.** Use docling defaults.
- **No multi-file batch mode.** `/teach` still takes one source argument per invocation.
- **No new fetcher layers.** Confluence/GDoc/GitHub fetchers are unchanged — their output is already markdown, so they bypass docling entirely.
- **No docling version pinning strategy, model cache management, or pre-download UX.** Install once via `/bedrock:setup` or lazy auto-install, and accept the first-run model download latency.
- **No changes to `/bedrock:sync`'s own ingestion logic.** Sync continues to call its existing fetchers. (If sync later needs docling or the merge step, that's a follow-up PRD.)
- **No rollback or versioning of the cumulative graph.** Once a node is merged in, it stays until `/bedrock:compress` dedupes it.
- **No new MCP integrations.**
- **No user confirmation prompt for the docling auto-install step.** Silent install + one-line status message only.

## Technical Context

**Relevant files in the codebase:**
- `skills/teach/SKILL.md` (352 lines, English) — edits in Phases 1.1 (classify), 1.3.5 (local-file fetch), 2.1 (graphify invocation target dir), 3 (delegation input), 4 (report). Plus a new docling conversion sub-phase and an auto-install check.
- `skills/preserve/SKILL.md` (535 lines) — new **Phase 0 — Merge incoming graphify output** inserted before existing phases. Must handle the first-ingestion edge case (no existing `graphify-out/`) and the legacy call site compatibility check.
- `skills/setup/SKILL.md` (913 lines) — docling install step, analogous to graphify autoinstall (`.vibeflow/prds/graphify-setup-autoinstall.md`).
- `skills/sync/SKILL.md` — **no logic changes** (uses `/preserve`, inherits the merge behavior for free).

**Budget note:** `.vibeflow/index.md` suggests ≤ 4 files per task. The three SKILL.md changes above plus the documentation refresh (README.md, CLAUDE.md, etc.) will exceed this budget. Recommend gen-spec splits into at least two specs — e.g. `spec-1: preserve-graphify-merge` and `spec-2: teach-docling-integration` — so each spec stays under budget and can be implemented/reviewed independently. The merge work in `/preserve` is also useful on its own and could land first.

**Patterns to follow (from `.vibeflow/patterns/`):**
- `skill-architecture.md` — phased execution with numbered `## Phase N — <Title>` sections, `## Critical Rules` table at end.
- `skill-delegation.md` — `/teach` remains a fetcher/orchestrator; single-write-point (`/bedrock:preserve`) is preserved.
- `vault-writing-rules.md` — `updated_at`/`updated_by` conventions, git workflow (`commit-push`/`commit-push-pr`/`commit-only` strategies, `vault: ...` commit format).

**Constraints:**
- Project is markdown-only by design (no build system, no tests per `.vibeflow/index.md`). All logic lives inside skill markdown as procedural instructions executed by Claude. Docling introduces a runtime dependency but not a build-time one — same model as graphify.
- Suggested budget per `.vibeflow/index.md`: ≤ 4 files per task. This PRD fits: `skills/teach/SKILL.md`, `skills/setup/SKILL.md`, possibly one new fetcher helper skill (e.g. `skills/docling/SKILL.md` if we decide to extract), and `CLAUDE.md` (if the dependency list needs updating).
- Precedent for auto-install-on-first-use: see `.vibeflow/prds/graphify-setup-autoinstall.md`.
- Precedent for internal helper skills (fetchers): `skills/confluence-to-markdown/SKILL.md`, `skills/gdoc-to-markdown/SKILL.md` — docling conversion could follow this pattern or stay inline in `/teach`.

## Open Questions

None. All 5 prior open questions resolved during discovery:

1. **Node-ID collision in `graph.json` merge:** merge metadata — union `sources`, most-recent `updated_at`, union labels/tags.
2. **`.graphify_analysis.json` after merge:** mark stale inside `/preserve`'s Phase 0; `/bedrock:compress` recomputes on next run.
3. **Docling invocation:** inline `docling <file>` via Bash inside `/teach`. No separate fetcher skill.
4. **Auto-install UX:** silent install with one-line status message.
5. **Docling routing rule:** run docling on every file type docling supports, except GitHub repos (which continue through the clone → graphify flow). Docling-unsupported types fall through to raw passthrough.

Implementation detail to confirm in `/vibeflow:gen-spec`: the exact mechanism for the `stale: true` marker on `.graphify_analysis.json` (new top-level field vs sidecar file) and how `/bedrock:compress` reads it.
