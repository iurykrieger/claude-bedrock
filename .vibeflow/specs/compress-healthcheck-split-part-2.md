# Spec: /bedrock:healthcheck — Vault Health Report (Part 2 of 2)

> Source PRD: `.vibeflow/prds/compress-healthcheck-split.md`
> Generated: 2026-04-15

## Objective

Create a new read-only `/bedrock:healthcheck` skill that produces a diagnostic report of vault health without modifying any files, enabling safe and frequent vault audits.

## Context

The current `/bedrock:compress` bundles health reporting (Phase 1.5 graph integrity + Phase 4.2 health report) with mutation logic. This means users cannot get a vault health overview without also triggering the consolidation workflow. Part 1 strips all health reporting from compress. This spec (Part 2) creates a dedicated, read-only skill that owns all diagnostic checks.

The healthcheck skill is designed to run at any frequency — interactively, on a cron, or as a pre-flight check before other skills. It never writes, never commits, and never requires confirmation. Its output is actionable: it tells you what's wrong and which skill to run to fix it.

## Definition of Done

1. `skills/healthcheck/SKILL.md` exists and implements all 5 checks: (1) graphify-out validation, (2) setup verification, (3) orphan entities, (4) dangling content, (5) old content (>15 days)
2. The skill is strictly read-only — it uses ONLY read tools (`Bash`, `Read`, `Glob`, `Grep`) and NEVER uses `Write`, `Edit`, `Skill`, or `Agent`
3. SKILL.md follows the skill architecture pattern: YAML frontmatter (`name`, `description`, `user_invocable`, `allowed-tools`), Plugin Paths section, Overview with agent type declaration ("read-only agent"), numbered phases, critical rules table
4. `CLAUDE.md` skills table includes a new row for `/bedrock:healthcheck` with accurate description
5. No mutation logic in healthcheck — no git operations, no entity writes, no file modifications. Suggestions to run `/bedrock:compress` or `/bedrock:teach` are text-only (never invocations).

## Scope

### Files touched (2)
1. `skills/healthcheck/SKILL.md` — new file
2. `CLAUDE.md` — add healthcheck row to skills table

### What's in

- **Check 1 — graphify-out:** Verify `graphify-out/` directory exists. If yes: verify `graph.json` exists, is valid JSON, and contains nodes. Report node count, code node count, last modification date. Flag if stale (>30 days). If directory or file is missing: report "Not found. Run `/bedrock:teach` on an actor repository to generate."
- **Check 2 — Setup:** Verify all expected directories exist (`actors/`, `people/`, `teams/`, `topics/`, `discussions/`, `projects/`, `fleeting/`, `concepts/`). Verify each directory has a `_template.md`. Verify entity definitions exist in the plugin directory (`entities/*.md`). Verify `.claude-plugin/plugin.json` exists and is valid JSON. Report missing items.
- **Check 3 — Orphan entities:** For each entity file across all directories, count inbound wikilinks from other entity files (Grep for `[[entity-name]]` across the vault). Entities with 0 inbound links are orphans. Exclude templates. Report orphan count per type and list entity names.
- **Check 4 — Dangling content:** Identify entities that have: (a) no inbound wikilinks (orphan), AND (b) no outbound wikilinks in the body, AND (c) no frontmatter relation arrays with values. These are fully disconnected — they exist in the vault but participate in no relationships. Report separately from orphans (dangling is a strict subset of orphans).
- **Check 5 — Old content:** For each entity, read `updated_at` from frontmatter. Flag entities where `updated_at` is older than 15 days from the current date. Report count per type and list entity names sorted by age (oldest first).

- **Output format:** Markdown summary table printed to the terminal:

```markdown
## /bedrock:healthcheck — Report

| Check | Status | Count | Details |
|---|---|---|---|
| graphify-out | OK / WARN / MISSING | N nodes | Last updated: YYYY-MM-DD |
| Setup | OK / WARN | N issues | Missing: ... |
| Orphan entities | OK / WARN | N orphans | actors: 2, people: 1, ... |
| Dangling content | OK / WARN | N dangling | [[entity-1]], [[entity-2]], ... |
| Old content (>15d) | OK / WARN | N stale | Oldest: [[entity-3]] (45d) |

### Suggestions
- Run `/bedrock:compress` to fix N alignment issues
- Run `/bedrock:teach` to regenerate graphify-out
- Review N stale entities for relevance
```

