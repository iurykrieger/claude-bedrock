---
name: teach
description: >
  Teaches the Second Brain to recognize a new external data source. Ingests content from
  Confluence, Google Docs, CSV, local Markdown, or GitHub repositories, extracts entities
  (actors, discussions, projects, people, teams, topics), incorporates them into the vault,
  and registers the source for future re-ingestion.
  Use when: "bedrock teach", "bedrock-teach", "teach", "ingest source", "import document", "/bedrock:teach",
  or when the user provides a Confluence, Google Docs, or GitHub URL, or a local file path
  to incorporate into the vault.
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, Agent, mcp__plugin_github_github__*, mcp__plugin_atlassian_atlassian__*
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

## Overview

This skill receives an external source (URL or local path), extracts its content, identifies
entities relevant to the vault, and incorporates them — creating new ones or merging with existing ones.
At the end, it passes the source URL to `/bedrock:preserve` which registers the provenance in the `sources` field of each generated entity.

**You are an execution agent.** Follow the phases below in order, without skipping steps.

---

## Phase 1 — Detect and Read Source

### 1.1 Classify the input

The user provides an argument. Classify it in the following priority order:

| Input | Detected type | Reading method |
|---|---|---|
| URL containing `confluence` or `atlassian.net` | confluence | Invoke skill `/confluence-to-markdown` passing the URL |
| URL containing `docs.google.com` | gdoc | Invoke skill `/gdoc-to-markdown` passing the URL |
| URL containing `github.com` | github-repo | See section 1.2 below |
| Local path ending in `.csv` | csv | See section 1.3 below |
| Local path ending in `.md` or `.txt` | markdown | Use Read to read the file directly |
| No match above | manual | Ask the user: "Could not identify the source type. Paste the content or provide a valid URL/path." |

If no argument was provided: ask the user "What source do you want to ingest? Provide a URL (Confluence, Google Docs, GitHub) or a local file path (.md, .csv, .txt)."

### 1.2 Reading a GitHub repository

For GitHub URLs (e.g.: `https://github.com/acme-corp/billing-api`):

1. Extract `owner/repo` from the URL
2. Use GitHub MCP directly (NOT via subagent — MCP permissions are not inherited):
   - `mcp__plugin_github_github__get_file_contents` → read the repo's README.md
   - `mcp__plugin_github_github__list_commits` → last 10 commits
   - `mcp__plugin_github_github__list_pull_requests` → last 5 PRs (state=all, sort=updated)
3. Compile everything into a single markdown text

> **Best-effort:** If any MCP call fails, continue with what was obtained. Do NOT block ingestion.

### 1.2.1 Semantic extraction via graphify (GitHub repos) — MANDATORY

After reading via MCP (1.2), run the graphify pipeline on the local repository to extract
entities and semantic relationships (functions, classes, concepts, design decisions).

**IMPORTANT:** Graphify is a MANDATORY part of /bedrock:teach for github-repos. Do NOT skip, do NOT suggest
"run later", do NOT present as an optional step. The persistence of resulting knowledge-nodes
is also mandatory — it is part of the /bedrock:teach flow, not a separate step.

**Pre-conditions:**
1. Extract `repo-name` from the URL (last segment: `acme-corp/billing-api` → `billing-api`)
2. Check if the repo exists locally at `../<repo-name>/` (repos may be in subdirectories like `../payments/<repo-name>/` — search recursively)
3. If the repo does NOT exist locally in any subdirectory of `../`: clone via `git clone` from GitHub and proceed.

**If the repo exists locally:**

1. Check if graphify is installed (invoking the `/graphify` skill internally is not necessary — use the Python pipeline directly):

```bash
# Detect Python and check graphify
GRAPHIFY_BIN=$(which graphify 2>/dev/null)
if [ -n "$GRAPHIFY_BIN" ]; then
    PYTHON=$(head -1 "$GRAPHIFY_BIN" | tr -d '#!')
    case "$PYTHON" in
        *[!a-zA-Z0-9/_.-]*) PYTHON="python3" ;;
    esac
else
    PYTHON="python3"
fi
"$PYTHON" -c "import graphify" 2>/dev/null || "$PYTHON" -m pip install graphifyy -q 2>/dev/null || "$PYTHON" -m pip install graphifyy -q --break-system-packages 2>&1 | tail -3
mkdir -p graphify-out
"$PYTHON" -c "import sys; open('graphify-out/.graphify_python', 'w').write(sys.executable)"
```

