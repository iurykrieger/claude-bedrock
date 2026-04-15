# Spec: Configurable Git Strategy — Part 1 (Core Engine + Config)

> Generated via /vibeflow:gen-spec on 2026-04-15
> PRD: `.vibeflow/prds/configurable-git-strategy.md`
> Budget: ≤ 4 files | Part 1 of 2

## Objective

Vault owners can configure which git strategy Bedrock skills use when committing and pushing changes, starting with the primary write path (`/bedrock:preserve`) and vault initialization (`/bedrock:setup`).

## Context

Today, all writing skills hardcode a trunk-based git workflow: commit + push to `main` with rebase retry (max 2 attempts). The logic is duplicated in `skills/preserve/SKILL.md` (lines 528-551), `skills/compress/SKILL.md` (lines 392-413), and `skills/sync/SKILL.md` (lines 903-917). There is no configuration surface — `.bedrock/config.json` currently stores only language, preset, and domains.

This part introduces the strategy engine in the most critical path (preserve, which is the single write point for all entity operations) and the config schema (setup).

## Definition of Done

1. **Config schema expanded:** `.bedrock/config.json` schema in `skills/setup/SKILL.md` includes a `git` object with a `strategy` field accepting `"commit-push"`, `"commit-push-pr"`, or `"commit-only"`.
2. **Default is backwards-compatible:** When `git.strategy` is absent or set to `"commit-push"`, the preserve skill behaves identically to today's trunk-based workflow (commit + push to main + rebase retry).
3. **`commit-push-pr` works in preserve:** When strategy is `"commit-push-pr"`, the preserve skill creates a branch (`vault/<YYYY-MM-DD>-<slug>`), commits, pushes the branch, and opens a PR targeting `main` via `gh pr create`.
4. **`commit-only` works in preserve:** When strategy is `"commit-only"`, the preserve skill commits locally and does not push.
5. **Setup offers strategy selection:** `/bedrock:setup` includes a git strategy selection step (after language/preset) and persists the choice to `.bedrock/config.json`. Reconfigure mode also allows changing the strategy.
6. **No violations of conventions.md Don'ts:** No flat tags, no path-qualified wikilinks, no direct entity writes from detection skills. Skill structure follows the skill-architecture pattern.

## Scope

- **`skills/setup/SKILL.md`**: Add git strategy selection step in Phase 1 or 2. Update config schema in Phase 3.3 to include `git` block. Update reconfigure mode to support strategy changes. Update idempotency display to show current strategy.
- **`skills/preserve/SKILL.md`**: Replace hardcoded git workflow in Phase 6.2 with a strategy dispatcher that reads `.bedrock/config.json` and branches into the appropriate flow.

## Anti-scope

- Compress and sync skill updates (Part 2)
- CLAUDE.md documentation updates (Part 2)
- Custom branch naming templates
- PR reviewers, labels, assignees, auto-merge
- Per-skill strategy overrides
- GitLab/Bitbucket support
- Migration tooling for existing vaults

## Technical Decisions

### 1. Config schema shape

```json
{
  "version": "1.0.0",
  "language": "en-US",
  "preset": "engineering",
  "domains": ["payments", "checkout"],
  "git": {
    "strategy": "commit-push"
  },
  "initialized_at": "2026-04-15",
  "initialized_by": "init@agent"
}
```

**Why a nested `git` object?** Future extensibility (e.g., `git.target_branch`, `git.pr_template`) without polluting the top-level namespace. The `git` key is optional — absence means `commit-push` (backwards compat).

### 2. Branch naming for `commit-push-pr`

Convention: `vault/<YYYY-MM-DD>-<slug>` where `<slug>` is derived from the commit message (first entity name or "batch" for multi-entity commits).

Examples:
- `vault/2026-04-15-billing-api`
- `vault/2026-04-15-batch-7-entities`

**Why date-prefixed?** Avoids branch name collisions across runs. Keeps branches chronologically sortable. Matches the vault's date-centric entity naming patterns.

If a branch already exists (e.g., second run on the same day for the same entity), append a counter: `vault/2026-04-15-billing-api-2`.

### 3. PR creation

```bash
gh pr create --title "<commit message>" --body "Automated by /bedrock:preserve" --base main
```

**Why reuse commit message as PR title?** The commit convention (`vault(<type>): <verb> <name> [source: <source>]`) is already descriptive. No need for a separate PR title format.

**Why minimal PR body?** The commit diff is the content. Anti-scope explicitly excludes PR templates and metadata.

### 4. Config reading strategy

The preserve skill reads `.bedrock/config.json` once at the start of Phase 6 (git phase). If the file doesn't exist or lacks the `git` key, it defaults to `commit-push`. This is a single `cat .bedrock/config.json` check — no complex parsing.

### 5. `commit-only` skip logic

For `commit-only`, the skill commits and then outputs:
```
Git strategy: commit-only — changes committed locally. Use `git push` manually when ready.
```

No rebase retry logic needed since there's no push.

## Applicable Patterns

- **skill-architecture** — Phase structure, Plugin Paths, Critical Rules table must be maintained in edited skills
- **vault-writing-rules** — Git workflow section (dimension 6) is being evolved from a fixed rule to a configurable one; the convention itself must be updated in Part 2
- **skill-delegation** — Preserve remains the single write point; its git phase is the primary target

## Risks

| Risk | Mitigation |
|---|---|
| `gh` CLI not installed when user picks `commit-push-pr` | Check `which gh` at the start of the git phase. If missing, warn and fall back to `commit-push` with a message. |
| Branch name collisions | Date prefix + slug + counter suffix. Check `git branch --list vault/<date>-<slug>*` before creating. |
| Config file missing in older vaults | Default to `commit-push` when `.bedrock/config.json` is absent or lacks `git` key. |
| Rebase conflicts on PR branch | Not applicable — PR branches don't need rebase against main. The PR itself handles merge. |

## Dependencies

None — this is Part 1.
