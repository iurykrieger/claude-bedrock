---
name: teach
description: >
  Teaches the Second Brain to recognize a new external data source. Fetches content from
  Confluence, Google Docs, GitHub repositories, remote URLs, CSV, local Markdown, or PDF,
  runs the /graphify extraction pipeline, and delegates entity persistence to /bedrock:preserve.
  Use when: "bedrock teach", "bedrock-teach", "teach", "ingest source", "import document", "/bedrock:teach",
  or when the user provides a Confluence, Google Docs, or GitHub URL, or a local file path
  to incorporate into the vault.
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Agent, WebFetch, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
---

# /bedrock:teach — External Source Ingestion into the Second Brain

## Plugin Paths

Entity definitions and templates are in the plugin directory, not at the vault root.
Use the "Base directory for this skill" provided at invocation to resolve paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- Plugin CLAUDE.md: `<base_dir>/../../CLAUDE.md` (already injected automatically into context)

Where `<base_dir>` is the path provided in "Base directory for this skill".

---

## Vault Resolution

Resolve which vault to teach. This skill can be invoked from any directory.

**Step 1 — Parse `--vault` flag:**
Check if the input arguments include `--vault <name>`. If found, extract the vault name and remove it from the arguments (the remaining text is the source URL/path).

**Step 2 — Resolve vault path:**

1. **If `--vault <name>` was provided:**
   Read the vault registry at `<base_dir>/../../vaults.json`. Find the entry matching the name.
   If not found: error — "Vault `<name>` is not registered. Run `/bedrock:vaults` to see available vaults."
   If found: set `VAULT_PATH` to the entry's `path` value. Store the resolved vault name as `VAULT_NAME`.

