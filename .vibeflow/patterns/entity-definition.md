---
tags: [entity, definition, classification, zettelkasten, semantic]
modules: [entities/]
applies_to: [entities]
confidence: inferred
---
# Pattern: Entity Definition

<!-- vibeflow:auto:start -->
## What
Entity definitions are semantic reference documents that define what each entity type represents, when to create it, when NOT to create it, how to distinguish it from similar types, required frontmatter fields, Zettelkasten role, linking rules, and completeness criteria.

## Where
All 9 entity definitions live in `entities/`: actor.md, person.md, team.md, topic.md, discussion.md, project.md, fleeting.md, knowledge-node.md, sources-field.md.

## The Pattern
Every entity definition follows a fixed structure with these sections:

1. **`# Entity: <Name>`** — title
2. **Source of truth reference** — `> Source of truth for required fields: <template path>`
3. **`## What it is`** — 1-2 paragraph definition of the entity type
4. **`## When to create`** — bulleted list of positive criteria
5. **`## When NOT to create`** — bulleted list of exclusion criteria
6. **`## How to distinguish from other types`** — table with `| Looks like... | But is... | Key difference |`
7. **`## Required fields (frontmatter)`** — table with `| Field | Type | Description |`
8. **`## Zettelkasten Role`** — classification (permanent/bridge/index/fleeting), purpose in graph, linking rules, completeness criteria
9. **`## Examples`** — "This IS" and "This is NOT" examples with numbered explanations

The 7 entity types map to Zettelkasten roles:
- **Permanent notes:** actors, people, teams (stable, consolidated facts)
- **Bridge notes:** topics, discussions (connect permanents, explain relationships)
- **Index notes:** projects (curate reading paths, thematic MOCs)
- **Fleeting notes:** fleeting (inbox, raw ideas, temporary)

Additionally, `knowledge-node` is a sub-entity of actors (extension of permanent), and `sources-field` documents the provenance metadata field.

## Rules
- Entity definitions are the authoritative reference for classification — skills MUST consult them
- The distinction table ("How to distinguish") is critical for disambiguation
- Completeness criteria determine whether content goes to its target type or to `fleeting/`
- "When NOT to create" criteria are as important as "When to create"
- Examples section always has both positive ("This IS") and negative ("This is NOT") examples

## Examples from this codebase
File: entities/actor.md
```markdown
## How to distinguish from other types

| Looks like... | But is... | Key difference |
|---|---|---|
| Actor | Topic (deprecation) | If the focus is "this system is going to be shut down", it is a deprecation topic that **references** the actor |
| Actor | Project | If the focus is "we are building a new system", it is a project until the system has a repo and deployment |
| Actor | Person | Repo names can look like people's names. If it has a GitHub repo and deploys, it is an actor |
```

File: entities/fleeting.md
```markdown
## Promotion Criteria

A fleeting note should be promoted to permanent or bridge when **any** of the 3 criteria is met:
### 1. Critical mass
### 2. Corroboration
### 3. Active relevance
```

File: entities/topic.md
```markdown
## Zettelkasten Role

**Classification:** bridge note
**Purpose in the graph:** Connect permanent notes (actors, people, teams) explaining *why* they relate in the context of a subject that evolves over time.
```
<!-- vibeflow:auto:end -->

## Anti-patterns (if found)
- The `knowledge-node.md` entity definition is written in Portuguese while all others are in English. This inconsistency suggests it was added later (after the genericization effort).
