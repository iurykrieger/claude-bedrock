# Spec: Multiple Vaults — Part 2: Vault Resolution in Core Skills

> Source PRD: `.vibeflow/prds/multiple-vaults.md`
> Generated via /vibeflow:gen-spec on 2026-04-15

## Dependencies

- `.vibeflow/specs/multiple-vaults-part-1.md` — Registry and vaults skill must exist first

## Objective

The 3 core skills (preserve, query, healthcheck) resolve vault paths through the global registry, enabling users to run them from any directory with `--vault <name>` or automatic resolution.

## Context

After Part 1, the vault registry exists and vaults can be registered by name. But all existing skills still assume CWD is the vault root. This part adds the vault resolution chain to the 3 most critical skills:

- **preserve** — the single write point; every vault modification flows through it. Must resolve vault path before any file read/write or git operation.
- **query** — the primary read skill; searches entities via Glob/Grep against vault directories.
- **healthcheck** — read-only diagnostic; scans all entity directories for integrity checks.

These 3 form the "core" because preserve is the write bottleneck and query/healthcheck are the standalone read skills (they don't delegate to other skills).

## Definition of Done

1. **Vault resolution section in all 3 skills** — Each skill has a `## Vault Resolution` section (after Plugin Paths) that implements the 4-step precedence chain: `--vault` flag > CWD detection > default vault > error
2. **`--vault` flag works for preserve** — `/bedrock:preserve --vault my-vault <entities>` writes to the named vault regardless of CWD; all file paths and git commands use the resolved vault path
3. **`--vault` flag works for query** — `/bedrock:query --vault my-vault <question>` searches the named vault's entities regardless of CWD
4. **`--vault` flag works for healthcheck** — `/bedrock:healthcheck --vault my-vault` diagnoses the named vault regardless of CWD
5. **Git commands use `git -C`** — In preserve (the only git-writing skill of the 3), all git operations use `git -C <vault_path>` instead of assuming CWD. Healthcheck has no git writes. Query has no git operations.
6. **CWD detection works** — If the user is inside a registered vault directory (or subdirectory), the skill auto-resolves to that vault without requiring `--vault`
7. **No violations of skill-architecture pattern** — Phase numbering preserved; Plugin Paths section unchanged; Critical Rules table updated with vault resolution rules

## Scope

- **Vault Resolution boilerplate** — A standardized `## Vault Resolution` section added to each skill, placed immediately after `## Plugin Paths`. The section:
  1. Parses the skill's input arguments for `--vault <name>`
  2. If found: reads `<base_dir>/../../vaults.json`, looks up the name, sets `VAULT_PATH`
  3. If not found: checks if CWD is inside any registered vault path (prefix match on registered paths)
  4. If not found: reads the default vault from `vaults.json`, sets `VAULT_PATH`
  5. If no resolution: error message listing available vaults and instructions
  6. Validates `VAULT_PATH` exists on disk
  7. Reads `.bedrock/config.json` from `VAULT_PATH` (for git strategy, language, etc.)

- **`skills/preserve/SKILL.md`** (edit) — Add Vault Resolution section. Replace all CWD-relative entity paths (`actors/`, `people/`, etc.) with `<VAULT_PATH>/actors/`, etc. Replace `git pull --rebase origin main` with `git -C <VAULT_PATH> pull --rebase origin main`. Same for `git add`, `git commit`, `git push`. Replace `.bedrock/config.json` reads with `<VAULT_PATH>/.bedrock/config.json`.

- **`skills/query/SKILL.md`** (edit) — Add Vault Resolution section. Replace entity Glob/Grep paths (e.g., `actors/<term>*.md`) with `<VAULT_PATH>/actors/<term>*.md`. No git operations to change.

- **`skills/healthcheck/SKILL.md`** (edit) — Add Vault Resolution section. Replace entity Glob paths (e.g., `actors/*.md`, `actors/*/*.md`) with `<VAULT_PATH>/actors/*.md`. No git operations (read-only skill).

## Anti-scope

- Vault resolution in teach, compress, sync — that's Part 3
- Changes to the vault resolution precedence chain itself (defined in Part 1's CLAUDE.md)
- Any behavioral changes to how preserve, query, or healthcheck work beyond path resolution
- Multi-vault queries (searching across vaults)

## Technical Decisions

| Decision | Choice | Trade-off |
|---|---|---|
| Vault resolution as skill-level section, not a shared include | Duplicated boilerplate in each SKILL.md | Pro: each skill is self-contained (Claude Code loads one skill at a time, no shared module system). Con: ~20 lines duplicated per skill. This is the only viable approach given the plugin architecture — skills are independent markdown files with no import mechanism. |
| `VAULT_PATH` variable naming | Consistent across all skills | Pro: easy to search-replace and audit. Con: none — it's an internal convention. |
| CWD detection via prefix match | Check if CWD starts with any registered vault's absolute path | Pro: works from subdirectories (e.g., `cd my-vault/actors` still resolves). Con: could false-match if one vault path is a prefix of another (e.g., `/vaults/a` and `/vaults/ab`). Mitigation: use longest-match. |
| Preserve git commands all use `git -C` | Uniform pattern, no `cd` into vault | Pro: predictable, easy to audit. Con: slightly more verbose. Worth it for consistency. |

## Applicable Patterns

- **Skill Architecture** (`.vibeflow/patterns/skill-architecture.md`) — Vault Resolution section is added as a new mandatory section; phase numbering must shift if a new phase is needed (Phase 0 in preserve is currently `git pull` — it becomes vault resolution + git pull)
- **Skill Delegation** (`.vibeflow/patterns/skill-delegation.md`) — When other skills delegate to preserve, they must pass `--vault` through. Since Part 3 handles teach/compress/sync, the delegation contract doesn't change in this part.
- **Vault Writing Rules** (`.vibeflow/patterns/vault-writing-rules.md`) — Git conventions remain the same; only the invocation changes (`git -C`). Commit messages, branch naming, strategy selection unchanged.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Stale `vaults.json` (vault moved/deleted) | Medium | Low — skill errors clearly | Vault Resolution validates path exists; error message suggests re-running `/bedrock:setup` |
| Path resolution ambiguity (nested vault dirs) | Very low | Medium | Use longest-match for CWD detection |
| Preserve git -C breaks on repos with unusual configs | Very low | High — writes fail | Test with a standard Obsidian vault git repo; `git -C` is well-supported |
| Boilerplate drift between skills | Medium | Low — cosmetic inconsistency | Part 1's CLAUDE.md documents the canonical boilerplate; auditable via `/vibeflow:audit` |
