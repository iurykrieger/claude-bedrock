## Audit Report: rename-query-to-ask-part-2

**Spec:** `.vibeflow/specs/rename-query-to-ask-part-2.md`
**Date:** 2026-04-15
**Verdict: PASS**

### DoD Checklist

- [x] **Check 1** — `README.md` references `/bedrock:ask` in both the skills table (line 67) and architecture diagram (line 95). 2 occurrences replaced, 0 occurrences of `/bedrock:query` remain. Evidence: `README.md:67,95`
- [x] **Check 2** — `skills/setup/SKILL.md` references `/bedrock:ask` in all 3 occurrences: skills table (line 540), onboarding instruction header and command (lines 1082–1083). Evidence: `skills/setup/SKILL.md:540,1082,1083`
- [x] **Check 3** — `skills/teach/SKILL.md` references `/bedrock:ask` instead of `/bedrock:query` (line 254). 1 occurrence replaced. Evidence: `skills/teach/SKILL.md:254`
- [x] **Check 4** — `index.html` skill card references `/bedrock:ask` with `data-i18n="sk_ask"` (line 532). English i18n key renamed to `sk_ask` (line 597). Portuguese i18n key renamed to `sk_ask` (line 628). Evidence: `index.html:532,597,628`
- [x] **Check 5** — Final grep sweep: 0 occurrences of `/bedrock:query` or `skills/query` remain in the codebase outside `.vibeflow/`. Verified via `Grep pattern="bedrock:query|skills/query" glob="!.vibeflow/**"` returning 0 matches.

### Pattern Compliance

- [x] **vault-writing-rules.md** — PASS. All replacements are mechanical string substitutions. No vault entity writes were performed. Example text in `skills/setup/SKILL.md:1083` preserves the kebab-case command format (`/bedrock:ask what do we know about <actor>?`). No wikilinks or frontmatter were modified.

### Convention Violations

None found.

- All 4 modified files retain their original structure and formatting
- i18n key rename (`sk_query` → `sk_ask`) is consistent across both language blocks (en, pt-BR)
- No content or logic changes introduced — purely mechanical string replacement as specified

### Tests

No test runner detected (markdown-only Claude Code plugin — no package.json, pyproject.toml, or build system). Verify that the landing page renders correctly by opening `index.html` in a browser and checking the skill card displays `/bedrock:ask`.

### Budget

Files changed: 4 / ≤ 4 budget (`README.md`, `skills/setup/SKILL.md`, `skills/teach/SKILL.md`, `index.html`)

### Anti-scope

All anti-scope items respected: YES
- No `.vibeflow/` file updates
- No content or logic changes — purely mechanical
- No changes to `CLAUDE.md` or `skills/ask/SKILL.md` (Part 1 scope)

### Overall: PASS
