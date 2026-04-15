# PRD: Layered Fallback Fetcher Architecture

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The current fetcher modules (`skills/gdoc/` and `skills/confluence/`) have inconsistent fallback strategies, different auth guidance styles, and no MCP layer. Meanwhile, `/bedrock:sync` bypasses the internal fetchers entirely — it calls external skills (`/confluence-to-markdown`, `/gdoc-to-markdown`) instead of the internal modules that `/bedrock:teach` uses. This means two different code paths fetch the same sources with different behavior, error handling, and fallback logic.

Additionally, the fetcher naming (`gdoc`, `confluence`) doesn't match the external skill names they replaced (`gdoc-to-markdown`, `confluence-to-markdown`), creating confusion about which is internal vs external.

## Target Audience

Bedrock plugin developers (maintaining fetchers) and Bedrock skill authors (teach, sync, and future skills that need to fetch external content).

## Proposed Solution

Refactor both fetcher modules into a standardized 3-layer fallback architecture:

**Layer 1 — MCP (preferred):** If an MCP server exists for the source type and is authenticated, use it. If it exists but isn't configured, guide the user through setup before falling to the next layer. If the user explicitly declines MCP setup, skip to Layer 2.

**Layer 2 — API fetch (curl):** Use direct API calls with authentication tokens (env vars). If credentials are missing or invalid, provide standardized guidance and fall to Layer 3.

**Layer 3 — Web Scraping (Claude in Chrome):** Open the URL in Chrome and extract content via DOM scraping. If Chrome MCP is unavailable or user isn't logged in, provide guidance and abort.

Each layer follows the same pattern: **try → detect misconfiguration → guide user → fall through (or abort if last layer).**

Concrete changes:
1. Rename `skills/gdoc/` → `skills/gdoc-to-markdown/` and `skills/confluence/` → `skills/confluence-to-markdown/`
2. Rewrite both fetcher SKILL.md files with the 3-layer fallback architecture
3. Standardize auth guidance messaging across both fetchers
4. Update `/bedrock:teach` to reference the new fetcher paths
5. Update `/bedrock:sync` to use the internal fetcher modules instead of external skills

## Success Criteria

- Both fetchers implement the 3-layer fallback (MCP → API → Browser) with consistent structure
- Auth guidance messages follow the same tone, format, and structure across both fetchers
- `/bedrock:teach` and `/bedrock:sync` both use the internal fetcher modules (no external skill calls)
- Fetcher directories renamed to `gdoc-to-markdown` and `confluence-to-markdown`
- Architecture is extensible: adding a new fetcher means creating a new `skills/<name>/SKILL.md` following the same 3-layer pattern

## Scope v0

- Rewrite `skills/gdoc-to-markdown/SKILL.md` with 3-layer fallback (MCP layer is a no-op/skip since no GDocs MCP exists — but the section exists as a placeholder)
- Rewrite `skills/confluence-to-markdown/SKILL.md` with 3-layer fallback (MCP layer uses `plugin:atlassian:atlassian`)
- Standardize auth guidance format across both fetchers
- Keep `scripts/extract.js` as-is (Confluence browser extraction script — no changes needed)
- Update `skills/teach/SKILL.md` Phase 1 references to new fetcher paths
- Update `skills/sync/SKILL.md` to invoke internal fetcher modules instead of external `/confluence-to-markdown` and `/gdoc-to-markdown` skills
- Update `.vibeflow/index.md` if fetcher count or names changed

## Anti-scope

- No new fetcher types (Jira, Notion, Slack, etc.) — architecture only, not new implementations
- No changes to `/bedrock:preserve`, `/bedrock:compress`, `/bedrock:query`, or `/bedrock:setup`
- No changes to `extract.js` DOM scraping logic
- No changes to entity definitions or templates
- No OAuth interactive flow implementation — use existing static tokens and MCP auth
- No changes to the output contract (fetchers still return Markdown content + metadata to callers)
- No changes to the graphify integration in teach

## Technical Context

**Existing patterns to follow:**
- Skill Architecture pattern (`.vibeflow/patterns/skill-architecture.md`): YAML frontmatter, phased execution, Plugin Paths section, Critical Rules table
- Skill Delegation pattern (`.vibeflow/patterns/skill-delegation.md`): fetchers are internal modules, not user-invocable skills — they return data to callers

**Available MCP tools:**
- `plugin:atlassian:atlassian` — installed, requires OAuth. Once authed, provides Confluence page access. Auth flow: `mcp__plugin_atlassian_atlassian__authenticate` → user completes OAuth → tools become available.
- No Google Docs MCP installed — GDocs MCP layer will be a documented placeholder that checks and skips.

**Key integration points:**
- `skills/teach/SKILL.md` Phase 1 (lines ~56-57, ~103-119): reads fetcher SKILL.md files by relative path
- `skills/sync/SKILL.md` (lines ~134-147): currently calls external skills — must switch to internal fetcher invocation

**Confluence fetcher current layers:** REST API (primary) → Chrome DOM extraction (fallback)
**GDocs fetcher current layers:** Google Drive API (primary) → Public URL export (fallback)

Both need MCP prepended as Layer 1, and the existing layers renumbered as Layer 2 and Layer 3. For GDocs, the current "public URL export" moves to a sub-strategy within Layer 2 (API), and Chrome scraping becomes the new Layer 3.

## Open Questions

None.
