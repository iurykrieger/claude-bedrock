# Spec: Layered Fallback Fetcher Architecture

> Generated from `.vibeflow/prds/fetcher-layered-fallback.md` on 2026-04-15

## Objective

Standardize all content fetchers into a 3-layer fallback architecture (MCP → API → Browser) with consistent structure, rename them for clarity, and unify callers (teach + sync) to use the same internal fetcher modules.

## Context

Two internal fetcher modules exist (`skills/gdoc/` and `skills/confluence/`) with different fallback strategies and auth guidance styles. `/bedrock:teach` reads them inline as internal modules. `/bedrock:sync` bypasses them entirely and calls external skills (`/confluence-to-markdown`, `/gdoc-to-markdown`). The result: two code paths for the same sources with different behavior. Neither fetcher has an MCP layer — they jump straight to API calls.

## Definition of Done

1. **Renamed:** `skills/gdoc/` directory renamed to `skills/gdoc-to-markdown/`; `skills/confluence/` directory renamed to `skills/confluence-to-markdown/`. Old directories do not exist.
2. **3-layer structure:** Both `SKILL.md` files implement Step 1 (Parse URL) → Step 2 (Layer 1: MCP) → Step 3 (Layer 2: API) → Step 4 (Layer 3: Browser) → Output Contract, in that order.
3. **MCP layer behavior:** Confluence fetcher attempts `plugin:atlassian:atlassian` MCP. GDocs fetcher checks for a GDocs MCP, finds none, and skips with a log message. Both guide the user to configure MCP if it exists but is unauthenticated, and skip to Layer 2 only if the user explicitly declines or MCP is unavailable.
4. **Auth guidance standardized:** Every auth guidance message across both fetchers follows the same format: `> **{Layer} not available:** {reason}. {setup instruction}. {fallback message}.`
5. **Teach updated:** `skills/teach/SKILL.md` references `<base_dir>/../gdoc-to-markdown/SKILL.md` and `<base_dir>/../confluence-to-markdown/SKILL.md` (new paths). Critical Rules table updated accordingly.
6. **Sync updated:** `skills/sync/SKILL.md` Phase 2 invokes the internal fetcher modules (reads `SKILL.md` and follows instructions) instead of calling external `/confluence-to-markdown` and `/gdoc-to-markdown` skills.
7. **Conventions compliance:** No violations of `.vibeflow/conventions.md` Don'ts. Fetcher SKILL.md files follow the skill-architecture pattern (YAML frontmatter, phased steps, Hard Rules table). `scripts/extract.js` is unchanged.

## Scope

### Files to change (4 files, within budget ≤ 4)

| File | Action | Description |
|---|---|---|
| `skills/confluence-to-markdown/SKILL.md` | Rewrite (rename from `skills/confluence/SKILL.md`) | 3-layer fallback: Atlassian MCP → REST API → Chrome DOM extraction |
| `skills/gdoc-to-markdown/SKILL.md` | Rewrite (rename from `skills/gdoc/SKILL.md`) | 3-layer fallback: (no MCP, skip) → Google API / public export → Chrome scraping |
| `skills/teach/SKILL.md` | Edit | Update fetcher path references in Phase 1 and Critical Rules table |
| `skills/sync/SKILL.md` | Edit | Replace external skill calls with internal fetcher module reads in Phase 2 |

### Auxiliary moves (no content changes)

| Path | Action |
|---|---|
| `skills/confluence/scripts/extract.js` | Move to `skills/confluence-to-markdown/scripts/extract.js` (unchanged content) |
| `skills/confluence/` | Delete after move |
| `skills/gdoc/` | Delete after rename |

## Anti-scope

- No new fetcher types (Jira, Notion, Slack, etc.)
- No changes to `/bedrock:preserve`, `/bedrock:compress`, `/bedrock:query`, `/bedrock:setup`
- No changes to `extract.js` DOM scraping logic
- No changes to entity definitions or templates
- No changes to the output contract (fetchers return Markdown + metadata)
- No changes to graphify integration in teach
- No OAuth interactive flow implementation
- No changes to `.vibeflow/index.md` (fetcher count is the same, just renamed)

## Technical Decisions

### 1. Standardized fetcher structure

Every fetcher SKILL.md follows this skeleton:

```
# {Source} Fetcher
## Step 1 — Parse URL
## Step 2 — Layer 1: MCP
## Step 3 — Layer 2: API
## Step 4 — Layer 3: Browser (Claude in Chrome)
## Output Contract
## Hard Rules
## Troubleshooting
```

**Why:** Uniform structure makes it trivial to add a new fetcher — copy the skeleton, fill in source-specific logic. Callers don't need to know fetcher internals; they just "read SKILL.md and follow instructions."

