# Spec: Concept Entity Type

> Generated from `.vibeflow/prds/concept-entity.md` on 2026-04-14

## Objective

Give the vault a dedicated `concept` entity type so that graphify-extracted concepts (patterns, principles, techniques, protocols, abstractions) land as self-contained permanent notes in `concepts/` instead of being scattered across topics or lost in fleeting.

## Context

Today the vault has 8 entity types, none purpose-built for timeless, definitional knowledge. Graphify extracts concepts from documents, papers, and code, but `/bedrock:preserve`'s classification logic (lines 142–149) has no `concept` target — `file_type: document` concepts get classified as `topic` (bridge note with lifecycle) or `fleeting`, and `file_type: code` concepts get forced into `knowledge-node` (actor sub-entity). The result is concept fragmentation: the same idea described differently in multiple files with no canonical source of truth.

The fix is surgical: add the entity definition, template, update CLAUDE.md references, and extend preserve's classification logic.

## Definition of Done

1. **Entity definition exists** — `entities/concept.md` follows the entity-definition pattern: all 9 sections present (What/When/When NOT/Distinguish/Required fields/Zettelkasten Role/Examples), with at least 2 positive and 2 negative examples
2. **Template exists** — `templates/concepts/_template.md` follows the template-structure pattern: YAML frontmatter with inline comments, Zettelkasten role comment, linking instruction comment, body sections, Expected Bidirectional Links table
3. **CLAUDE.md updated** — `concept` appears in: Entity Types table (directory=`concepts/`, pattern=`slug.md`), Tags table (`type/concept`), Update Rules table (body=append-only, frontmatter=merge), Zettelkasten Principles table (role=permanent note), and Git commit convention types
4. **Preserve classification handles concepts** — `skills/preserve/SKILL.md` section 1.3 step 4 includes a concept classification rule, section 1.4 references concept as permanent, the type enum in section 1.1 includes `concept`, the directory table in section 4.1 includes `concept`, and linking rules in section 4.1.1 cover concept as permanent note
5. **Disambiguation is clear** — the entity definition's "How to distinguish" table explicitly differentiates concept from topic (timeless vs temporal), concept from knowledge-node (actor-independent vs actor-specific), and concept from fleeting (self-contained vs fragmentary)
6. **No conventions.md violations** — hierarchical tags only, bare wikilinks only, kebab-case filenames, English keys in frontmatter, no path-qualified wikilinks

## Scope

### In
- `entities/concept.md` — new entity definition (9-section pattern)
- `templates/concepts/_template.md` — new template with frontmatter schema
- `CLAUDE.md` — add concept to 5 tables (Entity Types, Tags, Update Rules, Zettelkasten, Git types)
- `skills/preserve/SKILL.md` — extend classification logic, type enum, directory table, linking rules

### Out (anti-scope)
- No migration of existing entities (future `/bedrock:compress` task)
- No changes to `knowledge-node` entity type or its template
- No new skills (no `/bedrock:concept`)
- No changes to `/bedrock:query`, `/bedrock:teach`, `/bedrock:sync`, `/bedrock:compress` skills
- No changes to `.vibeflow/index.md` or `.vibeflow/conventions.md` (that's a separate `/vibeflow:analyze` run)

## Technical Decisions

### 1. Zettelkasten role: permanent note
**Decision:** Concepts are permanent notes, alongside actors, people, and teams.
**Trade-off:** Could be "bridge" since concepts connect multiple entities. But concepts don't explain *why* entities relate (that's topics/discussions) — they define *what something IS*. Permanent is correct: stable, timeless, consolidated, self-contained.
**Justification:** Confirmed in discovery. Topics are temporal (what is HAPPENING), concepts are definitional (what something IS). A topic can reference a concept, not the other way around.

### 2. No `status` field
**Decision:** Concepts don't have a lifecycle status (unlike topics with open/in-progress/completed).
**Trade-off:** Some concepts do evolve (e.g., "REST" vs "GraphQL" adoption). But evolution is tracked in topics that *reference* the concept — the concept itself remains a stable definition.
**Justification:** Adding status would blur the line with topics. If a concept needs temporal tracking, a topic should reference it.

### 3. Filename pattern: `slug.md` (no date prefix)
**Decision:** Concept filenames are bare slugs like actors (`event-sourcing.md`, `circuit-breaker.md`).
**Trade-off:** Could use date prefix like topics (`2026-04-event-sourcing.md`). But concepts are timeless — a creation date adds no semantic value and makes filenames longer without benefit.
**Justification:** Follows the same reasoning as actors, people, and teams (other permanents).

### 4. Classification heuristic placement in preserve
**Decision:** Add concept classification between the existing `file_type: document` line (146) and the god-nodes line (148) in section 1.3 step 4. Also add concept to the Zettelkasten classification in section 1.4 as permanent.
**Trade-off:** Could create a separate classification phase for concepts. But the existing classify-by-file-type flow works — concepts are a subset of `file_type: document` and `file_type: paper` nodes that meet specific criteria.
**Justification:** Minimal changes to preserve's flow. The heuristic is: if a document/paper node describes a pattern, principle, technique, protocol, or abstraction AND is self-contained AND is not actor-specific → `concept`.

### 5. Frontmatter: `related_to` array instead of typed relation arrays
**Decision:** Use a single `related_to: ["[[entity-name]]"]` array instead of separate `actors`, `people`, `topics` arrays.
**Trade-off:** Typed arrays (like topics have `actors` and `people`) enable Dataview queries per relation type. But concepts relate to any entity type equally — a concept like "event sourcing" might relate to actors, topics, and other concepts. A single array keeps the template simple and avoids forcing the author to categorize every relation.
**Justification:** Body wikilinks with context provide the semantic relationship. The frontmatter array is structural — it just lists what's connected.

## Applicable Patterns

| Pattern | Where it applies |
|---|---|
| `patterns/entity-definition.md` | `entities/concept.md` — follow the 9-section structure exactly |
| `patterns/template-structure.md` | `templates/concepts/_template.md` — YAML frontmatter with inline comments, Zettelkasten comment, bidirectional links table |
| `patterns/vault-writing-rules.md` | All files — hierarchical tags, bare wikilinks, English keys, kebab-case filenames |
| `patterns/skill-delegation.md` | `skills/preserve/SKILL.md` — concept follows the same delegation contract as all other types |

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Concept/topic boundary confusion during classification | Concepts misclassified as topics or vice versa | Strong disambiguation table in entity definition + explicit heuristic in preserve with ordering: check concept criteria BEFORE falling through to topic |
| Existing vault entities not updated to link to concepts | New concept files are orphaned | Anti-scope: migration is a `/bedrock:compress` task. Concepts will gain links naturally as new content is ingested |
| Preserve classification logic grows complex | Harder to maintain, more edge cases | Concept classification is a single additional rule in a well-structured if/else chain. Keep the heuristic simple: pattern/principle/technique/protocol/abstraction + self-contained + not actor-specific |
