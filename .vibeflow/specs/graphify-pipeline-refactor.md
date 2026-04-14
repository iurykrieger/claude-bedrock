# Spec: Refactor /teach and /preserve to use /graphify as the sole extraction engine

> Generated via /vibeflow:gen-spec on 2026-04-14
> PRD: `.vibeflow/prds/graphify-pipeline-refactor.md`

## Objective

Replace /teach's inline graphify Python code and per-input-type extraction logic with a single `/graphify` skill invocation, and add a graphify output input mode to /preserve, so that all content processing flows through graphify's mature pipeline.

## Context

`skills/teach/SKILL.md` (654 lines) contains ~250 lines of hand-rolled graphify integration: direct `graphify.*` Python API calls, subagent dispatch for extraction, `graphify-out/src/` copy logic, merge/cleanup code, and per-input-type extraction paths. This duplicates what the `/graphify` skill already does better via its full pipeline (detect → extract → build → cluster → analyze → obsidian export). The coupling to graphify internals means teach breaks when graphify's Python API changes. Meanwhile, non-GitHub inputs (Confluence, GDocs, CSV) get lower-quality extraction because they bypass graphify entirely or use a partial path.

The `/graphify` skill already supports `--obsidian --obsidian-dir <path>` which outputs both `graph.json` (structured) and per-node obsidian markdown files — exactly what /preserve needs to write vault entities.

## Definition of Done

1. **`/teach` invokes `/graphify` via the Skill tool** for every input type (GitHub, Confluence, GDocs, CSV, Markdown, PDF, remote URLs). Zero `graphify.*` Python imports or `graphify.detect`/`graphify.build`/`graphify.extract` calls remain in teach SKILL.md.

2. **`/teach` fetches all remote content to `/tmp/bedrock-teach-<ts>/`** before invoking graphify. Each input type has a documented fetch strategy. graphify receives only a local path.

3. **`/preserve` accepts graphify output as a third input mode** (Phase 1.3) alongside existing structured YAML (1.1) and free-form text (1.2). It reads `graph.json` for node metadata/relationships and `graphify-out/obsidian/*.md` for pre-rendered content, then converts to the internal structured format.

4. **`/preserve` owns entity classification for graphify input** — it reads graphify output, classifies nodes into vault entity types using entity definitions, filters, matches against existing vault, and presents for user confirmation. Zero classification logic in /teach. Users can invoke `/bedrock:preserve` directly with a graphify-out/ directory.

5. **`/setup` declares graphify as a required dependency** — the "optional" messaging in Phase 1.2 is updated to indicate graphify is required for /teach to function.

6. **`/teach` cleans up `/tmp/bedrock-teach-<ts>/`** after /preserve confirms completion (not after graphify finishes).

7. **No violations of conventions.md Don'ts** — skill structure follows the skill-architecture pattern (frontmatter, Plugin Paths, phased execution, Critical Rules table), delegation follows skill-delegation pattern (teach → preserve), no direct entity writes from /teach.

## Scope

### File 1: `skills/teach/SKILL.md` (major rewrite)

**Phase 1 — Fetch** (replaces current Phase 1 entirely):

- **1.1 Classify input** — Keep the existing classification table but simplify: the table maps input to a fetch strategy, not an extraction strategy. Add `remote-url` type for generic URLs.

  | Input | Detected type | Fetch method |
  |---|---|---|
  | URL containing `confluence` or `atlassian.net` | confluence | Invoke `/confluence-to-markdown`, save output to tmp |
  | URL containing `docs.google.com` | gdoc | Invoke `/gdoc-to-markdown`, save output to tmp |
  | URL containing `github.com` | github-repo | `git clone --depth 1` to tmp + GitHub MCP enrichment |
  | Remote URL (any other) | remote-url | WebFetch or `curl`, save content as markdown to tmp |
  | Local path ending in `.csv` | csv | Copy to tmp (pass through raw) |
  | Local path ending in `.md`, `.txt`, `.pdf` | local-file | Copy to tmp |
  | No match | manual | Ask user for content |

