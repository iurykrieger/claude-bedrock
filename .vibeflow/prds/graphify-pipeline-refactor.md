# PRD: Refactor /teach and /preserve to use /graphify as the sole extraction engine

> Generated via /vibeflow:discover on 2026-04-14

## Problem

The `/bedrock:teach` skill currently contains ~250 lines of bespoke graphify integration code (steps 1.2.1 through 1.4.1) that duplicates what `/graphify` already does better — AST extraction, semantic extraction via parallel subagents, graph building, clustering, and community analysis. Each input type (GitHub, Confluence, GDocs, CSV, Markdown) has its own extraction path, and graphify is only invoked for GitHub repos (with a partial, hand-rolled integration) and optionally for external sources. This creates maintenance burden, inconsistent extraction quality across input types, and a fragile coupling between /teach and graphify internals (direct Python API calls to `graphify.detect`, `graphify.build`, etc.).

Meanwhile, `/graphify` is a mature, generalized pipeline that handles code, docs, PDFs, images, and video uniformly through a single invocation. By making /teach delegate ALL extraction to /graphify (via the skill invocation, not Python API calls), the extraction logic lives in one place, benefits from graphify's caching, parallel subagents, and community detection, and /teach becomes a thin orchestrator focused on what it does best: classifying input, fetching remote content, and preparing it for processing.

On the /preserve side, it currently receives a hand-crafted YAML entity list from /teach and does its own entity classification. With graphify producing both `graph.json` (structured relationships) and obsidian markdown files (pre-rendered content), /preserve can consume richer, more consistent input — using graph.json for relationship mapping and obsidian output for entity content.

## Target Audience

- **Primary:** The /teach and /preserve skills themselves (internal refactoring)
- **Secondary:** Vault users who ingest external content via `/bedrock:teach` — they benefit from more consistent, higher-quality extraction across all input types

## Proposed Solution

Restructure the teach → graphify → preserve pipeline into three clean layers:

1. **`/teach` = Fetcher + Orchestrator.** Classifies input type, fetches remote content to a local temporary path (cloning repos to `/tmp`, downloading URLs, converting Confluence/GDocs to markdown), then invokes `/graphify <local-path> --mode deep --obsidian --obsidian-dir <vault_path>` as a single skill invocation. After graphify completes, hands the output over to /preserve. Cleans up temporary files.

2. **`/graphify` = Extraction Engine.** Unchanged — receives a local path, runs the full pipeline (detect → extract → build → cluster → analyze), outputs to `<vault_path>/graphify-out/` (graph.json, GRAPH_REPORT.md, obsidian/ directory with per-node markdown files).

3. **`/preserve` = Vault Writer.** Gains the ability to read graphify output directly: reads `graph.json` for node metadata, relationships, communities, and confidence scores; reads `graphify-out/obsidian/*.md` for pre-rendered content. Maps graphify nodes to vault entity types using existing entity definitions. Reconciles with existing vault entities via textual matching (existing Phase 2 logic). Presents proposal and executes writes as before.

## Success Criteria

- `/bedrock:teach` invokes `/graphify` for ALL input types (GitHub, Confluence, GDocs, CSV, Markdown, PDF) — no input-type-specific extraction logic remains in /teach
- `/bedrock:teach` SKILL.md is reduced by at least 40% in line count (removal of inline graphify Python code)
- `/bedrock:preserve` can accept graphify output (graph.json + obsidian/) as an input mode alongside the existing structured YAML and free-form text modes
- All existing vault writing rules, entity definitions, bidirectional linking, and git workflow are preserved
- Knowledge-nodes are still created from graphify's code nodes (the entity type and its rules don't change)
- GitHub repo pre-processing (MCP calls for README, PRs, commits) still happens in /teach before handing to graphify
- Temporary files (cloned repos, downloaded content) are cleaned up after processing

## Scope v0

1. **Update `/bedrock:setup`** — Add graphify as a required dependency check during vault initialization. Verify the `/graphify` skill is installed and accessible. Warn/guide installation if missing.

2. **Refactor `/teach` Phase 1 — Fetch** — Replace all input-type-specific extraction logic with a unified fetch-to-tmp pattern:
   - Input classification (keep existing table)
   - Each input type gets a fetch strategy, all targeting `/tmp/bedrock-teach-<timestamp>/`:
     - **GitHub repo:** `git clone` to `/tmp/bedrock-teach-<ts>/<repo-name>/` + MCP enrichment (README, PRs, commits) saved as `_github_metadata.md` alongside cloned code
     - **Confluence URL:** invoke `/confluence-to-markdown`, save output to `/tmp/bedrock-teach-<ts>/<slug>.md`
     - **Google Docs URL:** invoke `/gdoc-to-markdown`, save output to `/tmp/bedrock-teach-<ts>/<slug>.md`
     - **Remote URL (any other):** scrape/fetch content, save to `/tmp/bedrock-teach-<ts>/<slug>.md`
     - **CSV file:** copy to `/tmp/bedrock-teach-<ts>/` (graphify treats as text)
     - **Local Markdown/PDF:** copy to `/tmp/bedrock-teach-<ts>/`
   - All fetched content lands in one directory — this becomes graphify's input path

