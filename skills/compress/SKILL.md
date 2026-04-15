---
name: compress
description: >
  Scans the vault, identifies duplicated or fragmented content between entities of the same type,
  builds a unification proposal in table format, and executes after user confirmation.
  Generates a health report (unresolved wikilinks, orphan entities, stale entities).
  Use when: "bedrock compress", "bedrock-compress", "clean vault", "consolidate vault", "unify entities",
  "find duplications", "/bedrock:compress".
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

# /bedrock:compress — Vault Consolidation and Health Check

## Plugin Paths

Entity definitions and templates are in the plugin directory, not the vault root.
Use the "Base directory for this skill" provided at invocation to resolve paths:

- Entity definitions: `<base_dir>/../../entities/`
- Templates: `<base_dir>/../../templates/{type}/_template.md`
- Plugin CLAUDE.md: `<base_dir>/../../CLAUDE.md` (already injected automatically into context)

Where `<base_dir>` is the path provided in "Base directory for this skill".

---

## Overview

This skill scans all entities in the vault, detects semantically duplicated
or fragmented content WITHIN the same entity type, proposes unification to the user, and executes
after explicit confirmation. It also generates a vault health report.

**You are an execution agent.** Follow the phases below in order, without skipping steps.

**Critical rules:**
- **NEVER** execute changes without explicit user confirmation
- **NEVER** compare entities of different types (actor vs topic, etc.)
- **NEVER** delete entities — only consolidate content
- **NEVER** modify frontmatter (except `updated_at` and `updated_by`)
- **NEVER** modify templates (`_template.md`), conventions, or patterns
- **NEVER** remove existing wikilinks
- People/Teams/Topics: **append-only** — add consolidation note, never delete content
- Actors: **free merge** — may edit body freely

---

## Phase 0 — Sync the Vault

Execute:
```bash
git pull --rebase origin main
```

If it fails:
- No remote: warn "No remote configured. Working locally." and proceed.
- Conflict: `git rebase --abort` and warn the user. Do NOT proceed without resolving.

---

## Phase 1 — Scan the Vault

For each entity type (`actors`, `people`, `teams`, `topics`, `discussions`, `projects`, `fleeting`):

1. List all `.md` files in the directory, **excluding `_template.md` and `_template_node.md`**
   - For actors: include both `actors/*.md` (flat) and `actors/*/*.md` (folder)
   - Include code entities: `actors/*/nodes/*.md`
2. For each entity, read frontmatter + body
3. For code entities: additionally extract `graphify_node_id` and `actor` from frontmatter
4. Extract **claims** — distinct factual assertions:
   - Each bullet point, table row, or paragraph is a potential claim
   - **Ignore** empty structural sections (template placeholders)
   - **Ignore** "Expected Bidirectional Links" section (reference, not content)
   - **Ignore** "Recent Activity" section (temporal, not factual)
   - **Ignore** standard mandatory callouts (`[!warning] Deprecated`, `[!danger] PCI Scope`, etc.)

**Output:** map `type → [{entity, claims[]}]`

### Optimization for large vaults

If the vault has more than 100 entities in a type, process in batches of 30.
Use subagents via Agent tool to parallelize reading by entity type.

---

## Phase 1.5 — Graph Integrity (graphify)

If `graphify-out/graph.json` exists, verify consistency between the graph and the vault.
If it does NOT exist: skip this phase and report "Graph.json not found. Run /bedrock:teach to generate." in the health report.

### 1.5.1 Load data

```bash
$(cat graphify-out/.graphify_python 2>/dev/null || echo python3) -c "
import json
from pathlib import Path
g = json.loads(Path('graphify-out/graph.json').read_text())
nodes = g.get('nodes', [])
code_nodes = [n for n in nodes if n.get('file_type') == 'code']
print(f'{len(nodes)} total nodes, {len(code_nodes)} code nodes')
"
```

Collect:
- `graph_nodes`: all nodes from graph.json with `file_type: code` and their `id`
- `vault_code_entities`: all code entities in `actors/*/nodes/*.md` with their `graphify_node_id`
- `vault_actors`: list of actors (folders in `actors/` that contain `<name>.md`)

### 1.5.2 Check A — Orphan code entities (actor removed)

For each code entity found in Phase 1:
1. Extract `actor` from frontmatter (wikilink to the parent actor)
2. Resolve the actor: verify if `actors/<actor-name>/<actor-name>.md` exists
3. If it does NOT exist: mark as **orphan (actor removed)**

