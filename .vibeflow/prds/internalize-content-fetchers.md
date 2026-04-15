# PRD: Internalize Content Fetchers into Bedrock Plugin

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The `/bedrock:teach` skill depends on two external skills (`confluence-to-markdown` and `gdoc-to-markdown`) that live in a separate repository (`stone/common/skills`). This means anyone installing the bedrock plugin must also have those skills installed — a fragile, undocumented coupling that breaks the plugin's self-containment promise.

When a user runs `/bedrock:teach` with a Confluence or Google Docs URL, the skill invokes these external skills via the Skill tool. If they're not installed, the ingestion silently fails or errors out. There's no graceful degradation or clear setup guidance.

## Target Audience

Bedrock plugin users who run `/bedrock:teach` to ingest content from Confluence pages or Google Docs/Sheets into their vault.

## Proposed Solution

Internalize the content-fetching logic from `confluence-to-markdown` and `gdoc-to-markdown` into the bedrock plugin as **internal modules** (not user-invocable skills). The `/teach` skill calls these modules directly instead of invoking external skills via the Skill tool.

Each module implements the same two-strategy approach (API-first, browser fallback) from the original skills. The `claude-in-chrome` browser fallback is treated as an optional dependency — `/bedrock:setup` checks for it and informs the user if it's unavailable.

## Success Criteria

1. `/bedrock:teach` successfully ingests Confluence pages without `confluence-to-markdown` being installed as a separate skill.
2. `/bedrock:teach` successfully ingests Google Docs/Sheets without `gdoc-to-markdown` being installed as a separate skill.
3. `/bedrock:setup` validates the optional `claude-in-chrome` MCP dependency and reports availability.
4. `/bedrock:setup` validates required environment variables (`CONFLUENCE_API_TOKEN`, `CONFLUENCE_USER_EMAIL`, `GOOGLE_ACCESS_TOKEN`) and reports which source types are available.
5. The internalized modules are NOT invocable as standalone skills — only `/teach` can use them.

## Scope v0

- Create internal module `fetchers/confluence.md` with the Confluence fetching logic (API strategy + browser fallback).
- Create internal module `fetchers/gdoc.md` with the Google Docs/Sheets fetching logic (API strategy + public URL fallback).
- Copy the `scripts/extract.js` (Confluence DOM extractor) into the plugin's `fetchers/scripts/` directory.
- Update `/bedrock:teach` Phase 1 (Fetch) to call internal modules instead of invoking external skills via the Skill tool.
- Update `/bedrock:setup` to check for: `CONFLUENCE_API_TOKEN`, `CONFLUENCE_USER_EMAIL`, `GOOGLE_ACCESS_TOKEN`, and `claude-in-chrome` MCP availability.
- Remove any references to external `confluence-to-markdown` or `gdoc-to-markdown` skill invocations from `/teach`.

## Anti-scope

- **NOT** creating user-invocable skills (`/bedrock:fetch-confluence` etc.) — these are internal-only.
- **NOT** internalizing `fetch-meetings-notes` — that's a consumer of `gdoc-to-markdown`, not a content fetcher.
- **NOT** changing the `/teach` → `/graphify` → `/preserve` pipeline — only Phase 1 (Fetch) is affected.
- **NOT** adding new source types beyond what the original skills support.
- **NOT** modifying authentication strategies — same env vars, same API endpoints.
- **NOT** translating or adapting the `fetch-meetings-notes` Portuguese report format.

## Technical Context

### Current `/teach` Phase 1 flow (from `skills/teach/SKILL.md`)
The skill classifies input by source type (Confluence, GDocs, GitHub, URL, CSV, local) and fetches content to `/tmp/bedrock-teach-<ts>/`. For Confluence and GDocs, it currently invokes external skills via the Skill tool.

### Original skills structure (from `stone/common/skills`)
- `confluence-to-markdown`: Two strategies — Confluence REST API v2 with Basic Auth (primary) → Claude in Chrome DOM extraction (fallback). Returns Markdown inline.
- `gdoc-to-markdown`: Two strategies — Google Drive API export (primary) → public URL export (fallback). Supports both Docs and Sheets. Saves to `/tmp/gdoc_{id}.md` or `/tmp/gsheet_{id}.md`.

### Plugin conventions (from `.vibeflow/conventions.md`)
- Skills live in `skills/<name>/SKILL.md` — but these are NOT skills, they're internal modules.
- A new `fetchers/` directory at plugin root is the proposed location for internal modules.
- The `/teach` SKILL.md references fetcher logic inline rather than via Skill tool invocation.

### Dependencies
- **Required:** `CONFLUENCE_API_TOKEN` + `CONFLUENCE_USER_EMAIL` (for Confluence API), `GOOGLE_ACCESS_TOKEN` (for Google APIs)
- **Optional:** `claude-in-chrome` MCP (browser fallback for Confluence)
- **Existing:** `/graphify` skill (unchanged), `/bedrock:preserve` skill (unchanged)

## Open Questions

None.
