---
name: query
description: >
  Smart vault reader skill. Receives a natural language question,
  searches the vault for the information, cross-references context between entities via wikilinks,
  prioritizes recent information, and optionally fetches external sources by delegating to
  known skills (/confluence-to-markdown, /gdoc-to-markdown, GitHub MCP).
  Use when: "bedrock query", "bedrock-query", "/bedrock:query", any question about the vault, "what do we know about",
  "who owns", "what's the status of", "tell me about", "how does it work", or any
  Second Brain query.
user_invocable: true
allowed-tools: Bash, Read, Glob, Grep, Skill, Agent, mcp__plugin_github_github__get_file_contents, mcp__plugin_github_github__list_commits, mcp__plugin_github_github__list_pull_requests
---

# /bedrock:query — Smart Vault Reader

## Plugin Paths

Entity definitions and templates are in the plugin directory, not at the vault root.
Use the "Base directory for this skill" provided at invocation to resolve the paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- Plugin CLAUDE.md: `<base_dir>/../../CLAUDE.md` (already automatically injected into context)

Where `<base_dir>` is the path provided in "Base directory for this skill".

---

## Overview

This skill receives a natural language question, searches the vault to find the answer,
cross-references context between entities via wikilinks, prioritizes recent information, and optionally
fetches external sources when local information is insufficient.

**You are a query agent. You only READ — never write, edit, or delete files.**

If the query reveals outdated or missing information, suggest that the user run
`/bedrock:preserve` or `/bedrock:teach` to update the vault. Never perform the update yourself.

---

## Phase 1 — Analyze the Question

### 1.1 Classify the question

Read the user's question and identify:

1. **Mentioned entities** — names of systems, people, teams, topics, projects, or discussions.
   They may appear as:
   - Exact filename (e.g.: "billing-api", "squad-payments")
   - Human-readable name (e.g.: "Billing API", "Squad Payments")
   - Alias or acronym (e.g.: "BillingAPI", "BRB")
   - Contextual reference (e.g.: "the billing service", "the notifications team")

2. **Relevant domain(s)** — `payments`, `notifications`, `orders`, `integrations`, `checkout`, `compliance`, `internal-tools`.
   Infer from the mentioned entities or the question context.

3. **Type of information sought:**
   - **Status/overview** — "what is X?", "what's the status of X?"
   - **Architecture/stack** — "how does X work?", "what's the stack of X?"
   - **People/teams** — "who owns X?", "who works with Y?"
   - **History/decisions** — "what was decided about X?", "what happened with Y?"
   - **Relationships** — "what depends on X?", "how does Y relate to Z?"
   - **Deprecation** — "what is being deprecated?", "what's the deprecation plan for X?"

### 1.2 Assess clarity

If the question is too ambiguous to produce a targeted search (e.g.: "tell me everything",
"how does the system work?", "what's going on?"), ask for clarification:

> "Your question is broad. Can you specify: which system, team, or topic would you like to know more about?"

If the question mentions something that clearly isn't part of the vault (e.g.: something personal,
unrelated technology), inform: "I didn't find anything in the vault about this."

### 1.3 Phase 1 Result

At the end, you should have:
- **search_terms**: list of names, aliases, and keywords to search for
- **domains**: list of relevant domains (may be empty if not identified)
- **info_type**: classification of the type of information sought
- **explicit_entities**: entities mentioned directly by name (if any)

---

## Phase 2 — Local Vault Search

### 2.0 Check graph availability

```bash
if [ -f "graphify-out/graph.json" ] && [ -s "graphify-out/graph.json" ]; then
    echo "graph_available"
else
    echo "graph_not_available"
fi
```

- **If `graph_available`:** use Phase 2-G (graphify delegation) below.
- **If `graph_not_available`:** skip to Phase 2-S (sequential search).

### Phase 2-G — Graphify Delegation (when graph available)