### 1.5.3 Check B — Orphan code entities (node removed from graph)

For each code entity with `graphify_node_id` defined:
1. Verify if the `graphify_node_id` exists in `graph_nodes` (IDs from graph.json)
2. If it does NOT exist: mark as **orphan (node removed from graph)** — the code was probably
   deleted from the repository and /bedrock:teach reprocessed without generating this node

### 1.5.4 Check C — Graph nodes not persisted

For each node in `graph_nodes` (nodes with `file_type: code` in graph.json):
1. Verify if a code entity exists in `vault_code_entities` with the corresponding `graphify_node_id`
2. If it does NOT exist: register as **node not persisted** — /bedrock:teach extracted this node but
   /bedrock:preserve did not write it to the vault (may indicate that /bedrock:teach did not complete the preservation phase)

### 1.5.5 Check D — graph.json stale

1. Check the modification date of `graphify-out/graph.json`
```bash
stat -f "%Sm" -t "%Y-%m-%d" graphify-out/graph.json 2>/dev/null || stat -c "%y" graphify-out/graph.json 2>/dev/null | cut -d' ' -f1
```
2. If the date is older than 30 days: mark as **stale**
3. Suggest: "Graph.json is outdated (>30 days). Run /bedrock:teach or /sync to update."

### 1.5.6 Result

Store counters for the health report:
- `graph_exists`: yes/no
- `graph_total_nodes`: N
- `vault_code_entities_count`: M
- `nodes_synced`: nodes present in both the graph and the vault
- `orphan_actor_removed`: code entities whose actor does not exist
- `orphan_node_removed`: code entities whose graphify_node_id is not in the graph
- `nodes_not_persisted`: graph nodes without a corresponding code entity
- `graph_updated_at`: modification date of graph.json
- `graph_stale`: yes/no

---

## Phase 2 — Detect Duplication

For each entity type, compare claims **WITHIN the same type** (NEVER cross-type).

**Code entities:** compare WITHIN the same actor (code entities from different actors are not
compared with each other, as they may represent legitimately similar functions in distinct repos).
Two code entities from the same actor with semantically identical descriptions → cluster.

### 2.1 Semantic duplication
Two claims that say the same thing with different words.
Example:
- Actor A: "Card payments API"
- Actor B: "Service that processes credit card payments"

### 2.2 Fragmentation
Information about the same subject scattered across 3+ entities without consolidation.
Example:
- Actor A mentions "uses Kafka for events"
- Actor B mentions "publishes events to Kafka"
- Actor C mentions "consumes Kafka events from B"
- No entity consolidates the complete flow

### 2.3 Generate clusters

For each duplication found, create a cluster:

```yaml
cluster:
  id: N
  type: actor | person | team | topic | discussion | project
  description: "description of the duplicated content"
  entities:
    - name: "entity-a"
      claim: "text of the duplicated claim"
    - name: "entity-b"
      claim: "text of the duplicated claim"
  primary_entity: "entity-a"  # the most complete/relevant
  unified_content: "consolidated text"
```

**Criteria for choosing the primary entity:**
- Most complete (more claims, more details)
- Most recent (most recent `updated_at`)
- Most connected (more inbound/outbound wikilinks)

If no duplication is found, inform the user and skip to the Health Report (Phase 4.2).

---

## Phase 3 — Build Proposal

For each cluster, present to the user:

```markdown
### Cluster N: <description of the duplicated content>

**Type:** <entity type>

**Entities involved:**
| Entity | Claim |
|---|---|
| [[entity-a]] | "description X of the service" |
| [[entity-b]] | "service does X" |

**Proposal:**
- **Keep in:** [[entity-a]] (most complete/relevant entity)
- **Unified content:** "consolidated description..."
- **Remove from / Consolidate in:** [[entity-b]]

**Impact:** N entities, M claims
```

### Proposal summary

After listing all clusters:

```markdown
## Summary

| # | Description | Type | Entities | Claims |
|---|---|---|---|---|
| 1 | ... | actor | 2 | 3 |
| 2 | ... | topic | 3 | 5 |

**Total:** N clusters, M entities, P claims

Confirm execution? (yes/no)
```

### Graph orphan cleanup proposal (if Phase 1.5 found orphans)

If Phase 1.5 identified orphan code entities or unpersisted nodes, present an additional proposal:

