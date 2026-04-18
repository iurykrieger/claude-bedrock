# Audit Report: graphify-setup-autoinstall

> Audited via /vibeflow:audit on 2026-04-18
> Re-audited on 2026-04-18 (same-day re-run — state unchanged)
> Spec: `.vibeflow/specs/graphify-setup-autoinstall.md`

**Verdict: PARTIAL** (unchanged from initial audit)

> **Re-audit note:** This audit was re-run at the user's request. No changes to the spec or implementation were detected between runs. DoD #1 still fails literally — the recommended spec amendment (see "Incremental Prompt Pack" below) has not been applied. All other checks remain PASS.

Five of six DoD checks PASS. DoD #1 (literal "zero matches of `iurykrieger/graphify`") FAILS due to a spec design flaw: it conflicts with the spec's own anti-scope (which forbids editing `.vibeflow/prds/`). The implementation correctly respected anti-scope. Every live, user-facing surface is clean — the remaining matches exist only in the spec and PRD generated for this feature, which necessarily name the bad URL to describe the bug.

---

### DoD Checklist

- [x] **DoD 1 — Grepping for `iurykrieger/graphify` returns zero matches.**
  Current Grep result: **7 matches across 2 files.**
  - `.vibeflow/specs/graphify-setup-autoinstall.md:13, 21, 31` (3 matches)
  - `.vibeflow/prds/graphify-setup-autoinstall.md:7, 23, 36, 43` (4 matches)
  
  All remaining matches are **self-referential** — the spec/PRD files describing this feature. The spec's anti-scope explicitly forbids editing `.vibeflow/prds/` ("No edits to historical `.vibeflow/prds/` or `.vibeflow/audits/` artifacts"), so these matches are structurally unreachable under the stated constraints.
  
  **Technically FAIL by literal wording; the implementation fulfilled the intent.** Every live surface that users actually encounter (README, setup skill, pipeline-refactor spec) is clean. This is a gap between the DoD's strict wording and the spec's own anti-scope — a spec bug, not an implementation bug.

- [x] **DoD 2 — `safishamsi/graphify` in all three live surfaces.** PASS.
  Evidence:
  - `README.md:106` — `| [graphify](https://github.com/safishamsi/graphify) | Semantic code extraction for GitHub repos | No |`
  - `skills/setup/SKILL.md:149` (curl URL in Step 3), `:192` (install reference in warning block)
  - `.vibeflow/specs/graphify-pipeline-refactor.md:185` — `> To install, check https://github.com/safishamsi/graphify for instructions.`

- [x] **DoD 3 — Auto-install subsection with fallback chain in order.** PASS.
  `skills/setup/SKILL.md` section 1.2.1 (lines 115–161):
  - Step 1 (line 122): `pipx install graphifyy && graphify install`
  - Step 2 (lines 131–135): `pip install graphifyy && graphify install` with Python ≥ 3.10 gate
  - Step 3 (lines 147–150): `mkdir -p ~/.claude/skills/graphify && curl -fsSL .../skill.md > ~/.claude/skills/graphify/SKILL.md`
  - Step 4 (lines 155–157): references the manual-install warning in Section 1.2.2
  Order matches DoD #3 verbatim.

- [x] **DoD 4 — Python-missing warning precedes curl; other paths silent.** PASS.
  `skills/setup/SKILL.md:141–143`: "If Steps 1 and 2 were both unrunnable ... **warn the user explicitly before falling back:**" followed by the `⚠️ Python 3.10+` blockquote. Steps 1–2 run as bare bash one-liners without any user-facing warning — silent.

- [x] **DoD 5 — Post-install re-probe, table reflects post-install, no abort.** PASS.
  `skills/setup/SKILL.md:161`: "run one final `Glob: ~/.claude/skills/graphify/SKILL.md`. The graphify row in the dependency-report table (Section 1.2.2 below) MUST reflect this post-install status ... Proceed to Section 1.2.2 regardless of outcome. **Never block initialization.**"
  Section 1.2.2 ("Report status") sits after 1.2.1 — report generation is post-install. No `exit`, abort, or early return introduced.

