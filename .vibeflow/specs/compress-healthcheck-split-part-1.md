# Spec: /bedrock:compress Rewrite — Vault Alignment Engine (Part 1 of 2)

> Source PRD: `.vibeflow/prds/compress-healthcheck-split.md`
> Generated: 2026-04-15

## Objective

Replace the current `/bedrock:compress` skill with a focused vault alignment engine that detects and fixes 5 types of structural misalignments, delegates all writes to `/bedrock:preserve`, and supports tiered autonomy for scheduled execution.

## Context

The current `skills/compress/SKILL.md` (456 lines) mixes two responsibilities: duplicate-claim consolidation and health reporting. It also writes entities directly (bypassing `/bedrock:preserve`), which is a known anti-pattern documented in `.vibeflow/patterns/skill-delegation.md`. The rewrite strips all health reporting logic (moved to Part 2: `/bedrock:healthcheck`) and replaces the duplicate-claim consolidation with 5 alignment capabilities that cover the gaps the current skill misses: broken backlinks, concept fragmentation, entity miscategorization, undiscovered entities, and misnamed entities.

The tiered autonomy model enables scheduling via `/schedule`: mechanical fixes (backlinks, missing entities) run autonomously; semantic fixes (concept match, recategorization, entity merge) are detected but queued as fleeting notes for human review.

## Definition of Done

1. `skills/compress/SKILL.md` is fully rewritten with all 5 alignment capabilities: (1) broken backlinks, (2) concept match, (3) entity misalignment, (4) duplicated entities, (5) misnamed entities — each with explicit detection logic and fix procedure
2. Tiered autonomy model is implemented: capabilities 1 and 4 are marked as autonomous (no confirmation needed in cron mode); capabilities 2, 3, and 5 are marked as queued (written to a fleeting note in cron mode, confirmation-gated in interactive mode)
3. All entity writes are delegated to `/bedrock:preserve` via the Skill tool — compress NEVER uses Write/Edit on entity files directly
4. SKILL.md follows the skill architecture pattern: YAML frontmatter (`name`, `description`, `user_invocable`, `allowed-tools`), Plugin Paths section, Overview with agent type, numbered phases, critical rules table
5. `CLAUDE.md` skills table is updated to reflect the new compress description (alignment engine, not consolidation/health)
6. No health reporting logic remains in compress — no orphan checks, no stale-entity checks, no graph integrity checks, no dangling content checks

## Scope

### Files touched (2)
1. `skills/compress/SKILL.md` — complete rewrite
2. `CLAUDE.md` — update compress row in the skills table

### What's in
- **Capability 1 — Broken backlinks:** Scan all entities. For each wikilink `[[B]]` found in entity A (body or frontmatter arrays), verify that B has a backlink to A. If not, register as broken. Fix: delegate to `/bedrock:preserve` with action `update` to add the missing backlink in B.
- **Capability 2 — Concept match:** Scan entity bodies for recurring terms/phrases that appear in 3+ entities without a corresponding `concept` entity. Read `entities/concept.md` to validate that the detected term meets concept criteria (timeless, definitional, actor-independent). Fix: delegate to `/bedrock:preserve` with action `create` for a new concept entity, and `update` for each referencing entity to add the wikilink.
- **Capability 3 — Entity misalignment:** For each entity, read its frontmatter `type` field. Read the corresponding entity definition from `entities/<type>.md`. Evaluate the entity's content against the "When to create" and "When NOT to create" criteria. If a different type scores higher, flag as misaligned. Fix: delegate to `/bedrock:preserve` to create the entity under the correct type and mark the original as `promoted` (for fleeting) or add a consolidation callout pointing to the new entity.
- **Capability 4 — Duplicated entities:** Scan all entity bodies for proper nouns, service names, team names, and person names that are mentioned 3+ times across different files but have no corresponding entity file. Fix: delegate to `/bedrock:preserve` with action `create` and link all referencing entities.
- **Capability 5 — Misnamed entities:** Scan for name variants of the same real-world entity (e.g., "Iury" and "Iury Krieger", "billing-api" and "BillingAPI"). Use frontmatter `aliases` to check for known variants. When the same entity is referenced by different names without a shared wikilink target, flag as misnamed. Fix: choose the canonical name (kebab-case for the filename, readable for the alias), merge content into the canonical entity via `/bedrock:preserve`, add variants to `aliases`.
- **Autonomy model:** Skill accepts an optional `--mode` argument: `interactive` (default, all 5 capabilities prompt for confirmation) or `cron` (capabilities 1,4 execute autonomously; capabilities 2,3,5 write proposals to `fleeting/YYYY-MM-DD-compress-proposals.md` via `/bedrock:preserve`).
- **Phase structure:** Phase 0 (git pull), Phase 1 (scan vault + detect all 5 misalignment types), Phase 2 (build proposal — summary table per capability), Phase 3 (user confirmation in interactive mode / autonomous+queue split in cron mode), Phase 4 (delegate to `/bedrock:preserve`), Phase 5 (git commit + push + final report).

