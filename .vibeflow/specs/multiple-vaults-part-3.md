# Spec: Multiple Vaults — Part 3: Vault Resolution in Detection Skills

> Source PRD: `.vibeflow/prds/multiple-vaults.md`
> Generated via /vibeflow:gen-spec on 2026-04-15

## Dependencies

- `.vibeflow/specs/multiple-vaults-part-1.md` — Registry must exist
- `.vibeflow/specs/multiple-vaults-part-2.md` — Preserve must be vault-aware (detection skills delegate to it)

## Objective

The 3 detection skills (teach, compress, sync) resolve vault paths through the global registry and pass `--vault` through to preserve when delegating, completing multi-vault support across all skills.

## Context

After Part 2, the core skills (preserve, query, healthcheck) are vault-aware. The remaining 3 skills are "detection" skills — they analyze content, detect entities, and delegate writes to preserve. They need vault resolution for two reasons:

1. **Reading vault state** — teach reads existing entities for matching; compress reads all entities for deduplication; sync reads entities and external sources for reconciliation.
2. **Delegating to preserve** — when invoking `/bedrock:preserve` via the Skill tool, they must pass `--vault <name>` so preserve knows which vault to write to.

Additionally, sync and compress have their own git operations (Phase 0 `git pull`, final phase `git commit/push`) that need `git -C` treatment. Teach delegates all git to preserve.

## Definition of Done

1. **Vault resolution section in all 3 skills** — Each skill has a `## Vault Resolution` section implementing the same 4-step precedence chain as Part 2
2. **`--vault` flag works for teach** — `/bedrock:teach --vault my-vault <URL>` ingests content into the named vault; the resolved vault name is passed through to preserve during delegation
3. **`--vault` flag works for compress** — `/bedrock:compress --vault my-vault` runs deduplication and consolidation against the named vault
4. **`--vault` flag works for sync** — `/bedrock:sync --vault my-vault --github` syncs the named vault with external sources
5. **Vault name propagated to preserve** — When teach, compress, or sync delegate to preserve, they pass `--vault <resolved_vault_name>` in the Skill invocation arguments. This ensures preserve resolves to the same vault.
6. **Git commands use `git -C` in sync and compress** — All `git pull`, `git add`, `git commit`, `git push` in sync (3 git blocks for sources/people/github modes) and compress use `git -C <VAULT_PATH>`
7. **No violations of skill-delegation pattern** — The structured entity list contract is unchanged; only the Skill invocation adds `--vault`. Detection skills still NEVER write entities directly.

## Scope

- **`skills/teach/SKILL.md`** (edit) — Add Vault Resolution section after Plugin Paths. Teach reads vault entities for matching (Phase 2) — these Glob/Grep paths need `<VAULT_PATH>` prefix. Phase 4 (delegate to preserve) must pass `--vault <name>` in the Skill tool call. Teach has no direct git operations (preserve handles git).

- **`skills/compress/SKILL.md`** (edit) — Add Vault Resolution section. Compress reads all entities in Phase 1 — Glob paths need `<VAULT_PATH>` prefix. Phase 0 `git pull --rebase origin main` becomes `git -C <VAULT_PATH> pull --rebase origin main`. Note: compress writes entities directly in Phase 4 (known anti-pattern from `.vibeflow/patterns/skill-delegation.md`) — these direct writes also need `<VAULT_PATH>` prefix. The `.bedrock/config.json` read for git strategy needs `<VAULT_PATH>` prefix.

- **`skills/sync/SKILL.md`** (edit) — Add Vault Resolution section. Sync has 3 modes (sources, people, github), each with their own git blocks. ALL `git pull/add/commit/push` commands across all 3 modes need `git -C <VAULT_PATH>`. Entity Glob/Grep paths need `<VAULT_PATH>` prefix. The 3 `.bedrock/config.json` reads (one per mode's git phase) need `<VAULT_PATH>` prefix. Delegation to preserve (in sources and people modes) must pass `--vault <name>`.

## Anti-scope

- Refactoring sync's 3 modes into separate files (known tech debt, not in scope)
- Fixing compress's direct-write anti-pattern (out of scope — just ensure paths are correct)
- Any behavioral changes beyond path resolution
- New sync modes or teach source types

## Technical Decisions

| Decision | Choice | Trade-off |
|---|---|---|
| Pass vault name (not path) to preserve | `--vault my-vault` not `--vault /abs/path` | Pro: preserve re-resolves from registry, ensuring consistency. Con: extra registry read. Negligible cost — a single JSON parse. |
| Sync's 3 git blocks all get `git -C` independently | No shared "git helper" | Pro: each mode remains self-contained and auditable. Con: 3x the mechanical change. Acceptable because sync is already 1,056 lines and introducing abstractions would increase complexity. |
| Compress direct writes use `<VAULT_PATH>` | Path-prefix the Write/Edit calls, not refactor to delegate | Pro: minimal change, doesn't widen scope. Con: doesn't fix the anti-pattern. Acceptable — fixing the anti-pattern is a separate task. |

## Applicable Patterns

- **Skill Architecture** (`.vibeflow/patterns/skill-architecture.md`) — Vault Resolution section follows same placement convention (after Plugin Paths). Phase numbering preserved.
- **Skill Delegation** (`.vibeflow/patterns/skill-delegation.md`) — The delegation contract gains one new field: `--vault <name>` is passed alongside the structured entity list when invoking preserve via the Skill tool. The entity list format itself is unchanged.
- **Vault Writing Rules** (`.vibeflow/patterns/vault-writing-rules.md`) — Git conventions (commit message format, strategy selection) unchanged. Only the command invocation changes (`git -C`).

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Sync's 3 git blocks are easy to miss one | High | Medium — one mode breaks | Grep for all `git ` commands in sync after editing; verify each has `-C <VAULT_PATH>` |
| Compress direct writes miss a path | Medium | Medium — writes to wrong location | Grep for all `Write`/`Edit` calls in compress; verify each uses `<VAULT_PATH>` prefix |
| Preserve vault resolution disagrees with caller | Low | High — writes to wrong vault | Pass vault name (not path) so preserve re-resolves from same registry |
| Teach vault read paths miss graphify output | Low | Medium — graphify matching fails | Check if graphify output paths are vault-relative or absolute; adjust if needed |
