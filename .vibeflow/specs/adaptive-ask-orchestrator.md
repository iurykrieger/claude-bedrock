# Spec: Adaptive Context Orchestrator for /bedrock:ask

> Generated from: `.vibeflow/prds/adaptive-ask-orchestrator.md`
> Date: 2026-04-15

## Objective

Make `/bedrock:ask` vault-first and adaptive — simple questions are answered from vault content alone (zero graphify calls), graphify is invoked only when the LLM judges it necessary, and remote content is internalized via `/teach` delegation instead of producing dead-end suggestions.

## Context

`skills/ask/SKILL.md` (~522 lines) currently decomposes every question into sub-queries (Phase 1.4) and always fires graphify calls (Phase 2-G), falling back to sequential search only when the graph is unavailable. This means even "who owns billing-api?" — answerable by reading one vault file — triggers 1–3 graphify Skill invocations. The old Phase 5 (external fetch) could read remote URLs but only as read-only supplements — it couldn't internalize content into the vault.

The skill was just rewritten in the `rename-query-to-ask` PR, so there's no legacy baggage — this is a clean evolution of the adaptive orchestration approach.

## Definition of Done

1. Phase 2 implements vault-first search: for every question, the skill runs Glob/Grep + entity reads + 1-level wikilink follow **before** any graphify invocation or teach delegation
2. Phase 3 implements an LLM self-assessment decision point with three explicit outcomes: `vault_sufficient`, `needs_graphify`, or `needs_remote_content` — the assessment is based on the LLM's judgment of the content already read against the question, not a heuristic rule table
3. When outcome is `vault_sufficient`, the skill proceeds directly to response composition — zero graphify calls, zero teach delegations
4. When outcome is `needs_graphify`, the skill invokes graphify via Skill tool (up to `max_graphify_calls` from config), blends results with the vault reads already collected, then proceeds to response composition
5. When outcome is `needs_remote_content`, the skill delegates to `/teach` via Skill tool (passing the URL and a brief context), waits for completion, re-reads the newly created/updated entities, then proceeds to response composition
6. Skill structure follows the skill-architecture pattern: Plugin Paths section, phased execution, agent type declaration ("You are an adaptive context orchestrator agent"), Critical Rules table reflecting the vault-first principle and escalation rules

## Scope

### In

Rewrite `skills/ask/SKILL.md` with the following phase structure:

**Phase 0 — Read Configuration** (keep as-is)
- Read `query.max_graphify_calls` from `.bedrock/config.json` (default 3)

**Phase 1 — Analyze the Question** (simplify)
- Keep 1.1 (classify question), 1.2 (assess clarity), 1.3 (classification result)
- **Remove** 1.4 (decompose into sub-queries) — no longer needed; the LLM decides after reading content, not before

**Phase 2 — Vault-First Search** (rewrite — absorbs old Phase 2-S + old Phase 3)
- Always runs, regardless of graph availability
- 2.1: Read relevant entity definitions from plugin
- 2.2: Search entities by filename, alias, name, content (Glob/Grep)
- 2.3: Filter by domain (if identified in Phase 1)
- 2.4: Read found entities (limit: 15)
- 2.5: Follow wikilinks (1 level depth) for entities relevant to the question
- Output: a set of vault entities with their content, wikilinks, and any external URLs found

**Phase 3 — Context Assessment + Conditional Escalation** (NEW — core of this spec)
- **3.1 Self-Assessment:** The LLM evaluates whether the vault content from Phase 2 is sufficient to answer the question. Guidance for the assessment:
  - `vault_sufficient` — The question is factual/status/ownership and the vault entities contain a clear answer. Examples: "who owns X", "what's the status of Y", "what team manages Z", "what is X".
  - `needs_graphify` — The question involves code-level relationships, cross-domain dependencies, architectural paths, or the vault entities reference systems whose connections aren't explicit in the markdown. The LLM feels it's missing structural context that the knowledge graph could provide.
  - `needs_remote_content` — The vault entities reference external URLs (Confluence, GDocs, GitHub) that appear directly relevant to the question, but the content behind those URLs isn't ingested in the vault. The answer likely lives in that remote content.
  - When multiple outcomes apply (e.g., needs both graphify and remote content), prioritize: `needs_remote_content` > `needs_graphify` > `vault_sufficient`. Rationale: remote content must be internalized first for the vault to be complete; graphify can run on richer data after ingestion.

- **3-G Graphify Escalation** (when `needs_graphify`):
  - 3-G.0: Check graph availability (`graphify-out/graph.json`). If missing, display `> [!warning]` callout with `/graphify build` instruction and skip to response composition with vault-only content.
  - 3-G.1: Formulate 1–N graphify calls based on what's missing (same modes: `explain`, `query`, `path`). The LLM decides the calls based on the gap between what it has and what the question needs — not from a Phase 1 decomposition plan.
  - 3-G.2: Execute graphify calls sequentially via Skill tool (up to `max_graphify_calls`)
  - 3-G.3: Deduplicate and blend graphify results with vault reads from Phase 2
  - 3-G.4: If graphify results reveal remote URLs that need ingestion → escalate to 3-T

- **3-T Teach Delegation** (when `needs_remote_content`):
  - 3-T.1: Identify the URL(s) to ingest (limit: 2 URLs per ask invocation)
  - 3-T.2: For each URL, invoke `/bedrock:teach` via the Skill tool, passing:
    - The URL
    - Brief context: "Ingesting to answer: '<original question>'"
  - 3-T.3: `/teach` handles its own flow (fetch, extract, user confirmation, preserve). `/ask` waits for completion.
  - 3-T.4: After `/teach` completes, re-read the newly created/updated entities from the vault
  - 3-T.5: If `/teach` fails or the user declines, continue with available content. Best-effort — never block.

