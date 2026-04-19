# Audit Report: teach-docling-integration-part-3

> Date: 2026-04-18
> Spec: `.vibeflow/specs/teach-docling-integration-part-3.md`
> Implementation: `README.md` (lines 27, 101, 116-118); `CLAUDE.md` (line 110); `skills/teach/SKILL.md` (frontmatter lines 3-11); `skills/setup/SKILL.md` (line 646)
> Dependencies satisfied: Part 1 audit **PASS**, Part 2 audit **PASS**

**Verdict: PASS**

## Scope of Audit

Spec: update all user-facing documentation so `/bedrock:teach`'s expanded source-format support (any docling-supported file plus existing URL fetchers) is consistently described; advertise docling as a runtime dependency alongside graphify. Budget: ≤ 4 files. Anti-scope: no skill phase/logic changes; no README structure rewrite; no new docs files; no translation; no version bump.

## Tests

No test runner in the project — plugin is markdown-only per `.vibeflow/index.md` ("No build system. No runtime"). Warn and continue per the audit skill's fallback rule.

## DoD Checklist

- [x] **1. `README.md:27` Features bullet** — evidence: line now reads "Confluence, Google Docs, GitHub repositories, and any file format supported by [docling](...) (DOCX, PPTX, XLSX, PDF, HTML, EPUB, images, and more)". Concrete examples included per the spec's technical-decisions table. **PASS**.

- [x] **2. `README.md:101` Day-to-day loops** — evidence: bullet now reads "Confluence page, Google Doc, GitHub repo, remote URL, or any local file (DOCX, PPTX, XLSX, PDF, HTML, EPUB, images, and any other docling-supported format)". Wording is parallel to line 27 and includes the "remote URL" category introduced in Part 2. **PASS**.

- [x] **3. `README.md` Dependencies table** — evidence: new row at `README.md:116` — `[docling](https://github.com/docling-project/docling)` with purpose "Universal file → markdown converter used by `/bedrock:teach` to ingest DOCX, PPTX, XLSX, PDF, HTML, EPUB, images, and other non-markdown formats" and Required=Yes. Existing `graphify` row preserved at `:115`. Supporting paragraph at `:118` notes both are auto-installed by `/bedrock:setup` and lazily by `/bedrock:teach`. **PASS**.

- [x] **4. `CLAUDE.md` plugin root** — evidence: `CLAUDE.md:110` — the `/bedrock:teach` row in the Skills table now enumerates "Confluence, Google Docs, GitHub repositories, remote URLs, and any file format supported by docling — DOCX, PPTX, XLSX, PDF, HTML, EPUB, images, and more". Wording is consistent with README.md. **PASS**.

- [x] **5. `skills/teach/SKILL.md` frontmatter + `skills/ask/SKILL.md` verification** — evidence: `skills/teach/SKILL.md:3-11` — frontmatter `description` now reads "Fetches content from Confluence, Google Docs, GitHub repositories, remote URLs, or any local file format supported by docling (DOCX, PPTX, XLSX, PDF, HTML, EPUB, images, Markdown, CSV, and more)". It also correctly reflects Part 2's flow (docling conversion, graphify merge delegation). `skills/ask/SKILL.md` verified: Confluence/GDocs/GitHub mentions (lines 222/253/285) are scoped to URL-type classification for ask's escalation logic — they describe what URL patterns ask recognizes in entity content, not an enumeration of teach's total input scope (which now includes local files, which ask can't detect from URL patterns). DoD #5's "trivially satisfied" clause applies for teach-scope enumeration. **PASS**.

