# Audit Report: ask-graph-index

> Audited: 2026-05-05
> Spec: `.vibeflow/specs/ask-graph-index.md`
> Implementation: `skills/ask/SKILL.md`

**Verdict: PASS**

---

### Tests

No test runner detected — this is a markdown-only project (Claude Code plugin consisting entirely of prompt files). Verification performed via static analysis of the skill text.

---

### DoD Checklist

- [x] **1. Phase 2 reads `graph.json` before any glob/grep** — `### 2.0 Check graph.json and score nodes` at line 161, before `### 2.1 Read entity definitions` at line 202. The bash availability check (lines 165–171) is the first operation of Phase 2. ✅

- [x] **2. LLM scoring instruction covers all three signals** — Lines 179–182: primary signal (label match), secondary signal (community resonance), boost (is_god_node: true). All three are present with clear priority ordering (Primary > Secondary > Boost). ✅

- [x] **3. Fallback path is explicit** — Line 195: "For each search term that produced **zero** matching graph nodes → proceed to steps 2.2–2.4 (glob/grep) for **that term only**." Per-term fallback — not per-query, as per spec Decision 3. ✅

- [x] **4. Phase 3-G escalation condition checks graph coverage, not just file existence** — `#### 3-G.0 Assess graph coverage` at line 350. Two-step assessment: Step 1 checks graph availability (from Phase 2.0 state); Step 2 evaluates coverage for the specific gap using nodes already collected in Phase 2.0. Live `/graphify` is only invoked when coverage is insufficient or when in doubt (soft gate preserved at line 372). ✅

- [x] **5. Nodes without `.md` counterparts are handled** — Lines 192–193: "If not found: record graph metadata only (label, community, relevant edge labels) — use this metadata in Phase 5 response to surface the concept even without a vault file." Also reflected in Phase 2.6 output (line 293): "Graph-only nodes: concepts/entities from `graph.json` with no vault `.md`". ✅

- [x] **6. Critical Rules table is updated** — Line 583: `| Graph-first in Phase 2 | Phase 2.0 always runs before glob/grep. grep is a fallback for search terms that produced no matching graph nodes, not the primary strategy. |` ✅

- [x] **7. No violations of conventions.md Don'ts** — No path-qualified wikilinks in new sections. No flat tags. Phase numbering sequential (2.0 → 2.1 → … → 2.6; 3-G.0 → 3-G.1 → … → 3-G.4). Critical Rules table at the end. YAML frontmatter keys in English. ✅

---

### Pattern Compliance

- [x] **patterns/skill-architecture.md** — YAML frontmatter present with `name`, `description`, `user_invocable: true`, `allowed-tools`. Plugin Paths section present. Overview with agent type declaration present. Phases sequential (0 → 1 → 2 → 3 → 4 → 5). Sub-phases use decimal notation throughout. Critical Rules table at end. Phase 2.0 inserted using decimal numbering without renumbering existing phases — exactly as required. ✅

- [x] **patterns/skill-delegation.md** — `/ask` remains a read-only agent (line 84: "You only READ — never write, edit, or delete files directly."). No write operations to `graph.json` or any vault file introduced. Graph reads via Bash check and Read tool only. New phases (2.0, 3-G.0) perform only read operations. ✅

---

### Convention Violations

None.

---

### Minor Observations (not DoD failures)

**Entity budget accounting across sub-phases:**

The 15-entity limit is stated in two places that don't reference each other:
- Phase 2.0 step 4 (line 184): "Select top N nodes (N ≤ 15, same limit as the current entity read budget)"
- Phase 2.5 (line 286): "Do not read more than 15 entities total (2.4 + 2.5 combined)"

The Phase 2.5 limit explicitly covers 2.4 + 2.5, but does not mention 2.0. In practice, graph nodes resolved in 2.0 consume the same read budget as grep results in 2.4. A future improvement could unify the budget language to "15 entities total across 2.0 + 2.4 + 2.5 combined." This is not a blocking issue — the spec explicitly states "N ≤ 15, same limit" in 2.0, which conveys the intent — but the unified total limit statement in 2.5 should eventually be updated for consistency.

**Overview section:**
Lines 78–81 still describe the skill as "vault-first approach" without mentioning the graph-first strategy. This is semantically correct (graph.json IS vault content), but a future pass could update the Overview to mention Phase 2.0 explicitly for discoverability.

---

### Budget

Files changed: **1** (`skills/ask/SKILL.md`) / ≤ 4 budget.

---

### Overall

All 7 DoD checks: **PASS**
Pattern compliance: **PASS**
Convention violations: **0**
Tests: **N/A (markdown-only project)**
Budget: **1/4**

**Ready to ship.**
