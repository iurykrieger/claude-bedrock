# Bedrock — CLAUDE.md

Instructions for AI agents working on Obsidian vaults powered by the Bedrock plugin.

---

## What is Bedrock?

**Bedrock** is a Claude Code plugin that turns any Obsidian vault into a structured Second Brain. It provides entity management, ingestion, compression, and sync automation — all via Claude Code skills.

This is **not a codebase**. The target vault is markdown-only — no build system, no tests, no deployable artifacts. The primary consumers are humans reading in Obsidian and AI agents writing via skills.

---

## Entity Types

The vault organizes knowledge into 8 entity types, each in its own directory:

| Entity | Directory | Filename pattern | Example |
|---|---|---|---|
| Actors | `actors/` | `repo-name.md` | `billing-api.md` |
| People | `people/` | `first-last.md` | `alice-smith.md` |
| Teams | `teams/` | `squad-name.md` | `squad-payments.md` |
| Concepts | `concepts/` | `slug.md` | `event-sourcing.md` |
| Topics | `topics/` | `YYYY-MM-category-slug.md` | `2026-04-feature-new-checkout.md` |
| Discussions | `discussions/` | `YYYY-MM-DD-slug.md` | `2026-04-02-daily-payments.md` |
| Projects | `projects/` | `slug.md` | `processing-3-0.md` |
| Fleeting | `fleeting/` | `YYYY-MM-DD-slug.md` | `2026-04-09-new-tokenization-service.md` |

Each entity type has a `_template.md` defining the required frontmatter and structure. **Always follow the template when creating new entities.**

Entity semantic definitions live in the plugin's `entities/` directory — used by `/bedrock:teach` and `/bedrock:preserve` to classify content.

---

## Writing Rules

### Language
- **English (en-US)** for all content by default (configurable via `/bedrock:setup`)
- Technical terms in English are accepted (PCI, API, Kafka, etc.)

### Frontmatter
- YAML between `---` delimiters
- **Keys always in English** (`type`, `name`, `status`, `updated_at`, `updated_by`)
- **Values in the vault's configured language** (`description: "Billing and invoicing API"`)
- Array references use wikilink syntax: `["[[name1]]", "[[name2]]"]`
- Every entity must have `updated_at` (YYYY-MM-DD) and `updated_by` (person or `name@agent`)

### Wikilinks
- Bare names only: `[[notification-service]]`, never `[[actors/notification-service]]`
- Bidirectional links expected (see template for link table per entity type)
- Add new links, **never remove** existing ones
- Links to non-existent files are fine — Obsidian shows them as creation invitations

### Tags (hierarchical)
Tags use `/` separator for multi-dimensional filtering in Obsidian graph view:

| Dimension | Prefix | Values |
|---|---|---|
| Type | `type/` | `actor`, `person`, `team`, `concept`, `topic`, `discussion`, `project`, `fleeting` |
| Status | `status/` | `active`, `deprecated`, `planning`, `blocked`, `done`, `in-progress`, `open`, `completed`, `cancelled`, `raw`, `reviewing`, `promoted`, `archived` |
| Domain | `domain/` | `payments`, `finance`, `notifications`, `checkout`, `orders`, `integrations`, `compliance`, `core`, `data`, `infra`, `marketplace`, `internal-tools`, `platform`, `security` |
| Scope | `scope/` | `pci`, `sox`, `lgpd` (fintech), `hipaa` (health), `gdpr` (Europe), `soc2` (SaaS) |
| Category | `category/` | `deprecation`, `bugfix`, `troubleshooting`, `rfc`, `incident`, `feature`, `compliance` |

These are examples — both domains and scopes are extensible. Add new values as your organization grows (e.g. new teams, new compliance requirements).

Rules:
- `type/*` mandatory on all entities
- `status/*` mandatory on actors and topics
- `domain/*` mandatory on actors and teams
- `scope/*` and `category/*` only when applicable

### Aliases
- Minimum 1 alias per entity (Obsidian `aliases` field)
- Must not duplicate the filename
- Format: `aliases: ["Readable Name", "Acronym"]`