- **Phase structure:** Phase 1 (scan vault — read all entity files, extract frontmatter and wikilinks), Phase 2 (run all 5 checks against the scan data), Phase 3 (generate and display report).

## Anti-scope

- No writes — healthcheck never modifies files, never commits, never pushes
- No skill invocations — healthcheck never calls `/bedrock:compress`, `/bedrock:teach`, or `/bedrock:preserve`. It suggests; it doesn't act.
- No subagents — all checks run sequentially in a single agent context (vault scans are fast for read-only operations)
- No graph integrity cross-validation (code entity vs. graph.json node matching). That level of detail was in the old compress; in the new split, compress owns alignment and healthcheck owns high-level diagnostics. Healthcheck checks if graph.json exists and is fresh — not whether individual nodes match vault entities.
- No configurable thresholds — 15 days (old content) and 30 days (stale graph) are hardcoded in v0
- No persistent report files — output is terminal-only. Users can copy/paste or redirect if needed.

## Technical Decisions

### 1. Read-only tool restriction
**Decision:** `allowed-tools` is restricted to `Bash, Read, Glob, Grep` — no `Write`, `Edit`, `Skill`, or `Agent`.
**Trade-off:** Cannot parallelize checks via subagents. Cannot write reports to files.
**Justification:** The read-only guarantee is the core value proposition. If healthcheck can write, users lose trust in running it freely. Terminal output is sufficient — the report is consumed immediately, not stored.

### 2. Single-pass scan shared across checks
**Decision:** Phase 1 scans the entire vault once and stores the data in memory. Phases 2's five checks all operate on the same scan data.
**Trade-off:** Phase 1 may be slow on very large vaults (500+ entities).
**Justification:** Multiple passes would be slower. A single scan ensures consistency — all checks see the same vault state. For vaults under 500 entities (typical Bedrock vaults), this is fast.

### 3. Dangling as a strict subset of orphans
**Decision:** Dangling content is defined as orphan + no outbound links + no frontmatter relations. It's a severity escalation, not a separate category.
**Trade-off:** Could define dangling differently (e.g., entities with no meaningful body content).
**Justification:** The structural definition (no inbound, no outbound, no relations) is deterministic and unambiguous. Content quality assessment would require semantic judgment, which belongs in compress, not healthcheck.

### 4. Status column with OK / WARN / MISSING
**Decision:** Each check reports a status: `OK` (no issues), `WARN` (issues found), `MISSING` (prerequisite not met, e.g., graphify-out absent).
**Trade-off:** No `ERROR` state — healthcheck itself never fails, it just reports what it finds.
**Justification:** A diagnostic tool should always produce output. If a directory doesn't exist, that's a finding, not an error.

### 5. 15-day threshold for old content
**Decision:** Entities with `updated_at` older than 15 days are flagged.
**Trade-off:** 15 days is aggressive — the old compress used 60 days. May produce noise for stable entities (concepts, established actors).
**Justification:** The user explicitly requested 15 days. For stable entities, the suggestion is to "review for relevance" — not to delete or modify. The threshold nudges regular vault maintenance.

## Applicable Patterns

| Pattern | How it applies |
|---|---|
| `patterns/skill-architecture.md` | YAML frontmatter, Plugin Paths, phased execution, critical rules table. Agent type: "read-only agent" |
| `patterns/entity-definition.md` | Orphan and dangling checks need to know which directories contain entities and which files are templates (to exclude them) |
| `patterns/vault-writing-rules.md` | Wikilink format (`[[bare-name]]`) used for parsing inbound/outbound links during scan |

**New pattern note:** This is the first read-only skill in the Bedrock plugin. If the pattern proves useful, consider documenting a "read-only skill" sub-pattern in `.vibeflow/patterns/`.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 15-day threshold generates excessive noise for stable entities (concepts, long-lived actors) | High | Low | Report is advisory — no action is forced. Users learn to filter. Threshold can be adjusted in a future version. |
| Orphan check false positives — newly created entities that haven't been linked yet | Medium | Low | Orphan status is a finding, not a defect. The suggestion is to review, not to delete. |
| Large vaults (500+ entities) make Phase 1 scan slow | Low | Medium | Bedrock vaults are typically under 200 entities. If this becomes a problem, Phase 1 can be optimized with parallel reads per directory. |

## Dependencies

- None (Part 2 is independent — Part 1 can be implemented in any order)