2. **If no `--vault` flag — CWD detection:**
   Read `<base_dir>/../../vaults.json`. Check if the current working directory is inside any registered vault path
   (CWD starts with a registered vault's absolute path). If multiple match, use the longest path (most specific).
   If found: set `VAULT_PATH` to the matching vault's `path`. Store its name as `VAULT_NAME`.

3. **If CWD detection fails — default vault:**
   From the registry, find the vault with `"default": true`.
   If found: set `VAULT_PATH` to the default vault's `path`. Store its name as `VAULT_NAME`.

4. **If no resolution:**
   Error — "No vault resolved. Available vaults:" followed by the registry listing.
   "Use `--vault <name>` to specify, or run `/bedrock:setup` to register a vault."

**Step 3 — Validate vault path:**
```bash
test -d "<VAULT_PATH>" && echo "exists" || echo "missing"
```
If missing: error — "Vault path `<VAULT_PATH>` does not exist on disk. Run `/bedrock:setup` to re-register."

**Step 4 — Read vault config:**
```bash
cat <VAULT_PATH>/.bedrock/config.json 2>/dev/null
```
Extract `language` and other relevant fields for use in later phases.

**From this point forward, ALL vault file operations use `<VAULT_PATH>` as the root.**
- Graphify output: `<VAULT_PATH>/graphify-out/`
- When delegating to `/bedrock:preserve`, pass `--vault <VAULT_NAME>`

---

## Overview

This skill receives an external source (URL or local path), fetches its content to a temporary
directory, runs the `/graphify` extraction pipeline on it, and delegates entity persistence
to `/bedrock:preserve`.

**You are a fetcher and orchestrator agent.** Your job is to:
1. Classify the input and fetch content to `/tmp`
2. Invoke `/graphify` to extract a knowledge graph
3. Delegate entity writes to `/bedrock:preserve`
4. Clean up temporary files

You do NOT classify entities, create vault files, or write to the vault directly.
All extraction is done by `/graphify`. All writes are done by `/bedrock:preserve`.

Follow the phases below in order, without skipping steps.

---

## Phase 1 — Fetch

### 1.1 Classify the input

The user provides an argument. Classify it in the following priority order:

| Input | Detected type | Fetch method |
|---|---|---|
| URL containing `confluence` or `atlassian.net` | confluence | Read `skills/confluence-to-markdown/SKILL.md`, follow instructions, save output to tmp |
| URL containing `docs.google.com` | gdoc | Read `skills/gdoc-to-markdown/SKILL.md`, follow instructions, save output to tmp |
| URL containing `github.com` | github-repo | `git clone --depth 1` to tmp + GitHub MCP enrichment |
| URL starting with `http://` or `https://` (any other) | remote-url | WebFetch content, save as markdown to tmp |
| Local path ending in `.csv` | csv | Copy to tmp (pass through raw) |
| Local path ending in `.md`, `.txt`, or `.pdf` | local-file | Copy to tmp |
| Local directory path | local-dir | Copy directory to tmp |
| No match above | manual | Ask the user: "Could not identify the source type. Paste the content or provide a valid URL/path." |

If no argument was provided: ask the user "What source do you want to ingest? Provide a URL (Confluence, Google Docs, GitHub) or a local file path (.md, .csv, .txt, .pdf)."

### 1.2 Create temporary directory

All content is fetched to a temporary directory. This is the single input path for `/graphify`.

```bash
TEACH_TMP="/tmp/bedrock-teach-$(date +%s)"
mkdir -p "$TEACH_TMP"
echo "Temporary directory: $TEACH_TMP"
```

Store the path for use in subsequent phases.

### 1.3 Fetch content

Execute the fetch strategy for the detected type. All content lands in `$TEACH_TMP/`.

#### 1.3.1 GitHub repository

For GitHub URLs (e.g.: `https://github.com/acme-corp/billing-api`):

1. Extract `owner/repo` and `repo-name` from the URL
2. Clone the repository (shallow):
   ```bash
   git clone --depth 1 <url> "$TEACH_TMP/<repo-name>"
   ```
3. GitHub MCP enrichment — call directly in main context (NOT via subagent — MCP permissions are not inherited):
   - `mcp__plugin_github_github__get_file_contents` → read the repo's README.md
   - `mcp__plugin_github_github__list_commits` → last 10 commits
   - `mcp__plugin_github_github__list_pull_requests` → last 5 PRs (state=all, sort=updated)
4. Compile MCP results into a single markdown file and save as `$TEACH_TMP/<repo-name>/_github_metadata.md`

> **Best-effort:** If any MCP call fails, continue with what was obtained. Do NOT block ingestion.

#### 1.3.2 Confluence

For Confluence URLs:
1. Read the internal skill at `<base_dir>/../confluence-to-markdown/SKILL.md`
2. Follow its instructions to parse the URL, choose layer (MCP → API → browser), and extract content
3. Save the returned Markdown content to `$TEACH_TMP/<slug>.md`
   - `<slug>` is derived from the page title or URL path (kebab-case, lowercase)

If all three layers (MCP, API, browser) are unavailable: warn the user with the guidance message from the fetcher module and abort this source type.

#### 1.3.3 Google Docs / Sheets

For Google Docs or Sheets URLs:
1. Read the internal skill at `<base_dir>/../gdoc-to-markdown/SKILL.md`
2. Follow its instructions to parse the URL, detect document type (Doc vs Sheet), choose layer (MCP → API/public export → browser), and extract content
3. The fetcher saves output to `/tmp/gdoc_{docId}.md` or `/tmp/gsheet_{docId}.md`
4. Copy the output file to `$TEACH_TMP/<slug>.md`
   - `<slug>` is derived from the document title or URL path (kebab-case, lowercase)

If all three layers (MCP, API/public export, browser) are unavailable: warn the user with the guidance message from the fetcher module and abort this source type.

#### 1.3.4 Remote URL (generic)

For any other HTTP/HTTPS URL:
1. Use WebFetch to download the content
2. If the response is HTML: extract text content (strip tags, keep structure)
3. Save as `$TEACH_TMP/<slug>.md`
   - `<slug>` is derived from the URL path or domain (kebab-case, lowercase)

If WebFetch fails: warn "Could not fetch URL. Check if the URL is accessible." and abort.

#### 1.3.5 Local file (CSV, Markdown, PDF, text)

For local files:
1. Verify the file exists using Read
2. Copy to tmp:
   ```bash
   cp "<local-path>" "$TEACH_TMP/"
   ```

No pre-processing — files are passed through raw to `/graphify`.

#### 1.3.6 Local directory

For local directories:
1. Verify the directory exists
2. Copy to tmp (excluding heavy directories):
   ```bash
   rsync -a --exclude='.git' --exclude='node_modules' --exclude='bin' --exclude='obj' \
     --exclude='.vs' --exclude='TestResults' --exclude='packages' \
     "<local-dir>/" "$TEACH_TMP/$(basename <local-dir>)/"
   ```

### 1.4 Phase 1 result

At the end of this phase, you should have:
- **`$TEACH_TMP`**: directory with all fetched content (local path for graphify)
- **`source_url`**: original URL or file path provided by the user
- **`source_type`**: `confluence`, `gdoc`, `github-repo`, `remote-url`, `csv`, `local-file`, `local-dir`, or `manual`

Report: "Phase 1 complete: Content fetched to `$TEACH_TMP`. Source type: `<source_type>`."

---

## Phase 2 — Extract

### 2.1 Invoke /graphify

Use the Skill tool to invoke `/graphify` with the fetched content:

```
/graphify $TEACH_TMP --mode deep --obsidian --obsidian-dir <VAULT_PATH>
```

Where `<VAULT_PATH>` is the resolved vault path from the Vault Resolution section.

**IMPORTANT:**
- Invoke via the Skill tool — never call graphify Python API directly
- `/graphify` runs its full pipeline: detect → extract (AST + semantic) → build → cluster → analyze → obsidian export
- Output lands in `<VAULT_PATH>/graphify-out/`

### 2.2 Verify output

After `/graphify` completes, verify the output:

```bash
if [ -f "<VAULT_PATH>/graphify-out/graph.json" ] && [ -s "<VAULT_PATH>/graphify-out/graph.json" ]; then
    echo "graphify output verified: graph.json exists and is non-empty"
else
    echo "ERROR: graphify-out/graph.json is missing or empty"
fi
```

**If graph.json is missing or empty:**
- Warn the user: "graphify extraction failed — no graph produced. Check the content and try again."
- Clean up tmp: `rm -rf "$TEACH_TMP"`
- Abort gracefully

### 2.3 Phase 2 result

The following files should exist in `<VAULT_PATH>/graphify-out/`:
- `graph.json` — knowledge graph (nodes, edges, communities)
- `GRAPH_REPORT.md` — audit report with god nodes, surprising connections
- `obsidian/*.md` — one markdown file per node
- `.graphify_analysis.json` — communities, cohesion scores, god nodes

Report: "Phase 2 complete: graphify extraction finished. Graph: N nodes, M edges."

---

## Phase 3 — Delegate to /bedrock:preserve

### 3.1 Compile input for /preserve

Pass the graphify output path and provenance metadata to `/bedrock:preserve`:

```
graphify_output_path: <VAULT_PATH>/graphify-out/
source_url: <source_url from Phase 1>
source_type: <source_type from Phase 1>
```

**IMPORTANT:** `/teach` does NOT classify graphify nodes into entity types.
Entity classification, filtering, matching, and user confirmation are all `/bedrock:preserve`'s responsibility (Phase 1.3).

### 3.2 Invoke /preserve

Use the Skill tool to invoke `/bedrock:preserve --vault <VAULT_NAME>` passing the graphify output reference
and provenance metadata as the argument. The `--vault <VAULT_NAME>` flag ensures preserve writes to the same vault.

### 3.3 Receive result

The `/bedrock:preserve` returns:
- List of entities created/updated
- Commit hash (if there was a commit)
- Any errors or warnings

Record the result for use in the report (Phase 4).

---

## Phase 4 — Cleanup and Report

### 4.1 Cleanup temporary directory

After `/bedrock:preserve` confirms completion, remove the temporary directory:

```bash
rm -rf "$TEACH_TMP"
echo "Temporary directory cleaned up: $TEACH_TMP"
```

**IMPORTANT:** Clean up AFTER /preserve confirms, not after graphify finishes.
The graphify output in `graphify-out/` is NOT cleaned up — it lives in the vault
and is used by `/bedrock:ask` for graph traversal.

### 4.2 Report

Present to the user:

```
## /bedrock:teach — Report

### Ingested source
- **Type:** <source_type>
- **URL/Path:** <source_url>

### Extraction (via /graphify)
- **Graph:** N nodes, M edges, P communities
- **Report:** graphify-out/GRAPH_REPORT.md

### Entities processed (via /bedrock:preserve)
| Type | Name | Action |
|---|---|---|
| actor | billing-api | update |
| topic | 2026-04-migration-payments | create |
| code | process-transaction | create |

### Provenance
Each entity above received in the `sources` frontmatter field:
- url: <source_url>
- type: <source_type>
- synced_at: <today's date>

### Git
- Commit: <hash from /bedrock:preserve or "no entities">
- Push: success / failed (reason)

### Suggestions
- [list of entities mentioned in the content but not created, if any]
- [recommendations for future re-ingestion, if applicable]
```

---

## Critical Rules

| Rule | Detail |
|---|---|
| Invoke /graphify via Skill tool | NEVER call graphify Python API directly (`graphify.detect`, `graphify.build`, `graphify.extract`, etc.). Always invoke via the Skill tool. |
| All remote content fetched to /tmp | Every input type is fetched to `/tmp/bedrock-teach-<ts>/` before invoking graphify. graphify receives only a local path. |
| /teach does NOT classify entities | Entity classification, filtering, matching, and user confirmation are `/bedrock:preserve`'s responsibility. /teach passes the graphify output path and provenance metadata. |
| Delegate to /bedrock:preserve | ALL entities are persisted via `/bedrock:preserve` — teach does NOT create, update, or write vault entities. |
| Cleanup /tmp after /preserve confirms | Remove `/tmp/bedrock-teach-<ts>/` only after /preserve confirms completion, not after graphify finishes. |
| Provenance via source_url | ALWAYS include `source_url` and `source_type` when delegating to /bedrock:preserve. |
| Internal fetcher skills | Read internal skills from `<base_dir>/../confluence-to-markdown/SKILL.md` and `<base_dir>/../gdoc-to-markdown/SKILL.md` for content fetching. Never invoke external skills. |
| Best-effort for external sources | If MCP or fetch fails, warn and continue with what was obtained. Never block ingestion. |
| MCP in main context | Do NOT use subagents for GitHub/Atlassian MCP calls — permissions are not inherited. |
| Maximum 2 push attempts | After that, abort and inform (handled by /preserve). |
| Sensitive data | NEVER include credentials, tokens, passwords, PANs, CVVs. |
| Vault resolution first | Resolve `VAULT_PATH` before any file operation — never assume CWD is the vault |
| Pass --vault to /preserve | ALWAYS include `--vault <VAULT_NAME>` when delegating to `/bedrock:preserve` |