```markdown
## Graph Orphans

### Orphan code entities (actor removed)
| # | Code entity | Actor (removed) | Proposed action |
|---|---|---|---|
| 1 | [[node-name]] | [[actor-name]] | `git rm actors/<actor>/nodes/<node>.md` |

### Orphan code entities (node removed from graph)
| # | Code entity | graphify_node_id | Proposed action |
|---|---|---|---|
| 1 | [[node-name]] | `id_in_graph` | `git rm actors/<actor>/nodes/<node>.md` |

### Graph nodes not persisted
| # | Node ID | Label | Proposed action |
|---|---|---|---|
| 1 | `node_id` | Node Label | Run `/bedrock:teach` on the corresponding actor |

Confirm orphan cleanup? (yes/no/partial)
```

**IMPORTANT:** Orphan cleanup is SEPARATE from duplicate consolidation.
The user can confirm one without the other. Allow partial confirmation by actor
(e.g., "clean orphans only from billing-api").

**STOP HERE and wait for user confirmation.**

If the user says "no" or asks for adjustments, adjust the proposal and re-present.
If the user partially confirms (e.g., "only clusters 1 and 3"), execute only the confirmed ones.

---

## Phase 4 — Execute

### 4.1 Consolidate entities

For each cluster confirmed by the user:

#### Actors (free merge)
1. Read the primary entity (`entity-a`)
2. Incorporate the unified content into the body of the primary entity
3. Read the secondary entity (`entity-b`)
4. Remove the duplicated claim from the body of the secondary entity
5. Update frontmatter of both:
   ```yaml
   updated_at: <today's date YYYY-MM-DD>
   updated_by: "compress@agent"
   ```

#### People / Teams / Topics (append-only)
1. Read the primary entity (`entity-a`)
2. Add the unified content as a new section or supplement in the body
3. Read the secondary entity (`entity-b`)
4. **Do NOT delete** the original content. Add a callout after the duplicated claim:
   ```markdown
   > [!info] Content consolidated in [[entity-a]]
   > This content has been consolidated in the primary entity. See [[entity-a]] for the most complete version.
   ```
5. Update frontmatter of both:
   ```yaml
   updated_at: <today's date YYYY-MM-DD>
   updated_by: "compress@agent"
   ```

#### Discussions / Projects (append-only)
Follow the same rule as People/Teams/Topics: append-only with consolidation callout.

#### Orphan code entities (if confirmed by the user)

For each confirmed orphan code entity (actor removed or node removed from graph):
1. Execute `git rm actors/<actor>/nodes/<node-name>.md`
2. If the folder `actors/<actor>/nodes/` becomes empty: keep it (do not delete empty folder)
3. Remove the code entity reference from the "Knowledge Nodes" section of the parent actor (if actor exists)
4. Update `updated_at` and `updated_by` of the parent actor (if touched)

**IMPORTANT:** Code entities are the only entity that can be deleted via `git rm`.
All other entities follow the consolidation rule (never delete).
The graph.json is NOT modified — if nodes need to be removed from the graph, run /bedrock:teach with `--update`.

### 4.2 Generate Health Report

Leverage the full vault scan to generate:

#### Unresolved wikilinks
- Scan all entity files
- Extract all wikilinks `[[name]]`
- Check if a corresponding file exists in any entity directory
- List those that do not resolve

#### Orphan entities
- Entities with no inbound wikilinks (no other entity points to them)
- Check via Grep across all entity files

#### Stale entities
- Entities with `updated_at` older than 60 days from the current date
- Extract `updated_at` from the frontmatter of each entity

#### Stagnant fleeting notes
- Fleeting notes with `raw` status for more than 30 days (based on `captured_at`)
- For each stagnant fleeting note, check if it meets promotion criteria (see `entities/fleeting.md`):
  - **Critical mass:** >3 paragraphs with verifiable sources → suggest promotion
  - **Corroboration:** information confirmed by an existing permanent → suggest promotion
  - If no criteria met → suggest archiving (`status: archived`)
- Include in the health report with suggested actions:
  ```
  | Fleeting Note | Days in raw | Suggested action |
  |---|---|---|
  | [[2026-03-05-novo-servico]] | 35 | Promote (critical mass) |
  | [[2026-03-01-ideia-vaga]] | 39 | Archive (no promotion criteria met) |
  ```

#### Graph Integrity (if graphify-out/graph.json exists)

Using the data collected in Phase 1.5, generate the integrity section:

