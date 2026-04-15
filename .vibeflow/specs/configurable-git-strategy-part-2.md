# Spec: Configurable Git Strategy — Part 2 (Propagate + Docs)

> Generated via /vibeflow:gen-spec on 2026-04-15
> PRD: `.vibeflow/prds/configurable-git-strategy.md`
> Budget: ≤ 4 files | Part 2 of 2

## Objective

All writing skills (compress, sync) respect the vault's configured git strategy, and CLAUDE.md documents the 3 available strategies.

## Context

Part 1 introduced the git strategy config schema and implemented strategy dispatch in `/bedrock:preserve` and `/bedrock:setup`. However, two other skills — compress and sync — have their own independent git phases that still hardcode trunk-based push-to-main. This part propagates the same strategy dispatch to those skills and updates the project's CLAUDE.md to document the new configurable workflow.

**After Part 1, the state is:**
- `.bedrock/config.json` has a `git.strategy` field (3 valid values)
- `/bedrock:preserve` reads config and dispatches correctly
- `/bedrock:setup` offers strategy selection during initialization
- `/bedrock:compress` and `/bedrock:sync` still hardcode trunk-based push

## Definition of Done

1. **Compress reads config:** `skills/compress/SKILL.md` Phase 5 reads `.bedrock/config.json` and dispatches to the correct git strategy (same 3 strategies as preserve).
2. **Sync reads config:** `skills/sync/SKILL.md` Phase 5.4 reads `.bedrock/config.json` and dispatches to the correct git strategy (same 3 strategies as preserve).
3. **Fallback works:** When `.bedrock/config.json` is absent or lacks `git` key, both skills behave identically to today (commit + push to main).
4. **CLAUDE.md updated:** The "Git Workflow" section documents the 3 strategies, their behavior, and the config field. The trunk-based description becomes the default case, not the only case.
5. **Consistent strategy description:** The git workflow instructions in compress and sync match the structure and wording used in preserve (from Part 1), ensuring all 3 skills describe the strategies identically.

## Scope

- **`skills/compress/SKILL.md`**: Replace hardcoded git workflow in Phase 5 (lines ~392-413) with a strategy dispatcher that reads `.bedrock/config.json`. Same logic and branch naming as preserve.
- **`skills/sync/SKILL.md`**: Replace hardcoded git workflow in Phase 5.4 (lines ~903-917) with a strategy dispatcher that reads `.bedrock/config.json`. Same logic and branch naming as preserve.
- **`CLAUDE.md`**: Update the "Git Workflow" section to document: (a) the `git.strategy` config field, (b) the 3 strategies and their behavior, (c) branch naming convention for `commit-push-pr`.

## Anti-scope

- Changes to preserve or setup (already done in Part 1)
- Custom branch naming templates
- PR metadata (reviewers, labels, assignees)
- Per-skill strategy overrides
- Non-GitHub platforms
- Vibeflow pattern updates (vault-writing-rules will be updated by /vibeflow:analyze on next run)

## Technical Decisions

### 1. Identical dispatch block across skills

The strategy dispatch logic in compress and sync should mirror preserve's implementation exactly. This means copying the same conditional structure:

1. Read `.bedrock/config.json` (default to `commit-push` if missing/no `git` key)
2. Branch into:
   - `commit-push`: existing logic (commit + push main + rebase retry)
   - `commit-push-pr`: create branch, commit, push branch, `gh pr create`
   - `commit-only`: commit locally, skip push

**Why duplicate instead of abstracting?** Skills are markdown prompts, not executable code. There's no shared function mechanism. Each skill must contain self-sufficient instructions. The duplication is acceptable because the logic is small (~20 lines of bash per skill) and rarely changes.

### 2. Branch naming consistency

Compress and sync use the same branch naming convention as preserve: `vault/<YYYY-MM-DD>-<slug>`.

For compress: `vault/2026-04-15-compress-25-entities`
For sync: `vault/2026-04-15-sync-github-5-actors`

The slug is derived from each skill's existing commit message convention.

### 3. CLAUDE.md documentation structure

The current "Git Workflow" section in CLAUDE.md (4 bullet points) expands to include a strategy table:

```markdown
### Git Workflow

Bedrock supports 3 git strategies, configured via `.bedrock/config.json`:

| Strategy | Behavior | When to use |
|---|---|---|
| `commit-push` (default) | Commit + push to `main` + rebase retry | Solo vaults, trusted contributors |
| `commit-push-pr` | Commit to branch + push + open PR | Team vaults requiring review |
| `commit-only` | Commit locally, no push | Offline or local-only vaults |
```

Existing conventions (commit message format, max 2 retries) remain unchanged.

## Applicable Patterns

- **skill-architecture** — Phase structure and Critical Rules table must be maintained
- **vault-writing-rules** — Section 6 (Git Workflow) is being updated in CLAUDE.md
- **skill-delegation** — Compress has a known anti-pattern (direct writes); its git phase is separate from preserve's delegation. This spec only touches the git phase, not the write path.

## Risks

| Risk | Mitigation |
|---|---|
| Compress/sync strategy drifts from preserve | DoD check #5 enforces consistent wording. Code review should compare the 3 blocks. |
| CLAUDE.md becomes stale if strategies are added later | The strategies are defined in config schema (Part 1); CLAUDE.md is documentation only. |
| Sync skill's multiple modes (sources, people, github) each have git logic | Only the final git phase (5.4) needs updating — all modes converge to the same commit+push block. Verify during implementation. |

## Dependencies

- `.vibeflow/specs/configurable-git-strategy-part-1.md` — Config schema, preserve strategy dispatch, and setup selection must be implemented first.
