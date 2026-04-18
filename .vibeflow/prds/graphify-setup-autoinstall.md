# PRD: Fix graphify references and auto-install on setup

> Generated via /vibeflow:discover on 2026-04-18

## Problem

Users running `/bedrock:setup` on a fresh machine hit a dead end when the graphify dependency is missing. The setup skill currently points them to `https://github.com/iurykrieger/graphify` — a repository that **returns 404** because it does not exist. The correct upstream is `https://github.com/safishamsi/graphify`, but no live surface of this project points there.

Compounding the problem, even with the correct URL graphify is a **required** dependency for `/bedrock:teach` to function, so users currently face manual installation friction on every fresh setup. The setup skill already has the authority to perform the install (it lands a single skill file at a known path — `~/.claude/skills/graphify/SKILL.md`), but today it only prints instructions.

The net effect: new users see a 404, don't know how to recover, and `/bedrock:teach` silently fails the first time they try to use it.

## Target Audience

Anyone running `/bedrock:setup` for the first time on a machine that does not already have graphify installed. Primarily:
- Engineers adopting Bedrock on a new laptop or CI runner
- Users re-installing after a wipe / environment reset

## Proposed Solution

Two linked changes:

1. **Correct every reference** to the graphify repository. Replace `iurykrieger/graphify` with `safishamsi/graphify` in all three live surfaces: `skills/setup/SKILL.md`, `README.md`, and `.vibeflow/specs/graphify-pipeline-refactor.md`.

2. **Auto-install graphify silently** during `/bedrock:setup` Phase 1.2 (Dependency Check) when the graphify skill file is not detected. The install runs without asking the user for consent, using a fallback chain that tolerates common environment gaps:
   1. `pipx install graphifyy && graphify install` (isolated, preferred)
   2. `pip install graphifyy && graphify install` (if pipx unavailable)
   3. Manual `curl` fallback — `mkdir -p ~/.claude/skills/graphify && curl -fsSL https://raw.githubusercontent.com/safishamsi/graphify/v1/skills/graphify/skill.md > ~/.claude/skills/graphify/SKILL.md` (if Python 3.10+ unavailable — **warn the user** that Python is missing before falling back)
   4. Print install instructions pointing to `https://github.com/safishamsi/graphify` and continue (last resort if all methods fail)

Setup remains non-blocking at every step — never abort initialization for a graphify install failure.

## Success Criteria

- Running `/bedrock:setup` on a machine without graphify results in `~/.claude/skills/graphify/SKILL.md` existing at the end of Phase 1.2 (verifiable with a single `ls`).
- Grepping the repo for `iurykrieger/graphify` returns zero matches.
- Grepping the repo for `safishamsi/graphify` returns at least three matches (README, setup skill, spec).
- The dependency check report in Phase 1.2 reports graphify as `installed` after setup runs on a machine where it was missing at start.
- If auto-install fails (e.g., no internet, no Python, no pip/pipx), setup still completes and the final message tells the user exactly how to install graphify manually with the correct upstream URL.

## Scope v0

- Replace `iurykrieger/graphify` → `safishamsi/graphify` in:
  - `skills/setup/SKILL.md`
  - `README.md`
  - `.vibeflow/specs/graphify-pipeline-refactor.md`
- Extend `skills/setup/SKILL.md` Phase 1.2 with a new install subsection that:
  - Triggers only when the graphify detection probe (`Glob: ~/.claude/skills/graphify/SKILL.md`) fails
  - Runs the fallback chain silently (no user prompt for consent)
  - Warns the user explicitly only when falling back to the `curl` path because Python 3.10+ is missing
  - Re-runs the detection probe after install and reports the new status in the dependency table
  - Never blocks setup — falls through to the existing "proceed regardless" behavior if all install methods fail

## Anti-scope

- **No confirmation prompt before install.** Silent install is the product decision.
- **No uninstall / upgrade logic.** Setup only installs graphify when it's missing; existing installations are not touched.
- **No Python version bootstrapping.** If Python 3.10+ is missing, we warn and fall back to `curl` — we do not attempt to install Python.
- **No changes to `/bedrock:teach` or other skills.** Only `/bedrock:setup` gets new install behavior.
- **No changes to the graphify detection probe path.** The skill continues to use `Glob: ~/.claude/skills/graphify/SKILL.md`.
- **No modifications to other optional dependencies** (Confluence, Google, claude-in-chrome) — they remain advisory only.
- **No changes to historical `.vibeflow/prds/` or `.vibeflow/audits/`**, only the live spec `.vibeflow/specs/graphify-pipeline-refactor.md`.
- **No new config flags** in `.bedrock/config.json` to toggle auto-install behavior.

## Technical Context

Relevant existing patterns (from `.vibeflow/`):

- **Phased skill execution** — `/bedrock:setup` follows a Phase 0 → 4 flow. The new install logic fits cleanly as a subsection within the existing Phase 1.2 Dependency Check (`skills/setup/SKILL.md:101-170`), right after the detection probe and before the "report format" output.
- **Never-block critical rule** — Rule #1 in the setup skill's Critical Rules table (`skills/setup/SKILL.md:1195`) mandates that initialization never aborts for missing dependencies. The fallback chain must preserve this guarantee: any failure mode (no network, no Python, install error) must still let setup continue.
- **Bash as allowed tool** — The setup skill's frontmatter already declares `allowed-tools: Bash, Read, Write, Glob, Grep` (`skills/setup/SKILL.md:11`), so shelling out to `pipx`, `pip`, and `curl` requires no manifest change.
- **Markdown-only plugin** — Bedrock has no build system or test suite; changes are applied by editing markdown files. Verification is done by re-running `/bedrock:setup` on a machine in the relevant failure mode.

Install contract (verified against the upstream README at the time of discovery):

- PyPI package name: `graphifyy` (temporary — the `graphify` name is being reclaimed)
- CLI / skill name after install: `graphify`
- Skill payload lands at: `~/.claude/skills/graphify/SKILL.md`
- Manual install URL: `https://raw.githubusercontent.com/safishamsi/graphify/v1/skills/graphify/skill.md`

## Open Questions

None.