**Phase 4 — Prioritize by Recency** (keep as-is from current Phase 4)

**Phase 5 — Respond to the User** (keep as-is from current Phase 6, renumber)
- Same response composition rules, Zettelkasten hierarchy, fleeting note handling
- **Remove** old Phase 5 (external fetch via /confluence-to-markdown, /gdoc-to-markdown) — replaced by Phase 3-T teach delegation

**Critical Rules table** — Update to reflect:
- Vault-first principle (Phase 2 always runs before any escalation)
- LLM self-assessment (no heuristic rule tables)
- `/teach` delegation via Skill tool (never write directly)
- Best-effort for all escalations (graphify failure, teach failure = continue with available content)
- Limit: 15 entities, 2 teach delegation URLs per invocation

**Allowed-tools update:** Remove `mcp__plugin_github_github__*` from frontmatter — GitHub reads are now `/teach`'s concern. Keep: `Bash, Read, Glob, Grep, Skill, Agent`

### Out (anti-scope)

- No changes to `/graphify`, `/teach`, `/preserve`, or any other skill
- No heuristic rule tables for the self-assessment — LLM judgment only, with guidance
- No caching of results between invocations
- No automatic graph rebuilds
- No changes to README.md, CLAUDE.md, index.html, setup, teach — SKILL.md-only
- No direct file writes from `/ask` — all writes delegated through `/teach`
- No old-style external fetch (Phase 5 with /confluence-to-markdown, /gdoc-to-markdown) — fully replaced by /teach delegation

## Technical Decisions

### 1. Vault-first, then assess (not classify-then-route)

The previous approach classified the question first (Phase 1.4) and pre-planned graphify calls before reading any vault content. The new approach reads vault content first, then the LLM decides whether more context is needed. This is "try cheap first, escalate when needed."

**Trade-off:** Can't predict the execution path upfront — latency varies by question. But the common case (simple questions) gets dramatically faster, and the expensive path (graphify) is only triggered when needed. Net win on average token usage.

### 2. LLM self-assessment over heuristic rules

The decision to escalate is made by the LLM after reading vault content, not by a rule table in Phase 1. The spec provides guidance (what constitutes `vault_sufficient` vs `needs_graphify` vs `needs_remote_content`) but the LLM makes the call.

**Trade-off:** Less predictable than a rule table — the same question might take different paths depending on vault state. This is a feature: the skill adapts to what's actually in the vault, not what the question looks like in isolation.

### 3. `/teach` delegation replaces external fetch entirely

The old Phase 5 (external fetch via /confluence-to-markdown, /gdoc-to-markdown, GitHub MCP) is removed. When remote content is needed, `/ask` delegates to `/teach` which internalizes it — creating vault entities that persist for future questions.

**Trade-off:** First occurrence of a question requiring remote content is slower (teach is heavier than a quick fetch). But subsequent questions about the same topic are fast (content is now in the vault). This compounds — the vault gets richer over time.

### 4. Escalation priority: remote > graphify > sufficient

When multiple outcomes apply, remote content ingestion takes priority. Rationale: graphify operates on the vault's knowledge graph. If the vault is missing content, graphify will also miss it. Internalizing first gives graphify richer data to work with.

**Trade-off:** If the user just wants a quick partial answer, they'll have to wait for /teach. But the /teach confirmation gate gives them the option to decline.

## Applicable Patterns

- **skill-architecture.md** — YAML frontmatter, Plugin Paths section, phased execution, Critical Rules table. Phase 0 (config read) follows the existing pattern.
- **skill-delegation.md** — `/teach` delegation follows the same Skill tool invocation pattern as `teach → preserve`. `/ask` → `/teach` is a new delegation direction but uses the same mechanism.
- **vault-writing-rules.md** — `/ask` remains architecturally read-only. All writes flow through `/teach` → `/preserve`. The read-only agent declaration stays.

**New pattern introduced:** Adaptive escalation (vault-first → self-assess → conditional escalation). This is new to the plugin and may be documented as a pattern if other skills adopt it.

## Risks

| Risk | Mitigation |
|---|---|
| LLM self-assessment is inconsistent — sometimes escalates unnecessarily, sometimes doesn't escalate when it should | The guidance in Phase 3.1 defines clear examples for each outcome. The Critical Rules table reinforces the vault-first principle. Over time, the assessment calibrates as the skill is used. |
| `/teach` delegation makes some questions much slower (fetch + extract + confirm + preserve) | Best-effort: if teach fails or user declines, continue with available content. The confirmation gate gives users control. Limit of 2 URLs per invocation caps the worst case. |
| Removing GitHub MCP from allowed-tools means `/ask` can't read GitHub content at all without /teach | This is intentional — the old external fetch was read-only and ephemeral. /teach internalizes, which is better long-term. If users want quick GitHub reads without ingestion, they can use /teach directly. |
| Vault-first search for broad domain questions ("tell me about payments") reads many entities before deciding it needs graphify | Phase 2 retains the 15-entity limit. For broad questions, the LLM will likely hit the limit and assess `needs_graphify` quickly. |

## Dependencies

None — this rewrites `skills/ask/SKILL.md` which already exists from the rename-query-to-ask PR.
