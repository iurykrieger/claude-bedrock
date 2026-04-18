# Spec: Fix graphify references and auto-install on setup

> Generated via /vibeflow:gen-spec on 2026-04-18
> Source PRD: `.vibeflow/prds/graphify-setup-autoinstall.md`
> Budget: ≤ 4 files

## Objective

`/bedrock:setup` points every graphify reference to `safishamsi/graphify` and silently installs the dependency when it is missing, so users never hit a 404 link and `/bedrock:teach` works on the first run.

## Context

Today three live surfaces (`skills/setup/SKILL.md`, `README.md`, `.vibeflow/specs/graphify-pipeline-refactor.md`) point to `https://github.com/iurykrieger/graphify`, which returns 404. `/bedrock:setup` Phase 1.2 detects graphify via `Glob: ~/.claude/skills/graphify/SKILL.md`, and when missing only prints instructions — leaving `/bedrock:teach` broken on first use.

Graphify is distributed as a PyPI package (`graphifyy` — temporary name while the upstream reclaims `graphify`) that installs a Claude Code skill at `~/.claude/skills/graphify/SKILL.md`. Install entrypoint: `pip install graphifyy && graphify install` (or pipx-equivalent). Manual fallback via `curl` for the skill file directly.

The setup skill already declares `allowed-tools: Bash, Read, Write, Glob, Grep`, so shelling out to `pipx`, `pip`, and `curl` requires no manifest change. Critical Rule #1 of the skill mandates that initialization never blocks for missing dependencies — every install path must fall through on failure.

## Definition of Done

1. Grepping the repo for the literal string `iurykrieger/graphify` returns zero matches.
2. `safishamsi/graphify` appears in all three live surfaces: `README.md` (optional-dependencies table), `skills/setup/SKILL.md` (dependency-check guidance), and `.vibeflow/specs/graphify-pipeline-refactor.md` (install reference).
3. `skills/setup/SKILL.md` Phase 1.2 contains a new auto-install subsection that triggers only when the graphify detection probe fails and executes the fallback chain in order: `pipx install graphifyy && graphify install` → `pip install graphifyy && graphify install` → `mkdir -p ~/.claude/skills/graphify && curl -fsSL https://raw.githubusercontent.com/safishamsi/graphify/v1/skills/graphify/skill.md > ~/.claude/skills/graphify/SKILL.md` → print manual install instructions.
4. The Python-missing path (steps 1 and 2 skipped because Python 3.10+ is not available) emits an explicit warning to the user before falling back to `curl`; all other paths run silently (no consent prompt).
5. After attempting install, the detection probe is re-run and the Phase 1.2 dependency table reflects the post-install status (`installed` or `NOT FOUND`); every install failure path flows to the existing "proceed regardless" behavior without `exit`, abort, or early return — preserving Critical Rule #1 (never block initialization).
6. **[craftsmanship]** The new subsection follows the Skill Architecture pattern from `.vibeflow/patterns/skill-architecture.md` — decimal sub-phase numbering (`### 1.2.x`) consistent with the existing phase structure, no modifications to `allowed-tools` (Bash already declared), no violations of `conventions.md` Don'ts, and no duplication of existing dependency-check boilerplate.

## Scope

- **Edit `skills/setup/SKILL.md`**
  - Replace `iurykrieger/graphify` → `safishamsi/graphify` in the existing Phase 1.2 graphify warning block (line ~142).
  - Add a new sub-phase (e.g., `### 1.2.1 Auto-install graphify if missing`) that implements the fallback chain described in DoD #3 and the Python-missing warning described in DoD #4.
  - Ensure the dependency table (produced later in Phase 1.2) is generated **after** the install attempt so the displayed status is post-install.
- **Edit `README.md`** — update the Optional Dependencies table row for graphify (line ~106) to point to `https://github.com/safishamsi/graphify`.
- **Edit `.vibeflow/specs/graphify-pipeline-refactor.md`** — replace the install reference on line ~185.

## Anti-scope

- No new `allowed-tools` entries — Bash already covers shell-outs.
- No prompt for user consent before installing.
- No uninstall, upgrade, or version-pinning logic.
- No Python bootstrapping — if Python 3.10+ is missing we warn and fall back to `curl`, never attempt to install Python.
- No changes to `/bedrock:teach`, `/bedrock:ask`, or any other skill.
- No changes to the detection probe path (`~/.claude/skills/graphify/SKILL.md`).
- No changes to other optional dependencies (Confluence, Google, claude-in-chrome).
- No new fields in `.bedrock/config.json` to toggle auto-install behavior.
- No edits to historical `.vibeflow/prds/` or `.vibeflow/audits/` artifacts.
- No new skill file, no new plugin file, no new templates.
- **Budget cap: 3 files maximum.** If a fourth file appears necessary, stop and revisit scope.