3. **Refactor `/teach` Phase 2 — Extract** — Single `/graphify` skill invocation:
   - Invoke via Skill tool: `/graphify /tmp/bedrock-teach-<ts>/ --mode deep --obsidian --obsidian-dir <vault_path>`
   - graphify runs its full pipeline (detect → extract → build → cluster → analyze)
   - Output lands in `<vault_path>/graphify-out/`

4. **Refactor `/teach` Phase 3 — Classify + Confirm** — Read graphify output and map to vault entities:
   - Read `graph.json` + `obsidian/*.md` from graphify output
   - Map graphify nodes to vault entity types using entity definitions
   - Present entity list for user confirmation (keep existing Phase 3.3 UX)

5. **Refactor `/teach` Phase 4 — Delegate** — Pass graphify output path to /preserve instead of hand-crafted YAML

6. **Refactor `/teach` Phase 5 — Cleanup** — Remove `/tmp/bedrock-teach-<ts>/` directory after /preserve confirms completion

7. **Add graphify input mode to `/preserve` Phase 1** — New section 1.3: "Graphify output input"
   - Read `<vault_path>/graphify-out/graph.json` for nodes, edges, communities, confidence
   - Read `<vault_path>/graphify-out/obsidian/*.md` for pre-rendered content per node
   - Correlate obsidian filenames with graph.json node IDs (same stem)
   - Classify each node into vault entity type using entity definitions
   - Convert to internal structured format and proceed to Phase 2 (matching)

8. **Remove /teach inline graphify code** — Delete all Python `graphify.*` imports, subprocess calls, manual graph building, subagent dispatch for extraction, `graphify-out/src/` copy logic, extraction merge logic

## Anti-scope

- **NOT modifying `/graphify` itself** — it is a separate skill outside this plugin; we consume its output as-is
- **NOT modifying `/sync`** — even though it has similar extraction patterns, that's a separate refactoring
- **NOT changing entity definitions or templates** — the entity type system stays the same
- **NOT changing the knowledge-node entity type** — it's still created from graphify code nodes
- **NOT adding new input types** — we support the same inputs as today (Confluence, GDocs, GitHub, CSV, Markdown)
- **NOT modifying the git workflow or commit conventions**
- **NOT changing /preserve's existing structured input or free-form input modes** — the graphify mode is additive
- **NOT handling graphify installation/upgrade** — `/bedrock:setup` guarantees graphify is installed; /teach assumes it's available

## Technical Context

### Current Architecture (from .vibeflow/)

**Skill delegation pattern** (patterns/skill-delegation.md): All skills delegate entity writes to `/bedrock:preserve`. This pattern is preserved — /teach still delegates to /preserve.

**Skill architecture** (patterns/skill-architecture.md): Skills have YAML frontmatter, Plugin Paths section, phased execution. Both refactored skills keep this structure.

**Key constraint:** MCP calls (GitHub, Atlassian) cannot run in subagents — permissions are not inherited. /teach must make these calls in the main context before invoking graphify.

### graphify Output Format

When invoked with `--obsidian --obsidian-dir <path>`:
- `graphify-out/graph.json` — NetworkX node-link format with nodes (id, label, file_type, source_file, source_location) and edges (source, target, relation, confidence, confidence_score)
- `graphify-out/GRAPH_REPORT.md` — Human-readable audit report with god nodes, surprising connections, community labels
- `graphify-out/obsidian/*.md` — One markdown file per node, with frontmatter (tags, aliases) and body content
- `graphify-out/obsidian/graph.canvas` — Obsidian canvas with community layout
- `graphify-out/.graphify_analysis.json` — Communities, cohesion scores, god nodes, surprises

### Node-to-Entity Mapping Strategy

/preserve will need to map graphify nodes to vault entities:
- `file_type: code` nodes → `knowledge-node` entities (existing behavior)
- `file_type: document` nodes → classify via entity definitions (topic, discussion, fleeting, etc.)
- `file_type: paper` nodes → likely `topic` or `fleeting` depending on completeness
- God nodes (high-degree) → likely `actor` or `topic` entities
- Community labels → can inform `domain/*` tags

### Reconciliation: graph.json ↔ obsidian files

graphify's `to_obsidian()` uses `node_id` as the filename stem (kebab-cased). /preserve correlates by:
1. Reading graph.json → get all nodes with metadata
2. For each node, check if `graphify-out/obsidian/<node_id_kebab>.md` exists
3. If yes: use the obsidian file's content as the entity body content
4. If no: generate content from graph.json metadata alone

## Resolved Decisions

1. **graphify invocation method:** Skill invocation via the Skill tool (`/graphify <path> --mode deep --obsidian --obsidian-dir <vault>`). No direct Python API calls — clean decoupling.

2. **Content fetching:** ALL remote content (any URL type) is fetched/scraped/cloned by /teach to `/tmp/bedrock-teach-<ts>/` before invoking graphify. Each content type has its own fetch strategy but all land in the same temp directory. graphify receives a local path only.

3. **Cleanup timing:** /teach cleans up `/tmp/bedrock-teach-<ts>/` after /preserve confirms completion — not after graphify finishes.

4. **graphify availability:** `/bedrock:setup` guarantees graphify is installed as a required dependency.

5. **CSV handling:** Pass through raw to graphify — no pre-processing (no header detection, no truncation). graphify handles it as text.

## Open Questions

None.
