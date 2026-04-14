# Spec: Rename knowledge-node to code — Part 1 (write pipeline)

> Source PRD: `.vibeflow/prds/rename-knowledge-node-to-code.md`
> Generated: 2026-04-14

## Objective

Rename the `knowledge-node` entity type to `code` in the entity definition, the write pipeline (preserve + teach), and the concept entity cross-reference — so that graphify's `file_type: code` maps directly to entity type `code` without naming translation.

## Context

The plugin's extraction pipeline flows: `/teach` → `/graphify` → `/preserve` → vault. Graphify classifies source code nodes as `file_type: code`, but preserve maps them to `knowledge-node`. This naming gap adds cognitive overhead and causes confusion in the classification logic. The entity definition `entities/knowledge-node.md` is also written in Portuguese (flagged as known tech debt in `.vibeflow/index.md`), so this rename doubles as an opportunity to rewrite it fully in English.

Additionally, `entities/concept.md` (recently added) references `knowledge-node` in its distinction table — this must be updated to stay consistent.

No `_template_node.md` file exists in the plugin. Skills reference it as a path that exists in target vaults. References to this template name stay as-is (the template rename in vaults is a separate concern — out of scope here).

## Definition of Done

1. `entities/knowledge-node.md` is deleted and `entities/code.md` exists with identical structure but `type: "code"`, `tags: [type/code]`, and all internal references updated
2. `entities/code.md` is fully written in English (zero Portuguese content — resolves the known tech debt)
3. `skills/preserve/SKILL.md` references `code` instead of `knowledge-node` in all occurrences (~12): type lists, classification logic, directory mapping, creation rules, section headers
4. `skills/teach/SKILL.md` references `code` instead of `knowledge-node` in all occurrences (~1): entity type in example table
5. `entities/concept.md` references `code` instead of `knowledge-node` in distinction table and any other mentions (~3)
6. Zero occurrences of the string `knowledge-node` remain in the 4 modified files (entities/code.md, preserve, teach, concept.md)
7. Entity definition follows the entity-definition pattern: 9 sections (What/When/When NOT/Distinguish/Required fields/Optional fields/Zettelkasten Role/Examples)

## Scope

- **`entities/knowledge-node.md` → `entities/code.md`:** Delete old file via `git rm`. Create new file with all content rewritten: `type: "knowledge-node"` → `type: "code"`, `tags: [type/knowledge-node]` → `tags: [type/code]`, all prose references. Ensure English throughout.
- **`skills/preserve/SKILL.md`:** Replace all `knowledge-node` with `code` in: entity type YAML lists (line ~64), classification logic (line ~145), directory mapping table (line ~356), section 4.1.2 header and body (lines ~364-382), filter rules (line ~152), backlink instructions (line ~381). Keep `_template_node.md` references unchanged (template file naming is out of scope).
- **`skills/teach/SKILL.md`:** Replace `knowledge-node` with `code` in the entity mapping example (line ~273).
- **`entities/concept.md`:** Replace `knowledge-node` with `code` in distinction table rows and any prose references (~3 occurrences).

## Anti-scope

- **No directory structure changes.** Code entities still live at `actors/<actor>/nodes/`. The `nodes/` subdirectory stays.
- **No template file rename.** `_template_node.md` references in skills stay as-is — template files live in target vaults, not this plugin.
- **No semantic changes.** The entity's purpose, required fields, Zettelkasten role, and relationship to actors are unchanged.
- **No vault migration.** Existing vaults with `type: "knowledge-node"` are not touched.
- **No query/compress skill updates.** Those are Part 2.
- **No `.vibeflow/` metadata updates.** Index, conventions, patterns — handled as cleanup after both parts land.

## Technical Decisions

| Decision | Trade-off | Justification |
|---|---|---|
| Delete + create instead of `git mv` | Loses git rename tracking | The file content changes substantially (Portuguese → English rewrite + rename), so `git mv` wouldn't track it as a rename anyway. Cleaner to `git rm` old + create new. |
| Keep `_template_node.md` references unchanged | Template name still says "node" not "code" | Template files exist in target vaults, not this plugin. Renaming them is a vault migration concern, not a plugin concern. |
| Rewrite entity definition in English during rename | Extra work beyond pure rename | The Portuguese content was flagged as tech debt. Since we're rewriting the file anyway, fixing it now costs nothing extra. |

## Applicable Patterns

- **Entity definition pattern** (`.vibeflow/patterns/entity-definition.md`): The new `entities/code.md` must follow the 9-section structure exactly. Use existing English entity definitions (e.g., `entities/actor.md`) as style reference.
- **Vault writing rules** (`.vibeflow/patterns/vault-writing-rules.md`): Tag `type/code` replaces `type/knowledge-node`. All tag rules apply.

## Risks

| Risk | Mitigation |
|---|---|
| Preserve/teach diverge from query/compress during interim (Part 1 done, Part 2 pending) | Tolerable: query/compress only *read* entities — they don't create new ones with the type name. The write pipeline (Part 1) is consistent. Part 2 should land immediately after. |
| Missing an occurrence of `knowledge-node` in a modified file | DoD check #6 is an exhaustive grep — zero occurrences must remain in the 4 files. |
| Entity definition rewrite loses semantic content | Use the current `entities/knowledge-node.md` as source of truth for content. Translate and update terminology, but preserve all classification rules, distinction criteria, and examples. |
