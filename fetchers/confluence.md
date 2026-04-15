# Confluence Fetcher

Internal module — invoked by `/bedrock:teach` Phase 1, not user-invocable.

Fetches a Confluence page and returns its content as Markdown. Two strategies in order:
Confluence REST API with Basic Auth (primary), browser DOM extraction via Claude in Chrome (fallback).

**Dependency:** Browser fallback requires `fetchers/scripts/extract.js` (relative to plugin root).

---

## Step 1 — Parse URL

Parse the Confluence URL. Accept these formats:
- `https://<domain>.atlassian.net/wiki/spaces/<spaceKey>/pages/<pageId>/<title>`
- `https://<domain>.atlassian.net/wiki/spaces/<spaceKey>/pages/<pageId>`
- `https://<domain>.atlassian.net/wiki/x/<shortlink>`
- `https://<domain>.atlassian.net/wiki/pages/viewpage.action?pageId=<pageId>`

Extract:
- **Base URL**: `https://<domain>.atlassian.net` (everything before `/wiki/...`)
- **Page ID**: the numeric ID from the URL path (segment after `/pages/`) or `pageId` query parameter

## Step 2 — Choose Strategy

- **If `CONFLUENCE_API_TOKEN` and `CONFLUENCE_USER_EMAIL` env vars exist** → use **Strategy A (API)**
- **If env vars missing but Claude in Chrome MCP is available** → use **Strategy B (Browser)**
- **If neither is available** → abort with:
  "Cannot fetch Confluence page. Either set `CONFLUENCE_API_TOKEN` and `CONFLUENCE_USER_EMAIL` env vars (recommended), or have the Claude in Chrome extension running with Confluence logged in."

Inform the caller which strategy is being used before proceeding.

---

## Strategy A — Confluence REST API (primary)

### A.1 Read credentials

```bash
echo "CONFLUENCE_API_TOKEN: ${CONFLUENCE_API_TOKEN:+set}" && echo "CONFLUENCE_USER_EMAIL: ${CONFLUENCE_USER_EMAIL:+set}"
```

### A.2 Compute Basic Auth header

```bash
echo -n "${CONFLUENCE_USER_EMAIL}:${CONFLUENCE_API_TOKEN}" | base64
```

### A.3 Fetch the page

Use `WebFetch`:
```
WebFetch(
  url: "{baseUrl}/wiki/api/v2/pages/{pageId}?body-format=storage",
  headers: {
    "Authorization": "Basic {base64_value}",
    "Accept": "application/json"
  }
)
```

If WebFetch cannot send the Authorization header, fall back to `curl` via Bash:
```bash
curl -sL -H "Authorization: Basic {base64_value}" -H "Accept: application/json" \
  "{baseUrl}/wiki/api/v2/pages/{pageId}?body-format=storage"
```

### A.4 Extract content from response

The API returns JSON with:
- `title` — page title
- `body.storage.value` — XHTML content (Confluence storage format)

### A.5 Convert XHTML to Markdown

Convert the storage format XHTML to Markdown using these rules:

| XHTML element | Markdown output |
|---|---|
| `<h1>` through `<h6>` | `#` through `######` |
| `<p>` | Paragraph with blank line separation |
| `<strong>`, `<b>` | `**text**` |
| `<em>`, `<i>` | `*text*` |
| `<s>`, `<del>` | `~~text~~` |
| `<a href="...">` | `[text](url)` |
| `<ul>` / `<ol>` / `<li>` | Markdown lists (respect nesting) |
| `<table>` | Markdown table with `\|` separators and header row |
| `<ac:structured-macro ac:name="code">` | Fenced code block with language from `<ac:parameter ac:name="language">` |
| `<pre>` | Fenced code block |
| `<code>` (inline) | `` `code` `` |
| `<blockquote>` | `> text` |
| `<hr>` | `---` |
| Confluence macros (`<ac:*>`) with text | Extract text content |
| Confluence macros with no text (images, drawio, attachments) | Skip silently |

### A.6 Error handling

| HTTP status | Action |
|---|---|
| 401 Unauthorized | If Claude in Chrome available → fall back to Strategy B. Otherwise: "API returned 401. Check that `CONFLUENCE_API_TOKEN` is valid." |
| 403 Forbidden | "API returned 403. User does not have access to this page." |
| 404 Not Found | "API returned 404. Page ID may be wrong — verify the URL." |

---

## Strategy B — Browser DOM Extraction (fallback)

### B.1 Load Chrome tools

Via ToolSearch:
```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__tabs_create_mcp
select:mcp__claude-in-chrome__navigate
select:mcp__claude-in-chrome__javascript_tool
```

### B.2 Get browser context

```
mcp__claude-in-chrome__tabs_context_mcp(createIfEmpty: true)
```

### B.3 Navigate to the page

```
mcp__claude-in-chrome__tabs_create_mcp()
mcp__claude-in-chrome__navigate(url: "<full confluence URL>", tabId: <id>)
```

### B.4 Execute extraction script

Read `fetchers/scripts/extract.js` from the plugin directory using the Read tool. Then execute it:

```
mcp__claude-in-chrome__javascript_tool(
  action: "javascript_exec",
  text: <contents of extract.js>,
  tabId: <id>
)
```

The script returns JSON:
```json
{
  "status": "ready",
  "totalLength": 52969,
  "totalChunks": 6,
  "chunkSize": 10000,
  "title": "Page Title",
  "instructions": "Run window.__confluence.chunk(0), window.__confluence.chunk(1), etc."
}
```

If the script returns an `error` field: handle accordingly (login page, empty content, wrong page).

### B.5 Read chunks

For each chunk from `0` to `totalChunks - 1`:
```
mcp__claude-in-chrome__javascript_tool(
  action: "javascript_exec",
  text: "window.__confluence.chunk(N)",
  tabId: <id>
)
```

Concatenate all chunks into a single Markdown string.

### B.6 Validate

Check that the result is not empty and not a login page. If validation fails:
"Browser extraction failed. Check that you are logged into Confluence in Chrome."

---

## Output Contract

Return to the caller (`/bedrock:teach`):
- **Markdown content**: the full page content as Markdown
- **Page title**: extracted from API response (`title` field) or browser extraction (`title` in JSON)

The caller is responsible for saving the content to `$TEACH_TMP/<slug>.md`.

---

## Hard Rules

| Rule | Detail |
|---|---|
| Read-only | Never write back to Confluence. |
| No OAuth interactive flows | Use only existing API token or browser session. |
| Validate before returning | Do not return empty content, HTML error pages, or login pages. |
| API preferred | Strategy A is always tried first when credentials are available. |
| Skip rich media silently | Images, diagrams, drawio, and attachment macros are omitted without error. |
| Best-effort | If a strategy fails, try the next. If all fail, report and abort — do not retry indefinitely. |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| API returns 401 | Token expired — regenerate at https://id.atlassian.com/manage-profile/security/api-tokens |
| API returns 403 | User lacks page access |
| API returns 404 | Wrong page ID — verify URL |
| Chrome extension disconnected | Refresh it, call `tabs_context_mcp(createIfEmpty: true)` |
| Browser redirects to login | User not authenticated — log into Confluence in Chrome, retry |
| `extract.js` returns empty | Page may not have loaded — wait and retry, or check if page is empty |
| Shortlink URL (`/wiki/x/...`) with API | Navigate in browser first to resolve full URL with page ID |
