# Spec: Internalize Content Fetchers — Part 2: Wire Fetchers into Teach and Setup

> Source PRD: `.vibeflow/prds/internalize-content-fetchers.md`
> Generated: 2026-04-15

## Objective

`/bedrock:teach` uses internal fetcher modules for Confluence and Google Docs ingestion, and `/bedrock:setup` validates the required env vars and optional Claude in Chrome dependency.

## Context

Part 1 created the internal fetcher modules (`fetchers/confluence.md`, `fetchers/gdoc.md`, `fetchers/scripts/extract.js`). Today, `/teach` Phase 1 invokes external skills via the Skill tool and aborts if they're not installed. `/setup` checks for the external skills via Glob on `~/.claude/skills/`.

After this spec:
- `/teach` reads the internal fetcher modules directly and follows their instructions inline
- `/setup` checks env vars and MCP availability instead of probing for external skill files
- External skill references are fully removed

## Definition of Done

1. `/teach` Phase 1.3.2 (Confluence) reads `fetchers/confluence.md` from the plugin directory and follows its instructions inline — no Skill tool invocation of `/confluence-to-markdown`
2. `/teach` Phase 1.3.3 (Google Docs) reads `fetchers/gdoc.md` from the plugin directory and follows its instructions inline — no Skill tool invocation of `/gdoc-to-markdown`
3. The strings `/confluence-to-markdown` and `/gdoc-to-markdown` do not appear anywhere in `skills/teach/SKILL.md` (as skill invocation targets)
4. `/setup` Phase 1.2 dependency check validates: `CONFLUENCE_API_TOKEN` + `CONFLUENCE_USER_EMAIL` env vars, `GOOGLE_ACCESS_TOKEN` env var, and `claude-in-chrome` MCP availability — with clear reporting of which source types are available
5. `/setup` no longer checks for external skills `confluence-to-markdown` or `gdoc-to-markdown` via Glob
6. Follows skill-architecture pattern from `.vibeflow/patterns/` (phased structure, Plugin Paths, Critical Rules table preserved in both skills)

## Scope

### Update `skills/teach/SKILL.md`

**Phase 1.3.2 (Confluence) — replace external skill invocation:**

Current:
```markdown
#### 1.3.2 Confluence

For Confluence URLs:
1. Invoke skill `/confluence-to-markdown` passing the URL
2. Save the output to `$TEACH_TMP/<slug>.md`

If the skill is not installed: warn "confluence-to-markdown skill not found..." and abort.
```

Replace with:
```markdown
#### 1.3.2 Confluence

For Confluence URLs:
1. Read the internal fetcher module at `<base_dir>/../../fetchers/confluence.md`
2. Follow its instructions to parse the URL, choose strategy (API or browser), and extract content
3. Save the returned Markdown content to `$TEACH_TMP/<slug>.md`
   - `<slug>` is derived from the page title or URL path (kebab-case, lowercase)

If neither API credentials nor Claude in Chrome are available: warn the user with the guidance message from the fetcher module and abort this source type.
```

**Phase 1.3.3 (Google Docs) — replace external skill invocation:**

Current:
```markdown
#### 1.3.3 Google Docs

For Google Docs URLs:
1. Invoke skill `/gdoc-to-markdown` passing the URL
2. Save the output to `$TEACH_TMP/<slug>.md`

If the skill is not installed: warn "gdoc-to-markdown skill not found..." and abort.
```

Replace with:
```markdown
#### 1.3.3 Google Docs / Sheets

For Google Docs or Sheets URLs:
1. Read the internal fetcher module at `<base_dir>/../../fetchers/gdoc.md`
2. Follow its instructions to parse the URL, detect document type (Doc vs Sheet), choose strategy (API or public export), and extract content
3. The fetcher saves output to `/tmp/gdoc_{docId}.md` or `/tmp/gsheet_{docId}.md`
4. Copy the output file to `$TEACH_TMP/<slug>.md`
   - `<slug>` is derived from the document title or URL path (kebab-case, lowercase)

If neither API token nor public export work: warn the user with the guidance message from the fetcher module and abort this source type.
```

**Phase 1.1 classification table — update fetch method column:**

| Input | Detected type | Fetch method |
|---|---|---|
| URL containing `confluence` or `atlassian.net` | confluence | Read `fetchers/confluence.md`, follow instructions, save output to tmp |
| URL containing `docs.google.com` | gdoc | Read `fetchers/gdoc.md`, follow instructions, save output to tmp |

(Other rows unchanged.)

**Critical Rules table — update:**
- Remove: "If skill is not installed, warn and abort"
- Add: "Read internal fetcher modules from `<base_dir>/../../fetchers/` — never invoke external skills for content fetching"

### Update `skills/setup/SKILL.md`

**Phase 1.2 — replace external skill dependency checks with env var / MCP checks:**

Current dependency table:
```markdown
| Dependency | Check method | What it unlocks |
|---|---|---|
| graphify | Glob: `~/.claude/skills/graphify/SKILL.md` | Required. Extraction engine... |
| confluence-to-markdown | Glob: `~/.claude/skills/confluence-to-markdown/SKILL.md` | Confluence page ingestion... |
| gdoc-to-markdown | Glob: `~/.claude/skills/gdoc-to-markdown/SKILL.md` | Google Docs ingestion... |
```

