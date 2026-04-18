> You are only seeing this prompt; there is no context outside it.

# Prompt Pack — Fix README inconsistencies

## 1. Objective and Definition of Done

**Objective:** Fix three inconsistencies in the root `README.md` so new users can install, understand, and use the Bedrock plugin without confusion.

**Definition of Done:**
- [ ] The **Installation** section uses the correct install command: `/plugin install bedrock@claude-bedrock` (not `/plugin install iurykrieger/claude-bedrock`).
- [ ] The **How It Works** section gives users a clear, actionable mental model of how to use the plugin (first-time use flow + day-to-day commands), not just an internal delegation diagram.
- [ ] The dependency section lists `graphify` as **required** and removes `confluence-to-markdown` and `gdoc-to-markdown` (they are now internal skills, no longer external dependencies).
- [ ] All other sections remain untouched (no drive-by edits).
- [ ] Markdown renders correctly (links valid, tables aligned, fenced code blocks closed).

## 2. Anti-scope

- Do NOT rewrite sections that aren't listed above (keep Features, Skills table, Vault Structure, Configuration, Contributing, Project Structure, License as-is).
- Do NOT change the banner, badges, or header block.
- Do NOT change `CLAUDE.md`, skill files, or entity definitions.
- Do NOT introduce new sections beyond what is strictly needed to fix the three issues.
- Do NOT change the install command for local development (`claude --plugin-dir ./claude-bedrock`) — only the marketplace install command is wrong.
- Do NOT translate or change the language (stay in English).
- Do NOT bump the plugin version or touch `.claude-plugin/plugin.json`.

## 3. Budget

≤ 1 file: `README.md` only.

## 4. Patterns to Follow

This repo is a Claude Code plugin (markdown-only, no build system). Conventions relevant to README edits:

- **Language:** English (en-US) for all user-facing content.
- **Skill references:** always use the invocation syntax `/bedrock:<name>` (e.g., `/bedrock:setup`, `/bedrock:teach`).
- **Plugin marketplace install format:** `/plugin install <plugin-name>@<marketplace-name>` where `<plugin-name>` is from `.claude-plugin/plugin.json` (`"name": "bedrock"`) and `<marketplace-name>` is the repo slug (`claude-bedrock`).
- **Tables:** aligned with `---` separators, short cells, pipe-delimited.
- **Fenced code blocks:** use triple backticks with a language hint when relevant (`bash`, ` ` for plain).
- **Voice:** terse, instructional, second person when addressing the user.

Reference: the 8 registered skills (from `skills/` directory) are: `ask`, `compress`, `healthcheck`, `preserve`, `setup`, `sync`, `teach`, `vaults`. Plus two internal-only skills (`confluence-to-markdown`, `gdoc-to-markdown`) that are invoked by `teach`/`sync` — these should NOT be surfaced as user commands.

## 5. Where to Work

### File: `README.md` (root)

#### 5a. Fix the install command — Installation section

Current (incorrect):
```markdown
## Installation

​```bash
/plugin marketplace add iurykrieger/claude-bedrock
/plugin install iurykrieger/claude-bedrock
​```
```

Change to:
```markdown
## Installation

​```bash
/plugin marketplace add iurykrieger/claude-bedrock
/plugin install bedrock@claude-bedrock
​```
```

Rationale: `/plugin install` takes `<plugin-name>@<marketplace-name>`. The plugin name is `bedrock` (see `.claude-plugin/plugin.json`), and the marketplace name is `claude-bedrock`.

#### 5b. Rewrite the "How It Works" section