If installation fails: warn "Graphify not available. Continuing with textual extraction." and proceed.

2. **Detect:** Detect files in the local repository.

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('../<repo-name>'))
print(json.dumps(result))
" > graphify-out/.graphify_detect.json
```

Present a summary to the user: `Corpus: X files · ~Y words`

3. **Copy source into the vault (resolve subagent permissions):**

Subagents CANNOT read files outside the vault directory. For the semantic extraction
to work, copy the repo files to `graphify-out/src/<repo-name>/`:

```bash
# Copy source code into the vault (subagents can only read inside the vault)
rm -rf graphify-out/src/<repo-name>
mkdir -p graphify-out/src/<repo-name>
# Copy only relevant files (exclude .git, bin, obj, node_modules)
rsync -a --exclude='.git' --exclude='bin' --exclude='obj' --exclude='node_modules' \
  --exclude='packages' --exclude='.vs' --exclude='TestResults' \
  <path-do-repo>/ graphify-out/src/<repo-name>/
echo "Source copied: $(find graphify-out/src/<repo-name> -type f | wc -l) files"
```

**IMPORTANT:** `graphify-out/` is in `.gitignore` — the copied files will not be committed.

After copying, re-run detect on the copied path so that the paths in nodes reference `graphify-out/src/`:
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('graphify-out/src/<repo-name>'))
Path('graphify-out/.graphify_detect.json').write_text(json.dumps(result, indent=2))
print(f'Detect (local copy): {result.get(\"total_files\", 0)} files')
"
```

4. **Extract:** Run AST + semantic extraction via subagents.

**Pre-extraction cleanup (MANDATORY):**

Before dispatching subagents, clean stale extraction files to prevent
subagents from reading data from previous runs of OTHER repos:

```bash
# Clean previous extractions (do NOT delete graph.json — it is the central cross-repo graph)
rm -f graphify-out/.graphify_extract.json
rm -f graphify-out/.graphify_extract_*.json
rm -f graphify-out/.graphify_ast.json
echo "Pre-extraction cleanup completed"
```

**CRITICAL — Instructions for subagents:**

When dispatching extraction subagents, MANDATORILY include in the prompt:
- "You MUST read files ONLY from `graphify-out/src/<repo-name>/`. Do NOT read `graphify-out/graph.json` or any existing `.graphify_extract*.json` file. This is a FRESH extraction."
- "Save the result in `graphify-out/.graphify_extract_<repo-name>.json`"

This prevents contamination by nodes from other repos that exist in the graph.json from previous runs.

Use subagents for semantic extraction (follow the complete /graphify skill pipeline:
Part A AST + Part B semantic in parallel). All paths now point to
`graphify-out/src/<repo-name>/` — accessible by subagents.

**Output:** The extraction result must be saved in a **repo-specific** file:
`graphify-out/.graphify_extract_<repo-name>.json` (NOT the generic `.graphify_extract.json`).

If multiple subagents are used (e.g.: per module), each saves to its own file
(e.g.: `.graphify_extract_<repo-name>_api.json`, `.graphify_extract_<repo-name>_gateway.json`)
and step 5 performs the merge.

**IMPORTANT:** If the actor was previously processed (check if `graphify-out/graph.json` exists
and contains nodes with `source_file` referencing this repo), use `--update` for incremental extraction:
- Check cache via `graphify.cache.check_semantic_cache`
- Extract only new/modified files
- This ensures that re-runs of /bedrock:teach on the same actor do not duplicate nodes

5. **Build + Cluster + Analyze:** Build graph, cluster, analyze.

**Subagent merge (if multiple files):**

If the extraction used multiple subagents (e.g.: per module), merge the partial files
before building the graph:

```bash
$(cat graphify-out/.graphify_python) -c "
import json, glob
from pathlib import Path

all_nodes, all_edges, seen_ids = [], [], set()
for f in sorted(glob.glob('graphify-out/.graphify_extract_<repo-name>*.json')):
    data = json.loads(Path(f).read_text())
    for n in data.get('nodes', []):
        if n['id'] not in seen_ids:
            all_nodes.append(n)
            seen_ids.add(n['id'])
    all_edges.extend(data.get('edges', []))

# Deduplicate edges
edge_keys = set()
unique_edges = []
for e in all_edges:
    key = (e['source'], e['target'], e['relation'])
    if key not in edge_keys:
        unique_edges.append(e)
        edge_keys.add(key)

merged = {'nodes': all_nodes, 'edges': unique_edges}
Path('graphify-out/.graphify_extract_<repo-name>.json').write_text(json.dumps(merged, indent=2))
print(f'Merged extraction: {len(all_nodes)} nodes, {len(unique_edges)} edges')
"
```

