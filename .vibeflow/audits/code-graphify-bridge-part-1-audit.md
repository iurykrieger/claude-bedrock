# Audit Report: code-graphify-bridge — Part 1 (Foundation)

**Verdict: PASS**

> Audited: 2026-05-04
> Spec: `.vibeflow/specs/code-graphify-bridge-part-1.md`
> Files in scope: `templates/actors/_template_node.md` (NEW), `entities/code.md` (MOD), `skills/setup/SKILL.md` (MOD)

## DoD Checklist

- [x] **1. `_template_node.md` exists with full frontmatter, comments, and bidirectional links table** — `templates/actors/_template_node.md:1-66` exists. Frontmatter (`---` block at lines 1-17) carries every "Required fields" entry from `entities/code.md`: `type` (line 2), `name` (3), `aliases` (4), `actor` (5), `node_type` (6), `source_file` (7), `description` (9), `graphify_node_ids` (10), `confidence` (11), `updated_at` (14), `updated_by` (15), `tags` (16). Optional `source_location` (8), `relations` (12), and `sources` (13) also present. Inline comments enumerate valid values for `aliases`, `actor`, `node_type`, `source_file`, `source_location`, `graphify_node_ids`, `confidence`, `relations`, `sources`, and `tags` extension dimensions. Zettelkasten role comment at line 19; linking rules comment at line 20. "Expected Bidirectional Links" table at lines 49-58 with the 4 expected directions (Code→Actor, Actor→Code, Code→Code, Topic→Code) marked as removable on real pages (line 51).
- [x] **2. `graphify_node_id` (string) → `graphify_node_ids` (array<string>)** — `entities/code.md:47` carries the new field with type `array<string>`, concrete example `["billing_api_processTransaction", "billing_api_processTransactionV2"]`, and an explicit explanation that multiple ids represent graphify nodes grouped by semantic similarity (`semantically_similar_to` edges or community co-membership). The "Always at least one id." invariant is stated. Cross-references at `entities/code.md:32` (How to distinguish table) and `entities/code.md:98` (Completeness Criteria) were updated to use the new field name for internal consistency.
- [x] **3. `vault_entity_path` documented with example and TODO marker** — `entities/code.md:64-83` introduces a new top-level "## Graph Bridge" section. Documents both directions of the bridge (Vault → graph and Graph → vault). Includes a concrete JSON node example (lines 71-79) showing `vault_entity_path: "actors/billing-api/nodes/process-transaction.md"` alongside the existing graphify fields (`id`, `label`, `file_type`, `source_file`). Owner stated explicitly at line 81: "The owner of the `vault_entity_path` write is `/bedrock:preserve` Phase 6.5." TODO callout at line 83 references "Part 3 of the `code-graphify-bridge` spec" so the gap is visible until Part 3 lands.
- [x] **4. `skills/setup/SKILL.md` copies `_template_node.md` to the vault** — `skills/setup/SKILL.md:553` adds the row `templates/actors/_template_node.md → actors/_template_node.md` to the §3.2 "Copy Templates" table. The existing template-loop logic (lines 561-563: "For each template: 1. Use Read..., 2. Use Write...") iterates this table, so the new row is processed automatically. Final report table in §6 (`skills/setup/SKILL.md:1234`) lists `actors/_template_node.md` under "Files Created", so the user sees the file in the post-setup summary.
- [x] **5. Backward compatibility note for legacy singular field** — `entities/code.md:60-62` adds the `### Backward compatibility` subsection: "Legacy vaults may still carry the singular `graphify_node_id: \"<id>\"` (string) instead of the new `graphify_node_ids: [...]` (array). Both forms are valid for read — `/bedrock:preserve` accepts either at parse time and always writes the array form when the entity is touched. Migration is in-line: a singular field is upgraded to an array on the first update; there is no batch migration." Sets the contract that Part 2 will implement.
- [x] **6. Quality gate (pattern compliance)** — see "Pattern Compliance" section below. Both `_template_node.md` and `entities/code.md` follow their respective patterns. One authorized deviation in `entities/code.md` (new `## Graph Bridge` top-level section) is explicitly permitted by spec DoD #3.

## Pattern Compliance

