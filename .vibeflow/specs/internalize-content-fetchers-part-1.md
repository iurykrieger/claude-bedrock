# Spec: Internalize Content Fetchers — Part 1: Create Fetcher Modules

> Source PRD: `.vibeflow/prds/internalize-content-fetchers.md`
> Generated: 2026-04-15

## Objective

The bedrock plugin contains self-contained internal fetcher modules so that `/bedrock:teach` can fetch Confluence and Google Docs content without depending on externally installed skills.

## Context

Today, `/bedrock:teach` Phase 1 invokes external skills (`/confluence-to-markdown`, `/gdoc-to-markdown`) via the Skill tool. These skills live in a separate repository (`stone/common/skills`) and must be independently installed. If missing, `/teach` warns and aborts for those source types.

The external skills follow a two-strategy pattern: API-first (Confluence REST API, Google Drive API) with fallback (Claude in Chrome browser extraction for Confluence, public URL export for Google Docs). Both are mature and stable — ~200 lines each.

This spec creates the internal fetcher modules. Part 2 (separate spec) wires them into `/teach` and `/setup`.

## Definition of Done

1. `fetchers/confluence.md` exists at plugin root with complete Confluence fetch instructions (URL parsing, API strategy with Basic Auth, browser fallback via Claude in Chrome, XHTML-to-Markdown conversion rules)
2. `fetchers/gdoc.md` exists at plugin root with complete Google Docs/Sheets fetch instructions (URL parsing, document type detection, API strategy with bearer token, public export fallback, CSV-to-Markdown table conversion for Sheets)
3. `fetchers/scripts/extract.js` exists and is byte-identical to the source at `stone/common/skills/skills/automation/confluence-to-markdown/scripts/extract.js`
4. Fetcher modules are NOT structured as skills — no YAML frontmatter with `user_invocable`, no `Plugin Paths` section, no `allowed-tools`. They are internal reference documents with procedural instructions only.
5. No violations of `conventions.md` Don'ts (no flat tags, no path-qualified wikilinks, no sensitive data)

## Scope

### Create `fetchers/confluence.md`

Internal procedural module with these sections:

**Header:** Title, one-line purpose ("Internal module — invoked by /bedrock:teach Phase 1, not user-invocable"), and a note about the `extract.js` dependency.

**Parse URL:** Accept Confluence URL formats (from original skill Phase 1):
- `https://<domain>.atlassian.net/wiki/spaces/<spaceKey>/pages/<pageId>/<title>`
- `https://<domain>.atlassian.net/wiki/spaces/<spaceKey>/pages/<pageId>`
- `https://<domain>.atlassian.net/wiki/x/<shortlink>`
- `https://<domain>.atlassian.net/wiki/pages/viewpage.action?pageId=<pageId>`

Extract base URL and page ID.