### Callouts
| Callout | When | Mandatory? |
|---|---|---|
| `> [!warning] Deprecated` | Actor/topic with status deprecated | Yes |
| `> [!danger] PCI Scope` | Actor with `pci: true` | Yes |
| `> [!danger] SOX Scope` | Actor with SOX scope | Yes |
| `> [!info]`, `> [!todo]`, `> [!bug]` | Contextual highlights | No — use sparingly |

### Filenames
- Kebab-case, no accents, lowercase
- Actor filenames = GitHub repository name (canonical identifier)

---

## Update Rules

| Entity | Body | Frontmatter |
|---|---|---|
| **Actors** | May modify and merge — new data replaces stale content | Merge new data, never delete fields |
| **People, Teams, Concepts, Topics** | Append-only — never delete content from another agent/human | Merge new data, never delete fields |
| **All** | Never remove existing wikilinks | Always update `updated_at` and `updated_by` |

---

## Skills

These are the Claude Code skills provided by the Bedrock plugin:

| Skill | Purpose |
|---|---|
| `/bedrock:query` | Smart vault reader — answers questions by searching and cross-referencing entities |
| `/bedrock:teach` | Ingest external sources (Confluence, GDocs, GitHub, CSV) — extracts entities — delegates to `/bedrock:preserve` |
| `/bedrock:preserve` | Single write point — entity detection, matching, create/update, bidirectional links, git commit |
| `/bedrock:compress` | Deduplication and vault health — broken links, orphan entities, stale content |
| `/bedrock:sync` | Re-sync entities with external sources. Flags: `--people` (sync contributors), `--github` (sync PRs/activity) |

---

## Git Workflow

- **Trunk-based**: push directly to `main`
- **Pull before write**: `git pull --rebase origin main`
- **Commit convention**: `vault(<type>): <verb> <name> [source: <origin>]`

| Field | Values |
|---|---|
| `<type>` | `person`, `team`, `actor`, `concept`, `topic`, `discussion`, `project`, `note` |
| `<verb>` | `creates`, `updates`, `links`, `compresses` |
| `<origin>` | `memory`, `github`, `jira`, `confluence`, `gdoc`, `sheets`, `manual`, `compress` |

Examples:
```
vault(actor): updates billing-api [source: github]
vault: teaches roadmap-26q1, creates 7 topics [source: confluence]
vault: compresses 25 entities across 8 clusters [source: compress]
```

---

## Zettelkasten Principles

The vault follows adapted Zettelkasten principles. Each entity type has a **role** in the knowledge graph:

| Role | Entity types | Behavior |
|---|---|---|
| **Permanent notes** | `actors/`, `people/`, `teams/`, `concepts/` | Consolidated, stable knowledge. Self-contained. |
| **Bridge notes** | `topics/`, `discussions/` | Connect permanents, explaining *why* they relate. |
| **Index notes** | `projects/` | Curation — organize reading paths (thematic MOCs). |
| **Fleeting notes** | `fleeting/` | Inbox — raw ideas, forming concepts. Temporary by design. |

### Linking Rules

1. **Frontmatter = structural.** Arrays in frontmatter define organizational relationships (team, members, actors). Feed Dataview queries.
2. **Body = semantic.** Wikilinks in the body must have textual context: "processes payments via [[billing-api]]", not just "[[billing-api]]".
3. **Bridges are the connective tissue.** If two actors relate, the explanation lives in a topic or discussion — not duplicated in both.
4. **Index notes point, they don't explain.** Projects direct the reader to bridges and permanents.
5. **Fleeting notes are temporary.** They should be promoted (to permanent/bridge) or archived.
6. **Provenance via `sources` field.** Every entity can record where its data came from in the `sources` frontmatter field (list of `{url, type, synced_at}`). See `entities/sources-field.md` in the plugin.

Details in `entities/*.md` (section "Zettelkasten Role" per type) within the plugin directory.

---

## Don'ts

- **Never** use flat tags (`[actor]`) — always hierarchical (`[type/actor]`)
- **Never** use path-qualified wikilinks — `[[name]]`, not `[[dir/name]]`
- **Never** use display names in wikilinks — `[[notification-service]]`, not `[[NotificationService]]`
- **Never** delete content in people/teams/concepts/topics written by another agent or human
- **Never** delete existing wikilinks or frontmatter fields
- **Never** commit credentials, tokens, PANs, CVVs, or any sensitive data
- **Never** log raw card data (PAN, CVV, tracks, EMV) in documentation examples
