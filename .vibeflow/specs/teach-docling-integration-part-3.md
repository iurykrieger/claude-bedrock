# Spec: Documentation refresh for docling-enabled /teach

> Part 3 of 3 — Split from `.vibeflow/prds/teach-docling-integration.md`
> Generated via /vibeflow:gen-spec on 2026-04-18

## Objective

Update all user-facing documentation so it consistently describes `/bedrock:teach`'s expanded ingestion scope (any docling-supported file format plus the existing URL fetchers) and advertises docling as a runtime dependency.

## Context

Parts 1 & 2 change `/bedrock:teach` to accept any docling-supported file format. Existing documentation — `README.md`, `CLAUDE.md`, and several `SKILL.md` files — still advertises the narrow Confluence/GDoc/GitHub/CSV/MD/PDF allowlist. Users reading the README will assume unsupported formats require manual conversion; agents reading the `/teach` frontmatter `description` will apply the old classification in their routing decisions. Fixing the docs is a small, isolable change but it must happen — Success Criterion #6 in the PRD.

## Definition of Done

1. **`README.md` Features bullet (≈ line 27):** "External source ingestion" item broadened from "Confluence, Google Docs, GitHub, CSV" to include "any file format supported by docling — DOCX, PPTX, XLSX, HTML, EPUB, PDF, images, and more".
2. **`README.md` Day-to-day loops (≈ line 101):** the "Capture knowledge from a source" line broadened in the same way, with a parenthetical example list.
3. **`README.md` Dependencies table (≈ line 113+):** new row for docling — purpose ("Universal file → markdown conversion used by `/bedrock:teach`") and Required ("Yes"). graphify row preserved.
4. **`CLAUDE.md` (plugin root):** skill table row for `/bedrock:teach` and any other enumeration of ingestion formats reflects docling support.
5. **`skills/teach/SKILL.md` frontmatter `description`:** narrows to reflect the new expanded scope (e.g. "Fetches content from Confluence, Google Docs, GitHub repositories, remote URLs, or any docling-supported file format…"). Note: if Part 2 already edited this field, Part 3 only verifies consistency.
6. **`skills/ask/SKILL.md`:** any mention of `/teach`'s input scope updated to align with the new wording. If no such mention exists, DoD item is trivially satisfied (verified, no edit needed).
7. **Craftsmanship gate:** no documentation file still advertises the old narrow allowlist as the complete set. New wording is consistent across all files (exact phrasing not required, but the allowlist framing must be gone). No violations from `.vibeflow/conventions.md` Don'ts (kebab-case, English en-US, no flat tags, no removed wikilinks).

## Scope

- `README.md` — lines 27, 101, and the Dependencies table.
- `CLAUDE.md` (plugin root).
- `skills/teach/SKILL.md` — frontmatter `description` field (verify or edit).
- `skills/ask/SKILL.md` — verify; edit only if teach input scope is referenced.

## Anti-scope

- **No changes to skill phases or skill logic** — those are Parts 1 & 2.
- **No rewrite of README structure, branding, or visuals.**
- **No new documentation files** (no separate `docs/docling.md`, no new `docs/INGESTION.md`).
- **No translation** — English only per `.vibeflow/conventions.md`.
- **No changes to `docs/` assets beyond textual references** (banner.png etc. untouched).
- **No changes to entity templates, entity definitions, or other skill SKILL.md files** (`preserve`, `compress`, `sync`, `setup`, `vaults`, `healthcheck`) unless they contain explicit mentions of the old allowlist.
- **No version bump**, changelog entry, or release note (separate concern).

## Technical Decisions

| Decision | Alternatives considered | Rationale |
|---|---|---|
| **Canonical wording: "any file format supported by docling, plus Confluence, Google Docs, and GitHub repositories"** | "any file format" (misleading); exhaustive list (stale fast) | Precise — acknowledges docling boundaries without listing every supported format. |
| **Example list in README (DOCX, PPTX, XLSX, HTML, EPUB, PDF, images)** | No examples; full docling list | Concrete examples help discoverability; full list is maintained upstream by docling. |
| **docling in Dependencies table as Required=Yes** | Optional | Without docling, the new allowlist-free `/teach` can't honor its contract for most formats; auto-install makes it effectively required. |
| **Skill description field is a minimal truthful list** | Exhaustive list | Agents reading the description use it for routing — keep it accurate and short. |
| **No new `docs/docling.md`** | Dedicated doc page | Overkill for v0; docling's own docs are canonical. Link from README if needed. |

## Applicable Patterns

- **`.vibeflow/conventions.md`** — English (en-US), kebab-case filenames, consistent wording, hierarchical tags only (no doc-level flat tags), no removed wikilinks.
- **`.vibeflow/patterns/vault-writing-rules.md`** — Append don't remove; if existing doc content is being replaced, preserve semantic meaning and any existing wikilinks.

No patterns introduced.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Part 3 ships before Parts 1 & 2, producing misleading docs | Medium | Medium | Explicit `Dependencies` field; execution order documented; reviewer checks. |
| Doc wording drifts across files | Medium | Low | Establish `skills/teach/SKILL.md` `description` as the single source of truth; README references the same phrasing. |
| Some doc file has an old allowlist reference we missed | Medium | Low | DoD item 7 requires a project-wide grep for the old narrow wording ("Confluence, Google Docs, GitHub, CSV" as the complete list) before closing the spec. |
| Users expect docling to be pre-installed when reading "Required=Yes" | Low | Low | README already points to `/bedrock:setup` for installation; clarify in the dependencies row. |

## Dependencies

- `.vibeflow/specs/teach-docling-integration-part-1.md` — merge behavior must be live.
- `.vibeflow/specs/teach-docling-integration-part-2.md` — docling conversion + expanded classification must be live before docs claim the capability.