**Build graph:**

```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections
from graphify.export import to_json
from pathlib import Path

# Read repo-specific extraction (NOT the generic .graphify_extract.json)
extraction = json.loads(Path('graphify-out/.graphify_extract_<repo-name>.json').read_text())

# Merge with existing graph.json (if it exists)
existing_graph = Path('graphify-out/graph.json')
if existing_graph.exists():
    existing = json.loads(existing_graph.read_text())
    # IMPORTANT: remove nodes from the SAME repo before merging (avoid duplicates from re-runs)
    repo_id_prefix = '<repo-name>'.replace('-', '_')
    existing['nodes'] = [n for n in existing.get('nodes', [])
                         if not n.get('id', '').startswith(repo_id_prefix)]
    existing['edges'] = [e for e in existing.get('edges', [])
                         if not e.get('source', '').startswith(repo_id_prefix)
                         and not e.get('target', '').startswith(repo_id_prefix)]
    # Add new nodes and edges
    for node in extraction.get('nodes', []):
        existing.setdefault('nodes', []).append(node)
    for edge in extraction.get('edges', []):
        existing.setdefault('edges', []).append(edge)
    merged = existing
else:
    merged = extraction

G = build_from_json(merged)
communities = cluster(G)
cohesion = score_all(G, communities)
to_json(G, communities, 'graphify-out/graph.json')

print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
"
```

6. **Result:** Store the extracted nodes for use in Phase 3:
   - `graphify-out/.graphify_extract_<repo-name>.json` — nodes and edges from this extraction (repo-specific file)
   - `graphify-out/graph.json` — updated central graph (merge of all repos)
   - Set flag `graphify_available = true` for Phase 3

7. **Cleanup:** After complete extraction, remove the local copy:
```bash
rm -rf graphify-out/src/<repo-name>
```

### 1.3 CSV reading

For `.csv` files:

1. Use Read to read the file
2. If the file has more than 200 lines: truncate to the first 200 and warn the user
3. Interpret the first line as a header
4. Treat the CSV as tabular text — do NOT assume a fixed schema
5. The content will be semantically analyzed in Phase 3

### 1.4 Phase 1 Result

At the end of this phase, you should have:
- **content**: markdown text from the source (may be long)
- **url_or_path**: original URL or file path
- **source_type**: `confluence`, `gdoc`, `github-repo`, `csv`, `markdown`, or `manual`
- **graphify_available**: `true` if graphify was executed successfully (1.2.1 or 1.4.1)

### 1.4.1 Graphify add for external sources (confluence, gdoc, markdown)

For non-GitHub sources (confluence, gdoc, markdown), add the content to the central graph
via `graphify add`. This allows /bedrock:query (Part 3) to perform cross-source queries.

**Pre-conditions:**
- `source_type` is `confluence`, `gdoc`, or `markdown`
- graphify is installed (check with `$(cat graphify-out/.graphify_python) -c "import graphify"`)

**If graphify is available:**

1. Save markdown content to a temporary file:
```bash
mkdir -p graphify-out/raw
# Save content in graphify-out/raw/<source-slug>.md
```

2. Run `graphify add`:
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from graphify.extract import collect_files, extract
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.export import to_json
from pathlib import Path

# Detect + extract from the new file
result = detect(Path('graphify-out/raw/<source-slug>.md'))
files = [Path('graphify-out/raw/<source-slug>.md')]

# Semantic extraction (single file — no subagents needed)
# Use Read to read the file and extract entities as a single subagent
# The result follows the same .graphify_extract.json format

# Merge with existing graph.json
existing_graph = Path('graphify-out/graph.json')
if existing_graph.exists():
    existing = json.loads(existing_graph.read_text())
    # ... merge logic (same as 1.2.1 step 4)
else:
    existing = extraction

