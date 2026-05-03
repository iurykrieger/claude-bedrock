# Bedrock Error Reporter Hook — Design

**Date:** 2026-05-03
**Author:** iury.krieger@stone.com.br
**Status:** Draft

---

## 1. Goal

Automatically open a GitHub Issue on `iurykrieger/claude-bedrock` whenever a **framework error** occurs during a `/bedrock:*` skill execution, so the maintainer learns about real-world failures without depending on manual user reports.

The hook ships as part of the `bedrock` Claude Code plugin and is enabled by default for all users.

---

## 2. Scope

### In scope (framework errors)

- **Technical failures** during a bedrock skill turn:
  - Bash commands invoked by skill scripts returning non-zero exit codes
  - Python tracebacks emitted from scripts under `skills/*/scripts/`
  - Tool results flagged with `is_error: true`
- **Logical failures** reported by Claude in the assistant's text:
  - Pattern-matched against a small, auditable regex catalog
  - Examples: "graphify returned invalid structure", "vault.json corrupt", "failed to execute bedrock skill"

### Out of scope (NOT reported)

- Errors in the user's vault content (broken wikilinks, missing frontmatter fields, malformed entities)
- Errors from non-bedrock tool calls (e.g., user editing unrelated files in the same session)
- User input mistakes (typos in skill arguments, missing flags)
- Errors when no `/bedrock:*` invocation exists in the current turn

---

## 3. Architecture

### 3.1 Flow

```
turn ends → Stop hook fires
              ↓
        FAST GATE: "/bedrock:" in last-turn slice?
              ↓ no  → exit 0 (~5ms)
              ↓ yes
        OPT-OUT CHECK: read .bedrock/config.json → error_reporting != false?
              ↓ no  → exit 0
              ↓ yes
        EXTRACT: skill_name, tool_results, assistant_text from slice
              ↓
        DETECT: scan_tool_results() + scan_assistant_text()
              ↓ no errors → exit 0
              ↓ errors found
        DEDUPE: hash each error, group by hash
              ↓
        For each unique hash:
          - lookup gh issue list (with 5min local cache)
          - exists & open    → comment on existing
          - exists & closed  → reopen + comment ("regression")
          - not exists       → create new issue
              ↓
        AUTH FAILURE FALLBACK: log to ~/.claude-bedrock-cache/error-reporter.log
                               and skip the rest of the session
```

### 3.2 Performance budget

| Path | Target latency | What runs |
|---|---|---|
| No-bedrock turn (99% case) | ~5ms in-process; ~50ms total incl. Python startup | Read transcript slice, single grep, exit |
| Bedrock turn, no errors | ~20ms in-process; ~70ms total incl. Python startup | Slice + 2 scanners (regex catalog) |
| Bedrock turn with errors | bounded by `gh` CLI | Hash + cache lookup + (optional) `gh` call |

**Measured (2026-05-03):** Fast gate path (no-bedrock transcript) averages 50ms per invocation wall-clock time over 10 runs (0.49–0.52s total). In-process work (excluding Python interpreter startup) is under 50ms per the unit test assertion.

The hook **must never block** Claude's response stream. If any step exceeds 5s, the script aborts and logs locally.

---

## 4. Components

### 4.1 Hook script — `hooks/error-reporter.py`

**Language:** Python 3 (already a plugin dependency via `docling`/`graphify`).

**Inputs (from Claude Code Stop hook environment):**
- `CLAUDE_TRANSCRIPT_PATH` — path to the JSONL transcript of the current session
- `CLAUDE_SESSION_ID` — session identifier
- `CLAUDE_PROJECT_DIR` — project root (used to find `.bedrock/config.json`)

**Outputs:**
- Exit code 0 always (failures must not break Claude Code)
- Side effects: GitHub issues created/commented, local cache and log files updated

**Pipeline:**

```python
def main():
    transcript = read_last_turn(os.environ["CLAUDE_TRANSCRIPT_PATH"])

    # 1. Fast gate
    if "/bedrock:" not in transcript:
        sys.exit(0)

    # 2. Opt-out check
    if not is_reporting_enabled():
        sys.exit(0)

    # 3. Extract context
    skill_name = extract_skill_invocation(transcript)
    tool_results = extract_tool_results(transcript)
    assistant_text = extract_assistant_text(transcript)

    # 4. Detect errors
    errors = scan_tool_results(tool_results) + scan_assistant_text(assistant_text)
    if not errors:
        sys.exit(0)

    # 5. Dedupe + dispatch
    for err in dedupe_by_hash(errors):
        try:
            handle_error(err, skill_name)
        except Exception:
            log_local(err)  # never raise

    sys.exit(0)
```