The graphify query engine handles all graph traversal (BFS, DFS, path-finding, node explanation).
`/bedrock:query` delegates to `/graphify` via the Skill tool and receives structured JSON,
then post-processes the result with vault-specific logic in Phase 2.5.

#### 2-G.1 Route question type to graphify mode

From the Phase 1 results (search_terms, info_type, explicit_entities), select the graphify command:

| Phase 1 info_type | Graphify invocation |
|---|---|
| Relationship, status, overview, history, deprecation | `/graphify query "<original_question>"` |
| Path-finding ("how does X connect to Y", with 2 explicit entities) | `/graphify path "<entityA>" "<entityB>"` |
| Single-entity deep dive ("what is X?", "explain X", 1 explicit entity) | `/graphify explain "<entity>"` |
| Broad domain ("tell me about the payments domain") | `/graphify query "<question>"` |

#### 2-G.2 Invoke graphify via Skill tool

Use the Skill tool to invoke the selected graphify command. Append the following structured output
instruction to the invocation prompt:

```
After completing the traversal, return ONLY a JSON object with this structure (no prose, no markdown fences):
{
  "mode": "query|path|explain",
  "start_nodes": ["node_id1", "node_id2"],
  "nodes": [
    {"id": "node_id", "label": "Human Readable Name", "source_file": "relative/path", "community": 0, "source_location": "file:line"}
  ],
  "edges": [
    {"source": "node_id", "target": "node_id", "relation": "calls|references|...", "confidence": "EXTRACTED|INFERRED|AMBIGUOUS", "confidence_score": 0.9}
  ],
  "communities": {
    "0": {"label": "Community Name", "node_ids": ["id1", "id2"]}
  },
  "traversal": {"mode": "bfs|dfs", "depth": 3, "budget_used": 1200}
}
```

**IMPORTANT:**
- Invoke via the Skill tool — never call graphify Python API directly (`graphify.query`, `graphify.build`, etc.)
- This follows the same delegation pattern as `/bedrock:teach` → `/graphify`

#### 2-G.3 Parse graphify response

Extract the JSON object from the graphify Skill tool response.

- **If JSON parses successfully:** store as `graphify_result` for Phase 2.5. Report: "Graphify query returned N nodes, M edges."
- **If parsing fails** (graphify returned prose, error, or timeout): log warning "Graphify delegation failed — falling back to sequential search." Then execute Phase 2-S instead.

### Phase 2-S — Sequential Search (when graph not available or graphify delegation failed)

When the graph is not available or graphify delegation failed, use sequential search:

### 2.1 Read entity definitions

Use Read to read the entity definition files from the plugin (see "Plugin Paths" section):
- If the question is about a system → read `<base_dir>/../../entities/actor.md`
- If the question is about a person → read `<base_dir>/../../entities/person.md`
- If the question is about a team → read `<base_dir>/../../entities/team.md`
- If the question is about a topic/deprecation → read `<base_dir>/../../entities/topic.md`
- If the question is about a meeting/decision → read `<base_dir>/../../entities/discussion.md`
- If the question is about a project/initiative → read `<base_dir>/../../entities/project.md`
- If you don't know the type → read all entity definitions from the plugin to classify correctly

### 2.2 Search entities by name and alias

For each search term identified in Phase 1:

**Step 1 — Search by filename:**
```
Glob: actors/<term>*.md, people/<term>*.md, teams/<term>*.md,
      topics/*<term>*.md, discussions/*<term>*.md, projects/<term>*.md,
      sources/<term>*.md, fleeting/*<term>*.md
```

**Step 2 — Search by alias in frontmatter:**
```
Grep: pattern="aliases:.*<term>" in directories: actors/, people/, teams/,
      topics/, discussions/, projects/
      (case-insensitive)
```

**Step 3 — Search by name in frontmatter:**
```
Grep: pattern="name:.*<term>" or pattern="title:.*<term>"
      in the same directories (case-insensitive)
```