Current (confusing — it's an internal delegation diagram):
```markdown
## How It Works

Bedrock follows a **skill delegation model** where all write operations flow through `/bedrock:preserve` as the single write point:

​```
External Source → /bedrock:teach → entity detection → /bedrock:preserve → vault
GitHub/Confluence → /bedrock:sync  → diff analysis  → /bedrock:preserve → vault
User question   → /bedrock:ask   → search + graph  → read-only response
Vault health    → /bedrock:compress → dedup/merge   → vault updates
​```

Every entity includes structured frontmatter, hierarchical tags, and bidirectional wikilinks — making the Obsidian graph view a living map of your knowledge.
```

Replace with a user-facing "How to use it" explanation that covers: (1) first-time setup, (2) day-to-day usage loops, (3) what to expect in Obsidian. Keep it short (≤ ~40 lines). Suggested shape:

```markdown
## How It Works

Bedrock turns your vault into a living knowledge graph by combining **8 skills** you invoke from Claude Code. You never write entities by hand — skills detect, create, and link them for you, with Obsidian rendering the result as a graph.

### First-time use

1. Open a folder you want to turn into a vault (or an existing Obsidian vault).
2. Run `/bedrock:setup` — answers a few questions and scaffolds directories, templates, and example entities.
3. Open the folder in Obsidian. You'll already see a connected graph.

### Day-to-day loops

- **Capture knowledge from a source** — paste a Confluence page, Google Doc, GitHub repo, or local file into `/bedrock:teach`. Bedrock extracts entities and writes them to the vault with bidirectional links.
- **Ask the vault questions** — use `/bedrock:ask` for anything like *"who owns the billing API?"* or *"what's the status of project X?"*. It searches the graph, follows wikilinks, and answers with citations.
- **Keep sources fresh** — run `/bedrock:sync` to re-pull external sources, or `/bedrock:sync --github` / `--people` to surface recent activity and contributors.
- **Clean up drift** — run `/bedrock:compress` to fix broken backlinks, merge duplicates, and consolidate fragmented concepts. Run `/bedrock:healthcheck` for a read-only report.
- **Manage multiple vaults** — register several vaults with `/bedrock:vaults`; target a specific one with `--vault <name>`.

### What you get in Obsidian

Every entity has YAML frontmatter (type, status, domain, sources), hierarchical tags (`type/actor`, `status/active`, `domain/payments`), and bidirectional wikilinks. The graph view becomes a navigable map of people, systems, teams, topics, and projects — updated automatically as you teach Bedrock new content.
```

#### 5c. Fix the dependency section

Current (incorrect — graphify listed as optional, plus two that are no longer dependencies):
```markdown
## Optional Dependencies

| Tool | Purpose | Required? |
|---|---|---|
| [graphify](https://github.com/iurykrieger/graphify) | Semantic code extraction for GitHub repos | No |
| [confluence-to-markdown](https://github.com/mk-nickyang/confluence-to-markdown) | Confluence page ingestion | No |
| [gdoc-to-markdown](https://github.com/mr-fcharles/gdoc-to-markdown) | Google Docs ingestion | No |
```

Replace with:
```markdown
## Dependencies

| Tool | Purpose | Required? |
|---|---|---|
| [graphify](https://github.com/iurykrieger/graphify) | Semantic code extraction and knowledge-graph pipeline used by `/bedrock:teach` and `/bedrock:sync` | Yes |

Confluence and Google Docs ingestion are built into the plugin as internal skills (`/bedrock:confluence-to-markdown`, `/bedrock:gdoc-to-markdown`) invoked by `/bedrock:teach` and `/bedrock:sync` — no external installation required.
```

Rationale: `graphify` is called by `teach` and referenced throughout the teach/sync pipelines (see `skills/teach/SKILL.md` — graph extraction is not optional). The two former external tools are now skills shipped with the plugin (`skills/confluence-to-markdown/`, `skills/gdoc-to-markdown/`).

## 6. Directional Guidance

- Make three surgical edits, in order: install command → How It Works → Dependencies. Each one is independent; do not bundle them into a single rewrite.
- Keep existing tone (terse, instructional). Do not add marketing language.
- When rewriting "How It Works", lead with what the user does, not with internal architecture. The skill delegation diagram belongs in `CLAUDE.md`, not the README.
- In the dependencies rewrite, rename the section from "Optional Dependencies" to "Dependencies" since the only item left is required.
- Verify each skill name referenced actually exists in `skills/` before writing it.

## 7. How to Run/Test

No test runner (markdown-only plugin). Validate manually:

```bash
# Render README locally (if you have grip or similar)
grip README.md

# Or preview via GitHub (push a branch and open it)
```

Manual checklist after editing:
- [ ] `grep -n "iurykrieger/claude-bedrock" README.md` — should only appear in the `marketplace add` line and in badge/license URLs, NOT in the `/plugin install` line.
- [ ] `grep -n "bedrock@claude-bedrock" README.md` — must appear exactly once, in the install block.
- [ ] `grep -n "confluence-to-markdown\|gdoc-to-markdown" README.md` — must return zero hits (both are now internal skills, not mentioned in README).
- [ ] `grep -nE "^## " README.md` — section list still contains: Features, Installation, Quick Start, Skills, Vault Structure, How It Works, Dependencies, Configuration, Contributing, License (no duplicates, no orphans).
- [ ] Open the file in a markdown previewer and skim — tables align, code blocks closed, links resolve.

After merging, run `/vibeflow:audit` to verify DoD compliance.
