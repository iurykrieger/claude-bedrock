# Audit Report: Multiple Vaults — Part 3: Vault Resolution in Detection Skills

> Spec: `.vibeflow/specs/multiple-vaults-part-3.md`
> Audited: 2026-04-15

**Verdict: PASS**

## DoD Checklist

- [x] **1. Vault resolution section in all 3 skills** — `teach/SKILL.md:29`, `compress/SKILL.md:29`, `sync/SKILL.md:31` — each has `## Vault Resolution` with the 4-step precedence chain (--vault flag > CWD detection with longest-match > default vault > error). All 3 store `VAULT_NAME` for delegation passthrough. Placed after Plugin Paths, before Overview.
- [x] **2. --vault flag works for teach** — `teach/SKILL.md:33-34` parses `--vault <name>` and removes from arguments. Graphify invocation uses `<VAULT_PATH>` (line 216). Graphify output paths use `<VAULT_PATH>/graphify-out/` (lines 224, 231, 245, 262). Preserve delegation passes `--vault <VAULT_NAME>` (line 272).
- [x] **3. --vault flag works for compress** — `compress/SKILL.md:33-34` parses `--vault <name>` and removes before `--mode` parsing. Entity dirs prefixed with `<VAULT_PATH>/` (line 142). Phase 0 git uses `git -C <VAULT_PATH>` (line 118). Config read uses `<VAULT_PATH>/.bedrock/config.json` (line 64). Preserve delegation passes `--vault <VAULT_NAME>` (line 579).
- [x] **4. --vault flag works for sync** — `sync/SKILL.md:35-36` parses `--vault <name>` and removes before `--people`/`--github` parsing. Entity dirs prefixed across all 3 modes: sources (lines 236-242), people (lines 453-454, 571), github (lines 692-693, 775). Report path uses `<VAULT_PATH>/fleeting/` (line 1134). Both preserve delegations pass `--vault <VAULT_NAME>` (lines 350, 924).
- [x] **5. Vault name propagated to preserve** — 4 delegation points verified: `teach/SKILL.md:272`, `compress/SKILL.md:579`, `sync/SKILL.md:350` (sources mode), `sync/SKILL.md:924` (github mode). All use `/bedrock:preserve --vault <VAULT_NAME>`.
- [x] **6. Git commands use `git -C` in sync and compress** — Compress: 2 `git -C` instances (lines 118, 123), zero bare git. Sync: 30 `git -C` instances across 3 git blocks (sources Phase 0 + github actors Phase 5.4 + github report Phase 6.3), zero bare git. Teach confirmed: zero git operations (all delegated to preserve).
- [x] **7. No violations of skill-delegation pattern** — Entity list format unchanged in all 3 skills. Only addition is `--vault <VAULT_NAME>` in Skill tool invocation arguments. Teach still delegates graphify output to preserve. Compress still delegates structured entity list to preserve. Sync still delegates in both sources and github modes. No direct entity writes introduced.

## Pattern Compliance

- [x] **Skill Architecture** (`patterns/skill-architecture.md`) — Vault Resolution section consistently placed after Plugin Paths in all 3 skills. Phase numbering preserved. Critical Rules tables updated: `teach/SKILL.md:355-356`, `compress/SKILL.md:671-675`, `sync/SKILL.md:1273-1277`.
- [x] **Skill Delegation** (`patterns/skill-delegation.md`) — Delegation contract extended with `--vault <VAULT_NAME>` passthrough. Entity list format itself unchanged. Detection skills never write entities directly. Compress's known anti-pattern (direct writes in Phase 4) was NOT fixed (correctly per anti-scope) — paths were prefixed but pattern not refactored.
- [x] **Vault Writing Rules** (`patterns/vault-writing-rules.md`) — Git conventions unchanged: same commit messages, strategy selection, branch naming. Only invocation changed to `git -C <VAULT_PATH>`. Config reads correctly reference `<VAULT_PATH>/.bedrock/config.json` in all 3 git blocks of sync (lines 959, 1149) and compress (line 64).

## Convention Violations

None found.

## Tests

No test runner detected (markdown-only Claude Code plugin). Verify that tests were run manually.

## Budget

Files changed: 3 / ≤ 4 budget
- `skills/teach/SKILL.md` — edited (Vault Resolution + graphify paths + preserve delegation + Critical Rules)
- `skills/compress/SKILL.md` — edited (Vault Resolution + entity paths + git -C + preserve delegation + Critical Rules)
- `skills/sync/SKILL.md` — edited (Vault Resolution + entity paths + 3 git blocks with git -C + 2 preserve delegations + fleeting path + Critical Rules)