Replace with:
```markdown
| Dependency | Check method | What it unlocks |
|---|---|---|
| graphify | Glob: `~/.claude/skills/graphify/SKILL.md` | **Required.** Extraction engine for all `/bedrock:teach` ingestion. Without it, /teach cannot function. |
| CONFLUENCE_API_TOKEN + CONFLUENCE_USER_EMAIL | Bash: `test -n "$CONFLUENCE_API_TOKEN" && test -n "$CONFLUENCE_USER_EMAIL"` | Confluence page ingestion via `/bedrock:teach` (API strategy). |
| GOOGLE_ACCESS_TOKEN | Bash: `test -n "$GOOGLE_ACCESS_TOKEN"` | Google Docs and Sheets ingestion via `/bedrock:teach` (API strategy). |
| claude-in-chrome MCP | ToolSearch: `select:mcp__claude-in-chrome__tabs_context_mcp` (succeeds = available) | **Optional.** Browser fallback for Confluence pages when API credentials are unavailable. |
```

Update report format:
```markdown
## Dependency Check

| Dependency | Status | What it unlocks |
|---|---|---|
| graphify | installed / NOT FOUND | Extraction engine for /teach |
| Confluence API credentials | configured / NOT SET | Confluence page ingestion (API) |
| Google API token | configured / NOT SET | Google Docs/Sheets ingestion (API) |
| claude-in-chrome MCP | available / NOT FOUND | Browser fallback for Confluence |

### Source availability summary
| Source type | Status | Requirements |
|---|---|---|
| Confluence | ready / partial / unavailable | API credentials or Chrome extension |
| Google Docs | ready / limited / unavailable | API token or public documents only |
| Google Sheets | ready / limited / unavailable | API token (all tabs) or public (first tab only) |
| GitHub | ready | git CLI |
| Remote URL | ready | WebFetch |
| Local files | ready | filesystem access |
```

Guidance messages for missing env vars (optional dependencies — never block):
```markdown
> CONFLUENCE_API_TOKEN and CONFLUENCE_USER_EMAIL are not set.
> To ingest Confluence pages, generate an API token at:
> https://id.atlassian.com/manage-profile/security/api-tokens
> Then set: CONFLUENCE_API_TOKEN=<token> and CONFLUENCE_USER_EMAIL=<your-email>
>
> Alternative: If you have the Claude in Chrome extension with Confluence logged in, browser extraction will work as a fallback.
> This is optional — your vault will work without Confluence ingestion.
```

```markdown
> GOOGLE_ACCESS_TOKEN is not set.
> To ingest Google Docs/Sheets, generate an access token at:
> https://developers.google.com/oauthplayground/
> Select scope: https://www.googleapis.com/auth/drive.readonly
> Then set: GOOGLE_ACCESS_TOKEN=<token>
>
> Public Google Docs/Sheets can still be ingested without a token (limited).
> This is optional — your vault will work without Google ingestion.
```

## Anti-scope

- NOT modifying fetcher modules themselves — created in Part 1
- NOT changing Phase 2 (graphify), Phase 3 (preserve delegation), or Phase 4 (cleanup) of `/teach`
- NOT adding new source types to `/teach`
- NOT changing `/teach` or `/setup` allowed-tools frontmatter (no new tools needed — `Read` is already allowed)
- NOT adding env var validation to `/teach` itself — strategy selection is in the fetcher modules

## Technical Decisions

| Decision | Trade-off | Justification |
|---|---|---|
| `/teach` reads fetcher modules via Read tool at runtime | Adds one Read call per fetch; content occupies LLM context | The Read is cheap (~150-200 lines per module). This is how skills consume reference docs — consistent with how `/preserve` reads entity definitions and templates. |
| `/setup` checks env vars via Bash `test -n` | Env vars may be set but invalid (wrong token) | `/setup` can only verify presence, not validity. Actual validation happens at fetch time. This matches the existing best-effort pattern. |
| Claude in Chrome check via ToolSearch | ToolSearch success ≠ extension actually connected | Good enough for a setup check. If ToolSearch returns the schema, the MCP server is registered. Actual connectivity is tested at fetch time. |
| Source availability summary table in `/setup` | Extra output for the user | Users get a clear picture of what `/teach` can and cannot ingest before they start teaching. This prevents confusion and wasted attempts. |

## Applicable Patterns

- **skill-architecture.md** — Both `/teach` and `/setup` must preserve their existing structure: YAML frontmatter, Plugin Paths, phased execution, Critical Rules table.
- **skill-delegation.md** — The delegation chain (`/teach` → `/preserve`) is unchanged. Fetcher modules sit before this chain as Phase 1 implementation details.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `/teach` allowed-tools doesn't include a tool needed by a fetcher | Fetch fails at runtime with permission error | Verified: `/teach` already has `Bash`, `Read`, `Write`, `WebFetch`, and `mcp__plugin_atlassian_atlassian__*` in allowed-tools. ToolSearch is implicitly available. All fetcher strategies are covered. |
| Setup check gives false confidence (env var set but invalid) | User thinks Confluence is ready but `/teach` fails | Guidance message in `/setup` includes instructions for generating valid tokens. Runtime errors in fetcher modules provide specific error messages (401, 403, 404). |

## Dependencies

- `.vibeflow/specs/internalize-content-fetchers-part-1.md` — fetcher modules must exist before this spec can be implemented.