- **1.2 Create tmp directory:**
  ```bash
  TEACH_TMP="/tmp/bedrock-teach-$(date +%s)"
  mkdir -p "$TEACH_TMP"
  ```

- **1.3 Fetch content** — Execute the fetch strategy for the detected type. All content lands in `$TEACH_TMP/`.

  For **github-repo** specifically:
  1. `git clone --depth 1 <url> $TEACH_TMP/<repo-name>/`
  2. GitHub MCP enrichment (README, last 10 commits, last 5 PRs) — call directly in main context (NOT subagent)
  3. Save MCP results as `$TEACH_TMP/<repo-name>/_github_metadata.md`
  4. Store `source_url` and `source_type` for provenance

  For **confluence** and **gdoc**: invoke the respective skill, capture output, write to `$TEACH_TMP/<slug>.md`.

  For **remote-url**: use WebFetch to download content, save as `$TEACH_TMP/<slug>.md`. If WebFetch returns HTML, extract text content.

  Best-effort rule: if any fetch step fails, warn and continue with what was obtained.

- **1.4 Phase 1 result:** `$TEACH_TMP` directory with all fetched content, plus `source_url`, `source_type`, `source_slug` variables.

**Phase 2 — Extract** (replaces current Phase 1.2.1, 1.4.1, and all graphify integration code):

- **2.1 Invoke graphify** via the Skill tool:
  ```
  /graphify $TEACH_TMP --mode deep --obsidian --obsidian-dir <vault_path>
  ```
  Where `<vault_path>` is the current working directory (the vault root).

- **2.2 Verify output:** Check that `graphify-out/graph.json` exists and is non-empty. If graphify failed, warn user and abort gracefully.

- **2.3 Phase 2 result:** `graphify-out/` directory with `graph.json`, `GRAPH_REPORT.md`, `obsidian/*.md`, `.graphify_analysis.json`.

