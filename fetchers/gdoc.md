# Google Docs & Sheets Fetcher

Internal module — invoked by `/bedrock:teach` Phase 1, not user-invocable.

Fetches a Google Docs document or Google Sheets spreadsheet and converts it to a local Markdown file.
Supports both document types with automatic detection. Two strategies in order:
Google API with bearer token (primary), public URL export (fallback).

---

## Step 1 — Parse URL and Detect Type

Parse the URL. Accept these formats:

**Google Docs:**
- `https://docs.google.com/document/d/{docId}/edit`
- `https://docs.google.com/document/d/{docId}/edit#heading=...`
- `https://docs.google.com/document/d/{docId}/edit?tab=t.0`
- `https://docs.google.com/document/d/{docId}`
- Raw document ID (no URL) — treat as Doc by default

**Google Sheets:**
- `https://docs.google.com/spreadsheets/d/{docId}/edit`
- `https://docs.google.com/spreadsheets/d/{docId}/edit#gid=0`
- `https://docs.google.com/spreadsheets/d/{docId}`
- Raw spreadsheet ID — only if the user explicitly mentions "sheet" or "spreadsheet"

**Detect type:**
- URL contains `/spreadsheets/d/` → **Sheet**
- URL contains `/document/d/` → **Doc**
- Raw ID with no URL → default to **Doc** unless user context indicates Sheet

Extract the `{docId}` — the string between `/d/` and the next `/` or end of path.

## Step 2 — Choose Strategy

- **If `GOOGLE_ACCESS_TOKEN` env var exists** → use **Strategy A (API)**
- **If `GOOGLE_ACCESS_TOKEN` is NOT set** → attempt **Strategy B (Public Export)**
- **If Strategy B fails (private document)** → abort with:
  "This document requires authentication. Set the `GOOGLE_ACCESS_TOKEN` env var with a valid Google OAuth token. Generate one at https://developers.google.com/oauthplayground/ with the `https://www.googleapis.com/auth/drive.readonly` scope."

Inform the caller which strategy is being used and whether the document is a **Doc** or **Sheet**.

---

## Google Docs — Strategy A (API)

### A.1 Fetch as Markdown

Use `WebFetch`:
```
WebFetch(
  url: "https://www.googleapis.com/drive/v3/files/{docId}/export?mimeType=text/markdown",
  headers: { "Authorization": "Bearer {GOOGLE_ACCESS_TOKEN}" },
  prompt: "Return the COMPLETE raw content exactly as-is. Do not summarize or truncate."
)
```

If WebFetch cannot send the Authorization header, fall back to Bash:
```bash
curl -sL -H "Authorization: Bearer ${GOOGLE_ACCESS_TOKEN}" \
  "https://www.googleapis.com/drive/v3/files/{docId}/export?mimeType=text/markdown"
```

### A.2 Validate

- Valid Markdown content → proceed to Output
- 401 → "Token expired or invalid. Refresh `GOOGLE_ACCESS_TOKEN`."
- 403 → "No access to this document. Check permissions."
- 404 → "Document not found. Check the URL or document ID."
- Empty response → "The document appears to be empty."

**Do not post-process** the Markdown — return Google's native output as-is.

## Google Docs — Strategy B (Public Export)

### B.1 Fetch via public endpoint

```bash
curl -sL "https://docs.google.com/document/d/{docId}/export?format=md"
```

The `-L` flag follows the 307 redirect to `*.googleusercontent.com`.

### B.2 Validate

- Valid Markdown content → proceed to Output
- HTML error page or Google login page → document is private. Abort with authentication guidance.
- Empty response → "The document appears to be empty or inaccessible."

---

## Google Sheets — Strategy A (API)

### A.1 List all sheet tabs

```bash
curl -sL -H "Authorization: Bearer ${GOOGLE_ACCESS_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/{docId}?fields=sheets.properties"
```

Returns JSON with `sheets[].properties.title` (sheet name) and `sheets[].properties.sheetId` (gid).

### A.2 Export each tab as CSV

For each tab:
```bash
curl -sL -H "Authorization: Bearer ${GOOGLE_ACCESS_TOKEN}" \
  "https://docs.google.com/spreadsheets/d/{docId}/export?format=csv&gid={sheetGid}"
```

