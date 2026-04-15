# PRD: Multiple Vault Support

> Generated via /vibeflow:discover on 2026-04-15

## Problem

Bedrock skills today are locked to the current working directory. Every skill assumes CWD is the vault root — reading `.bedrock/config.json`, running `git pull --rebase origin main`, resolving entity directories with relative paths. This means users must explicitly `cd` into a vault folder before running any `/bedrock:*` command.

For teams that manage multiple company vaults (e.g., one per squad, one for platform-wide knowledge, one personal), this is a constant friction point. There is no way to say `/bedrock:teach --vault payments-vault <URL>` or `/bedrock:query --vault platform-vault <question>` from wherever you are in Claude Code. You have to remember paths, switch directories, and mentally track which vault you're operating on.

The result is that Bedrock feels like a local tool tied to a folder, not a knowledge platform that manages named resources.

## Target Audience

Teams and individuals using Bedrock to manage multiple Obsidian vaults — each vault representing a different knowledge domain (squad context, platform knowledge, personal notes). The primary user is a developer or tech lead running Claude Code from any project directory who wants to interact with their vaults without context-switching.

## Proposed Solution

Introduce a **global vault registry** stored in the plugin directory (`<plugin_dir>/vaults.json`) that maps vault names to filesystem paths. Vaults are registered during `/bedrock:setup` and managed via a new `/bedrock:vaults` command. All existing skills gain a `--vault <name>` flag to target a specific vault.

Vault resolution follows a precedence chain:
1. **Explicit flag** — `--vault <name>` targets the named vault
2. **CWD detection** — if the current directory is inside a registered vault, use it (backward compatible)
3. **Default vault** — use the vault marked as default in the registry
4. **Error** — no vault can be resolved; ask the user to specify

This keeps full backward compatibility — users already working inside a vault directory don't need to change anything.

## Success Criteria

- A user can run `/bedrock:teach --vault my-vault <URL>` from any directory and have it write to the correct vault
- A user can run `/bedrock:query --vault platform <question>` without being in the vault folder
- `/bedrock:vaults` lists all registered vaults with their paths and which is default
- `/bedrock:setup` in a new vault automatically registers it in the global registry
- All 7 skills (query, teach, preserve, compress, sync, healthcheck, setup) resolve vault paths through the new resolution chain
- Git operations (`pull`, `commit`, `push`) work correctly via `git -C <vault_path>` instead of assuming CWD

## Scope v0

- **Global vault registry file** — `<plugin_dir>/vaults.json` with schema: `{ vaults: [{ name, path, default }] }`
- **Vault resolution module** — shared logic in all skills: parse `--vault` flag, detect CWD, read default, error if unresolved
- **`/bedrock:vaults` skill** — list registered vaults, set default (`--set-default <name>`), remove (`--remove <name>`)
- **`/bedrock:setup` integration** — after initializing a vault, register it in the global registry (prompt for vault name)
- **Adapt all 7 skills** — replace CWD-relative paths with resolved vault path; replace bare `git` with `git -C <vault_path>`
- **`--vault` flag** — add to all user-invocable skills (query, teach, preserve, compress, sync, healthcheck)
- **CLAUDE.md updates** — document the vault resolution chain and `--vault` flag

## Anti-scope

- **Vault sharing/permissions** — who can access which vault is handled by filesystem and git permissions, not the plugin
- **Cross-vault operations** — querying across vaults, cross-vault wikilinks, or merging vault knowledge graphs
- **Vault migration** — moving a vault to a different path, merging two vaults into one
- **Multi-vault targeting** — teaching the same content to 2+ vaults in a single command
- **Vault discovery/auto-registration** — scanning the filesystem for existing vaults; registration is explicit via `/setup` or `/vaults`
- **Vault renaming** — achievable via remove + re-register; no dedicated command needed

## Technical Context

**Current architecture:**
- All skills use a `## Plugin Paths` boilerplate section that resolves entity definitions and templates relative to `<base_dir>` (the skill's own directory in the plugin). This works for plugin-internal resources.
- Vault resources (entities, `.bedrock/config.json`, git repo) are assumed to be at CWD. Every skill does bare `git pull`, `ls .bedrock/config.json`, `Glob("actors/*.md")`, etc.
- The plugin manifest lives at `.claude-plugin/plugin.json` and provides `<base_dir>` at invocation.

**What needs to change:**
- A new `## Vault Resolution` section must be added to every skill (or a shared preamble), replacing the CWD assumption.
- Git operations across all skills must switch from `git <command>` to `git -C <resolved_vault_path> <command>`.
- `/bedrock:setup` currently checks `ls .bedrock/config.json` for idempotency — this must also check the global registry.
- The single-write-point pattern (all writes go through `/bedrock:preserve`) means preserve is the critical path — it must resolve vault path before any file operation.

**Patterns to follow:**
- Skill architecture pattern (`.vibeflow/patterns/skill-architecture.md`): phased execution, Plugin Paths section, critical rules table
- Vault writing rules (`.vibeflow/patterns/vault-writing-rules.md`): git conventions, frontmatter rules
- Skill delegation (`.vibeflow/patterns/skill-delegation.md`): preserve as single write point

**Constraint:** Claude Code plugin `<base_dir>` is the skill's own directory, not the vault. The plugin directory can be derived from `<base_dir>` (two levels up). The global registry must live relative to the plugin root, not any specific vault.

## Open Questions

None.
