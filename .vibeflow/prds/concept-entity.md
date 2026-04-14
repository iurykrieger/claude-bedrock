# PRD: Concept Entity Type

> Generated via /vibeflow:discover on 2026-04-14

## Problem

Graphify extracts concepts from documents, papers, and code — self-contained ideas, patterns, or abstractions like "event sourcing", "PCI tokenization flow", or "circuit breaker pattern". Today these nodes have no dedicated entity type. Code-sourced concepts get forced into `knowledge-node` (which is tightly coupled to actors as sub-entities), while document/paper-sourced concepts fall through to `topic` or `fleeting` in preserve's classification logic.

The result is concept fragmentation: the same concept appears across multiple actors and topics with slightly different descriptions, no single source of truth, and no way to consolidate. This defeats the Zettelkasten principle of atomic, self-contained permanent notes and makes the knowledge graph noisier than it needs to be.

## Target Audience

AI agents running `/bedrock:teach` and `/bedrock:preserve` — they need a clear classification target for concept nodes extracted by graphify. Secondary: humans reading the vault in Obsidian, who benefit from a single canonical page per concept instead of scattered inline descriptions.

## Proposed Solution

Add a new top-level entity type `concept` with its own directory (`concepts/`), entity definition (`entities/concept.md`), and template (`templates/concepts/_template.md`). Concepts are **permanent notes** — stable, timeless, definitional. They describe *what something IS*, not what is happening with it. Topics, actors, discussions, and other entities reference concepts via wikilinks instead of re-describing them.

Update `/bedrock:preserve`'s classification logic to recognize concept nodes from graphify output and map them to this new entity type. Update `CLAUDE.md` to document the 8th entity type.

## Success Criteria

- Graphify concept nodes (from documents, papers, and code) are classified as `concept` entities by `/bedrock:preserve` instead of falling through to `topic` or `fleeting`
- A concept entity is a self-contained permanent note: it defines what something IS with enough context to stand alone
- Other entities (actors, topics, discussions) can reference concepts via `[[concept-name]]` wikilinks
- The concept entity follows all existing conventions: entity definition pattern, template structure, hierarchical tags, writing rules

## Scope v0

1. **Entity definition** — `entities/concept.md` following the entity-definition pattern (What/When/When NOT/Distinguish/Required fields/Zettelkasten Role/Examples)
2. **Template** — `templates/concepts/_template.md` with frontmatter schema and bidirectional link refs
3. **CLAUDE.md update** — add `concept` to the entity types table, tags table (`type/concept`), update rules table, Zettelkasten principles table (permanent note), and commit convention types
4. **Preserve skill update** — update classification logic in `skills/preserve/SKILL.md` to handle concept nodes from graphify output
5. **Teach skill update** — if `/teach` has any hardcoded entity type lists, add `concept` to them

## Anti-scope

- **No migration of existing entities.** Existing topics or fleeting notes that are actually concepts will NOT be reclassified in this PR. That's a future `/bedrock:compress` task.
- **No knowledge-node changes.** The `knowledge-node` entity type stays as-is (sub-entity of actors for code-level details). Concepts extracted from code that are actor-specific remain knowledge-nodes; only cross-cutting concepts become `concept` entities.
- **No new skill.** No `/bedrock:concept` skill — concepts are created and managed through the existing `/bedrock:preserve` pipeline.
- **No query skill changes.** `/bedrock:query` already searches all entity types by directory — adding `concepts/` is automatic.
- **No sync skill changes.** Concepts don't have external sources to sync (they're derived from other entities' sources).
- **No Obsidian plugin changes.** The vault is markdown-only; Obsidian discovers new folders automatically.

## Technical Context

### Existing patterns to follow
- **Entity definition pattern** (`.vibeflow/patterns/entity-definition.md`): fixed structure with 9 sections (What/When/When NOT/Distinguish/Required fields/Zettelkasten/Examples)
- **Template structure pattern** (`.vibeflow/patterns/template-structure.md`): YAML frontmatter with inline comments, Zettelkasten role comment, linking instruction comment, expected bidirectional links table
- **Vault writing rules** (`.vibeflow/patterns/vault-writing-rules.md`): hierarchical tags, wikilinks, aliases, callouts

### Key files to modify
- `entities/concept.md` (new)
- `templates/concepts/_template.md` (new)
- `CLAUDE.md` — entity types table, tags, update rules, zettelkasten principles, commit types
- `skills/preserve/SKILL.md` — classification logic (around lines 142-149 per vibeflow analysis)
- `skills/teach/SKILL.md` — entity type lists if hardcoded

### Zettelkasten role
**Permanent note.** Concepts are stable, timeless, definitional knowledge — like actors, people, and teams. They are self-contained and consolidated. Unlike knowledge-nodes (which are sub-entities of actors), concepts are top-level and actor-independent. Unlike topics (which are bridge notes with lifecycles), concepts have no status or temporal evolution.

### Classification heuristic for preserve
A graphify node should become a `concept` when:
- It describes a pattern, principle, technique, protocol, or abstraction
- It is self-contained (understandable without reading other entities)
- It is not specific to a single actor's implementation (that's a knowledge-node)
- It is not temporal/evolving (that's a topic)
- It has no lifecycle (no status field)

## Open Questions

None.