If the export endpoint fails for a specific tab, fall back to the Sheets API values endpoint:
```bash
curl -sL -H "Authorization: Bearer ${GOOGLE_ACCESS_TOKEN}" \
  "https://sheets.googleapis.com/v4/spreadsheets/{docId}/values/{sheetName}!A:ZZ"
```

Convert the JSON `values` array rows to comma-separated values to produce CSV.

### A.3 Convert CSV to Markdown tables

For each tab's CSV:
1. Parse CSV correctly — respect quoted fields (fields containing commas, newlines, or double quotes wrapped in `"..."` are a single field)
2. First row = header → `| col1 | col2 | ... |`
3. Separator row → `| --- | --- | ... |`
4. Data rows → `| val1 | val2 | ... |`
5. Escape pipe characters `|` within cell values as `\|`

### A.4 Concatenate all tabs

For each tab, prepend: `## {sheet_name}` followed by a blank line, then the Markdown table, then a blank line. Tabs appear in the same order as returned by the Sheets API metadata.

### A.5 Validate

- At least one tab produced valid content → proceed to Output
- 401 → "Token expired or invalid. Refresh `GOOGLE_ACCESS_TOKEN`."
- 403 → "No access. Check permissions or ensure token has `drive.readonly` scope."
- 404 → "Spreadsheet not found. Check the URL."
- All tabs empty → "The spreadsheet appears to be empty."

## Google Sheets — Strategy B (Public Export)

### B.1 Export first tab

```bash
curl -sL "https://docs.google.com/spreadsheets/d/{docId}/gviz/tq?tqx=out:csv&gid=0"
```

### B.2 Validate and convert

- Valid CSV → convert to Markdown table (same rules as Strategy A step A.3), proceed to Output
- HTML error page or Google login page → spreadsheet is private. Abort with authentication guidance.
- Empty response → "The spreadsheet appears to be empty or inaccessible."

### B.3 Multi-sheet limitation

Inform the caller: "Public export can only retrieve the first sheet tab. To export all tabs, set `GOOGLE_ACCESS_TOKEN`."

Format the single tab with heading `## Sheet1` followed by the Markdown table.

---

## Output Contract

### Save the file

- **Doc** → save to `/tmp/gdoc_{docId}.md`
- **Sheet** → save to `/tmp/gsheet_{docId}.md`

Write the Markdown content using the Write tool. Verify the file was written by reading the first few lines.

### Return to caller

Return to `/bedrock:teach`:
- **Output file path**: `/tmp/gdoc_{docId}.md` or `/tmp/gsheet_{docId}.md`
- **Document type**: Doc or Sheet
- **Strategy used**: API or Public Export
- **Tabs exported** (Sheets only): number of tabs

The caller copies the file to `$TEACH_TMP/<slug>.md`.

---

## Hard Rules

| Rule | Detail |
|---|---|
| Read-only | Never write back to Google Docs or Sheets. |
| No OAuth interactive flows | Use only the static token from `GOOGLE_ACCESS_TOKEN`. |
| Validate before saving | Do not save empty files, HTML error pages, or Google login pages. |
| API preferred | Strategy A is always tried first when the token is available. |
| No Markdown post-processing for Docs | Return Google's native Markdown export as-is. |
| Export all sheet tabs (API) | Do not skip tabs or allow selective export. |
| Respect CSV quoting rules | Quoted fields are single fields, even with commas or newlines inside. |
| Best-effort | If a strategy fails, try the next. If all fail, report and abort. |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| API returns 401 | Token expired — ask user to refresh `GOOGLE_ACCESS_TOKEN` |
| API returns 403 | User lacks access to the document/spreadsheet |
| API returns 404 | Document ID is wrong — verify URL |
| Public export returns HTML login page | Document is private — user must set `GOOGLE_ACCESS_TOKEN` |
| Content is truncated | Google Drive API limits exports to 10 MB — document may be too large |
| WebFetch fails to send Authorization header | Fall back to `curl -H "Authorization: Bearer {token}" -sL "<url>"` via Bash |
| Sheets 403 for metadata | Token may lack `drive.readonly` or `spreadsheets.readonly` scope |
| Sheets CSV export returns HTML | Export endpoint blocked — fall back to Sheets API values endpoint |
| Public Sheets export returns only first tab | Expected limitation — multi-sheet export requires `GOOGLE_ACCESS_TOKEN` |
