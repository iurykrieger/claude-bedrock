# Coding Conventions

<!-- vibeflow:auto:start -->
## File Organization
- All skills: `skills/<name>/SKILL.md` — one file per skill
- All entity definitions: `entities/<type>.md` — one file per entity type
- All templates: `templates/<type>/_template.md` — one file per entity type
- Plugin manifest: `.claude-plugin/plugin.json`
- Project instructions: `CLAUDE.md` at root

## Naming Conventions
- **Filenames:** kebab-case, no accents, lowercase (e.g., `knowledge-node.md`, `sources-field.md`)
- **Skill names:** single lowercase word matching directory name (e.g., `query`, `teach`, `preserve`)
- **Entity types:** singular lowercase (e.g., `actor`, `person`, `team`)
- **Frontmatter keys:** always English (e.g., `type`, `name`, `status`, `updated_at`)
- **Frontmatter values:** vault language (configurable, default pt-BR)
- **Tags:** hierarchical with `/` separator (e.g., `type/actor`, `status/active`, `domain/payments`)
- **Wikilinks:** bare kebab-case names (e.g., `[[billing-api]]`, never `[[actors/billing-api]]` or `[[BillingAPI]]`)

## Skill Structure Convention (via CLAUDE.md)
Every skill MUST include in this order:
1. YAML frontmatter with `name`, `description`, `user_invocable`, `allowed-tools`
2. `# /bedrock:<name>` heading
3. `## Plugin Paths` section (mandatory boilerplate for path resolution)
4. `## Overview` section with agent type declaration
5. Numbered phases (`## Fase N — <Title>` or `## Phase N — <Title>`)
6. `## Critical Rules` table at the end

## Entity Definition Convention (via CLAUDE.md)
Every entity definition MUST include:
1. `# Entity: <Name>` heading
2. `> Source of truth` reference to template
3. Sections: What it is, When to create, When NOT to create, How to distinguish, Required fields, Zettelkasten Role, Examples

## Template Convention (via CLAUDE.md)
Every template MUST include:
1. YAML frontmatter with all required fields and inline comments for valid values
2. `<!-- Zettelkasten role: ... -->` comment
3. `<!-- Links in the body... -->` linking instruction comment
4. `## Expected Bidirectional Links` reference table (marked as removable)

## Writing Rules (via CLAUDE.md)
- Aliases: minimum 1 per entity, must not duplicate filename
- `updated_at` and `updated_by`: mandatory on every entity, updated on every write
- Sources field: append-only, dedup by URL, most recent first
- Wikilinks: add new, NEVER remove existing
- Body update rules: actors can be modified; people/teams/topics are append-only
- Callouts: `[!warning] Deprecated` and `[!danger] PCI Scope` are mandatory when applicable

## Git Convention (via CLAUDE.md)
- Trunk-based: push directly to `main`
- Pull before write: `git pull --rebase origin main`
- Commit message: `vault(<type>): <verb> <name> [fonte: <source>]`
- Types: `pessoa`, `time`, `ator`, `assunto`, `discussao`, `projeto`, `nota`
- Verbs: `cria`, `atualiza`, `vincula`, `comprime`
- Sources: `memoria`, `github`, `jira`, `confluence`, `gdoc`, `sheets`, `manual`, `compress`
- Multi-entity: `vault: preserves N entities [fonte: <sources>]`
- Max 2 push attempts with rebase retry

## Don'ts
- Do NOT use flat tags (`[actor]`) — always hierarchical (`[type/actor]`)
- Do NOT use path-qualified wikilinks (`[[dir/name]]`) — always bare (`[[name]]`)
- Do NOT use display names in wikilinks (`[[NotificationService]]`) — always kebab-case (`[[notification-service]]`)
- Do NOT delete content in people/teams/topics written by another agent/human
- Do NOT delete existing wikilinks or frontmatter fields
- Do NOT commit credentials, tokens, PANs, CVVs, or any sensitive data
- Do NOT write entities directly from detection skills (teach, sync) — always delegate to preserve
- Do NOT block workflows for failed external sources — always best-effort
- Do NOT skip user confirmation before write operations
- Do NOT use subagents for MCP calls — permissions are not inherited
- Do NOT translate templates during setup — copy verbatim
<!-- vibeflow:auto:end -->