**Step 4 — Search by content (fallback):**
If steps 1-3 did not return sufficient results:
```
Grep: pattern="<term>" in entity directories (case-insensitive)
```

### 2.3 Filter by domain

If domains were identified in Phase 1, filter results:
```
Grep: pattern="domain/<domain>" in the found files (tags field of frontmatter)
```

Keep all results, but prioritize those matching the domain.

### 2.4 Read found entities

For each entity found (limit: 15 entities):

1. Read the frontmatter first (~first 30 lines) to confirm relevance
2. If relevant: read the full file
3. If not relevant (false positive from Grep): discard

Record for each entity read:
- filename, type, name
- wikilinks found in frontmatter and body
- external URLs found in the content (Confluence, Google Docs, GitHub)
- Explicit date in the filename (if any)

---

## Phase 2.5 — Vault-Specific Post-Processing

This phase applies to both graphify delegation results (Phase 2-G) and sequential search results (Phase 2-S).
When coming from Phase 2-G, consume `graphify_result`. When coming from Phase 2-S, consume the entity list
found via Glob/Grep. In both cases, the output is a list of resolved vault `.md` entities for Phase 3.

### 2.5.1 Resolve graphify nodes to vault .md files (only when coming from Phase 2-G)

For each node in `graphify_result.nodes`:

1. Extract `id` and `label` from the node
2. Resolve to a .md file in the vault:
   - **Nodes with `source_file` pointing to actors:** search for code entity in `actors/*/nodes/` via node `id` in frontmatter, or search for the parent actor in `actors/`
   - **Nodes with label matching an entity filename:** Glob for `actors/<label>*.md`, `topics/*<label>*.md`, etc.
   - **If not resolved:** record as "node without corresponding .md" — will be mentioned in the response
3. Read the resolved .md files (frontmatter + body) — limit: 15 entities total

### 2.5.2 Supplement with people/teams

Graphify does not index people and teams directly (they are vault entities, not code entities).
For questions involving people/teams:

1. Use Glob/Grep to search in `people/` and `teams/` for the search terms from Phase 1
2. Add results to those already obtained from graphify (or from sequential search)
3. Respect the total limit of 15 entities

### 2.5.3 Community exploration for broad questions (only when coming from Phase 2-G)

When the question is broad and does not mention specific entities (e.g.: "tell me about the payments domain",
"what's happening with notifications?", "overview of processing"):

1. Use `graphify_result.communities` from the graphify response — do NOT load graph.json directly
2. Identify the community whose label matches the domain or theme of the question
3. For the relevant community: resolve `node_ids` to vault .md files
4. Prioritize nodes that appear in more edges in `graphify_result.edges` (higher connectivity)
5. If `communities` data is missing or empty in the graphify response: skip this step and rely on node-level results from 2.5.1
6. Limit: 10 nodes per community exploration

---

## Phase 3 — Cross-reference Context via Wikilinks

> **Note:** When graphify delegation was used (Phase 2-G), the graphify response already returns
> connected nodes via edges. The wikilink cross-referencing in this phase is **complementary** —
> used mainly for entities that are not in the graph (people, teams, sources, fleeting). If the
> Phase 2.5 results already cover the question with 15 entities, this phase can be reduced or skipped.

### 3.1 Extract wikilinks from found entities

For each entity read in Phase 2, extract all wikilinks (`[[...]]`) from:
- Frontmatter: fields such as `team`, `members`, `actors`, `people`, `focal_points`,
  `related_topics`, `related_actors`, `related_teams`, `related_people`, `related_projects`
- Body: inline wikilinks in the text

### 3.2 Follow wikilinks (1 level of depth)

For each extracted wikilink that is relevant to the question:

1. Resolve the file: search for `<wikilink-name>.md` in entity directories
   ```
   Glob: actors/<name>.md, people/<name>.md, teams/<name>.md,
         topics/*<name>*.md, discussions/*<name>*.md, projects/<name>.md
   ```

2. Read the found file (frontmatter + body)

