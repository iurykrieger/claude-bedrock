## Audit Report: adaptive-ask-orchestrator

**Spec:** `.vibeflow/specs/adaptive-ask-orchestrator.md`
**Date:** 2026-04-15
**Verdict: PASS**

### DoD Checklist

- [x] **Check 1** — Phase 2 "Vault-First Search" (line 111) always runs for every question. Line 113: "This phase **always runs** for every question, regardless of graph availability." Sub-phases 2.1–2.5 implement Glob/Grep + entity reads + 1-level wikilink follow. Phase 3 (assessment + escalation) comes strictly after Phase 2. Critical Rules line 465 reinforces: "Phase 2 ALWAYS runs before any escalation." Evidence: `skills/ask/SKILL.md:111-209`
- [x] **Check 2** — Phase 3.1 "Self-Assessment" (line 218) implements LLM self-assessment with three explicit outcomes: `vault_sufficient` (line 223), `needs_graphify` (line 230), `needs_remote_content` (line 237). Each outcome has indicators and examples — no heuristic rule table. Priority defined at line 244–245. Critical Rules line 466: "not by a heuristic rule table." Evidence: `skills/ask/SKILL.md:218-254`
- [x] **Check 3** — When `vault_sufficient`, line 252: "skip directly to **Phase 4** (recency) then **Phase 5** (respond)." Phases 4 and 5 contain zero graphify or teach invocations — pure recency sorting and response composition. Evidence: `skills/ask/SKILL.md:252,380-457`
- [x] **Check 4** — Phase 3-G "Graphify Escalation" (line 258) invokes graphify via Skill tool (line 293–295) with structured JSON contract (lines 297–313), up to `max_graphify_calls` (line 291). Results are deduplicated and blended with Phase 2 vault reads (lines 319–324). Critical Rules line 470 enforces Skill tool usage. Evidence: `skills/ask/SKILL.md:258-329`
- [x] **Check 5** — Phase 3-T "Teach Delegation" (line 333) invokes `/bedrock:teach` via Skill tool (lines 349–362) passing URL + context. Re-reads newly created entities after completion (lines 364–369). Best-effort fallback on failure (lines 371–376). Limit of 2 URLs enforced at line 346. Critical Rules lines 469, 475 reinforce. Evidence: `skills/ask/SKILL.md:333-376`
- [x] **Check 6** — Plugin Paths section (line 19). Phased execution: Phase 0 (line 47), Phase 1 (line 67), Phase 2 (line 111), Phase 3 (line 213), Phase 4 (line 380), Phase 5 (line 403). Agent type declaration: line 39 "You are an adaptive context orchestrator agent." Critical Rules table at line 461 with 21 rules covering vault-first principle (465), LLM self-assessment (466), escalation priority (467), teach delegation (469), best-effort (473). Evidence: `skills/ask/SKILL.md:19,39,47,67,111,213,380,403,461`

### Pattern Compliance

- [x] **skill-architecture.md** — PASS. YAML frontmatter with `name`, `description`, `user_invocable`, `allowed-tools` (lines 1–14). Plugin Paths section (line 19). Overview with agent type declaration (line 39). Sequential phases 0–5. Critical Rules table at line 461. Allowed-tools simplified to `Bash, Read, Glob, Grep, Skill, Agent` per spec (GitHub MCP removed).
- [x] **skill-delegation.md** — PASS. `/graphify` invoked via Skill tool (line 295, Critical Rules line 470). `/bedrock:teach` invoked via Skill tool (lines 351–362, Critical Rules line 469). Both follow the same delegation mechanism as teach → preserve. New delegation direction (`/ask` → `/teach`) uses the established pattern.
- [x] **vault-writing-rules.md** — PASS. Read-only agent declaration at line 39. Line 41: "Writes happen exclusively through `/bedrock:teach` delegation." Critical Rules line 468: "`/ask` NEVER writes, edits, or deletes files directly." Bare wikilinks enforced (line 479). Sensitive data protection (line 482). `> [!warning]` callout follows vault conventions (line 274).

### Convention Violations

None found.

- File location: `skills/ask/SKILL.md` follows `skills/<name>/SKILL.md` convention
- Skill name: single lowercase word `ask`
- Phase numbering sequential with decimal sub-phases (2.1, 2.2, 3.1, 3-G.0, etc.)
- Old Phase 1.4 (sub-query decomposition) removed: 0 occurrences of `sub_query_plan` or `decompose into sub-queries`
- Old Phase 5 (external fetch) removed: 0 occurrences of `confluence-to-markdown`, `gdoc-to-markdown`, or `mcp__plugin_github` in the skill file
- No direct writes in the skill

### Tests

No test runner detected (markdown-only Claude Code plugin). Verify manually by invoking `/bedrock:ask` with:
1. A simple factual question ("who owns X?") — should answer from vault only, no graphify
2. A complex relationship question ("how does X connect to Y?") — should escalate to graphify
3. A question whose answer is behind an external URL in a vault entity — should delegate to /teach

### Budget

Files changed: 1 / ≤ 4 budget (`skills/ask/SKILL.md`)

### Anti-scope

All anti-scope items respected: YES
- No changes to `/graphify`, `/teach`, `/preserve`, or any other skill
- No changes to README.md, CLAUDE.md, index.html, setup, teach
- No heuristic rule tables — LLM judgment with guidance only
- No direct writes — all through /teach delegation
- Old external fetch fully removed, replaced by /teach delegation

### Overall: PASS
