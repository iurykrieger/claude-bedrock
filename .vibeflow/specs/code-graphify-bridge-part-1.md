# Spec: code-graphify-bridge — Part 1 (Foundation)

> Generated via /vibeflow:gen-spec on 2026-05-04
> Source PRD: `.vibeflow/prds/code-graphify-bridge.md`

## Objective

Physically materialize the `_template_node.md` template, update the `code` entity schema to support grouping (`graphify_node_ids` array) and back-pointer (`vault_entity_path`), and make `/bedrock:setup` install the template in the vault.

## Context

`entities/code.md:3` and `skills/preserve/SKILL.md:635` reference `actors/_template_node.md` as source of truth, but the file was never created. `/bedrock:setup` does not copy it. The first `/teach` against a fresh vault breaks when it tries to create a `code` entity.

In parallel, the current schema has `graphify_node_id: string` (singular). The PRD's solution requires grouping semantically similar nodes into a single `code` entity (Part 2), which demands an array. And the reverse back-pointer (`vault_entity_path` on the `graph.json` node, written by Phase 6.5 — Part 3) needs to be documented in `entities/code.md` before being implemented.

This part is foundation: it creates schema/template artifacts without changing runtime behavior. Parts 2 and 3 depend on it.

## Definition of Done

1. `templates/actors/_template_node.md` exists, contains every frontmatter field listed in `entities/code.md` ("Required fields"), includes inline comments for valid values, the `<!-- Zettelkasten role: permanent note extension -->` comment, the linking rules comment, and an "Expected Bidirectional Links" table.
2. `entities/code.md` replaces `graphify_node_id` (string) with `graphify_node_ids` (array of strings) in the "Required fields" table, with explanation that multiple ids represent graphify nodes grouped by semantic similarity.
3. `entities/code.md` documents in a new subsection (under "Required fields" or in a new "Graph Bridge" block) the optional `vault_entity_path` field on the `graph.json` node schema, with concrete example and a note that the write owner is `/bedrock:preserve` Phase 6.5 (referenced as TODO until Part 3 lands).
4. `skills/setup/SKILL.md` copies `templates/actors/_template_node.md` into `<VAULT_PATH>/actors/_template_node.md` during the vault template installation phase, alongside the other `_template.md` files.
5. Backward compat: `entities/code.md` carries an explicit note that legacy vaults with singular `graphify_node_id` remain valid for read — `/preserve` (Part 2) accepts both and always writes the array.
6. **Quality gate:** `_template_node.md` rigorously follows `patterns/template-structure.md` (frontmatter with inline comments, Zettelkasten role comment, linking rules comment, Expected Bidirectional Links table); `entities/code.md` follows `patterns/entity-definition.md` (fixed structure with What / When / Distinguish / Required fields / Zettelkasten Role / Examples).

## Scope

- Create `templates/actors/_template_node.md` with full frontmatter and body structure.
- Update `entities/code.md`:
  - Rename `graphify_node_id` → `graphify_node_ids` (array) in the table.
  - Add a section documenting `vault_entity_path` on the `graph.json` node.
  - Add a backward compat note for the legacy singular field.
- Update `skills/setup/SKILL.md` to copy the new template during vault provisioning.

## Anti-scope

- **DO NOT** rewrite `/preserve` Phase 1.3 (Part 2).
- **DO NOT** implement `/preserve` Phase 6.5 (Part 3).
- **DO NOT** update `/teach` to pass `actor_context` (Part 2).
- **DO NOT** migrate existing vaults with singular `graphify_node_id` — migration happens in-line as Parts 2 and 3 are exercised.
- **DO NOT** introduce runtime validation of the new schema (defer to `/healthcheck` in a future iteration).
- **DO NOT** change templates of other entities (`actor`, `person`, etc.).

## Technical Decisions

### 1. `graphify_node_ids` (array) vs canonical + aliases

**Decision:** plain array (`graphify_node_ids: ["id1", "id2", ...]`).
**Trade-off:** the alternative would be `graphify_node_id: "canonical"` + `graphify_node_aliases: [...]` to preserve "canonical vs variants" intent. Rejected because (a) graphify nodes grouped by semantic similarity have no natural hierarchy — which ID is "the canonical"?, (b) array is simpler to operate on (set operations: union, contains), (c) the `code` entity's `id` (kebab-case filename) is already the canonical vault identity — the array just records which graph ids point to it.

### 2. `vault_entity_path` documented in `entities/code.md`, not in a new entity

**Decision:** document the field in a new "Graph Bridge" subsection of `entities/code.md`, without creating `entities/graph-node-schema.md`.
**Trade-off:** a dedicated entity would be more reusable if other entity types later got back-pointers (concept, topic). Rejected for v0 because only `code` participates in the explicit bidirectional bridge; documenting it on the single consumer is more cohesive. Migrate to a dedicated entity if 2+ types adopt the pattern.

### 3. Template lives in the plugin, copied at setup

**Decision:** `_template_node.md` lives in the plugin (`templates/actors/`) and is copied to `<VAULT_PATH>/actors/_template_node.md` during `/bedrock:setup`.
**Trade-off:** the alternative would be to keep the template only in the plugin and have `/preserve` read from there via `<base_dir>`. Rejected because the other templates are already copied to the vault (`<VAULT_PATH>/<type>/_template.md`) — keep consistency with the rest of the project. Also lets users customize per vault.

### 4. Backward compat without proactive migration

**Decision:** `/preserve` (Part 2) reads `graphify_node_id` (singular) AND `graphify_node_ids` (array); always writes the array. Legacy vaults migrate in-line as entities are touched.
**Trade-off:** the alternative would be a one-shot command `/bedrock:compress --rebuild`. Rejected for v0 — touch-by-touch is safer, no risk of mass migration. The one-shot stays for v0.2 per the PRD.

## Applicable Patterns

- **`patterns/template-structure.md`** (mandatory): the new `_template_node.md` follows it strictly — frontmatter with inline comments, Zettelkasten role, linking rules comment, Expected Bidirectional Links table.
- **`patterns/entity-definition.md`** (mandatory): the update to `entities/code.md` keeps the fixed section structure.
- **`patterns/skill-architecture.md`** (advisory): the change to `skills/setup/SKILL.md` inserts a copy step inside an existing phase — does not create a new phase nor break numbering.

## Risks

| Risk | Mitigation |
|---|---|
| `_template_node.md` diverges from `entities/code.md` on schema | DoD #6 explicitly cross-references the two; manual review before commit. |
| Setup breaks trying to copy a non-existent template | Create the template BEFORE updating setup (order matters within the Part). |
| Legacy vault with singular `graphify_node_id` fails in `/healthcheck` | DoD #5 requires an explicit backward compat note in `entities/code.md`. `/healthcheck` does not strictly validate schema in v0 (out of scope). |
| `vault_entity_path` documented but not implemented leaves an expectation gap | Mark the subsection as "Owned by /preserve Phase 6.5 (Part 3)" so the status is explicit. |

## Dependencies

None — this is the foundation.

