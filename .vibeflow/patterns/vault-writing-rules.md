---
tags: [vault, writing, frontmatter, wikilinks, tags, git, conventions]
modules: [entities/, templates/, skills/]
applies_to: [entities, templates, skills]
confidence: inferred
---
# Pattern: Vault Writing Rules

<!-- vibeflow:auto:start -->
## What
A comprehensive set of writing conventions that govern how entities are created, updated, and linked in Obsidian vaults managed by Bedrock. These rules are enforced by the CLAUDE.md and all skills.

## Where
Defined in `CLAUDE.md` (root-level project instructions), referenced and enforced by all 6 skills, applied to entities in `actors/`, `people/`, `teams/`, `topics/`, `discussions/`, `projects/`, `fleeting/`.

## The Pattern
The writing rules cover 7 dimensions:

### 1. Language
- Content in the vault's configured language (default: pt-BR for original design, configurable via `/bedrock:setup`)
- Frontmatter keys always in English (`type`, `name`, `status`, `updated_at`)
- Frontmatter values in the vault language
- Technical terms in English are always acceptable (PCI, API, Kafka, etc.)

### 2. Frontmatter
- YAML between `---` delimiters
- Every entity MUST have `updated_at` (YYYY-MM-DD) and `updated_by` (person or `name@agent`)
- Array references use wikilink syntax: `["[[name1]]", "[[name2]]"]`
- Sources field follows append-only dedup-by-URL semantics

### 3. Wikilinks
- Bare names only: `[[notification-service]]`, never `[[actors/notification-service]]`
- Never display names: `[[notification-service]]`, not `[[NotificationService]]`
- Add new links, NEVER remove existing ones
- Links to non-existent files are acceptable (Obsidian creation invitations)

### 4. Tags (hierarchical)
- Always use `/` separator: `type/actor`, `status/active`, `domain/payments`
- Never flat tags: `[actor]` is wrong, `[type/actor]` is correct
- `type/*` mandatory on all entities
- `status/*` mandatory on actors and topics
- `domain/*` mandatory on actors and teams
- `scope/*` and `category/*` only when applicable

### 5. Update Rules
- **Actors:** body can be modified and merged; frontmatter is merge-only
- **People, Teams, Topics:** body is append-only (never delete content from another agent/human)
- **All entities:** never remove existing wikilinks; always update `updated_at` and `updated_by`
- **Knowledge-nodes:** can be deleted via `git rm` (only entity type that supports deletion)

### 6. Git Workflow
- Trunk-based: push directly to `main`
- Pull before write: `git pull --rebase origin main`
- Commit convention: `vault(<type>): <verb> <name> [fonte: <source>]`
- Max 2 push attempts with rebase retry

### 7. Callouts
- `> [!warning] Deprecated` — mandatory for deprecated actors/topics
- `> [!danger] PCI Scope` — mandatory for actors with `pci: true`
- `> [!danger] SOX Scope` — mandatory for actors with SOX scope

## Rules
- Filenames: kebab-case, no accents, lowercase
- Actor filenames = GitHub repository name (canonical identifier)
- Minimum 1 alias per entity (must not duplicate filename)
- Bidirectional links expected: if A links to B, B should link back to A
- Zettelkasten linking: frontmatter = structural, body = semantic (with textual context)

## Examples from this codebase
File: CLAUDE.md (wikilinks rule)
```markdown
### Wikilinks
- Bare names only: `[[notification-service]]`, never `[[actors/notification-service]]`
- Bidirectional links expected
- Add new links, **never remove** existing ones
- Links to non-existent files are fine
```

File: CLAUDE.md (git convention)
```markdown
vault(ator): atualiza billing-api [fonte: github]
vault: teaches roadmap-26q1, creates 7 topics [fonte: confluence]
vault: compress 25 entities across 8 clusters [fonte: compress]
```

File: CLAUDE.md (update rules)
```markdown
| **Actors** | May modify and merge | Merge new data, never delete fields |
| **People, Teams, Topics** | Append-only — never delete content | Merge new data, never delete fields |
```
<!-- vibeflow:auto:end -->

## Anti-patterns (if found)
- The `knowledge-node.md` entity definition is written in Portuguese while all other entity definitions are in English, which conflicts with the genericized project direction (the project was recently genericized to remove all organization-specific references).