3. **Do NOT follow wikilinks from this second level** — stop here to avoid context explosion

**Relevance criteria for following a wikilink:**
- The question is about relationships ("who owns", "what depends on") → follow all
- The question is about status/overview → follow team, people (focal points)
- The question is about history → follow related discussions, topics
- The question is about architecture → follow dependent actors

**Limit:** Do not read more than 15 entities total (Phase 2 + Phase 3 combined).
If the limit is reached, prioritize entities directly mentioned in the question.

---

## Phase 4 — Prioritize by Recency

### 4.1 Identify entities with explicit dates

For discussions and topics, extract the date from the filename:
- Pattern `YYYY-MM-DD-slug.md` → full date (e.g.: `2026-04-02`)
- Pattern `YYYY-MM-slug.md` → partial date, assume day 01 (e.g.: `2026-04-01`)

For consolidated entities (actors, people, teams, projects, sources):
- Treat as equally up-to-date — do not apply temporal ranking
- Trust that content is up-to-date via `/bedrock:preserve` and `/bedrock:compress`

### 4.2 Sort by recency

When the response involves multiple dated discussions or topics:
- Sort by date descending (most recent first)
- If the question is explicitly about something recent ("what happened lately",
  "latest decisions"), limit to entities from the last 30 days
- If the question is about history ("what happened with X over time"),
  include all dates but present chronologically (most recent first)

---

## Phase 5 — External Fetch (When Necessary)

### 5.1 Assess necessity

External fetch is only necessary when:
1. Local information is insufficient to answer the question, AND
2. The consulted entities contain relevant external URLs

If local information is sufficient: **skip this phase entirely**.

### 5.2 Identify external URLs

In the entities read (Phases 2 and 3), look for URLs:
- Confluence: URLs containing `confluence` or `atlassian.net`
- Google Docs: URLs containing `docs.google.com`
- GitHub: URLs containing `github.com` (repositories, issues, PRs)

### 5.3 Delegate reading to corresponding skill

For each relevant URL (limit: 3 external URLs per query):

| URL contains | Action |
|---|---|
| `confluence` or `atlassian.net` | Invoke skill `/confluence-to-markdown` passing the URL |
| `docs.google.com` | Invoke skill `/gdoc-to-markdown` passing the URL |
| `github.com` with file path | Use `mcp__plugin_github_github__get_file_contents` with owner, repo, and path extracted from the URL |
| `github.com` without path (repo root) | Use `mcp__plugin_github_github__get_file_contents` to read README.md + `mcp__plugin_github_github__list_commits` for the last 5 commits |

**External fetch rules:**
- **Best-effort:** If the skill or MCP fails, continue with local information. Never block the response.
- **1 level only:** Do not follow links found within the external document.
- **Limit of 3 URLs:** If there are more than 3 relevant URLs, prioritize those that seem most directly related to the question.

### 5.4 Integrate external content

Incorporate the obtained content into the response context. Clearly mark the origin:
- "(source: Confluence — <page title>)"
- "(source: Google Docs — <doc title>)"
- "(source: GitHub — <owner/repo>)"

---

## Phase 6 — Respond to the User

### 6.1 Compose the response

Build the response following these rules:

1. **Language:** Use the vault's configured language. Technical terms in English are accepted (PCI DSS, API, EKS, etc.)

2. **Response structure:**
   - Open with a direct answer to the question (1-3 sentences)
   - If necessary, expand with details organized by topic
   - Use headers (`##`, `###`) if the response is long (>5 paragraphs)
   - Use tables when the information is comparative or inventory-like

3. **Entity citations:**
   - Cite ALL consulted entities as wikilinks: `[[entity-name]]`
   - Use bare wikilinks (never `[[dir/entity-name]]`)
   - Group citations at the end if there are many, or inline when natural

4. **External source indication:**
   - If external fetch was used, clearly indicate: "I also consulted [external source]."
   - Include original URL for user reference

