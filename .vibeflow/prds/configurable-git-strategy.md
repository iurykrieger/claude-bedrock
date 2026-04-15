# PRD: Configurable Git Strategy

> Generated via /vibeflow:discover on 2026-04-15

## Problem

Today, all Bedrock skills that perform git operations (preserve, compress, sync) hardcode a trunk-based workflow: commit directly to `main`, push, and retry with rebase on conflict. This works well for single-user vaults but is problematic for shared/team vaults where direct pushes to `main` are undesirable — teams may require code review before merge, or vault owners may want local-only commits without any push.

There is no mechanism for vault owners to customize this behavior. The git strategy is buried deep inside each skill's execution phases, duplicated across 3 skills with no central configuration point.

## Target Audience

Bedrock plugin users who manage Obsidian vaults — specifically:
- **Team vault owners** who need PR-based review before changes land on `main`
- **Solo users** who want local-only commits (no push) for offline or private workflows
- **Existing users** who want the current trunk-based behavior to keep working unchanged

## Proposed Solution

Expand `.bedrock/config.json` with a `git` configuration block that lets vault owners choose one of three commit/push strategies. All skills that perform git operations read this config and follow the selected strategy instead of hardcoding trunk-based push.

Three strategies:
1. **`commit-push`** (default) — Current behavior. Commit + push directly to `main` with rebase retry. Backwards compatible.
2. **`commit-push-pr`** — Commit to a dedicated branch, push the branch, open a pull request targeting `main`. Branch name and PR title derived from the commit message convention.
3. **`commit-only`** — Commit locally, do not push. For offline or local-only vaults.

## Success Criteria

- Existing vaults with no `git` config in `.bedrock/config.json` behave exactly as today (`commit-push` to `main`).
- A vault configured with `commit-push-pr` creates a branch, pushes it, and opens a PR for every skill-triggered git operation.
- A vault configured with `commit-only` commits locally and never pushes.
- All 3 writing skills (preserve, compress, sync) respect the configured strategy.
- `/bedrock:setup` offers the git strategy choice during vault initialization and persists it in config.

## Scope v0

- Add `git.strategy` field to `.bedrock/config.json` schema (values: `commit-push`, `commit-push-pr`, `commit-only`)
- Define branch naming convention for `commit-push-pr` (e.g., `vault/<timestamp>-<slug>`)
- Update `skills/preserve/SKILL.md` git phase to read config and dispatch to the correct strategy
- Update `skills/compress/SKILL.md` git phase to read config and dispatch to the correct strategy
- Update `skills/sync/SKILL.md` git phase to read config and dispatch to the correct strategy
- Update `skills/setup/SKILL.md` to include git strategy selection during initialization and write it to config
- Update `CLAUDE.md` git workflow section to document the 3 strategies

## Anti-scope

- **No custom branch naming patterns** — v0 uses a fixed convention, not user-configurable templates
- **No PR reviewers/labels/assignees** — v0 opens a bare PR, no GitHub workflow automation
- **No per-skill strategy override** — v0 is vault-wide, not per-skill
- **No merge strategy config** — PRs are opened, not auto-merged
- **No GitLab/Bitbucket support** — v0 assumes GitHub (`gh` CLI) for PR creation
- **No migration tooling** — existing vaults without the field simply get the default behavior

## Technical Context

**Current config schema** (from `skills/setup/SKILL.md:419-429`):
```json
{
  "version": "1.0.0",
  "language": "<VAULT_LANGUAGE>",
  "preset": "<selected preset name>",
  "domains": ["<domain1>", "<domain2>"],
  "initialized_at": "<YYYY-MM-DD>",
  "initialized_by": "init@agent"
}
```

**Git operations live in 3 skills:**
- `skills/preserve/SKILL.md` (lines ~528-550) — main write path
- `skills/compress/SKILL.md` (lines ~392-411) — post-compression commit
- `skills/sync/SKILL.md` (lines ~903-914) — post-sync commit

All three duplicate the same trunk-based logic (commit, push, rebase retry). The new strategy should be defined once and referenced by all three — either via inline instructions in each skill or a shared convention described in CLAUDE.md.

**Dependencies:**
- `gh` CLI required for `commit-push-pr` strategy (PR creation)
- `git` CLI for all strategies (already required)

**Patterns to follow:**
- Config is read at the start of each skill via `.bedrock/config.json` (setup skill already defines this pattern)
- Skill delegation pattern: preserve is the single write point, but compress and sync have their own git phases

## Open Questions

None.
