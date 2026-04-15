## Audit Report: rename-query-to-ask-part-1

**Spec:** `.vibeflow/specs/rename-query-to-ask-part-1.md`
**Date:** 2026-04-15
**Verdict: PASS**

### DoD Checklist

- [x] **Check 1** — `skills/ask/SKILL.md` exists with `name: ask`, description mentioning orchestration/sub-queries/graphify, triggers `"bedrock ask"`, `"bedrock-ask"`, `"/bedrock:ask"`. Evidence: `skills/ask/SKILL.md:1-13`
- [x] **Check 2** — Phase 1.4 (lines 106–135) implements question decomposition with a rule table mapping question shapes to sub-query plans (explain, query, path modes). Phase 2-G (lines 154–216) executes sub-queries sequentially, accumulates nodes/edges, and deduplicates by id. Evidence: `skills/ask/SKILL.md:106-216`
- [x] **Check 3** — Phase 0 (lines 44–61) reads `query.max_graphify_calls` from `.bedrock/config.json`, defaults to 3 when config or field is absent, clamps to 1–5 range. Critical Rules table reinforces at line 503. Evidence: `skills/ask/SKILL.md:44-61,503`
- [x] **Check 4** — Phase 2-S (lines 218–225) displays `> [!warning] Knowledge graph unavailable` callout with explicit instruction: "Run `/graphify build` to rebuild the graph from the vault's actor repositories." Critical Rules table reinforces at line 505. Evidence: `skills/ask/SKILL.md:220-225,505`
- [x] **Check 5** — `CLAUDE.md` skills table at line 109 references `/bedrock:ask`. `skills/query/` directory is deleted (verified via filesystem check). Grep confirms 0 occurrences of `bedrock:query` in CLAUDE.md. Remaining references in `README.md`, `index.html`, `skills/setup/SKILL.md`, `skills/teach/SKILL.md` are explicitly Part 2 scope. Evidence: `CLAUDE.md:109`, filesystem check
- [x] **Check 6** — Plugin Paths section at line 18. Phased execution: Phase 0 (line 44), Phase 1 (line 64), Phase 2 (line 139), Phase 2.5 (line 295), Phase 3 (line 335), Phase 4 (line 374), Phase 5 (line 397), Phase 6 (line 439). Agent type declaration at line 37: "You are a query orchestrator agent." Critical Rules table at line 497 with 21 rules. Evidence: `skills/ask/SKILL.md:18,37,44,64,139,295,335,374,397,439,497`

### Pattern Compliance

- [x] **skill-architecture.md** — PASS. YAML frontmatter with `name`, `description`, `user_invocable`, `allowed-tools` (lines 1–14). Plugin Paths section (line 18). Overview with agent type (line 37). Sequential numbered phases 0–6 with decimal sub-phases. Critical Rules table at line 497. New Phase 0 (config read) follows the pattern's Phase 0 convention for pre-execution setup.
- [x] **skill-delegation.md** — PASS. Graphify invoked exclusively via Skill tool (lines 163–170). JSON output contract appended to every invocation (lines 174–189). Explicit "NEVER call graphify Python API directly" in both the IMPORTANT block (line 202) and Critical Rules table (line 502). Multiple invocations follow the same contract — consistent with teach→graphify pattern.
- [x] **vault-writing-rules.md** — PASS. Read-only agent: no Write/Edit in `allowed-tools`. Warning callout uses `> [!warning]` convention (line 222). Bare wikilinks enforced in Critical Rules (line 515). Vault language rule preserved (line 514).

### Convention Violations

None found.

- File location: `skills/ask/SKILL.md` follows `skills/<name>/SKILL.md` convention
- Skill name: single lowercase word `ask`
- Frontmatter keys in English
- Phase numbering sequential with decimal sub-phases
- No MCP calls via subagents (not in allowed-tools for subagents)
- No direct writes (read-only skill)

### Tests

No test runner detected (markdown-only Claude Code plugin — no package.json, pyproject.toml, or build system). Manual verification recommended: invoke `/bedrock:ask` against a vault with and without `graphify-out/graph.json` to confirm both paths work.

### Budget

Files changed: 2 / ≤ 4 budget (`skills/ask/SKILL.md` created, `CLAUDE.md` edited, `skills/query/` deleted)

### Anti-scope

All anti-scope items respected: YES
- `/graphify` — untouched
- `/bedrock:preserve`, `/bedrock:teach`, `/bedrock:compress`, `/bedrock:sync`, `/bedrock:setup` — untouched
- `README.md`, `index.html`, `skills/setup/SKILL.md`, `skills/teach/SKILL.md` — untouched (deferred to Part 2)
- No graphify result caching
- No automatic graph rebuilds

### Overall: PASS