G = build_from_json(existing)
communities = cluster(G)
to_json(G, communities, 'graphify-out/graph.json')
print(f'Graph updated: {G.number_of_nodes()} nodes')
"
```

3. Set `graphify_available = true`

**If graphify is NOT available:** proceed without it — existing textual extraction continues to work.
Do NOT block ingestion due to lack of graphify.

---

## Phase 2 — Load Vault Context

### 2.1 Read entity definitions

Use Read to read ALL entity definition files from the plugin (see "Plugin Paths" section):
`<base_dir>/../../entities/*.md`
These files define what each entity type is, when to create one, and how to distinguish between them.
Internalize these definitions — you will use them in Phase 3 to classify content.

### 2.2 List existing entities

Use Glob to list all files in each entity directory (excluding `_template.md`):
- `actors/*.md`
- `people/*.md`
- `teams/*.md`
- `topics/*.md`
- `discussions/*.md`
- `projects/*.md`
- `fleeting/*.md`
- `fleeting/*.md`

For each file found:
- Extract the filename without extension (e.g.: `billing-api`)
- Use Read to extract the `name` field from the YAML frontmatter
- Store: `{filename, name, type}` for matching in Phase 3

Report: "Phase 2: N entity definitions loaded, M existing entities cataloged."

---

## Phase 3 — Analyze Content and Extract Entities

### 3.1 Identify existing entities mentioned

For each entity cataloged in Phase 2, check if the filename OR name appears in the content:

**Matching rules:**
- Normalize for comparison: lowercase, no accents, no hyphens
- Partial matching is acceptable for compound names (e.g.: "billing api" matches "billing-api")
- Do NOT match substrings of 3 letters or fewer (e.g.: "api" does NOT match "billing-api")
- Do NOT match generic words (e.g.: "company", "service", "system")

For each match, record:
- Type (actor, person, team, topic, discussion, project)
- Filename (for wikilink)
- Action: `update`
- Extracted info: excerpt from content where it appears

### 3.1.1 Zettelkasten classification of content

For each content excerpt analyzed, classify by maturity before extracting entities:

**Consolidated content (-> permanent/bridge):**
- Concrete data: repository names, full names of people, specific dates, explicit decisions
- Self-contained information: understandable without external context
- Meets completeness criteria of at least 1 entity definition (see "Completeness Criteria" section in the plugin's entity definitions)

**Content in formation (-> fleeting):**
- Vague mentions: "someone mentioned...", "it seems like...", "maybe..."
- Fragments without context: partial names, loose ideas, hypotheses
- Generic TODOs without an owner or deadline
- Information that does NOT meet completeness criteria of any type

**Rule:** when classifying entities for the Phase 3 list, include the field `type: fleeting` for content in formation.
The `/bedrock:preserve` performs the final validation via Phase 1.3 (Zettelkasten Classification).

### 3.1.2 Classify graphify nodes (if graphify_available)

If `graphify_available = true` (Phase 1.2.1 or 1.4.1), read `graphify-out/.graphify_extract_<repo-name>.json`
and classify each node extracted by graphify:

1. **Read the extracted nodes:**
```bash
$(cat graphify-out/.graphify_python) -c "
import json
from pathlib import Path
extract = json.loads(Path('graphify-out/.graphify_extract_<repo-name>.json').read_text())
print(json.dumps({'nodes': len(extract.get('nodes', [])), 'edges': len(extract.get('edges', []))}, indent=2))
"
```

2. **For each node with `file_type: code`** (functions, classes, modules, endpoints):
   - Classify as `type: knowledge-node`
   - Fill in mandatory fields:
     - `name`: use the graphify node's `label`
     - `graphify_node_id`: use the graphify node's `id`
     - `actor`: infer from `source_file` or from the repo that was processed
     - `node_type`: infer from context (function, class, module, interface, endpoint)
     - `source_file`: use the graphify node's `source_file`
     - `confidence`: use the `confidence` of the strongest edge connected to the node (EXTRACTED > INFERRED > AMBIGUOUS)
     - `description`: generate description in the vault's configured language based on the label and context
   - Map graphify edges to the `relations` field (wikilinks to other knowledge-nodes)
   - Add to the entity list with `action: create` (or `update` if `graphify_node_id` already exists in the vault)

3. **For each node with `file_type: document` or `file_type: paper`** (concepts, decisions):
   - Do **NOT** automatically classify as knowledge-node
   - Use the plugin's entity definitions (see "Plugin Paths" section) to classify:
     - If it describes a broad architectural decision -> `type: topic`
     - If it describes a meeting or debate -> `type: discussion`
     - If it is a concept in formation -> `type: fleeting`
     - If it describes something specific to an actor -> `type: knowledge-node`
   - Apply Zettelkasten Classification rules (3.1.1)
   - Consult the "When to create", "When NOT to create", "How to distinguish from other types" sections of each entity definition

4. **Graphify edges -> relationships:**
   - For each edge between classified nodes, add to the `relations` list of the structured input
   - `EXTRACTED` edges -> certain relationship, include
   - `INFERRED` edges -> probable relationship, include with a note
   - `AMBIGUOUS` edges -> omit (will be reviewed in /bedrock:compress)

5. **Automatic actor migration to folder:**
   - If knowledge-nodes are going to be created for an actor that is still a flat file:
     - Migrate `actors/<name>.md` -> `actors/<name>/<name>.md` (via `git mv`)
     - Create `actors/<name>/nodes/`
     - Add "Knowledge Nodes" section to the actor's body

6. **Filter relevant nodes for persistence:**
   - Select the top ~50 nodes by relevance (god nodes, service classes, controllers, public interfaces)
   - Filtering criteria: degree > average, or label contains "Service", "Controller", "Client", "Factory", "Handler", "Mapper"
   - Test nodes (labels with "Tests", "Test", "Builder") are EXCLUDED — do not persist tests as knowledge-nodes
   - Trivial nodes (getters, setters, simple DTOs) are EXCLUDED
   - The filtered nodes will be included in the Phase 3.3 entity list as `type: knowledge-node`

**IMPORTANT:** The persistence of knowledge-nodes is MANDATORY — it is part of the /bedrock:teach flow.
Do NOT present as a "suggested next step". The filtered knowledge-nodes are included in the
entity list for user confirmation (Phase 3.3) and delegated to /bedrock:preserve (Phase 4)
along with the other entities.

Report: "Graphify: N code nodes extracted, M filtered for persistence (-> knowledge-nodes), P edges."

### 3.2 Identify NEW entities to create

Analyze the content looking for excerpts that describe something that does NOT exist in the vault but
fits an entity definition. For each candidate:

1. Consult the "When to create" section of the corresponding definition -> positive criteria
2. Consult the "When NOT to create" section -> exclusion criteria
3. If ambiguous, consult "How to distinguish from other types" -> disambiguation
4. If the candidate passes the criteria: register as a new entity

For each new entity, record:
- Type (actor, person, team, topic, discussion, project)
- Suggested canonical name (repo name for actors, full name for persons, etc.)
- Action: `create`
- Extracted info: excerpt from content that justifies creation

### 3.3 Present to user for confirmation

**MANDATORY:** Before creating/updating any entity, present the complete list:

```
## Detected entities

| # | Type | Name | Action | Extracted info | Source |
|---|---|---|---|---|---|
| 1 | actor | billing-api | update | Mentioned as dependency of the new flow | textual |
| 2 | discussion | 2026-04-04-planning-q2 | create | Meeting minutes with decisions about migration | textual |
| 3 | person | alice-smith | create | Mentioned as DRI of project X | textual |
| 4 | knowledge-node | ProcessTransaction | create | Transaction authorization orchestration function | graphify |
| 5 | knowledge-node | KafkaEventPublisher | create | Kafka event publishing | graphify |

Confirm? (y/n, or edit the list by removing unwanted lines)

> **Note:** Entities with source "graphify" were extracted via semantic analysis of the repository.
> Entities with source "textual" were extracted via pattern matching on the content.
```

- If the user confirms: proceed to Phase 4
- If the user edits: adjust the list per instructions
- If the user cancels: end with "Ingestion canceled. No entities modified."

---

## Phase 4 — Delegate Entities to /bedrock:preserve

All entities confirmed by the user (Phase 3) are delegated to `/bedrock:preserve`.
The `/bedrock:teach` does NOT create or update entities directly — that responsibility belongs to `/bedrock:preserve`.

### 4.1 Compile structured list

Build the entity list in the format accepted by `/bedrock:preserve`:

```yaml
entities:
  - type: discussion
    name: "2026-04-05-planning-q2"
    action: create
    content: "relevant excerpt from the content extracted in Phase 3..."
    relations:
      actors: ["actor-slug-1"]
      people: ["person-slug-1"]
    source: "<source_type from Phase 1>"
    source_url: "<url_or_path from Phase 1>"
    source_type: "<source_type from Phase 1>"
  - type: actor
    name: "billing-api"
    action: update
    content: "new context extracted in Phase 3..."
    source: "<source_type from Phase 1>"
    source_url: "<url_or_path from Phase 1>"
    source_type: "<source_type from Phase 1>"
```

**Compilation rules:**
- `type` and `name`: extracted from Phase 3 (user-confirmed list)
- `action`: `create` or `update` as identified in Phase 3
- `content`: excerpt from the source content that justifies the entity
- `relations`: infer relationships between entities in the list (if A mentions B, include B in A's relations)
- `source`: use the `source_type` detected in Phase 1 (confluence, gdoc, github-repo, csv, markdown, manual). For knowledge-nodes, use `"graphify"`
- `source_url`: URL or path of the external source (`url_or_path` field from Phase 1). The `/bedrock:preserve` uses this value to populate the `sources` field in the entity's frontmatter
- `source_type`: type of the external source (same value as `source`). The `/bedrock:preserve` uses this value for the `sources[].type` field
- `metadata`: include additional frontmatter fields when available (e.g.: `status`, `role`, `team`)

**Additional rules for knowledge-nodes (graphify source):**
- `type`: `knowledge-node`
- `metadata.graphify_node_id`: node id in graphify (e.g.: `billing_api_processTransaction`)
- `metadata.actor`: wikilink of the parent actor (e.g.: `"[[billing-api]]"`)
- `metadata.node_type`: `function`, `class`, `module`, `concept`, `decision`, `interface`, `endpoint`
- `metadata.source_file`: relative path in the actor's repo
- `metadata.confidence`: `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`
- `relations.knowledge_nodes`: wikilinks to other knowledge-nodes connected via graphify edges

### 4.2 Invoke /bedrock:preserve

Use the Skill tool to invoke `/bedrock:preserve` passing the structured list as an argument.

The `/bedrock:preserve` handles:
- Textual matching with existing entities
- Creating new entities following templates
- Updating existing entities (merge/append-only)
- Bidirectional linking (wikilinks)
- Git commit of entities

### 4.3 Wait for result

The `/bedrock:preserve` returns:
- List of entities created/updated
- Commit hash (if there was a commit)
- Any errors or warnings

Record the result for use in the final report (Phase 5).

---

## Phase 5 — Report

The `/bedrock:preserve` has already committed the entities (including the `sources` field populated with the source URL).
The `/bedrock:teach` does NOT make a separate commit — provenance is recorded within each entity by `/bedrock:preserve`.

Present to the user:

```
## /bedrock:teach — Report

### Ingested source
- **Type:** <source_type>
- **URL/Path:** <url>

### Entities processed (via /bedrock:preserve)
| Type | Name | Action |
|---|---|---|
| discussion | 2026-04-04-planning-q2 | create |
| actor | billing-api | update |
| person | alice-smith | create |

### Provenance
Each entity above received in the `sources` frontmatter field:
- url: <url_or_path>
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
| Mandatory confirmation | ALWAYS present entity list to user BEFORE creating/updating (Phase 3.3) |
| Entity definitions are the manual | Consult the plugin's entity definitions (see "Plugin Paths") to classify content |
| Delegate to /bedrock:preserve | ALL entities are persisted via `/bedrock:preserve` — teach does NOT create/update inline |
| Provenance via source_url | ALWAYS include `source_url` and `source_type` in the input delegated to /bedrock:preserve. The /bedrock:preserve populates the `sources` field in the frontmatter |
| Frontmatter keys in English | `type`, `name`, `updated_at`, etc. Values in the vault's configured language |
| Bare wikilinks | `[[name]]`, never `[[dir/name]]` |
| Wikilinks always kebab-case | `[[charge-service]]`, never `[[ChargeService]]` or `[[chargeService]]`. When generating wikilinks for knowledge-nodes, convert camelCase/PascalCase to kebab-case. E.g.: `ProcessTransaction` -> `[[process-transaction]]`, `KafkaEventPublisher` -> `[[kafka-event-publisher]]` |
| Append-only for people/teams/topics | NEVER delete existing content in the body |
| Actors can be modified | Free merge in body and frontmatter |
| Best-effort for external sources | If MCP fails, continue with what was obtained |
| MCP in main context | Do NOT use subagents for GitHub/Atlassian MCP calls |
| CSV truncated at 200 lines | Warn the user if the file is larger |
| Maximum 2 push attempts | After that, abort and inform |
| Sensitive data | NEVER include credentials, tokens, passwords, PANs, CVVs |
