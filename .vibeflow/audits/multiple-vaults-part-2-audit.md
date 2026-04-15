# Audit Report: Multiple Vaults — Part 2: Vault Resolution in Core Skills

> Spec: `.vibeflow/specs/multiple-vaults-part-2.md`
> Audited: 2026-04-15

**Verdict: PASS**

## DoD Checklist

- [x] **1. Vault resolution section in all 3 skills** — `preserve/SKILL.md:29`, `query/SKILL.md:30`, `healthcheck/SKILL.md:28` — each has `## Vault Resolution` section with identical 4-step precedence chain (--vault flag > CWD detection with longest-match > default vault > error). Placed after Plugin Paths, before Overview.
- [x] **2. --vault flag works for preserve** — `preserve/SKILL.md:33-34` parses `--vault <name>` and removes from arguments. All entity paths in Phase 2.1 (line 275) use `<VAULT_PATH>/` prefix. All git commands (16 instances: lines 90, 95, 580, 583, 603, 604, 609, 610, 637, 642, 647, 648, 658, 666) use `git -C <VAULT_PATH>`. Config read on line 591 uses `<VAULT_PATH>/.bedrock/config.json`.
- [x] **3. --vault flag works for query** — `query/SKILL.md:34-35` parses `--vault <name>` and extracts question. Entity Glob paths in Phase 2-S (lines 219-220), alias Grep (lines 226-227), Phase 2.5.1 (lines 280-281), Phase 2.5.2 (line 290), Phase 3.2 (lines 328-329) all use `<VAULT_PATH>/` prefix. Graphify-out check (line 137) uses `<VAULT_PATH>/graphify-out/`.
- [x] **4. --vault flag works for healthcheck** — `healthcheck/SKILL.md:32-33` parses `--vault <name>`. Phase 1.1 entity dirs (line 106) use `<VAULT_PATH>/` prefix including actor subfolder patterns (lines 109-110). Phase 2.1 graphify checks (lines 141, 143, 151, 153, 167, 170) use `<VAULT_PATH>/graphify-out/`. Phase 2.2.1 directory checks (line 199) use `<VAULT_PATH>/`.
- [x] **5. Git commands use `git -C`** — 16 `git -C <VAULT_PATH>` instances in preserve covering: pull (line 90), rebase abort (line 95), add (line 580), diff (line 583), commit (lines 603, 647, 666), push (lines 604, 610, 648), pull-rebase retry (line 609), branch list (line 637), checkout (lines 642, 658). Zero bare `git <command>` patterns found (verified via `^git [a-z]` regex). Query and healthcheck have no git operations (correct per spec).
- [x] **6. CWD detection works** — All 3 skills implement Step 2.2 "CWD detection" checking if CWD starts with any registered vault's absolute path, using longest-match for specificity. Evidence: `preserve/SKILL.md:43-46`, `query/SKILL.md:44-47`, `healthcheck/SKILL.md:42-45`.
- [x] **7. No violations of skill-architecture pattern** — Plugin Paths section unchanged in all 3 skills. Phase numbering preserved (no shifts needed — Vault Resolution is a new top-level section, not a phase). Critical Rules tables updated: `preserve/SKILL.md:733-735`, `query/SKILL.md:492-493`, `healthcheck/SKILL.md:379-380`.

## Pattern Compliance

- [x] **Skill Architecture** (`patterns/skill-architecture.md`) — All 3 skills maintain the required 5-section structure: YAML frontmatter, Plugin Paths, Overview, Phases, Critical Rules. Vault Resolution is a new section between Plugin Paths and Overview — consistent with the spec's "placed immediately after Plugin Paths" directive. Phase 0 in preserve remains "Sync the Vault" (git pull) — unchanged.
- [x] **Skill Delegation** (`patterns/skill-delegation.md`) — Delegation contract unchanged in this part. Preserve still accepts structured entity lists. The `--vault` passthrough from detection skills is deferred to Part 3 (correct per anti-scope).
- [x] **Vault Writing Rules** (`patterns/vault-writing-rules.md`) — Git conventions unchanged: same commit message format, strategy selection, branch naming. Only the invocation changed (`git -C`). Frontmatter/wikilink/tag rules not affected.

## Convention Violations

None found.

## Tests

No test runner detected (markdown-only Claude Code plugin). Verify that tests were run manually.

## Budget

Files changed: 3 / ≤ 4 budget
- `skills/preserve/SKILL.md` — edited (Vault Resolution + git -C + entity paths + Critical Rules)
- `skills/query/SKILL.md` — edited (Vault Resolution + entity paths + graphify paths + Critical Rules)
- `skills/healthcheck/SKILL.md` — edited (Vault Resolution + entity paths + graphify paths + Critical Rules)