## Anti-scope

- No health reporting (moved to `/bedrock:healthcheck` — Part 2)
- No graph integrity checks (graphify-out validation is healthcheck's responsibility)
- No orphan/stale/dangling entity checks (healthcheck's responsibility)
- No direct file writes — all entity mutations go through `/bedrock:preserve`
- No duplicate-claim consolidation (the old compress behavior is replaced, not preserved)
- No fleeting note promotion pipeline (capability 3 detects misalignment but the full promotion pipeline is handled by `/bedrock:preserve`)
- No custom thresholds (3+ mentions, 3+ entities are hardcoded in v0)

## Technical Decisions

### 1. Detection before action (two-pass architecture)
**Decision:** Phase 1 scans and detects ALL misalignments across all 5 capabilities before presenting anything. Phase 2 presents the full proposal. Phase 4 executes.
**Trade-off:** Requires holding the full scan in memory vs. incremental detect-and-fix. The two-pass approach gives the user a complete picture before any changes, which is critical for trust — especially for capabilities 2, 3, and 5 which involve judgment.
**Justification:** Consistent with how the current compress works (scan → propose → execute). The user confirmed this pattern works.

### 2. Cron mode via `--mode cron` argument
**Decision:** The skill detects its execution mode via an explicit `--mode` argument rather than auto-detecting whether it's running in a cron context.
**Trade-off:** Requires the `/schedule` invocation to pass `--mode cron` explicitly. Auto-detection would be more seamless but fragile (no reliable way to detect cron vs. interactive in Claude Code).
**Justification:** Explicit is better than implicit. The user sets up the schedule once and passes the flag.

### 3. Queued proposals as fleeting notes
**Decision:** In cron mode, semantic proposals (capabilities 2, 3, 5) are written as a single fleeting note `fleeting/YYYY-MM-DD-compress-proposals.md` via `/bedrock:preserve`.
**Trade-off:** Could use GitHub issues, a dedicated proposals directory, or inline callouts in existing entities instead. Fleeting notes are native to the vault and follow existing patterns (raw → reviewing → promoted/archived).
**Justification:** Fleeting notes are the vault's inbox by design (see `entities/fleeting.md`). A compress proposal is exactly "information that has not yet reached the threshold of a permanent change" — it fits the definition.

### 4. Entity definition consultation for capabilities 2 and 3
**Decision:** Compress reads `entities/<type>.md` definitions at runtime to validate concept detection (capability 2) and entity misalignment (capability 3).
**Trade-off:** Adds I/O overhead. Could hardcode heuristics instead.
**Justification:** Entity definitions are the authoritative reference for classification (per `patterns/entity-definition.md`). Hardcoding would diverge from the definitions as they evolve.

### 5. Delegation contract with `/bedrock:preserve`
**Decision:** Compress builds a structured entity list (the standard delegation contract from `patterns/skill-delegation.md`) and invokes `/bedrock:preserve` via the Skill tool. Source is always `compress`.
**Trade-off:** Preserve handles git commit/push, so compress's Phase 5 only handles the final report — not the commit itself.
**Justification:** Fixes the known anti-pattern. Aligns with the single-write-point pattern.

## Applicable Patterns

| Pattern | How it applies |
|---|---|
| `patterns/skill-architecture.md` | YAML frontmatter, Plugin Paths, phased execution, critical rules table |
| `patterns/skill-delegation.md` | All writes through `/bedrock:preserve`. Structured entity list as contract. No direct file writes. |
| `patterns/entity-definition.md` | Capabilities 2 and 3 read entity definitions to validate classification decisions |
| `patterns/vault-writing-rules.md` | Backlink rules (capability 1), append-only rules (capabilities 3, 5), wikilink format |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Capability 2 (concept match) generates too many false positives — common English words flagged as missing concepts | High | Medium | Filter against entity definitions' "When NOT to create" criteria. Require term to appear in 3+ entities AND match concept definition (timeless, definitional, actor-independent). Present all detections for user review. |
| Capability 5 (misnamed entities) incorrectly merges two genuinely different entities that happen to have similar names | Medium | High | Always present merge proposals with full context (both entity bodies). In cron mode, this is queued — never autonomous. The user makes the final call. |
| Capability 3 (entity misalignment) cascading — recategorizing one entity triggers a chain of related recategorizations | Low | Medium | Process one entity at a time. Do not re-scan after fixes in the same run. Users can run compress multiple times for iterative alignment. |
| `/bedrock:preserve` invocation with large entity lists slows down execution | Medium | Low | Batch entities by type when delegating. Preserve already supports batch input. |

## Dependencies

- None (Part 1 is independent — Part 2 can be implemented in any order)