- [x] **`patterns/template-structure.md`** — `templates/actors/_template_node.md` follows it strictly. Evidence:
  - YAML frontmatter between `---` delimiters ✓ (lines 1, 17)
  - Type-specific required fields with placeholder values (`""`, `[]`, `YYYY-MM-DD`) ✓ (lines 2-16)
  - Inline comments explaining valid values ✓ (10 of 14 fields commented; uncommented ones are self-explanatory: `type`, `name`, `description`, `updated_by`)
  - `sources: []` field for provenance ✓ (line 13, with shape comment matching `entities/sources-field.md`)
  - `updated_at` and `updated_by` mandatory ✓ (lines 14-15)
  - `tags: [type/code]` with inline comment showing additional dimensions ✓ (line 16)
  - `aliases: []` with "min 1 alias" note ✓ (line 4)
  - Zettelkasten role comment ✓ (line 19, "permanent note extension (sub-entity of actor)")
  - Linking rules comment ✓ (line 20)
  - Heading `# Code Node Name` ✓ (line 22)
  - Description blockquote ✓ (line 24)
  - Body sections (Details, What it does, Relations, Graph Bridge) ✓
  - "Expected Bidirectional Links" reference table marked as removable ✓ (line 51)

- [x] **`patterns/entity-definition.md`** — `entities/code.md` keeps the canonical 9-section structure intact:
  - `# Entity: Code` title (line 1) ✓
  - `> Source of truth for required fields: actors/_template_node.md` (line 3) ✓
  - `## What it is` (line 5) ✓
  - `## When to create` (line 11) ✓
  - `## When NOT to create` (line 18) ✓
  - `## How to distinguish from other types` table (line 26) ✓
  - `## Required fields (frontmatter)` table (line 36) + `### Optional fields` (line 53) + `### Backward compatibility` (line 60) ✓
  - `## Zettelkasten Role` (line 85) ✓
  - `## Examples` with "This IS" / "This is NOT" subsections (line 100) ✓

  **Authorized deviation:** A new `## Graph Bridge` top-level section was inserted between "Required fields" (line 36) and "Zettelkasten Role" (line 85). Spec DoD #3 explicitly authorized this placement: "in a new subsection (under 'Required fields' or in a new 'Graph Bridge' block)". The chosen placement is the most logical home — `vault_entity_path` is not a `code` frontmatter field but a graph.json field, so making it a subsection of "Required fields" would be misleading. Documented as a deliberate, spec-authorized deviation.

- [x] **`patterns/skill-architecture.md`** (advisory) — `skills/setup/SKILL.md` change is row insertion in two existing tables. Phase numbering preserved (§3.2 Copy Templates, §6 Files Created). YAML frontmatter, Plugin Paths section, Critical Rules table all unchanged. No new phases, no agent type change.

## Convention Violations (if any)

- **`skills/setup/SKILL.md:567-572`** — minor documentation drift, **not blocking**. The overwrite rule ("If a `_template.md` already exists in the destination, **overwrite it**") and the fallback message ("templates/<type>/_template.md directory") still reference the singular filename `_template.md`. With `_template_node.md` now in the table, the rule semantically still applies (Write tool overwrites by default; the loop logic is correct), but the prose refers to a hardcoded filename. Strictly interpreted, the fallback message would emit a wrong path if `_template_node.md` failed to copy ("templates/actors/_template.md" instead of "templates/actors/_template_node.md"). This is a small documentation gap, not a DoD violation; the actual copy operation is correct. Recommended polish for a future iteration.

## Tests

**No test runner detected** for this change. Project is markdown-only per `.vibeflow/index.md` ("This is a Claude Code plugin, not a traditional codebase. It consists entirely of markdown files"). The `hooks/` directory contains Python tests but is unrelated to Part 1 (no Python file was touched).

**Manual sanity checks performed during implementation:**
- `templates/actors/_template_node.md` parses as valid YAML; `graphify_node_ids` is a list (verified via `python3 -c "import yaml; ..."`).
- `grep` confirmed: `graphify_node_ids` array form appears in the Required fields table; backward compat note present; `vault_entity_path` documented in 4 distinct places (definition, JSON example, owner statement, TODO marker); setup table contains both row entries (§3.2 and §6).

## Budget

Files changed: **3 / ≤ 4** (1 created + 2 modified). Within budget.

## Anti-scope

All anti-scope items respected:
- `/preserve` Phase 1.3 — not touched.
- `/preserve` Phase 6.5 — not touched (only documented as TODO in `entities/code.md`).
- `/teach` — not touched.
- Batch migration of legacy vaults — not touched (in-line migration documented as the contract).
- Runtime schema validation — not touched.
- Other entity templates (`actor`, `person`, etc.) — not touched.

## Gaps

None blocking. Minor non-blocking polish item (see Convention Violations section): the §3.2 prose in `skills/setup/SKILL.md:567-572` could be generalized to cover both `_template.md` and `_template_node.md`. Not a Part 1 DoD requirement.

## Conclusion

Part 1 is complete and correct. Foundation for Parts 2 and 3 is in place: physical template exists, `code` entity schema is updated for grouping (`graphify_node_ids` array) and bridge (`vault_entity_path`), and `/bedrock:setup` will install the new template on fresh vaults. Backward compatibility contract is explicit. Pattern compliance is solid; the one deviation is spec-authorized.

**Ready to ship.**