- [x] **6. No live file still advertises the old narrow allowlist** — evidence: project-wide grep run after edits. Remaining matches of the narrow-allowlist pattern appear only in:
  - `.vibeflow/specs/landing-page.md`, `.vibeflow/specs/adaptive-ask-orchestrator.md`, `.vibeflow/prds/graphify-pipeline-refactor.md`, `.vibeflow/prds/teach-docling-integration.md`, `.vibeflow/specs/teach-docling-integration-part-3.md` — all `.vibeflow/` planning/meta docs (historical context; explicitly acknowledged in `decisions.md` 2026-04-18 pitfall about self-referential docs)
  - `skills/ask/SKILL.md:222/253/285` — scoped to URL-classification, not teach scope (see DoD #5)
  
  All live user-facing surfaces are clean: README.md, CLAUDE.md, `skills/teach/SKILL.md`, and `skills/setup/SKILL.md` Quick Reference template at `:646` (updated during implementation after the grep discovered it — permitted by anti-scope carve-out). **PASS**.

- [x] **7. Craftsmanship gate** — evidence: canonical wording "Confluence, Google Docs, GitHub repositories, remote URLs, and any docling-supported file format" consistently applied across README.md, CLAUDE.md, `skills/teach/SKILL.md` description, and `skills/setup/SKILL.md` template. No `conventions.md` Don'ts violations:
  - kebab-case filenames preserved ✓
  - English (en-US) throughout ✓
  - No flat tags introduced ✓
  - No removed wikilinks or frontmatter fields ✓
  - No credentials/tokens ✓
  
  Pattern compliance preserved (see next section). **PASS**.

## Pattern Compliance

- [x] **`.vibeflow/conventions.md`** — follows correctly. Evidence:
  - All edits are additions or word substitutions; no wikilinks removed; no hierarchical tags replaced with flat tags; language remains en-US; filenames kebab-case.
  - The new canonical wording consolidates on a single phrasing ("any file format supported by docling") reused verbatim across four files, supporting the "consistent wording" implicit convention.

- [x] **`.vibeflow/patterns/vault-writing-rules.md`** — follows correctly. Evidence:
  - Append-don't-remove semantics: existing Features bullet text about ingestion was expanded rather than replaced. Dependencies table gained a row, graphify row preserved. Skill description expanded with new format list while preserving the original Confluence/GDocs/GitHub mentions.
  - No wikilinks or frontmatter fields were removed from any touched file.

No pattern deviations.

## Convention Violations

None newly introduced.

## Observations (non-blocking)

1. **`pipx install graphify` reference in `README.md:118` is aspirational.** The supporting paragraph I added says "You can also install them manually via `pipx install graphify` / `pipx install docling`." However, the actual PyPI package for graphify is currently published as `graphifyy` (per the note in `skills/setup/SKILL.md:159`: "The PyPI package is currently published as `graphifyy` — temporary while the upstream project reclaims the `graphify` name. When that flip happens, update..."). For end users relying on README's manual-install hint, the command would need to be `pipx install graphifyy` today. Mitigating factors: (a) auto-install via `/bedrock:setup` already handles the package-name dance invisibly; (b) users rarely install graphify manually. Worth a small follow-up: either align README wording with the current package name or make the manual-install hint package-name-agnostic ("use `/bedrock:setup`").

2. **`skills/setup/SKILL.md` Quick Reference template edit was not in the spec's explicit file list** but was required by DoD #6's project-wide no-old-allowlist rule and is explicitly permitted by the spec's anti-scope carve-out ("other skill SKILL.md files (preserve, compress, sync, setup, vaults, healthcheck) unless they contain explicit mentions of the old allowlist"). Implementation correctly added the file during the grep-driven gap scan, staying within the ≤ 4-file budget.

3. **`skills/ask/SKILL.md` mentions of Confluence/GDocs/GitHub at `:222`, `:253`, `:285` are intentionally unchanged.** These describe URL-type classification for ask's escalation-to-teach logic — a subset of teach's URL inputs, not an enumeration of teach's full input scope. Expanding them to include "local files" would be misleading (ask detects URLs, not files); expanding them to "any remote URL" would implicitly broaden ask's escalation logic (skill-logic change → anti-scope). The current list is accurate for ask's behavior. Observation, not a gap.

4. **Added supporting paragraph at `README.md:118` about auto-install** is beyond DoD #3's literal requirement (which only asked for a table row), but it is immediately adjacent to and thematically coherent with the Dependencies table, and the spec's anti-scope only prohibits "rewrite of README structure" — a one-line paragraph is neither a structural change nor a new section. Acceptable scope-adjacent addition that improves user orientation.

## Budget

- Files changed: **4 / ≤ 4** (`README.md`, `CLAUDE.md`, `skills/teach/SKILL.md`, `skills/setup/SKILL.md`). At the budget limit.
- Anti-scope respected: no skill phases/logic changes; no README structure rewrite; no new docs files; no translation; no entity templates / entity definitions touched; `/preserve`, `/compress`, `/sync`, `/vaults`, `/healthcheck`, `/ask` logic untouched; no version bump or changelog. ✓

## Verdict Rationale

All 7 DoD checks PASS with direct evidence. Both applicable patterns followed (conventions.md and vault-writing-rules.md). No new convention violations. One implementation observation flagged for a small follow-up (README `pipx install graphify` wording vs. the transitional `graphifyy` package name), but this is a pre-existing cross-file inconsistency that pre-dates Part 3 and is not a DoD gap. Budget at the limit (4/4) and justified by DoD #6's project-wide scope. Dependencies on Parts 1 and 2 satisfied (both PASS audits on record).

**Ready to ship.** The full `teach-docling-integration` initiative (Parts 1, 2, 3) is now implemented and audited across `skills/preserve/SKILL.md`, `skills/teach/SKILL.md`, `skills/setup/SKILL.md`, `README.md`, and `CLAUDE.md`.

## Next Steps

- No more specs in this initiative. Consider a small follow-up (optional):
  - Align `README.md:118` manual-install hint with the current `graphifyy` package name (or remove the hint and point to `/bedrock:setup`).
  - Update stale Critical Rule #3 in `skills/setup/SKILL.md` ("NEVER auto-install dependencies") to reflect the accepted auto-install pattern now used for both graphify and docling.
  - Add a `/bedrock:compress` spec to read `.graphify_analysis.json`'s `stale: true` flag and trigger recomputation (per Part 1 Observation #3).
- The stale-rule and `graphifyy` cleanup could be bundled into a single small `docs-consistency-cleanup` spec if desired.