### 4.2 Logical-error regex catalog

Stored as a small, auditable list inside `error-reporter.py` (no external file to load — keeps fast path fast).

| ID | Pattern | Captures |
|---|---|---|
| `graphify_invalid` | `(?i)graphify.*returned.*invalid` | broken graphify output |
| `vault_corrupt` | `(?i)vault\.json.*corrupt` | malformed vault index |
| `skill_failure` | `(?i)bedrock\s+\w+\s+failed` | generic skill failure phrasing |
| `entity_unwritable` | `(?i)failed to (write|persist) entity` | preserve write path |
| `sync_unauthorized` | `(?i)sync.*unauthorized\|auth(entication)? failed.*sync` | sync skill auth errors |

The catalog starts small and grows organically as new failure patterns are observed in real issues. New entries require a one-line addition + test fixture.

### 4.3 Hash function

```python
def error_hash(skill: str, error_type: str, signature: str) -> str:
    raw = f"{skill}|{error_type}|{normalize(signature)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]
```

`normalize(signature)` strips:
- Absolute paths under user's home directory (replaced with `.../`)
- Session IDs, UUIDs, and timestamps
- Vault entity names (filtered against entity directories of the active vault)
- Line numbers in transcript references (but **keeps** line numbers in source files — those are stable)

### 4.4 Issue lookup with cache

```python
def find_existing_issue(hash: str) -> dict | None:
    cache_path = Path("~/.claude-bedrock-cache/issues-{hash}.json").expanduser()
    if cache_path.exists() and (now() - cache_path.stat().st_mtime < 300):
        return json.loads(cache_path.read_text())

    result = subprocess.run([
        "gh", "issue", "list",
        "--repo", "iurykrieger/claude-bedrock",
        "--label", "auto-reported",
        "--search", f"[bedrock][{hash}] in:title",
        "--state", "all",
        "--json", "number,state",
        "--limit", "1",
    ], capture_output=True, timeout=5)

    issues = json.loads(result.stdout)
    issue = issues[0] if issues else None
    cache_path.write_text(json.dumps({"issue": issue}))  # explicit envelope
    return issue

# When reading from cache:
#   data = json.loads(cache_path.read_text())
#   return data.get("issue")  # None if no issue, dict if cached hit
```

### 4.5 Issue content (template B — medium diagnostic)

**Title:**
```
[bedrock][<hash>] <skill>: <signature truncated to 80 chars>
```

**Labels:** `auto-reported`, `auto-bug`, `<skill>` (e.g. `bedrock:teach`).

Labels must be **pre-created in the `iurykrieger/claude-bedrock` repository** (one-time maintainer setup). The script does NOT attempt to create labels — most users don't have write permission to labels on a public repo they don't own. If a label is missing, `gh issue create` proceeds without it (using `--label "<name>" 2>/dev/null || gh issue create` retry strategy is **not** used; instead the script tolerates label-create failure).

**Body:**

```markdown
## Auto-reported error

**Skill:** `bedrock:teach`
**Error type:** `python_traceback`
**Plugin version:** `<read from .claude-plugin/plugin.json>`
**OS:** `<uname>`
**Hash:** `<hash>`

### Error signature
\`\`\`
<traceback or quoted text, max 1KB, paths normalized>
\`\`\`

### Failed command (if applicable)
\`\`\`bash
<command that failed, paths normalized>
\`\`\`

### First seen
<ISO 8601 UTC timestamp>

---
<sub>Auto-reported by Bedrock error hook. To opt out, set `error_reporting: false` in `.bedrock/config.json`.</sub>
```

**Reoccurrence comment** (when the issue already exists):

```markdown
Reoccurred at <UTC timestamp>. Plugin v<version>, <OS>.
```

If the issue is closed, the script reopens it via `gh issue reopen <num>` before commenting, and the comment is prefixed with `**Regression:**`.

### 4.6 Privacy — what's redacted

The `normalize()` function and content templates guarantee:
- ❌ No vault content (markdown bodies, frontmatter values)
- ❌ No absolute filesystem paths (replaced with `.../skills/...`)
- ❌ No vault entity names (people, teams, projects, etc.)
- ❌ No source URLs from the user's vault (Confluence pages, GDocs, internal repos). URLs in the captured signature are stripped completely (replaced with `<url-redacted>`)
- ✅ Skill name, plugin version, OS, error type, exception class, line numbers in plugin source files (under `skills/`, `hooks/`, etc.)

### 4.7 Auth failure handling

If `gh auth status` fails or `gh issue create` returns 401/403:

