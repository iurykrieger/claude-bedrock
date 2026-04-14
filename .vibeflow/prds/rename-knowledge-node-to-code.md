# PRD: Rename knowledge-node entity to code

> Generated via /vibeflow:discover on 2026-04-14

## Problem

The `knowledge-node` entity type was created before `/teach` delegated extraction to `/graphify`. Now that graphify is the extraction engine, there's a naming mismatch: graphify classifies nodes as `file_type: code`, but preserve maps them to a type called `knowledge-node`. The name is abstract, verbose, and doesn't match the vocabulary of the pipeline that produces these entities.

Renaming to `code` aligns the entity type with graphify's output taxonomy, reduces cognitive overhead for agents and humans reading the vault, and makes the distinction clearer — `code` entities capture functions, classes, endpoints, and design decisions found in source code; `concept` entities (a separate upcoming type) capture cross-cutting abstractions.

## Target Audience

AI agents running `/bedrock:preserve` and `/bedrock:teach` — they classify graphify output into entity types and need consistent naming across the pipeline. Secondary: humans reading entity definitions and vault content in Obsidian.

## Proposed Solution

Rename the entity type from `knowledge-node` to `code` everywhere it appears: entity definition, template, skills, tags, classification logic. The entity's semantics are unchanged — it remains a sub-entity of actors, living inside `actors/<actor>/nodes/`, representing granular code-level details extracted by graphify.

## Success Criteria

- All references to `knowledge-node` across the plugin are replaced with `code`
- The `file_type: code` → entity type `code` mapping in preserve's classification logic reads naturally without translation
- Existing tag convention updates: `type/knowledge-node` → `type/code`
- Entity definition, template, and all skills compile without stale references to the old name
- The concept entity PRD (`concept-entity.md`) is updated to reference `code` instead of `knowledge-node`

## Scope v0

1. **Entity definition rename** — `entities/knowledge-node.md` → `entities/code.md`. Update all internal references (`type: "knowledge-node"` → `type: "code"`, tags, examples, distinction table)
2. **Template update** — `actors/_template_node.md`: update `type` field and any references to "knowledge-node"
3. **Preserve skill update** — `skills/preserve/SKILL.md`: replace all `knowledge-node` references with `code` (classification logic, entity type lists, directory mapping, creation rules)
4. **Teach skill update** — `skills/teach/SKILL.md`: replace `knowledge-node` references with `code` in entity type lists and examples
5. **Other skills** — `skills/query/SKILL.md`, `skills/compress/SKILL.md`, `skills/sync/SKILL.md`: search-and-replace any `knowledge-node` references
6. **Concept entity PRD update** — `.vibeflow/prds/concept-entity.md`: replace `knowledge-node` with `code` in distinction table and anti-scope
7. **Vibeflow index update** — `.vibeflow/index.md`: update the key files list and known issues referencing `knowledge-node`

## Anti-scope

- **No semantic changes.** The entity's purpose, required fields, Zettelkasten role, and relationship to actors remain identical. This is a pure rename.
- **No directory structure changes.** Code entities still live at `actors/<actor>/nodes/`. The `nodes/` subdirectory name stays as-is.
- **No migration of existing vault entities.** If any vault already has `type: "knowledge-node"` in frontmatter, that's a future `/bedrock:compress` task — not part of this rename.
- **No CLAUDE.md changes.** `knowledge-node` was never listed in CLAUDE.md's entity types table (it's a sub-entity). The recent CLAUDE.md update added `concept` — no further changes needed for this rename.
- **No concept entity work.** The concept entity is a separate PRD and lands after this rename.

## Technical Context

### Files to modify
- `entities/knowledge-node.md` → rename to `entities/code.md` (rewrite internal references)
- `actors/_template_node.md` (update type field)
- `skills/preserve/SKILL.md` (~10 occurrences of `knowledge-node`)
- `skills/teach/SKILL.md` (~3 occurrences)
- `skills/query/SKILL.md`, `skills/compress/SKILL.md`, `skills/sync/SKILL.md` (search for occurrences)
- `.vibeflow/prds/concept-entity.md` (update references)
- `.vibeflow/index.md` (update key files list)

### Patterns to follow
- **Entity definition pattern** (`.vibeflow/patterns/entity-definition.md`): the renamed file must keep the same structure
- **Vault writing rules** (`.vibeflow/patterns/vault-writing-rules.md`): tag convention `type/code` replaces `type/knowledge-node`

### Known issue resolved
The `.vibeflow/index.md` notes that `entities/knowledge-node.md` is written in Portuguese while all other definitions are in English. This rename is an opportunity to ensure the rewritten `entities/code.md` is fully in English.

## Open Questions

None.
