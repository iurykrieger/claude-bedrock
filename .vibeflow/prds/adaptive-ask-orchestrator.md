# PRD: Adaptive Context Orchestrator for /bedrock:ask

> Generated via /vibeflow:discover on 2026-04-15

## Problem

The current `/bedrock:ask` implementation always fires graphify calls — even for simple factual questions like "who owns billing-api?" that could be answered by reading a single vault file. This wastes tokens, adds latency, and makes every question feel heavyweight. The skill decomposes questions into sub-queries and executes up to 3 graphify calls by default, regardless of complexity.

Additionally, when the answer points to remote content (a Confluence page URL, an uningested GitHub repo), the skill can only suggest the user run `/bedrock:teach` manually — it cannot close the loop by internalizing the content and continuing to answer.

Users experience slow, expensive responses for simple questions and dead-end responses for questions that require remote content.

## Target Audience

Users of the Bedrock Claude Code plugin who invoke `/bedrock:ask` to get answers from their vault — engineers, tech leads, and PMs navigating shared knowledge.

## Proposed Solution

Redesign `/bedrock:ask` as an **adaptive context orchestrator** with a "vault-first, escalate-when-needed" approach:

1. **Always start with vault-only search.** For every question, do a lightweight vault search first (Glob/Grep by filename/alias, read entities, follow wikilinks). This is cheap and fast.

2. **LLM self-assessment after vault read.** After reading vault content, the agent evaluates: "Do I have enough context to answer this question well?" This is not a heuristic rule table — the LLM uses its own judgment based on the content it has read and the question asked.

3. **Escalate only when needed:**
   - If vault content is sufficient → compose answer directly (no graphify).
   - If the question requires deeper graph understanding (code-level relationships, cross-domain dependencies, architectural paths) → invoke graphify.
   - If the answer points to remote content that isn't in the vault → delegate to `/teach` to internalize it, wait for completion, then continue answering.

4. **`/teach` delegation preserves read-only boundary.** `/ask` invokes `/teach` via the Skill tool. `/teach` handles its own user confirmation and preserve flow. `/ask` remains architecturally read-only — it delegates writes, it doesn't perform them.

## Success Criteria

- Simple factual questions ("who owns X?", "what is the status of Y?") are answered without any graphify calls — using vault content alone.
- Complex questions still get graphify-enhanced answers when needed.
- When remote content is referenced but not ingested, `/ask` delegates to `/teach` and continues answering with the newly ingested content — closing the loop in a single interaction.
- Token usage for simple questions drops significantly compared to the current always-graphify approach.

## Scope v0

- Rewrite Phase 1 + Phase 2 of `/bedrock:ask` to implement the adaptive flow:
  - Phase 1: Analyze question (keep existing classification)
  - Phase 2: Always start with vault-only search (Glob/Grep, entity reads, wikilink traversal)
  - Phase 2.5 (new): LLM self-assessment — "Do I have enough context?" Decision point:
    - Sufficient → skip to Phase 4 (compose answer)
    - Needs graph → invoke graphify (1–N calls, configurable max), blend with vault reads, then Phase 4
    - Needs remote content → delegate to `/teach` via Skill tool, wait for ingestion, re-read the newly created entities, then continue
- Keep `query.max_graphify_calls` config (default 3) — only consumed when graphify is actually invoked
- Keep graph unavailable warning (fallback to vault-only when graph is missing)
- Keep existing Phases 3–6 (wikilink cross-reference, recency, external fetch, response composition)
- Update Critical Rules table to reflect the adaptive flow and `/teach` delegation

## Anti-scope

- No changes to `/graphify` — consumed as-is
- No changes to `/teach` or `/preserve` — consumed as-is via Skill tool delegation
- No heuristic rule tables for complexity classification — the LLM self-assesses
- No caching of graphify or vault results between invocations
- No automatic graph rebuilds
- No changes to other files (README, index.html, setup, etc.) — this is a SKILL.md-only rewrite
- `/ask` does NOT write files directly — all writes go through `/teach` → `/preserve`

## Technical Context

**Current skill:** `skills/ask/SKILL.md` (~522 lines), phases:
- Phase 0: Read config
- Phase 1: Analyze question (classify, decompose into sub-queries)
- Phase 2: Orchestrated search (always graphify-first with sequential fallback)
- Phase 2.5: Blend and post-process
- Phases 3–6: Wikilink cross-reference, recency, external fetch, response

**What changes:** The "decompose into sub-queries" step (Phase 1.4) and the "always-graphify" Phase 2 are replaced with:
- Vault-first search (always runs)
- LLM self-assessment (decision point)
- Conditional graphify escalation (only when needed)
- Conditional `/teach` delegation (only when remote content is needed)

**Patterns to follow:**
- `skill-architecture.md` — phased execution, Plugin Paths, Critical Rules
- `skill-delegation.md` — `/teach` is invoked via Skill tool, same pattern as teach → preserve
- `vault-writing-rules.md` — `/ask` remains read-only; writes are delegated

**Key constraint:** `/teach` invocation from `/ask` must go through the Skill tool. `/teach` owns its own user confirmation gate. `/ask` cannot bypass it.

## Open Questions

None.