5. **When nothing is found:**
   - State explicitly: "I didn't find information about [X] in the vault."
   - If relevant, suggest: "You can use `/bedrock:teach <URL>` to ingest a source about this topic."
   - **NEVER fabricate information.** Only respond with what was found.

6. **Response prioritization (Zettelkasten hierarchy):**
   When composing the response, apply weight by Zettelkasten role:
   - **Permanent notes** (actors, people, teams) — maximum weight, consolidated information. Present as current facts.
   - **Bridge notes** (topics, discussions) — high weight, contextualized information. Most recent discussions/topics first.
   - **Index notes** (projects) — medium weight, organizational reference. Point to where the detail is.
   - **Literature notes** (sources) — medium weight, traceability metadata.
   - **Fleeting notes** — low weight, unconsolidated information. **ALWAYS** flag with disclaimer:
     `(source: fleeting note — unconsolidated information)`
   - If there is conflicting information between sources, point out the discrepancy.

7. **Fleeting note promotion detection (criterion 3: active relevance):**
   When a fleeting note is referenced in the response because it is relevant to the query:
   - Check if it meets promotion criteria (see `<base_dir>/../../entities/fleeting.md`):
     - Critical mass (>3 paragraphs with sources)
     - Corroboration (confirmed by an existing permanent)
   - If any criterion is met, add at the end of the response:
     `> [!info] Promotion suggested: [[fleeting-note-name]] can be promoted to permanent/bridge`
   - `/bedrock:query` does NOT promote automatically — it only flags. Promotion happens when
     `/bedrock:preserve` is invoked with the instruction to promote.

### 6.2 Post-response suggestions

When appropriate, suggest actions to the user:

- If information is outdated: "The vault may be outdated about [X]. Consider running `/bedrock:teach <source>` to update."
- If the question revealed gaps: "I didn't find [Y] in the vault. If you have this information, you can use `/bedrock:preserve` to record it."
- If the question is complex and the response incomplete: "For a more complete view, you may also consult [external URL found but not fetched]."

---

## Critical Rules

| Rule | Detail |
|---|---|
| Read-only | NEVER write, edit, or delete files. Only Read, Glob, Grep, Skill (graphify delegation + external fetch), Agent (parallel search), and GitHub MCP (reading) |
| Invoke graphify via Skill tool | NEVER call graphify Python API directly (`graphify.query`, `graphify.build`, etc.). Always invoke via the Skill tool. This follows the same delegation pattern as `/bedrock:teach` → `/graphify`. |
| Graphify fallback to sequential | If graphify delegation fails (parse error, timeout, no graph.json), fall back to Phase 2-S. Never block the query. |
| No fabrication | Respond ONLY with information found in the vault or consulted external sources. Never fabricate data |
| Clarification before guessing | If the question is ambiguous, ask for clarification. Do not assume |
| Limit of 15 entities | Do not read more than 15 entities per query (Phase 2.5 + Phase 3) |
| Limit of 3 external URLs | Do not fetch more than 3 external sources per query |
| 1 level of wikilinks | Do not follow wikilinks beyond the first level |
| 1 level of external links | Do not follow links within external documents |
| Best-effort for fetch | If external fetch fails, respond with local info |
| Vault language with technical terms in English | Response always in the vault's configured language |
| Bare wikilinks | `[[name]]`, never `[[dir/name]]` |
| Consolidated entities = up-to-date | Actors, people, teams do not need temporal ranking |
| Dated discussions/topics = prioritize recent | Sort by date in filename (YYYY-MM-DD) |
| Sensitive data | NEVER display credentials, tokens, PANs, CVVs found in the vault |
| Fleeting notes with disclaimer | ALWAYS flag information from fleeting notes with `(source: fleeting note — unconsolidated information)` |
| Promotion as side-effect | When a relevant fleeting note meets promotion criteria, flag with callout. Do NOT promote automatically |
| Weight hierarchy | permanent > bridge > index/literature > fleeting. Use as guideline, not mathematical formula |
