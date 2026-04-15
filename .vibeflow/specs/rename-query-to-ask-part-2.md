# Spec: /bedrock:ask — Codebase Reference Updates (Part 2: Rename Propagation)

> Generated from: `.vibeflow/prds/rename-query-to-ask.md`
> Date: 2026-04-15

## Objective

Eliminate all remaining references to `/bedrock:query` and `skills/query` across the codebase so the rename to `/bedrock:ask` is complete and consistent.

## Context

Part 1 created `skills/ask/SKILL.md`, deleted `skills/query/`, and updated `CLAUDE.md`. But 4 other files still reference the old name: `README.md`, `skills/setup/SKILL.md`, `skills/teach/SKILL.md`, and `index.html`. These are all mechanical find-and-replace changes — no logic changes required.

## Definition of Done

1. `README.md` references `/bedrock:ask` in the skills table and architecture diagram (2 occurrences)
2. `skills/setup/SKILL.md` references `/bedrock:ask` in all 3 occurrences (skills table + onboarding instructions)
3. `skills/teach/SKILL.md` references `/bedrock:ask` instead of `/bedrock:query` (1 occurrence)
4. `index.html` skill card references `/bedrock:ask` with updated name and i18n key (1 occurrence)
5. Zero occurrences of the strings `/bedrock:query` or `skills/query` remain in the codebase (excluding `.vibeflow/` analysis/audit files and git history)

## Scope

### In
- `README.md` — Replace `/bedrock:query` in skills table (line ~67) and architecture diagram (line ~95)
- `skills/setup/SKILL.md` — Replace `/bedrock:query` at line ~540 (skills table), line ~1082 (onboarding instruction), line ~1083 (example command)
- `skills/teach/SKILL.md` — Replace `/bedrock:query` at line ~254 (mention of query for graph traversal)
- `index.html` — Replace `/bedrock:query` at line ~532 (skill card name), update `data-i18n` key if it uses `sk_query`

### Out (anti-scope)
- No `.vibeflow/` file updates — those are analysis output, updated by `/vibeflow:analyze`
- No content or logic changes — purely mechanical string replacement
- No changes to `CLAUDE.md` or `skills/ask/SKILL.md` (handled in Part 1)

## Technical Decisions

### 1. Keep `data-i18n="sk_query"` key as `sk_ask` (rename it)

The i18n key in `index.html` should match the skill name for consistency. Rename `sk_query` → `sk_ask`. Since the landing page is a single-file HTML with inline translations, this is a safe rename.

**Trade-off:** If external translation files reference `sk_query`, they'd break. But the landing page uses inline `data-i18n` with no external translation system — safe.

## Applicable Patterns

- **vault-writing-rules.md** — Bare wikilinks, kebab-case naming. Not directly exercised here (no vault entity writes), but the rename must preserve these conventions in any example text that mentions the skill.

## Risks

| Risk | Mitigation |
|---|---|
| Missed occurrences | DoD check 5 enforces a final grep sweep for zero remaining references |
| Line numbers shifted since analysis | Use content-based matching (Grep for the string), not line numbers |

## Dependencies

- `.vibeflow/specs/rename-query-to-ask-part-1.md` — Part 1 must be completed first (skill must exist as `ask` before references are updated)
