# Spec: Rename knowledge-node to code — Part 2 (read pipeline)

> Source PRD: `.vibeflow/prds/rename-knowledge-node-to-code.md`
> Generated: 2026-04-14

## Objective

Complete the rename by updating the read/maintenance skills (query and compress) so that zero occurrences of `knowledge-node` remain in any plugin source file.

## Context

Part 1 renamed the entity definition and updated the write pipeline (preserve, teach, concept entity). This part handles the remaining two skills that reference `knowledge-node`:

- **`skills/query/SKILL.md`** — 1 occurrence in graph node resolution logic
- **`skills/compress/SKILL.md`** — 24 occurrences across inventory, orphan detection, clustering, proposal output, and commit messages

After this part lands, the rename is complete across the entire plugin.

## Definition of Done

1. `skills/query/SKILL.md` references `code` instead of `knowledge-node` in all occurrences (1 occurrence in graph node resolution)
2. `skills/compress/SKILL.md` references `code` instead of `knowledge-node` in all occurrences (~24): inventory listing, orphan detection sections (1.5.2, 1.5.3, 1.5.4), clustering rules, proposal tables, cleanup rules, health report, commit messages
3. Zero occurrences of the string `knowledge-node` remain in any file under `entities/` or `skills/` (full plugin source verification)
4. Compress skill section headers and table column names reflect the rename (e.g., "Orphan code entities" not "Orphan knowledge-nodes")
5. No semantic changes — all classification logic, orphan detection criteria, and clustering rules behave identically, just with the new type name

## Scope

- **`skills/query/SKILL.md`:** Replace 1 occurrence at line ~186: "search for knowledge-node in `actors/*/nodes/`" → "search for code entity in `actors/*/nodes/`".
- **`skills/compress/SKILL.md`:** Replace all 24 occurrences. Key areas:
  - Phase 1 inventory (line ~65-69): entity listing and frontmatter extraction
  - Phase 1.5 graph health (lines ~104-148): orphan detection sections (1.5.2, 1.5.3, 1.5.4), variable names, report fields
  - Phase 2 clustering (lines ~156-160): same-actor comparison rules
  - Phase 3 proposal (lines ~243-257): orphan cleanup proposal tables, section headers
  - Phase 4 execution (lines ~312-320): orphan cleanup rules, git rm instructions
  - Phase 5 health report (lines ~369-397): report fields, commit message examples

## Anti-scope

- **No entity definition changes.** Already done in Part 1.
- **No preserve/teach changes.** Already done in Part 1.
- **No semantic changes.** Orphan detection, clustering, and cleanup logic stays identical.
- **No `.vibeflow/` metadata updates.** Index, conventions, patterns cleanup is a separate housekeeping task after both parts land.
- **No vault migration.** Existing vaults are not touched.

## Technical Decisions

| Decision | Trade-off | Justification |
|---|---|---|
| Replace all 24 occurrences in compress atomically | Large diff in a single file | Compress is the most knowledge-node-heavy skill. Doing it all at once ensures consistency — partial replacement would break section cross-references (e.g., Phase 1.5 populates data that Phase 3 uses in proposals). |
| Update section headers (e.g., "Orphan code entities") | Minor prose change beyond pure token replacement | Headers that say "Orphan knowledge-nodes" would be confusing when the entity type is `code`. Natural language should match the type name. |

## Applicable Patterns

- **Skill architecture pattern** (`.vibeflow/patterns/skill-architecture.md`): Skills use phased execution — ensure phase cross-references remain consistent after the rename.
- **Vault writing rules** (`.vibeflow/patterns/vault-writing-rules.md`): Tag `type/code` and commit convention `vault(code):` replace previous `knowledge-node` references.

## Risks

| Risk | Mitigation |
|---|---|
| Missing occurrences in compress (24 is a lot) | DoD check #3 is a full grep across `entities/` + `skills/` — exhaustive verification. |
| Compress section cross-references break | Replace all occurrences in a single pass. Variable names, table headers, and prose all update together. |

## Dependencies

- `.vibeflow/specs/rename-knowledge-node-to-code-part-1.md` — must be implemented first (entity definition must exist as `code` before read-side skills reference it).