## Technical Decisions

### 1. Install method selection: runtime fallback chain (not config-driven)

The skill probes each install method by shelling out and checking exit codes. Chain:

1. `command -v pipx` → run `pipx install graphifyy && graphify install`
2. Else `command -v pip` (or `pip3`) and `python --version` ≥ 3.10 → run `pip install graphifyy && graphify install`
3. Else warn about missing Python → run `mkdir -p ~/.claude/skills/graphify && curl -fsSL https://raw.githubusercontent.com/safishamsi/graphify/v1/skills/graphify/skill.md > ~/.claude/skills/graphify/SKILL.md`
4. Else print manual instructions with `https://github.com/safishamsi/graphify` and continue.

**Why runtime over config:** users don't know in advance which tooling they have, and the check is cheap. A config knob would add surface area for anti-scoped behavior.

**Trade-off:** more decision points inside the skill means a slightly longer Phase 1.2. Accepted — still well under the skill's existing 1200-line footprint.

### 2. Success verification via probe re-run, not install-command exit code

`pipx`/`pip` can exit 0 even when the skill file is not written (PyPI publishing hiccups, post-install hook failures). After each attempted install, re-run `Glob: ~/.claude/skills/graphify/SKILL.md`. Only mark success when the file exists.

**Trade-off:** one extra Glob per install attempt. Negligible; much safer than trusting exit codes.

### 3. Silent by default, warn only on Python-missing path

The PRD mandates silent install for steps 1–2. The `curl` fallback (step 3) is triggered by a missing prerequisite the user should know about, so we surface that. Step 4 (print instructions) is only reached when everything else fails — user sees those instructions anyway.

**Trade-off:** users who prefer "no side effects without consent" get none. Product decision confirmed in discovery — accepted.

### 4. PyPI package name `graphifyy` hard-coded for now

The upstream README notes the `graphify` PyPI name is being reclaimed; today the package is `graphifyy`. Reference `graphifyy` directly in the skill; add a one-line comment noting the temporary name so a future update is cheap.

**Trade-off:** when upstream flips the name, this needs a follow-up edit. Accepted — alternative (`graphify||graphifyy` with try-each logic) doubles the code and the upstream cut-over is a predictable event.

### 5. Edit location: within Phase 1.2, not a new phase

The install work is a sub-step of the existing Dependency Check, not a new phase. Adding a new top-level phase would renumber downstream phases and break the Critical Rules table's implicit contract. Use `### 1.2.1 Auto-install graphify if missing` after the detection probe and before the dependency-report output.

**Trade-off:** Phase 1.2 grows. Accepted — locality > flatness.

## Applicable Patterns

From `.vibeflow/patterns/skill-architecture.md`:

- **Decimal sub-phase notation** (`1.1`, `1.2`, `1.2.1`) — the new install block must use this.
- **Agent-type consistency** — the setup skill declares itself a "setup agent" with procedural, phased instructions; the new block is written as step-by-step directives, not prose.
- **Best-effort external sources** — Critical Rule #1 ("NEVER block initialization") maps to `conventions.md` Don't #8 ("Do NOT block workflows for failed external sources — always best-effort"). The fallback chain embodies this.
- **`allowed-tools` discipline** — do not widen the declared tool set; Bash covers every new shell-out.

No new patterns introduced.

## Risks

| Risk | Mitigation |
|---|---|
| `pipx`/`pip` exits 0 without writing the skill file (e.g., post-install hook error) | Re-run the detection probe after every install attempt; only count success when `~/.claude/skills/graphify/SKILL.md` exists. |
| `curl` fails due to no network or upstream 404 (e.g., branch `v1` renamed) | `-fsSL` makes curl fail non-zero on HTTP errors. On failure, fall through to step 4 (print instructions). Setup continues. |
| Silent `pip install` surprises users who audit their Python environment | Product decision accepted in discovery. Out of scope. |
| PyPI package name `graphifyy` becomes `graphify` upstream | Inline comment flags the temporary name; a follow-up edit updates the install command. Single-line change. |
| New install block bloats Phase 1.2 beyond readability | Keep it to one `### 1.2.1` sub-phase with a concise fallback list. If it grows past ~60 lines, split into `### 1.2.1` (detection) and `### 1.2.2` (install). |
| The change to `.vibeflow/specs/graphify-pipeline-refactor.md` rewrites historical spec text | Edit scope is limited to the URL string inside the install reference — every other line of the spec is untouched. |