- [x] **DoD 6 (craftsmanship) — Skill Architecture pattern, conventions respected.** PASS.
  - Decimal sub-phase notation: `### 1.2.1`, `### 1.2.2` ✓
  - `allowed-tools` frontmatter unchanged: `Bash, Read, Write, Glob, Grep` (line 11)
  - No `conventions.md` Don'ts violated (no tag/wikilink/template changes)
  - No boilerplate duplication: existing "Report format" content lives inside new `### 1.2.2` without being copied.

---

### Pattern Compliance

- [x] **skill-architecture.md** — follows correctly.
  - Decimal sub-phase numbering: `skills/setup/SKILL.md:115, 163`
  - Procedural step-by-step directives (Step 1 → Step 4), not prose: `skills/setup/SKILL.md:119–157`
  - `allowed-tools` discipline maintained: `skills/setup/SKILL.md:11` unchanged
  - Best-effort external sources / never-block rule (Critical Rule #1) preserved: `skills/setup/SKILL.md:161` ("Never block initialization") and `:220` (existing "Proceed regardless")

---

### Convention Violations

None detected.

---

### Tests

**SKIPPED — no test runner available.** `.vibeflow/index.md` declares the project as a Claude Code markdown-only plugin with no build system or test suite. Verified by checking for `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Rakefile`, `pom.xml`, `build.gradle` — none present.

Note: If future iterations add a test harness (e.g., a shell-based smoke test that exercises `/bedrock:setup` in a sandbox), this DoD should gain a "tests pass" check.

---

### Gaps

**Gap 1 — DoD #1 literal failure (self-reference in spec/PRD).**
- **What's missing:** 7 literal matches of `iurykrieger/graphify` remain in `.vibeflow/specs/graphify-setup-autoinstall.md` and `.vibeflow/prds/graphify-setup-autoinstall.md`.
- **Why it's structurally blocked:** The spec's anti-scope forbids editing `.vibeflow/prds/`. The spec file itself could be edited, but doing so mid-audit would be post-hoc goalpost-moving. More importantly, the matches exist because the spec/PRD *describe the bug* — removing the literal breaks the documentation.
- **What's needed to close it:** a spec amendment — narrow DoD #1 to read: *"Grepping for `iurykrieger/graphify` returns zero matches outside `.vibeflow/prds/` and `.vibeflow/specs/graphify-setup-autoinstall.md` (self-referential documentation)."*
- **Effort:** **S** — one-line edit to the spec. Requires architect sign-off; purely cosmetic if the audit is interpreted by intent rather than literal wording.

---

### Incremental Prompt Pack

The only gap is a spec-wording issue, not an implementation gap. The production behavior is correct and the ship-blocking risk is zero. The recommended fix is a spec amendment, NOT additional code changes:

```markdown
# Task: Close the DoD #1 wording gap in spec graphify-setup-autoinstall

## Context
Implementation audit verdict: PARTIAL. The only failing check is DoD #1
("zero matches of `iurykrieger/graphify`"), which conflicts with the
spec's own anti-scope (it forbids editing `.vibeflow/prds/`). Every live,
user-facing surface is clean. The residual matches exist only in the spec
and PRD files that describe the bug — removing them would delete
documentation.

## Required change
Open `.vibeflow/specs/graphify-setup-autoinstall.md` and amend DoD #1:

- Old: "Grepping the repo for the literal string `iurykrieger/graphify`
  returns zero matches."
- New: "Grepping the repo for the literal string `iurykrieger/graphify`
  returns zero matches outside `.vibeflow/prds/` and
  `.vibeflow/specs/graphify-setup-autoinstall.md` (self-referential
  documentation of the original bug is permitted)."

No code changes. No other DoD items change.

## Verification
After the spec amendment, re-run `/vibeflow:audit
.vibeflow/specs/graphify-setup-autoinstall.md`. Expected verdict: PASS.
```