1. Log the would-be-created error to `~/.claude-bedrock-cache/error-reporter.log` (rotated at 1MB)
2. Set a session-scoped flag (`~/.claude-bedrock-cache/.auth-failed-<session_id>`) so subsequent invocations in the same session skip the slow path
3. Never prompt the user, never raise

---

## 5. Distribution

### 5.1 Plugin layout addition

```
claude-bedrock/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── hooks/
│   ├── hooks.json          ← registers Stop hook
│   └── error-reporter.py   ← the script
└── skills/...
```

### 5.2 `hooks/hooks.json` (illustrative — exact schema verified at implementation time)

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/error-reporter.py"
          }
        ]
      }
    ]
  }
}
```

When the user installs the `bedrock` plugin, Claude Code automatically loads this hook. No user action required.

> **Open question for implementation:** confirm the exact plugin-side hook registration syntax and the env var that resolves to the plugin root. The structure above matches Claude Code's user-level `settings.json` hooks. If plugins use a different schema, only this section changes.

### 5.3 Configuration

`.bedrock/config.json` gets a new top-level field:

```json
{
  "error_reporting": true
}
```

| Value | Behavior |
|---|---|
| `true` (default, also default if field missing) | Hook reports errors automatically |
| `false` | Hook exits at the opt-out check |

The default is `true` to match the maintainer's goal of getting telemetry from all users. The opt-out is documented in the issue body footer and in the plugin README.

---

## 6. Definition of Done

The implementation is complete when **all** of the following are true:

1. ✅ `hooks/error-reporter.py` exists and follows the pipeline in §4.1
2. ✅ `hooks/hooks.json` registers the Stop hook (or whatever syntax is correct for plugin-bundled hooks)
3. ✅ Fast gate path returns in under 200ms total (including Python interpreter startup) on a transcript without `/bedrock:`, measured with `time` over 10 invocations. In-process work (excluding interpreter startup) is under 50ms.
4. ✅ Logical-error regex catalog has at least the 5 patterns from §4.2 plus unit-style fixtures showing they match
5. ✅ A test fixture transcript with a planted `ModuleNotFoundError` produces exactly 1 GitHub issue title formatted per §4.5 (verified end-to-end against a test repo, not `iurykrieger/claude-bedrock`)
6. ✅ Re-running the same fixture produces a comment on the existing issue, not a new issue (dedup verified)
7. ✅ `error_reporting: false` in `.bedrock/config.json` causes the script to exit 0 without any `gh` call (verified by checking process did not invoke `gh`)
8. ✅ A simulated `gh auth status` failure causes the script to log locally and exit 0 (no exception, no prompt)
9. ✅ Issue body content matches §4.6 redaction rules — checked against a fixture containing user-vault paths and entity names
10. ✅ Plugin README and `.bedrock/config.json` schema documentation include the new `error_reporting` field and its default
11. ✅ Maintainer setup checklist created: labels `auto-reported`, `auto-bug`, and one per skill (`bedrock:ask`, `bedrock:teach`, `bedrock:preserve`, `bedrock:compress`, `bedrock:sync`, `bedrock:setup`, `bedrock:vaults`, `bedrock:healthcheck`) pre-created in `iurykrieger/claude-bedrock`

---

## 7. Open questions for implementation

Tracked separately from the design itself. None block presenting the design, but each gets resolved during implementation:

1. **Exact plugin-side hook registration syntax** — verify against Claude Code plugin docs at implementation time. If different, adjust §5.2 only.
2. **Env var for plugin root inside hook commands** — `${CLAUDE_PLUGIN_ROOT}` is illustrative; the real var name might differ.
3. **Vault path resolution from a Stop hook** — `.bedrock/config.json` lookup needs to know which vault is "active". Current plan: walk up from `CLAUDE_PROJECT_DIR` until we find `.bedrock/`, fall back to the default vault from `vaults.json`. Edge case if neither exists: assume `error_reporting: true` (consistent with default-on policy).
4. **Public-repo issue creation auth** — confirm whether anonymous users (without `gh auth`) can submit issues to a public repo, or whether all reporters need their own GH login. Current plan: silent skip if `gh auth status` fails.

---

## 8. Anti-scope (what this design explicitly does NOT do)

- Does not retry failed `gh` calls. One attempt, then log and skip.
- Does not collect anonymous telemetry beyond the issue body. No background pings.
- Does not modify any existing skill in `skills/` to make detection work — detection is transcript-based per §4.1.
- Does not add a UI prompt or notification when an issue is created. Silent reporting per the user's choice of automatic mode.
- Does not deduplicate across users — same hash from two different machines creates two `gh issue list` lookups, but if the issue exists, both comment on it. Cross-user dedup is naturally handled by the shared issue.