**Strategy A — Confluence REST API (primary):**
- Requires: `CONFLUENCE_API_TOKEN` + `CONFLUENCE_USER_EMAIL` env vars
- Endpoint: `{baseUrl}/wiki/api/v2/pages/{pageId}?body-format=storage`
- Auth: Basic Auth (`base64(email:token)`)
- Tool: `WebFetch` with Authorization header (fall back to `curl` via Bash if WebFetch can't send headers)
- Convert XHTML storage format to Markdown (include the full conversion table from the original skill: headings, paragraphs, bold, italic, strikethrough, links, lists, tables, code blocks, blockquotes, HR, Confluence macros)
- Error handling: 401/403/404 with user-facing messages

**Strategy B — Browser DOM Extraction (fallback):**
- Requires: `claude-in-chrome` MCP available
- Load Chrome tools via ToolSearch
- Navigate to URL, execute `extract.js`, read chunks
- Validate: not a login page, not empty
- This strategy is optional — if Claude in Chrome is unavailable, report and abort Confluence fetch

**Strategy selection:** API if env vars exist → Browser if Chrome MCP available → abort with guidance message.

**Output contract:** Markdown content string + page title. The caller (`/teach`) is responsible for saving to `$TEACH_TMP/<slug>.md`.

**Hard Rules:** Read-only, no OAuth interactive flows, validate before returning, API preferred, skip images/diagrams/rich macros silently.

### Create `fetchers/gdoc.md`

Internal procedural module with these sections:

**Header:** Title, one-line purpose, note about dual document type support (Docs + Sheets).

**Parse URL:** Accept Google Docs and Sheets URL formats (from original skill Phase 1):
- Docs: `https://docs.google.com/document/d/{docId}/...`
- Sheets: `https://docs.google.com/spreadsheets/d/{docId}/...`
- Raw document ID (default to Doc unless user says Sheet)

Detect document type from URL path. Extract `{docId}`.

**Google Docs — Strategy A (API):**
- Requires: `GOOGLE_ACCESS_TOKEN` env var
- Endpoint: `https://www.googleapis.com/drive/v3/files/{docId}/export?mimeType=text/markdown`
- Auth: Bearer token
- Tool: `WebFetch` with Authorization header (fall back to `curl` via Bash)
- Return native Markdown output from Google — no post-processing

**Google Docs — Strategy B (Public Export):**
- Endpoint: `https://docs.google.com/document/d/{docId}/export?format=md`
- Via `curl -sL` (follows 307 redirect)
- Validate: not HTML error page, not login page

**Google Sheets — Strategy A (API):**
- Requires: `GOOGLE_ACCESS_TOKEN` env var
- Step 1: List tabs via Sheets API metadata endpoint
- Step 2: Export each tab as CSV via authenticated export endpoint (with fallback to Sheets API values endpoint)
- Step 3: Convert CSV to Markdown tables (respect quoting, escape pipes)
- Concatenate all tabs with `## {sheet_name}` headings

**Google Sheets — Strategy B (Public Export):**
- Export first tab only via `curl -sL` to public CSV endpoint (`gviz/tq?tqx=out:csv&gid=0`)
- Inform about multi-sheet limitation

**Strategy selection:** API if `GOOGLE_ACCESS_TOKEN` exists → Public export → abort with guidance message.

**Output contract:** Markdown content string + document title + output file path (`/tmp/gdoc_{docId}.md` or `/tmp/gsheet_{docId}.md`). The caller (`/teach`) consumes the file path.

**Hard Rules:** Read-only, no OAuth interactive flows, no Markdown post-processing for Docs, export all tabs for Sheets, respect CSV quoting rules.

### Copy `fetchers/scripts/extract.js`

Verbatim copy of `stone/common/skills/skills/automation/confluence-to-markdown/scripts/extract.js`. No modifications. This is the Confluence DOM-to-Markdown extractor that runs in Chrome via `javascript_tool`.

## Anti-scope

- NOT wiring fetchers into `/teach` or `/setup` — that's Part 2
- NOT creating user-invocable skills — no frontmatter, no Skill tool registration
- NOT adding Atlassian MCP as an alternative strategy — the Confluence fetcher uses REST API + browser, not the Atlassian MCP plugin
- NOT modifying the extract.js script — verbatim copy
- NOT adding new source types (e.g., Notion, Slack)

## Technical Decisions

| Decision | Trade-off | Justification |
|---|---|---|
| Fetcher modules are plain Markdown files, not skills | Less discoverability (no Skill tool, no frontmatter) | These are internal implementation details of `/teach`, not user-facing capabilities. Skill overhead (frontmatter, Plugin Paths, allowed-tools) adds nothing since they're never invoked standalone. |
| Place in `fetchers/` at plugin root | New directory pattern not in conventions.md | Entity definitions (`entities/`), templates (`templates/`), and skills (`skills/`) each have their own top-level directory. Fetchers are a distinct structural unit — internal modules — and deserve their own namespace. |
| Browser fallback is documented but optional | Confluence ingestion may fail if no API token AND no Chrome | API is the reliable path. Browser fallback is best-effort. `/setup` (Part 2) will warn about availability. |
| Output contract differs between fetchers | Confluence returns inline content; GDocs returns file path | Matches the original skills' behavior. `/teach` already handles both patterns — it saves content to `$TEACH_TMP` regardless of how it receives it. |

## Applicable Patterns

- **skill-architecture.md** — NOT directly applicable (fetchers are not skills), but the phased structure and Hard Rules table convention are reused for consistency.
- **skill-delegation.md** — Relevant context: fetchers are consumed by `/teach`, which delegates entity writes to `/preserve`. The fetchers sit before the delegation chain.

This spec introduces a NEW pattern: **internal module** — a procedural reference document consumed inline by a skill, not invocable by the user or via the Skill tool. If this pattern is reused, it should be documented in `.vibeflow/patterns/`.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Fetcher modules grow stale as external skills evolve | Internal fetchers diverge from upstream | Accept this — internalization means owning the code. The external skills are stable and the API endpoints are Google/Atlassian standards. |
| extract.js breaks on Confluence UI changes | Browser fallback fails | This is the same risk the external skill had. API strategy is the reliable primary. |
| Fetcher modules are too long for LLM context when /teach reads them | Phase 1 of /teach becomes expensive in tokens | Keep modules concise — procedural steps only, no verbose explanations. Target ~150-200 lines each. |

## Dependencies

None — this is Part 1.