**Phase 3 — Delegate** (simplified — classification is /preserve's responsibility):

- **3.1 Compile input for /preserve** — Pass the graphify output path and provenance metadata:
  ```
  graphify_output_path: <vault_path>/graphify-out/
  source_url: <original URL or path>
  source_type: <detected type>
  ```
  /teach does NOT classify graphify nodes into entity types. That is /preserve's job (Phase 1.3).

- **3.2 Invoke /preserve** via Skill tool with the graphify output reference.

**Phase 4 — Cleanup + Report**:

- **4.1 Cleanup tmp** — `rm -rf $TEACH_TMP` (after /preserve confirms completion)
- **4.2 Report** — Same format as current Phase 5, using /preserve's return data.

**Critical Rules table:** Update to reflect new flow. Remove all graphify-specific rules (subagent dispatch, extraction merge, `graphify-out/src/` copy). Add:
- "Invoke /graphify via Skill tool — never call graphify Python API directly"
- "All remote content fetched to /tmp before graphify invocation"
- "Cleanup /tmp after /preserve confirms, not after graphify"
- "/teach does NOT classify entities — it passes graphify output to /preserve, which owns classification"

### File 2: `skills/preserve/SKILL.md` (moderate addition)

**Phase 1 — Add section 1.3: Graphify output input**

After existing sections 1.1 (Structured input) and 1.2 (Free-form input), add:

```markdown
### 1.3 Graphify output input

When called by `/bedrock:teach` (or any skill) with a graphify output reference,
OR when the user invokes `/bedrock:preserve` directly pointing at a graphify-out/ directory:

**Input format:**
- `graphify_output_path`: path to `graphify-out/` directory
- `source_url`: original external source URL/path (optional — may not be present for manual invocation)
- `source_type`: type of external source (optional)

**Processing:**

1. **Read graph.json** from `graphify_output_path/graph.json`:
   - Parse NetworkX node-link format
   - Extract all nodes with: id, label, file_type, source_file, source_location
   - Extract all edges with: source, target, relation, confidence, confidence_score
   - If graph.json is missing or empty: abort with error

2. **Read obsidian files** from `graphify_output_path/obsidian/*.md`:
   - For each markdown file, read frontmatter and body
   - Correlate with graph.json by matching filename stem to node id (kebab-cased)
   - If obsidian file doesn't exist for a node: fall back to graph.json metadata alone

3. **Read analysis** from `graphify_output_path/.graphify_analysis.json` (if exists):
   - Extract community assignments, god nodes, community labels
   - Use community labels to inform domain/* tags

4. **Classify graphify nodes into vault entity types** — /preserve owns this classification:
   - Read ALL entity definitions from plugin (see "Plugin Paths")
   - For each graphify node, classify:
     - `file_type: code` → `knowledge-node` (actor inferred from source_file path or repo name)
     - `file_type: document` → classify using entity definitions (When to create / When NOT to create / How to distinguish)
     - `file_type: paper` → `topic` or `fleeting` depending on completeness criteria
     - God nodes (high degree) → consider as `actor` or `topic`
     - Apply Zettelkasten classification: if content doesn't meet completeness criteria → `fleeting`

5. **Filter relevant nodes:**
   - For knowledge-nodes: select top ~50 by relevance (degree > average, service classes, controllers, public interfaces). Exclude test nodes and trivial nodes.
   - For document/paper nodes: include all.

6. **Match against existing vault** — Use existing textual matching logic from Phase 2 (filename, name, aliases, graphify_node_id). Mark matched nodes as `update`, unmatched as `create`.

7. **Build internal structured format** for each classified + filtered entity:
   - `type`: from classification (step 4)
   - `name`: from graphify node label (kebab-cased for filename)
   - `action`: create or update (from step 6 matching)
   - `content`: from obsidian markdown file body (or graph.json metadata if no obsidian file)
   - `relations`: from graph.json edges (convert node ids to entity slugs)
   - `source`: from input `source_type` (or "graphify" if not provided)
   - `source_url`: from input `source_url` (if provided)
   - `metadata`: for knowledge-nodes, include graphify_node_id, actor, node_type, source_file, confidence

8. **Proceed to Phase 3** (Change Proposal) — present the classified entity list for user confirmation, then execute writes as normal.
```

**Key change:** /preserve now owns entity classification for graphify input. This means users can invoke `/bedrock:preserve` directly with a graphify-out/ directory (bypassing /teach) and still get full classification + confirmation + writes. The existing Phase 2 (matching) is partially absorbed into step 6 above for graphify input; Phase 3 onward (proposal, execution, linking, publish, report) is unchanged.

### File 3: `skills/setup/SKILL.md` (minor edit)

**Phase 1.2 — Update graphify status:**

Change graphify from optional to required. Update the row in the dependency check table:

| Dependency | Check method | What it unlocks |
|---|---|---|
| graphify | Glob: `~/.claude/skills/graphify/SKILL.md` | **Required.** Extraction engine for all `/bedrock:teach` ingestion. Without it, /teach cannot process any content. |

Update the missing-dependency message from "This is optional — your vault will work without it" to:

```
> ⚠️ graphify is not installed. This is REQUIRED for /bedrock:teach to work.
> To install, check https://github.com/iurykrieger/graphify for instructions.
>
> Your vault will initialize, but /bedrock:teach will not function until graphify is installed.
```

Keep confluence-to-markdown and gdoc-to-markdown as optional (they're fetch strategies, not the extraction engine).

## Anti-scope

- NOT modifying `/graphify` itself — consumed as-is via Skill invocation
- NOT modifying `/sync` — separate refactoring
- NOT changing entity definitions, templates, or the knowledge-node entity type
- NOT adding new input types beyond what /teach already supports
- NOT changing /preserve's existing structured (1.1) or free-form (1.2) input modes
- NOT changing git workflow, commit conventions, or bidirectional linking logic
- NOT modifying /compress or /query skills

## Technical Decisions

### 1. Skill invocation vs Python API for graphify
**Decision:** Skill invocation via Skill tool.
**Trade-off:** Slower (starts new skill context, full pipeline) vs. direct API (faster, partial pipeline). Skill invocation wins because: (a) clean decoupling — /teach doesn't need to know graphify internals, (b) full pipeline guarantees consistent output format, (c) graphify can evolve independently.
**Risk mitigation:** The graphify pipeline already runs in ~45-90s for typical repos. The overhead of skill context startup is negligible compared to extraction time.

### 2. Unified fetch-to-tmp pattern
**Decision:** All remote content fetched to `/tmp/bedrock-teach-<ts>/` before graphify invocation.
**Trade-off:** Extra disk I/O for local files (copy to tmp) vs. graphify reading from original location. Copy wins because: (a) uniform interface — graphify always gets a single local path, (b) cleanup is simple (`rm -rf` one directory), (c) avoids graphify writing output files alongside user's original files.
**Risk mitigation:** Use `cp` for local files (cheap), `git clone --depth 1` for repos (shallow), and warn on very large files.

### 3. /preserve reads both graph.json and obsidian markdown
**Decision:** Dual read — graph.json for structure/metadata, obsidian files for content.
**Trade-off:** Single source (graph.json only, generate content) vs. dual source (richer content from obsidian output). Dual wins because: (a) obsidian files have pre-rendered content that graphify already wrote, (b) graph.json alone lacks body text for entities, (c) correlation is straightforward (filename stem = node id).
**Risk mitigation:** If obsidian file doesn't exist for a node, fall back to generating content from graph.json metadata alone.

### 4. Entity classification lives in /preserve, not /teach
**Decision:** /preserve owns classification of graphify nodes into vault entity types. /teach is a pure fetcher + orchestrator — it passes the graphify output path to /preserve without classifying.
**Trade-off:** Classification in /preserve (single skill owns the full write pipeline, users can invoke /preserve directly with graphify output) vs. classification in /teach (detection skill classifies, write skill just executes). /preserve wins because: (a) users can run `/bedrock:preserve` directly with local graphify output, bypassing /teach entirely, (b) /preserve already owns entity definitions + matching + Zettelkasten classification for its other input modes, (c) /teach becomes maximally thin — fetch + extract + delegate, nothing more.

### 5. CSV pass-through raw
**Decision:** No pre-processing — CSVs are copied to tmp and graphify handles them as text files.
**Trade-off:** Pre-processing (header detection, truncation) gives cleaner extraction vs. raw pass-through (simpler, graphify decides). Pass-through wins because the whole point of this refactoring is to let graphify handle extraction, not to pre-process for it.

## Applicable Patterns

| Pattern | File | How it applies |
|---|---|---|
| Skill Architecture | `.vibeflow/patterns/skill-architecture.md` | Both refactored skills must keep: YAML frontmatter, Plugin Paths, phased execution, Critical Rules table. /teach phases change from 5 to 5 but with different responsibilities. |
| Skill Delegation | `.vibeflow/patterns/skill-delegation.md` | /teach → /preserve delegation is preserved. The contract simplifies: /teach passes a graphify output path + provenance metadata (source_url, source_type). /preserve owns classification, matching, confirmation, and writes — its Phase 1.3 handles everything from raw graphify output to internal structured format. |
| Vault Writing Rules | `.vibeflow/patterns/vault-writing-rules.md` | All writing rules are preserved as-is. /preserve continues to be the single write point. No changes to frontmatter, wikilinks, tags, update rules, or git workflow. |

No new patterns introduced — this refactoring simplifies by removing inline graphify code, not by adding new patterns.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| graphify output format changes | /preserve's Phase 1.3 breaks silently | Pin to known graph.json schema (NetworkX node-link format). Add validation check on graph.json structure before processing. Document expected fields. |
| Large repos fill `/tmp` | Disk space issues during clone | Use `git clone --depth 1` (shallow). Warn user for repos > 500MB. Cleanup always runs even if later phases fail. |
| graphify skill invocation fails mid-pipeline | Partial output in `graphify-out/` | Verify `graph.json` exists and has > 0 nodes before proceeding. If missing, abort with clear error message. |
| obsidian file ↔ graph.json node id mismatch | /preserve can't correlate content to nodes | Fall back to graph.json metadata alone for unmatched nodes. Log warning for each unmatched node. |
| MCP calls for GitHub metadata fail | Less enrichment for repo ingestion | Best-effort — already the existing pattern. /teach warns but continues. graphify still extracts from the cloned code. |
