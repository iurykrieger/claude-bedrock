---
tags: [template, frontmatter, obsidian, vault, schema]
modules: [templates/]
applies_to: [templates]
confidence: inferred
---
# Pattern: Template Structure

<!-- vibeflow:auto:start -->
## What
Templates define the frontmatter schema and body structure for each entity type. They serve as the source of truth for required fields and are copied verbatim into target vaults during `/bedrock:setup`.

## Where
7 templates in `templates/<type>/_template.md`: actors, people, teams, topics, discussions, projects, fleeting.

## The Pattern
Every template follows a consistent structure:

1. **YAML frontmatter** between `---` delimiters containing:
   - Type-specific required fields with placeholder values (`""`, `[]`, `YYYY-MM-DD`)
   - Inline comments explaining valid values (e.g., `# api | worker | consumer | producer`)
   - `sources: []` field for provenance tracking
   - `updated_at` and `updated_by` fields (mandatory on all types)
   - `tags: [type/<type>]` with inline comment showing additional tag dimensions
   - `aliases: []` with inline comment requiring minimum 1 alias

2. **Zettelkasten role comment** — `<!-- Zettelkasten role: permanent note -->` (or bridge/index/fleeting)
3. **Linking rule comment** — instructions for how wikilinks in the body should work
4. **Heading** — `# Entity Name`
5. **Description blockquote** — `> Brief description...`
6. **Body sections** — type-specific sections with placeholder content
7. **Expected Bidirectional Links** — reference table showing which links should be bidirectional (marked as removable in real pages)

Key frontmatter conventions:
- Keys always in English
- Wikilink references use `"[[slug]]"` syntax in arrays
- Tags use hierarchical format: `[type/actor, status/active, domain/payments]`
- `sources` field follows the schema from `entities/sources-field.md`

## Rules
- Templates MUST be copied verbatim during setup — no translation or modification
- Every entity MUST have `updated_at`, `updated_by`, `tags`, and `aliases` fields
- Wikilink references in frontmatter arrays use the format `["[[slug]]"]`
- The "Expected Bidirectional Links" section is a development reference, not user content
- Inline comments in frontmatter serve as documentation for valid values

## Examples from this codebase
File: templates/actors/_template.md
```yaml
---
type: actor
name: ""
aliases: []  # ["Display Name", "SIGLA"] — min 1 alias
category: ""  # api | worker | consumer | producer | cronjob | lambda | monolith
description: ""
repository: ""
stack: ""
status: ""  # active | deprecated | in-development
team: "[[squad-name]]"
criticality: ""  # very-high | high | medium | low
pci: false
known_issues: []
sources: []  # [{url: "https://...", type: "confluence|gdoc|github-repo|csv|markdown|manual", synced_at: YYYY-MM-DD}]
updated_at: YYYY-MM-DD
updated_by: ""
tags: [type/actor]  # + status/* + domain/* + scope/*
---
```

File: templates/fleeting/_template.md
```yaml
---
type: fleeting
title: ""
aliases: []
source: ""  # session | teach | manual
captured_at: YYYY-MM-DD
status: "raw"  # raw | reviewing | promoted | archived
promoted_to: ""  # "[[target-note]]" when promoted
sources: []
updated_at: YYYY-MM-DD
updated_by: ""
tags: [type/fleeting, status/raw]
---
```
<!-- vibeflow:auto:end -->

## Anti-patterns (if found)
None found — templates are consistently structured across all entity types.
