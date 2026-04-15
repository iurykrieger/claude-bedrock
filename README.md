<p align="center">
  <img src="docs/banner.png" alt="Bedrock — Knowledge graph visualization" width="600">
</p>

<h1 align="center">Bedrock</h1>

<p align="center">
  <strong>Turn any Obsidian vault into a structured Second Brain with AI agents</strong>
</p>

<p align="center">
  <a href="https://github.com/iurykrieger/claude-bedrock/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/iurykrieger/claude-bedrock"><img src="https://img.shields.io/badge/claude--code-plugin-a882ff" alt="Claude Code Plugin"></a>
  <a href="https://github.com/iurykrieger/claude-bedrock"><img src="https://img.shields.io/github/v/tag/iurykrieger/claude-bedrock?label=version" alt="Version"></a>
</p>

---

Bedrock is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin that automates Obsidian vault management through AI-powered skills. It organizes knowledge into **7 entity types** following adapted [Zettelkasten](https://zettelkasten.de/overview/) principles — entity detection, bidirectional linking, ingestion from external sources, deduplication, and sync.

No build system. No runtime. Just markdown files, AI agents, and your Obsidian vault.

## Features

- **6 AI-powered skills** — query, teach, preserve, compress, sync, and setup
- **7 entity types** — actors, people, teams, topics, discussions, projects, and fleeting notes
- **External source ingestion** — Confluence, Google Docs, GitHub, CSV
- **Bidirectional wikilinks** — automatic cross-referencing with Obsidian graph view
- **Hierarchical tags** — multi-dimensional filtering (`type/`, `status/`, `domain/`, `scope/`)
- **Zettelkasten structure** — permanent, bridge, index, and fleeting note roles
- **Trunk-based git workflow** — structured commit conventions built in

## Installation

```bash
/plugin marketplace add iurykrieger/claude-bedrock
/plugin install iurykrieger/claude-bedrock
```

For local development:

```bash
claude --plugin-dir ./claude-bedrock
```

## Quick Start

After installing, run the setup wizard:

```
/bedrock:setup
```

This will guide you through:

1. **Language selection** — choose the vault content language (default: English)
2. **Dependency check** — verify optional tools (`graphify`, `confluence-to-markdown`, `gdoc-to-markdown`)
3. **Vault objective** — pick a preset (engineering team, product management, company wiki, personal second brain, open source project, or custom)
4. **Scaffold** — create directories, templates, config, and connected example entities

The setup creates all entity directories, copies templates, generates a vault-level `CLAUDE.md`, and scaffolds example entities with bidirectional wikilinks so you can see the graph in Obsidian immediately.

## Skills

| Skill | Purpose |
|---|---|
| `/bedrock:setup` | Interactive vault initialization and configuration |
| `/bedrock:ask` | Orchestrated vault reader — decomposes questions, searches graph and vault, cross-references entities |
| `/bedrock:teach` | Ingest external sources — extract and create entities |
| `/bedrock:preserve` | Single write point — detect, match, create/update entities with bidirectional links |
| `/bedrock:compress` | Deduplication and vault health — broken links, orphans, stale content |
| `/bedrock:sync` | Re-sync entities with external sources |

## Vault Structure

```
your-vault/
├── actors/          # Systems, services, APIs (permanent notes)
├── people/          # Contributors, team members (permanent notes)
├── teams/           # Squads, organizational units (permanent notes)
├── topics/          # Cross-cutting subjects with lifecycle (bridge notes)
├── discussions/     # Meeting notes, conversations (bridge notes)
├── projects/        # Initiatives with scope and deadline (index notes)
└── fleeting/        # Raw ideas, unstructured captures (fleeting notes)
```

Each directory contains a `_template.md` defining the frontmatter schema for that entity type.

## How It Works

Bedrock follows a **skill delegation model** where all write operations flow through `/bedrock:preserve` as the single write point:

```
External Source → /bedrock:teach → entity detection → /bedrock:preserve → vault
GitHub/Confluence → /bedrock:sync  → diff analysis  → /bedrock:preserve → vault
User question   → /bedrock:ask   → search + graph  → read-only response
Vault health    → /bedrock:compress → dedup/merge   → vault updates
```

Every entity includes structured frontmatter, hierarchical tags, and bidirectional wikilinks — making the Obsidian graph view a living map of your knowledge.

## Optional Dependencies

| Tool | Purpose | Required? |
|---|---|---|
| [graphify](https://github.com/iurykrieger/graphify) | Semantic code extraction for GitHub repos | No |
| [confluence-to-markdown](https://github.com/mk-nickyang/confluence-to-markdown) | Confluence page ingestion | No |
| [gdoc-to-markdown](https://github.com/mr-fcharles/gdoc-to-markdown) | Google Docs ingestion | No |

## Configuration

Configuration is stored in `.bedrock/config.json` inside your vault. Run `/bedrock:setup` again at any time to reconfigure.

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork and install the plugin locally:
   ```bash
   claude --plugin-dir ./claude-bedrock
   ```
3. **Create a branch** for your feature or fix
4. **Make your changes** — skills live in `skills/`, entity definitions in `entities/`, templates in `templates/`
5. **Test** by running the plugin against a test vault
6. **Open a PR** against `main`

### Project Structure

```
claude-bedrock/
├── .claude-plugin/    # Plugin manifest (plugin.json)
├── skills/            # Skill definitions (SKILL.md per skill)
│   ├── setup/
│   ├── query/
│   ├── teach/
│   ├── preserve/
│   ├── compress/
│   └── sync/
├── entities/          # Entity type definitions
├── templates/         # Frontmatter schema templates
├── docs/              # Documentation assets
├── CLAUDE.md          # AI agent instructions
└── README.md
```

## License

[MIT](LICENSE) — Iury Krieger
