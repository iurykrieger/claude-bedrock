# Spec: Multiple Vaults — Part 1: Registry, Vaults Skill, Setup Integration

> Source PRD: `.vibeflow/prds/multiple-vaults.md`
> Generated via /vibeflow:gen-spec on 2026-04-15

## Objective

Users can register, list, set-default, and remove named vaults from anywhere in Claude Code, establishing the foundation for location-independent vault operations.

## Context

Today, Bedrock has no concept of a "vault registry." Each vault is a standalone directory with `.bedrock/config.json` inside it. Skills assume CWD is the vault. There is no global state tracking which vaults exist or which is the default.

This part introduces the global registry (`vaults.json` in the plugin directory), a new `/bedrock:vaults` management skill, and integrates vault registration into the existing `/bedrock:setup` flow.

## Definition of Done

1. **Registry file created on first use** — Running `/bedrock:setup` in a new vault creates `<plugin_dir>/vaults.json` if it doesn't exist, and appends the vault entry with `name` and `path`
2. **Setup prompts for vault name** — `/bedrock:setup` asks the user for a vault name during initialization and stores it in the registry; if only one vault exists, it is marked as default
3. **Vaults skill lists registered vaults** — `/bedrock:vaults` (no flags) prints a table of all registered vaults showing name, path, and which is default
4. **Vaults skill sets default** — `/bedrock:vaults --set-default <name>` marks the named vault as default and unmarks any previous default
5. **Vaults skill removes a vault** — `/bedrock:vaults --remove <name>` removes the entry from the registry (does NOT delete files on disk) and confirms the action
6. **No violations of conventions.md** — New skill follows the skill-architecture pattern (YAML frontmatter, Plugin Paths section, Overview, Phases, Critical Rules table); no flat tags, no path-qualified wikilinks
7. **Backward compatible** — Existing vaults that were set up before this change continue to work; `/bedrock:setup` in an existing vault offers to register it in the global registry without breaking anything

## Scope

- **`<plugin_dir>/vaults.json`** — Schema: `{ "vaults": [{ "name": "<string>", "path": "<absolute-path>", "default": <boolean> }] }`. Created lazily on first vault registration. Location: `<base_dir>/../../vaults.json` (plugin root, alongside `.claude-plugin/`).
- **`skills/vaults/SKILL.md`** (new) — Management skill with 3 modes: list (default), `--set-default <name>`, `--remove <name>`. Read-only agent (no vault writes, no git). Validates vault path still exists on disk when listing.
- **`skills/setup/SKILL.md`** (edit) — After Phase 3 (config creation), add a new phase that: (a) reads or creates `vaults.json`, (b) prompts user for a vault name (suggest directory basename as default), (c) appends the vault entry, (d) marks as default if it's the only vault. In reconfigure mode, check if vault is already registered and offer to update.
- **`CLAUDE.md`** (edit) — Add a "Vault Resolution" section documenting the registry, the `--vault` flag, and the resolution precedence chain. Add `/bedrock:vaults` to the skills table.

## Anti-scope

- Vault resolution logic inside existing skills (query, teach, preserve, etc.) — that's Part 2 and Part 3
- `--vault` flag on any skill other than `/bedrock:vaults` — added in Part 2/3
- Cross-vault operations, vault migration, vault renaming
- Automatic vault discovery (scanning filesystem)
- Vault path validation beyond "directory exists" (no checking for `.bedrock/config.json` in vaults skill — that's setup's job)

## Technical Decisions

| Decision | Choice | Trade-off |
|---|---|---|
| Registry location | `<plugin_dir>/vaults.json` (plugin root) | Pro: accessible from any skill via `<base_dir>/../../vaults.json`. Con: if plugin is reinstalled, registry is lost. Mitigation: registry is cheap to rebuild via `/bedrock:setup`. |
| Registry format | Flat JSON array | Pro: simple, no dependencies. Con: no locking for concurrent access. Acceptable because Claude Code is single-session. |
| Default vault semantics | Exactly one vault marked `"default": true`; first registered vault is auto-default | Pro: predictable behavior. Con: user might forget which is default. Mitigated by `/bedrock:vaults` always showing it. |
| Vault name constraints | Kebab-case, lowercase, no spaces, unique | Consistent with existing filename conventions. Validated on registration. |
| Setup integration | New phase after config creation, not a separate command | Pro: natural flow — you set up a vault and it's registered. Con: couples setup with registry. Acceptable because setup is the canonical "create a vault" entry point. |

## Applicable Patterns

- **Skill Architecture** (`.vibeflow/patterns/skill-architecture.md`) — `/bedrock:vaults` MUST follow: YAML frontmatter, Plugin Paths section, Overview with agent type, numbered Phases, Critical Rules table
- **Vault Writing Rules** (`.vibeflow/patterns/vault-writing-rules.md`) — naming conventions (kebab-case), but git conventions don't apply here since vaults skill is read-only (no vault writes)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Plugin reinstall wipes `vaults.json` | Medium | Medium — user loses registry, not data | `/bedrock:setup` can re-register; add a note in CLAUDE.md about this |
| Vault path moves after registration | Low | Low — stale entry shows error on list | `/bedrock:vaults` validates path exists and flags missing vaults |
| Name collision during registration | Low | Low | Setup validates uniqueness before writing |