### 2. MCP detection and guidance flow

Each MCP layer follows this decision tree:

```
1. Check if relevant MCP tools exist (ToolSearch)
2. If tools found and authed → USE MCP → return content → done
3. If tools found but not authed → guide user to authenticate
   3a. If user completes auth → retry MCP → return content → done
   3b. If user declines → log "User declined MCP, falling to Layer 2" → continue
4. If tools not found → log "No {source} MCP installed, falling to Layer 2" → continue
```

**Why:** MCP is the cleanest path (no tokens to manage, no browser automation). Worth trying first and guiding setup. But never blocking — the user can always decline and move on.

### 3. GDocs: public URL export stays in Layer 2, not Layer 3

The current GDocs fetcher has "Google API" (primary) and "public URL export" (fallback). Both are API-level strategies (no browser). In the new architecture, both remain in Layer 2 as sub-strategies (A: API with token, B: public export without token). Layer 3 becomes Chrome scraping (new for GDocs).

**Why:** Public export is still a curl call, not browser automation. Grouping it with the API layer keeps the semantic meaning of layers consistent: Layer 2 = programmatic HTTP, Layer 3 = browser.

### 4. GDocs Chrome scraping (Layer 3) — new

The GDocs fetcher currently has no browser fallback. Adding a Chrome scraping layer for GDocs means: navigate to the doc URL, extract rendered content from the DOM. This requires a `scripts/extract.js` for GDocs (similar to the Confluence one).

**Trade-off:** This adds a new script file. But without it, GDocs has only 2 layers while Confluence has 3 — breaking the uniform architecture. A simple GDocs DOM extractor is straightforward (Google Docs renders content in a `div.kix-appview-editor` container).

**Decision:** Create `skills/gdoc-to-markdown/scripts/extract.js` for GDocs DOM extraction. Keep it minimal — extract text content from the editor container, convert basic formatting to Markdown.

**Note:** This is an exception to the 4-file budget — `extract.js` is a supporting script, not a skill file. The spec budget of ≤ 4 applies to skill/markdown files being rewritten or edited.

### 5. Auth guidance format

All auth guidance messages use a standardized callout format:

```
> **{Layer} not available:** {specific reason}.
> {step-by-step setup instruction}.
> Falling back to {next layer name}.
```

Example (Confluence API):
```
> **API not available:** `CONFLUENCE_API_TOKEN` or `CONFLUENCE_USER_EMAIL` environment variable is not set.
> Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens and export both variables:
> `export CONFLUENCE_API_TOKEN="your-token"` and `export CONFLUENCE_USER_EMAIL="your-email"`.
> Falling back to Browser extraction (Layer 3).
```

**Why:** Consistent format means users learn the pattern once. Every guidance message tells them: what failed, how to fix it, what happens next.

### 6. Sync integration — read-and-follow pattern

`/bedrock:sync` Phase 2 will switch from calling external Skill tools to the same "read the internal SKILL.md and follow its instructions" pattern that `/bedrock:teach` uses. This means:

```markdown
### 2.1 Confluence
For sources with `source_type: confluence`:
1. Read the internal fetcher at `<base_dir>/../confluence-to-markdown/SKILL.md`
2. Follow its instructions to fetch the page content
3. The fetcher returns Markdown content and page title
```

**Why:** Single code path. Same fallback behavior in teach and sync. No dependency on external skills that may not be installed.

## Applicable Patterns

| Pattern | How it applies |
|---|---|
| `patterns/skill-architecture.md` | Fetcher SKILL.md files must have YAML frontmatter, step-by-step structure, Hard Rules table |
| `patterns/skill-delegation.md` | Fetchers are internal modules — they return data to callers, they don't write to the vault |
| `patterns/vault-writing-rules.md` | Not directly applicable (fetchers are read-only), but naming conventions (kebab-case) apply to directory names |

**New pattern introduced:** Layered Fallback Fetcher — a 3-layer architecture (MCP → API → Browser) for content fetching. This could become a `.vibeflow/patterns/` doc after implementation stabilizes.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Atlassian MCP auth flow may be flaky or require manual browser steps | Medium | Layer 1 fails, falls to Layer 2 (graceful) | Auth guidance is clear; Layer 2 is the proven path |
| GDocs Chrome extraction may be fragile (Google changes DOM structure) | Medium | Layer 3 fails for GDocs | `extract.js` uses broad selectors; Layer 2 covers most cases anyway |
| Sync callers may break if they depend on external skill return format | Low | Sync fetching fails | The output contract is the same (Markdown content + metadata); only the invocation method changes |
| Renaming directories may break relative path resolution in teach/sync | Low | Fetcher not found at runtime | Update all references in the same commit; grep for old paths before closing |