```markdown
## Graph Integrity

| Metric | Value |
|---|---|
| Graph.json exists | yes/no |
| Nodes in graph.json | N |
| Code entities in vault | M |
| Synced nodes (graph <-> vault) | X |
| Orphan code entities (actor removed) | Y |
| Orphan code entities (node removed from graph) | Z |
| Graph nodes not persisted | W |
| Graph.json updated at | YYYY-MM-DD |
| Graph.json stale (>30d) | yes/no |
```

If graph.json does not exist: report only "Graph.json not found. Run /bedrock:teach to generate."
If graph.json exists but there are no orphans: report all counters with zeros.
If graph.json is stale: add warning "Suggestion: run /bedrock:teach or /sync to update the graph."

**Filter:** Report only actionable findings. Ignore:
- Wikilinks to entities that are valid references but not yet created (acceptable in Obsidian)
- Templates and configuration files

---

## Phase 5 — Git Commit + Report

### 5.1 Stage

```bash
git add actors/ people/ teams/ topics/ discussions/ projects/ fleeting/

# Check if there is anything to commit
git diff --cached --quiet && echo "Nothing to commit" && exit 0
```

### 5.2 Read git strategy

Read the vault's git strategy from `.bedrock/config.json`:

```bash
cat .bedrock/config.json 2>/dev/null
```

Extract the `git.strategy` field. If the file does not exist or has no `git` key, default to `"commit-push"`.

Valid values: `"commit-push"`, `"commit-push-pr"`, `"commit-only"`.

Prepare the commit message following the convention:
```
vault: compress N entities [source: compress]
```
If orphan code entities were removed, use:
```
vault: compress N entities, remove M orphan code entities [source: compress]
```

Where N = total number of entities touched.

### 5.3 Dispatch by strategy

**Strategy: `commit-push`** (default)

```bash
git commit -m "<message per convention>"
git push origin main
```

If push fails (conflict):
```bash
git pull --rebase origin main
git push origin main
```

If it fails 2x: STOP and inform the user.
If there is no remote: commit locally and warn.

---

**Strategy: `commit-push-pr`**

First, check that `gh` is available:

```bash
which gh 2>/dev/null
```

If `gh` is not found: warn the user and **fall back to `commit-push`** strategy (above).

If `gh` is available:

1. **Create a branch.** Derive the branch name from the commit message:

   `vault/<YYYY-MM-DD>-compress-<N>-entities` (e.g., `vault/2026-04-15-compress-25-entities`)

   Check for collisions:
   ```bash
   git branch --list "vault/<YYYY-MM-DD>-compress*"
   ```
   If the branch already exists, append a counter: `vault/2026-04-15-compress-25-entities-2`.

   ```bash
   git checkout -b <branch-name>
   ```

2. **Commit and push the branch:**
   ```bash
   git commit -m "<message per convention>"
   git push origin <branch-name>
   ```

3. **Open a pull request:**
   ```bash
   gh pr create --title "<commit message>" --body "Automated by /bedrock:compress" --base main
   ```

4. **Return to main:**
   ```bash
   git checkout main
   ```

---

**Strategy: `commit-only`**

```bash
git commit -m "<message per convention>"
```

Do not push. Output:
```
Git strategy: commit-only — changes committed locally. Use `git push` manually when ready.
```

### 5.4 Final Report

Present to the user:

```markdown
## /bedrock:compress — Report

### Processed clusters
| # | Description | Type | Entities | Unified claims |
|---|---|---|---|---|
| 1 | ... | actor | 2 | 3 |
| 2 | ... | topic | 3 | 5 |

**Total:** N clusters, M entities, P unified claims

### Health Report
| Check | Count | Details |
|---|---|---|
| Unresolved wikilinks | N | [[link1]], [[link2]], ... |
| Orphan entities | N | [[entity1]], [[entity2]], ... |
| Stale entities (>60d) | N | [[entity3]], [[entity4]], ... |

### Git
- Commit: `vault: compress N entities [source: compress]`
- Push: success / failed (reason)
```

If no clusters were processed (no duplication found or user refused all),
present only the Health Report.

---

## Error Handling

| Situation | Action |
|---|---|
| Empty vault (no entities) | Report "No entities found in the vault." and end |
| No duplication found | Report and skip to Health Report |
| User refuses all clusters | Report and skip to Health Report |
| Error reading entity | Skip entity, warn in the report |
| Conflict on git push | Rebase + retry (max 2). If it fails: warn the user |
| Entity without frontmatter | Skip entity, warn in the report |
