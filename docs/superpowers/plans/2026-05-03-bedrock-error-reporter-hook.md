# Bedrock Error Reporter Hook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a plugin-bundled `Stop` hook that detects bedrock framework errors during a turn and auto-creates deduplicated GitHub issues on `iurykrieger/claude-bedrock`.

**Architecture:** Single Python entrypoint at `hooks/error_reporter.py`, registered via `hooks/hooks.json`. Pipeline: fast-gate → opt-out → extract → detect → hash → lookup → create/comment/reopen. Tests use Python's stdlib `unittest` (no new runtime dep).

**Tech Stack:** Python 3.9+, stdlib only (`json`, `re`, `hashlib`, `subprocess`, `pathlib`, `unittest`), `gh` CLI for GitHub API.

**Spec reference:** [docs/superpowers/specs/2026-05-03-bedrock-error-reporter-hook-design.md](../specs/2026-05-03-bedrock-error-reporter-hook-design.md)

---

## File Structure

The hook ships as a flat-ish layout under `hooks/`. Single Python file as entrypoint with helper functions; tests live alongside.

```
claude-bedrock/
├── hooks/
│   ├── hooks.json                # Plugin hook manifest (Claude Code reads this)
│   ├── error_reporter.py         # Single-file entrypoint with all pipeline functions
│   └── tests/
│       ├── __init__.py           # Empty (marks package)
│       ├── fixtures/
│       │   ├── transcript_no_bedrock.jsonl
│       │   ├── transcript_bedrock_clean.jsonl
│       │   ├── transcript_bedrock_traceback.jsonl
│       │   └── transcript_bedrock_logical_error.jsonl
│       ├── test_transcript.py
│       ├── test_detection.py
│       ├── test_hashing.py
│       ├── test_redaction.py
│       ├── test_issues.py
│       └── test_main.py
├── docs/
│   └── superpowers/
│       └── (spec + plan)
└── README.md                     # Add error_reporting docs
```

**Why a single file:** the pipeline is small (~400 lines), and a single file keeps Python startup fast (no extra package import overhead on the hot path). Functions are pure where possible to keep them unit-testable.

---

## Task 0: Maintainer pre-requisites (manual, one-time)

**Owner:** repository maintainer (iurykrieger). NOT covered by code; tracked here so it's not forgotten.

- [ ] **Step 1: Create labels in `iurykrieger/claude-bedrock`**

Run on a machine authenticated to the upstream repo:

```bash
gh label create auto-reported --repo iurykrieger/claude-bedrock --color "ededed" --description "Reported by the bedrock error hook" --force
gh label create auto-bug --repo iurykrieger/claude-bedrock --color "d73a4a" --description "Bug auto-detected from a user session" --force
for skill in ask teach preserve compress sync setup vaults healthcheck; do
  gh label create "bedrock:$skill" --repo iurykrieger/claude-bedrock --color "0e8a16" --description "Affects /bedrock:$skill" --force
done
```

Expected: 10 labels created (or already exist). No code change in this step — verifying with `gh label list --repo iurykrieger/claude-bedrock | grep auto-reported` should show the label.

- [ ] **Step 2: Confirm token used by users has `public_repo` scope**

Document in plugin README that users need `gh auth login` with default scopes. Issue creation on a public repo only requires the user to be authenticated; no special scope.

---

## Task 1: Hook manifest + no-op script

**Goal:** Get the plugin to invoke a script on `Stop` events. Verify wiring before adding any logic.

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/error_reporter.py`

- [ ] **Step 1: Write `hooks/hooks.json`**

```json
{
  "description": "Auto-report bedrock framework errors as GitHub issues",
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/error_reporter.py\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Write minimal `hooks/error_reporter.py`**

```python
#!/usr/bin/env python3
"""Bedrock error reporter hook — auto-creates GitHub issues for framework errors.

Stop hook entrypoint. Reads transcript via stdin JSON, scans the last turn
for bedrock framework errors (technical + logical), opens deduplicated issues
on iurykrieger/claude-bedrock via the gh CLI.

Never raises, always exits 0. Failures log to ~/.claude-bedrock-cache/error-reporter.log.
"""
import sys


def main() -> int:
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Make it executable**

```bash
chmod +x hooks/error_reporter.py
```

- [ ] **Step 4: Smoke-test the wiring**

Run a manual test by invoking the script with a fake stdin payload:

```bash
echo '{"session_id":"test","transcript_path":"/tmp/nonexistent.jsonl"}' | python3 hooks/error_reporter.py
echo "Exit: $?"
```

Expected output: `Exit: 0` (silent success).

- [ ] **Step 5: Commit**

```bash
git add hooks/hooks.json hooks/error_reporter.py
git commit -m "feat(hooks): scaffold error reporter hook entrypoint"
```

---

## Task 2: Test infrastructure + fast-gate

**Goal:** TDD setup with `unittest`, then implement the fast gate that exits when no `/bedrock:` activity is in the transcript.

**Files:**
- Create: `hooks/tests/__init__.py`
- Create: `hooks/tests/fixtures/transcript_no_bedrock.jsonl`
- Create: `hooks/tests/fixtures/transcript_bedrock_clean.jsonl`
- Create: `hooks/tests/test_transcript.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Create empty `hooks/tests/__init__.py`**

```python
```

- [ ] **Step 2: Create fixture `transcript_no_bedrock.jsonl`**

JSONL = one JSON object per line. Mimic Claude Code's transcript format.

```json
{"role":"user","message":{"content":[{"type":"text","text":"List files"}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"Here are the files."}]}}
```

- [ ] **Step 3: Create fixture `transcript_bedrock_clean.jsonl`**

```json
{"role":"user","message":{"content":[{"type":"text","text":"/bedrock:ask what is the auth flow"}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"The auth flow uses OAuth."}]}}
```

- [ ] **Step 4: Write the failing test**

In `hooks/tests/test_transcript.py`:

```python
import unittest
from pathlib import Path
import sys

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er

FIXTURES = Path(__file__).parent / "fixtures"


class TestFastGate(unittest.TestCase):
    def test_returns_false_when_no_bedrock_in_transcript(self):
        is_bedrock = er.contains_bedrock_invocation(FIXTURES / "transcript_no_bedrock.jsonl")
        self.assertFalse(is_bedrock)

    def test_returns_true_when_bedrock_in_transcript(self):
        is_bedrock = er.contains_bedrock_invocation(FIXTURES / "transcript_bedrock_clean.jsonl")
        self.assertTrue(is_bedrock)

    def test_returns_false_when_transcript_missing(self):
        is_bedrock = er.contains_bedrock_invocation(FIXTURES / "does_not_exist.jsonl")
        self.assertFalse(is_bedrock)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: Run the test (expected to fail)**

```bash
cd /Users/iury.krieger/Workspace/iurykrieger/claude-bedrock/.claude/worktrees/stupefied-wilbur-756394
python3 -m unittest hooks.tests.test_transcript -v
```

Expected: AttributeError because `contains_bedrock_invocation` doesn't exist.

- [ ] **Step 6: Implement `contains_bedrock_invocation` in `hooks/error_reporter.py`**

Add at module level (above `main()`):

```python
from pathlib import Path


# Keep window small for performance: only the most recent N lines matter,
# since hook fires per turn and older lines are from prior turns.
_TRANSCRIPT_TAIL_LINES = 200


def _read_transcript_tail(transcript_path: Path) -> str:
    """Read up to the last _TRANSCRIPT_TAIL_LINES of a JSONL transcript.

    Returns empty string if the file does not exist or is unreadable.
    """
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except (FileNotFoundError, OSError):
        return ""
    return "".join(lines[-_TRANSCRIPT_TAIL_LINES:])


def contains_bedrock_invocation(transcript_path: Path) -> bool:
    """Fast gate: returns True if '/bedrock:' appears in the recent transcript tail.

    This is intentionally a substring check rather than parsing JSON — we're optimizing
    for the 99% case where the answer is no.
    """
    tail = _read_transcript_tail(Path(transcript_path))
    return "/bedrock:" in tail
```

- [ ] **Step 7: Re-run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_transcript -v
```

Expected: 3 tests pass.

- [ ] **Step 8: Wire fast-gate into `main()`**

Replace the existing `main()`:

```python
import json
import os


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    transcript_path = hook_input.get("transcript_path")
    if not transcript_path:
        return 0

    if not contains_bedrock_invocation(Path(transcript_path)):
        return 0

    # Slow path comes in later tasks
    return 0
```

- [ ] **Step 9: Run tests once more to ensure nothing regressed**

```bash
python3 -m unittest hooks.tests.test_transcript -v
```

Expected: still 3 passing.

- [ ] **Step 10: Commit**

```bash
git add hooks/tests hooks/error_reporter.py
git commit -m "feat(hooks): fast-gate transcript scan for /bedrock: activity"
```

---

## Task 3: Opt-out check via `.bedrock/config.json`

**Goal:** Skip everything when the active vault has `error_reporting: false`. Default is `true` (matches spec).

**Files:**
- Create: `hooks/tests/test_config.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# hooks/tests/test_config.py
import json
import unittest
from pathlib import Path
import sys
import tempfile

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestOptOut(unittest.TestCase):
    def test_reporting_enabled_default_when_no_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"git": {"strategy": "commit-push"}}))
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_disabled_when_field_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            self.assertFalse(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": True}))
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_walks_up_to_find_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            nested = Path(tmp) / "sub" / "deep"
            nested.mkdir(parents=True)
            self.assertFalse(er.is_reporting_enabled(nested))

    def test_reporting_enabled_when_config_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text("not json {{{")
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_config -v
```

Expected: AttributeError on `is_reporting_enabled`.

- [ ] **Step 3: Implement `is_reporting_enabled`**

Add to `hooks/error_reporter.py`:

```python
def is_reporting_enabled(start_dir: Path) -> bool:
    """Walk up from start_dir looking for .bedrock/config.json.

    Returns True (default) if no config found, config malformed, or field missing.
    Returns False only if config explicitly sets error_reporting: false.
    """
    current = Path(start_dir).resolve()
    for candidate in [current, *current.parents]:
        cfg_path = candidate / ".bedrock" / "config.json"
        if cfg_path.is_file():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except (json.JSONDecodeError, OSError):
                return True  # default-on if config unreadable
            return bool(cfg.get("error_reporting", True))
    return True
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_config -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Wire opt-out into `main()`**

Modify `main()` to call `is_reporting_enabled` after the fast gate:

```python
def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    transcript_path = hook_input.get("transcript_path")
    if not transcript_path:
        return 0

    if not contains_bedrock_invocation(Path(transcript_path)):
        return 0

    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    if not is_reporting_enabled(cwd):
        return 0

    # Slow path comes in later tasks
    return 0
```

- [ ] **Step 6: Commit**

```bash
git add hooks/tests/test_config.py hooks/error_reporter.py
git commit -m "feat(hooks): opt-out via .bedrock/config.json error_reporting flag"
```

---

## Task 4: Extract context (skill name, tool results, assistant text)

**Goal:** Parse the JSONL transcript and pull out the structured pieces we need to scan.

**Files:**
- Create: `hooks/tests/fixtures/transcript_bedrock_traceback.jsonl`
- Modify: `hooks/tests/test_transcript.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Create fixture `transcript_bedrock_traceback.jsonl`**

Mimics a real Bash tool result with a Python traceback in stderr:

```json
{"role":"user","message":{"content":[{"type":"text","text":"/bedrock:teach https://example.com/doc"}]}}
{"role":"assistant","message":{"content":[{"type":"tool_use","id":"toolu_1","name":"Bash","input":{"command":"python3 /Users/foo/.claude/plugins/.../skills/teach/scripts/extract.py /tmp/in.pdf"}}]}}
{"role":"user","message":{"content":[{"type":"tool_result","tool_use_id":"toolu_1","is_error":true,"content":"Traceback (most recent call last):\n  File \"/Users/foo/.claude/plugins/.../skills/teach/scripts/extract.py\", line 42, in <module>\n    import docling\nModuleNotFoundError: No module named 'docling'"}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"I tried to run the teach skill but docling is missing on this machine."}]}}
```

> Note: the assistant text intentionally avoids any phrasing that matches the logical-error catalog from Task 6 — we only want one technical error to come out of this fixture so Task 12's count assertion is unambiguous.

- [ ] **Step 2: Append failing tests to `test_transcript.py`**

```python
class TestExtraction(unittest.TestCase):
    def test_extract_skill_invocation(self):
        skill = er.extract_skill_invocation(FIXTURES / "transcript_bedrock_traceback.jsonl")
        self.assertEqual(skill, "bedrock:teach")

    def test_extract_tool_results(self):
        results = er.extract_tool_results(FIXTURES / "transcript_bedrock_traceback.jsonl")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["is_error"])
        self.assertIn("ModuleNotFoundError", results[0]["content"])

    def test_extract_assistant_text(self):
        text = er.extract_assistant_text(FIXTURES / "transcript_bedrock_traceback.jsonl")
        self.assertIn("docling is missing", text)

    def test_extract_skill_invocation_returns_none_when_absent(self):
        skill = er.extract_skill_invocation(FIXTURES / "transcript_no_bedrock.jsonl")
        self.assertIsNone(skill)
```

- [ ] **Step 3: Run tests (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_transcript -v
```

Expected: 4 new tests fail with AttributeError.

- [ ] **Step 4: Implement extraction functions in `error_reporter.py`**

Add helpers for parsing JSONL safely:

```python
import re
from typing import Iterable


_BEDROCK_INVOCATION_RE = re.compile(r"/bedrock:(\w+)")


def _iter_transcript_lines(transcript_path: Path) -> Iterable[dict]:
    """Yield parsed JSON objects from each non-empty JSONL line. Skips malformed lines."""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except (FileNotFoundError, OSError):
        return


def extract_skill_invocation(transcript_path: Path) -> str | None:
    """Return the most recent /bedrock:<skill> reference, e.g. 'bedrock:teach'."""
    last = None
    for entry in _iter_transcript_lines(transcript_path):
        for block in entry.get("message", {}).get("content", []) or []:
            text = block.get("text") if isinstance(block, dict) else None
            if not text:
                continue
            for match in _BEDROCK_INVOCATION_RE.finditer(text):
                last = f"bedrock:{match.group(1)}"
    return last


def extract_tool_results(transcript_path: Path) -> list[dict]:
    """Return all tool_result blocks from the transcript with their is_error flag and content."""
    results = []
    for entry in _iter_transcript_lines(transcript_path):
        for block in entry.get("message", {}).get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_result":
                content = block.get("content", "")
                if isinstance(content, list):
                    content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
                results.append({
                    "tool_use_id": block.get("tool_use_id", ""),
                    "is_error": bool(block.get("is_error", False)),
                    "content": str(content),
                })
    return results


def extract_assistant_text(transcript_path: Path) -> str:
    """Concatenate all text blocks from assistant messages."""
    parts = []
    for entry in _iter_transcript_lines(transcript_path):
        if entry.get("role") != "assistant":
            continue
        for block in entry.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return "\n".join(parts)
```

- [ ] **Step 5: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_transcript -v
```

Expected: 7 tests pass (3 from Task 2 + 4 new).

- [ ] **Step 6: Commit**

```bash
git add hooks/tests/fixtures/transcript_bedrock_traceback.jsonl hooks/tests/test_transcript.py hooks/error_reporter.py
git commit -m "feat(hooks): extract skill name, tool results, and assistant text from transcript"
```

---

## Task 5: Detect technical errors

**Goal:** From the extracted tool_results, surface the technical errors (is_error true, tracebacks, non-zero exit codes).

**Files:**
- Create: `hooks/tests/test_detection.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# hooks/tests/test_detection.py
import unittest
from pathlib import Path
import sys

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestTechnicalErrors(unittest.TestCase):
    def test_is_error_true_produces_one_error(self):
        results = [{"tool_use_id": "x", "is_error": True, "content": "Traceback (most recent call last):\n  File \"a.py\", line 1, in <module>\n    raise ValueError()"}]
        errors = er.detect_technical_errors(results)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "python_traceback")

    def test_is_error_with_bash_failure_no_traceback(self):
        results = [{"tool_use_id": "x", "is_error": True, "content": "bash: command not found: docling"}]
        errors = er.detect_technical_errors(results)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "bash_failure")

    def test_no_errors_when_is_error_false(self):
        results = [{"tool_use_id": "x", "is_error": False, "content": "ok"}]
        errors = er.detect_technical_errors(results)
        self.assertEqual(errors, [])

    def test_signature_captures_last_traceback_frame(self):
        content = "Traceback (most recent call last):\n  File \"a.py\", line 1, in foo\n  File \"b.py\", line 2, in bar\nValueError: bad input"
        results = [{"tool_use_id": "x", "is_error": True, "content": content}]
        errors = er.detect_technical_errors(results)
        self.assertIn("ValueError", errors[0]["signature"])
        self.assertIn("b.py", errors[0]["signature"])

    def test_traceback_in_non_error_result_is_still_caught(self):
        # Some tools return is_error=false but still have a traceback in stdout
        content = "stderr: Traceback (most recent call last):\nValueError: oops"
        results = [{"tool_use_id": "x", "is_error": False, "content": content}]
        errors = er.detect_technical_errors(results)
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_detection -v
```

Expected: 5 tests fail with AttributeError on `detect_technical_errors`.

- [ ] **Step 3: Implement `detect_technical_errors`**

Add to `error_reporter.py`:

```python
_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\):", re.MULTILINE)
_LAST_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+), in (\w+)\n([^\n]*\n)?([A-Z][\w\.]+(?:Error|Exception):.*)', re.MULTILINE)


def detect_technical_errors(tool_results: list[dict]) -> list[dict]:
    """Inspect tool results and surface technical errors.

    Returns a list of dicts with keys: error_type, signature, raw.
    error_type is one of: 'python_traceback', 'bash_failure'.
    """
    errors = []
    for r in tool_results:
        content = r.get("content", "") or ""
        is_err = r.get("is_error", False)

        if _TRACEBACK_RE.search(content):
            sig = _extract_traceback_signature(content)
            errors.append({
                "error_type": "python_traceback",
                "signature": sig,
                "raw": content[:1024],
            })
        elif is_err:
            # Non-traceback failure flagged by Claude Code
            sig = content.strip().splitlines()[0] if content.strip() else "unknown bash failure"
            errors.append({
                "error_type": "bash_failure",
                "signature": sig[:200],
                "raw": content[:1024],
            })
    return errors


def _extract_traceback_signature(content: str) -> str:
    """Pull the deepest frame + exception line from a Python traceback."""
    matches = list(_LAST_FRAME_RE.finditer(content))
    if matches:
        m = matches[-1]
        return f'File "{m.group(1)}", line {m.group(2)} | {m.group(5)}'
    # Fallback: last non-empty line
    lines = [ln for ln in content.splitlines() if ln.strip()]
    return lines[-1] if lines else "Traceback (no frames extracted)"
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_detection -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_detection.py hooks/error_reporter.py
git commit -m "feat(hooks): detect python tracebacks and bash failures in tool results"
```

---

## Task 6: Detect logical errors via regex catalog

**Goal:** Scan the assistant's text for canonical "bedrock failed" phrasings.

**Files:**
- Create: `hooks/tests/fixtures/transcript_bedrock_logical_error.jsonl`
- Modify: `hooks/tests/test_detection.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Create fixture `transcript_bedrock_logical_error.jsonl`**

```json
{"role":"user","message":{"content":[{"type":"text","text":"/bedrock:teach https://example.com/x"}]}}
{"role":"assistant","message":{"content":[{"type":"text","text":"I tried to run /bedrock:teach but graphify returned an invalid structure. Failed to persist entity 'foo-service'."}]}}
```

- [ ] **Step 2: Append failing tests**

In `hooks/tests/test_detection.py`:

```python
class TestLogicalErrors(unittest.TestCase):
    def test_graphify_invalid_pattern_matches(self):
        text = "I ran the skill but graphify returned invalid output."
        errors = er.detect_logical_errors(text)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "logical_graphify_invalid")

    def test_entity_unwritable_pattern_matches(self):
        text = "Failed to persist entity 'billing-api'."
        errors = er.detect_logical_errors(text)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_type"], "logical_entity_unwritable")

    def test_multiple_distinct_patterns_produce_multiple_errors(self):
        text = "graphify returned invalid output. Failed to write entity 'x'."
        errors = er.detect_logical_errors(text)
        self.assertEqual(len(errors), 2)

    def test_no_match_no_errors(self):
        text = "Everything went fine."
        errors = er.detect_logical_errors(text)
        self.assertEqual(errors, [])

    def test_signature_includes_match_text(self):
        text = "graphify returned an invalid structure here"
        errors = er.detect_logical_errors(text)
        self.assertIn("invalid", errors[0]["signature"].lower())
```

- [ ] **Step 3: Run tests (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_detection -v
```

Expected: 5 new tests fail with AttributeError.

- [ ] **Step 4: Implement `detect_logical_errors` with catalog**

Add to `error_reporter.py`:

```python
# Regex catalog. ID -> (pattern, description). Keep small to avoid false positives.
_LOGICAL_ERROR_CATALOG = {
    "graphify_invalid": re.compile(r"graphify.{0,40}(returned|gave|produced).{0,20}invalid", re.IGNORECASE),
    "vault_corrupt": re.compile(r"vault\.json.{0,30}corrupt", re.IGNORECASE),
    "skill_failure": re.compile(r"bedrock\s+\w+\s+(skill\s+)?failed", re.IGNORECASE),
    "entity_unwritable": re.compile(r"failed\s+to\s+(write|persist)\s+entity", re.IGNORECASE),
    "sync_unauthorized": re.compile(r"(sync.{0,30}unauthorized|auth(?:entication)?\s+failed.{0,30}sync)", re.IGNORECASE),
}


def detect_logical_errors(assistant_text: str) -> list[dict]:
    """Scan the assistant's narrative for known framework-failure phrasings.

    Each matched pattern produces one error entry. Multiple distinct patterns produce
    multiple errors; multiple matches of the same pattern collapse to one.
    """
    errors = []
    for pattern_id, regex in _LOGICAL_ERROR_CATALOG.items():
        match = regex.search(assistant_text)
        if not match:
            continue
        # Capture a small window around the match for the signature
        start = max(0, match.start() - 20)
        end = min(len(assistant_text), match.end() + 60)
        snippet = assistant_text[start:end].replace("\n", " ").strip()
        errors.append({
            "error_type": f"logical_{pattern_id}",
            "signature": snippet[:200],
            "raw": snippet[:1024],
        })
    return errors
```

- [ ] **Step 5: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_detection -v
```

Expected: 10 tests pass (5 technical + 5 logical).

- [ ] **Step 6: Commit**

```bash
git add hooks/tests/fixtures/transcript_bedrock_logical_error.jsonl hooks/tests/test_detection.py hooks/error_reporter.py
git commit -m "feat(hooks): detect logical bedrock failures via regex catalog"
```

---

## Task 7: Redaction of paths, URLs, entity names

**Goal:** Before any network call or persistence, scrub user-private data from error signatures.

**Files:**
- Create: `hooks/tests/test_redaction.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# hooks/tests/test_redaction.py
import unittest
from pathlib import Path
import sys

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestRedaction(unittest.TestCase):
    def test_user_home_path_redacted(self):
        text = '/Users/iury.krieger/Documents/vault/people/alice.md'
        out = er.redact(text)
        self.assertNotIn("/Users/iury.krieger", out)
        self.assertIn(".../", out)

    def test_linux_home_redacted(self):
        text = '/home/dev/.claude/plugins/x/file.py'
        out = er.redact(text)
        self.assertNotIn("/home/dev", out)
        self.assertIn(".../", out)

    def test_plugin_path_preserved_relative_to_plugin_root(self):
        text = '/Users/foo/.claude/plugins/cache/x/skills/teach/scripts/extract.py'
        out = er.redact(text)
        # Plugin-relative portion should remain readable
        self.assertIn("skills/teach/scripts/extract.py", out)

    def test_session_id_redacted(self):
        text = 'session_id=a1b2c3d4-5678-90ef-1234-567890abcdef failed'
        out = er.redact(text)
        self.assertNotIn("a1b2c3d4-5678", out)
        self.assertIn("<id-redacted>", out)

    def test_url_fully_redacted(self):
        text = 'fetched https://confluence.acme.internal/wiki/spaces/PAY/pages/12345/Spec'
        out = er.redact(text)
        self.assertNotIn("confluence.acme.internal", out)
        self.assertIn("<url-redacted>", out)

    def test_entity_filenames_in_paths_redacted(self):
        text = 'wrote /Users/foo/vault/people/alice-smith.md and teams/squad-payments.md'
        out = er.redact(text)
        self.assertNotIn("alice-smith", out)
        self.assertNotIn("squad-payments", out)

    def test_iso_timestamp_redacted(self):
        text = 'failed at 2026-05-03T14:22:31Z during sync'
        out = er.redact(text)
        self.assertNotIn("2026-05-03T14:22:31Z", out)
        self.assertIn("<ts-redacted>", out)

    def test_idempotent(self):
        text = 'session_id=a1b2c3d4-5678-90ef-1234-567890abcdef'
        once = er.redact(text)
        twice = er.redact(once)
        self.assertEqual(once, twice)
```

- [ ] **Step 2: Run the test (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_redaction -v
```

Expected: 8 tests fail with AttributeError.

- [ ] **Step 3: Implement `redact()` in `error_reporter.py`**

```python
_HOME_PATH_RE = re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|/root)(?:/[^/\s]+)*?(?=/\.claude/plugins/[^/\s]+/[^/\s]+)")
_GENERIC_HOME_PATH_RE = re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|/root)")
_PLUGIN_PREFIX_RE = re.compile(r"\.claude/plugins/[^/\s]+/[^/\s]+/")
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s'\"<>)]+", re.IGNORECASE)
_ISO_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?")
_VAULT_ENTITY_FILE_RE = re.compile(r"\b(?:people|teams|actors|concepts|topics|discussions|projects|fleeting)/[\w-]+\.md\b")


def redact(text: str) -> str:
    """Strip user-identifying data: paths, URLs, UUIDs, timestamps, entity filenames.

    Order matters: home-path-with-plugin-lookahead first (so the plugin prefix can
    then be collapsed), then bare home paths, then everything else.

    Replacement uses '...' (no trailing slash) because the slash that follows
    the home prefix is preserved in the original string. This avoids producing
    '...//' artifacts.
    """
    if not text:
        return text

    text = _HOME_PATH_RE.sub("...", text)
    text = _PLUGIN_PREFIX_RE.sub("", text)
    text = _GENERIC_HOME_PATH_RE.sub("...", text)
    text = _URL_RE.sub("<url-redacted>", text)
    text = _UUID_RE.sub("<id-redacted>", text)
    text = _ISO_TIMESTAMP_RE.sub("<ts-redacted>", text)
    text = _VAULT_ENTITY_FILE_RE.sub(lambda m: f"{m.group(0).split('/')[0]}/<entity>.md", text)
    return text
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_redaction -v
```

Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_redaction.py hooks/error_reporter.py
git commit -m "feat(hooks): redact paths, URLs, ids, timestamps, and entity filenames"
```

---

## Task 8: Error hashing and dedup grouping

**Goal:** Compute a stable, short hash per unique error so we can dedup across runs.

**Files:**
- Create: `hooks/tests/test_hashing.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing test**

```python
# hooks/tests/test_hashing.py
import unittest
from pathlib import Path
import sys

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestErrorHash(unittest.TestCase):
    def test_hash_is_8_hex_chars(self):
        h = er.error_hash("bedrock:teach", "python_traceback", 'File "a.py", line 1 | ValueError')
        self.assertEqual(len(h), 8)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_hash_is_deterministic(self):
        a = er.error_hash("bedrock:teach", "python_traceback", "ValueError: oops")
        b = er.error_hash("bedrock:teach", "python_traceback", "ValueError: oops")
        self.assertEqual(a, b)

    def test_hash_normalizes_user_paths_in_signature(self):
        a = er.error_hash("bedrock:teach", "python_traceback", 'File "/Users/alice/.claude/plugins/x/y/skills/teach/extract.py", line 1 | ValueError')
        b = er.error_hash("bedrock:teach", "python_traceback", 'File "/Users/bob/.claude/plugins/x/y/skills/teach/extract.py", line 1 | ValueError')
        self.assertEqual(a, b)

    def test_hash_differs_when_skill_differs(self):
        a = er.error_hash("bedrock:teach", "bash_failure", "command not found")
        b = er.error_hash("bedrock:ask", "bash_failure", "command not found")
        self.assertNotEqual(a, b)


class TestDedupe(unittest.TestCase):
    def test_dedupe_collapses_duplicates(self):
        errs = [
            {"error_type": "python_traceback", "signature": 'File "a.py", line 1 | ValueError', "raw": "x"},
            {"error_type": "python_traceback", "signature": 'File "a.py", line 1 | ValueError', "raw": "x"},
        ]
        out = er.dedupe_by_hash(errs, skill="bedrock:teach")
        self.assertEqual(len(out), 1)
        self.assertIn("hash", out[0])

    def test_dedupe_preserves_distinct(self):
        errs = [
            {"error_type": "python_traceback", "signature": 'File "a.py", line 1 | ValueError', "raw": "x"},
            {"error_type": "python_traceback", "signature": 'File "b.py", line 2 | KeyError', "raw": "y"},
        ]
        out = er.dedupe_by_hash(errs, skill="bedrock:teach")
        self.assertEqual(len(out), 2)
```

- [ ] **Step 2: Run the test (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_hashing -v
```

Expected: 6 tests fail with AttributeError.

- [ ] **Step 3: Implement `error_hash` and `dedupe_by_hash`**

```python
import hashlib


def error_hash(skill: str, error_type: str, signature: str) -> str:
    """Deterministic 8-char hash over normalized error identity."""
    normalized = redact(signature)
    raw = f"{skill}|{error_type}|{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def dedupe_by_hash(errors: list[dict], skill: str) -> list[dict]:
    """Collapse duplicate errors by hash. Adds 'hash' key to each surviving entry."""
    seen = {}
    for err in errors:
        h = error_hash(skill, err["error_type"], err["signature"])
        if h in seen:
            continue
        err = {**err, "hash": h}
        seen[h] = err
    return list(seen.values())
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_hashing -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_hashing.py hooks/error_reporter.py
git commit -m "feat(hooks): error hashing with redaction-aware dedupe"
```

---

## Task 9: Issue lookup with local cache

**Goal:** Before opening an issue, check `gh issue list` (with a 5-min file cache) to know whether to create, comment, or reopen.

**Files:**
- Create: `hooks/tests/test_issues.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing test (mock-based)**

```python
# hooks/tests/test_issues.py
import json
import time
import unittest
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch, MagicMock

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestIssueLookup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_none_when_no_match_and_no_cache(self):
        with patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, "[]", "")
            issue = er.find_existing_issue("abcdef12", cache_dir=self.cache_dir)
        self.assertIsNone(issue)

    def test_returns_issue_when_gh_finds_one(self):
        with patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, json.dumps([{"number": 42, "state": "open"}]), "")
            issue = er.find_existing_issue("abcdef12", cache_dir=self.cache_dir)
        self.assertEqual(issue, {"number": 42, "state": "open"})

    def test_uses_cache_within_ttl(self):
        cache_path = self.cache_dir / "issues-abcdef12.json"
        cache_path.write_text(json.dumps({"issue": {"number": 99, "state": "open"}}))
        with patch("error_reporter._run_gh") as mock_gh:
            issue = er.find_existing_issue("abcdef12", cache_dir=self.cache_dir)
        mock_gh.assert_not_called()
        self.assertEqual(issue, {"number": 99, "state": "open"})

    def test_cache_miss_after_ttl(self):
        cache_path = self.cache_dir / "issues-abcdef12.json"
        cache_path.write_text(json.dumps({"issue": None}))
        # Backdate file mtime past TTL
        old = time.time() - 600
        import os
        os.utime(cache_path, (old, old))
        with patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, json.dumps([{"number": 7, "state": "closed"}]), "")
            issue = er.find_existing_issue("abcdef12", cache_dir=self.cache_dir)
        mock_gh.assert_called_once()
        self.assertEqual(issue, {"number": 7, "state": "closed"})

    def test_returns_none_when_gh_command_fails(self):
        with patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (1, "", "auth required")
            issue = er.find_existing_issue("abcdef12", cache_dir=self.cache_dir)
        self.assertIsNone(issue)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 5 tests fail with AttributeError on `find_existing_issue` / `_run_gh`.

- [ ] **Step 3: Implement `_run_gh` and `find_existing_issue`**

```python
import subprocess


_REPO = "iurykrieger/claude-bedrock"
_CACHE_TTL_SECONDS = 300
_DEFAULT_CACHE_DIR = Path.home() / ".claude-bedrock-cache"


def _run_gh(args: list[str], timeout: int = 5) -> tuple[int, str, str]:
    """Run gh CLI. Returns (exit_code, stdout, stderr). Never raises on subprocess errors."""
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, "", "gh not available or timed out"


def find_existing_issue(error_hash: str, cache_dir: Path | None = None) -> dict | None:
    """Look up an existing auto-reported issue by hash, with file-based 5-min cache.

    Returns None if no matching issue, or if gh is unavailable.
    """
    cache_dir = cache_dir or _DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"issues-{error_hash}.json"

    # Cache hit?
    if cache_path.is_file():
        age = time.time() - cache_path.stat().st_mtime
        if age < _CACHE_TTL_SECONDS:
            try:
                payload = json.loads(cache_path.read_text())
                return payload.get("issue")
            except (json.JSONDecodeError, OSError):
                pass  # fall through to fresh lookup

    code, stdout, _ = _run_gh([
        "issue", "list",
        "--repo", _REPO,
        "--label", "auto-reported",
        "--search", f"[bedrock][{error_hash}] in:title",
        "--state", "all",
        "--json", "number,state",
        "--limit", "1",
    ])
    if code != 0:
        return None
    try:
        issues = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    issue = issues[0] if issues else None
    try:
        cache_path.write_text(json.dumps({"issue": issue}))
    except OSError:
        pass
    return issue
```

(Add `import time` and `import subprocess` at the top if not already present.)

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_issues.py hooks/error_reporter.py
git commit -m "feat(hooks): cached gh issue lookup keyed by error hash"
```

---

## Task 10: Issue create / comment / reopen

**Goal:** Given a (possibly missing) existing issue, do the right thing: create new, comment on open, or reopen + comment if closed.

**Files:**
- Modify: `hooks/tests/test_issues.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Append failing tests**

In `hooks/tests/test_issues.py`:

```python
class TestIssueDispatch(unittest.TestCase):
    def setUp(self):
        self.err = {
            "hash": "abcdef12",
            "error_type": "python_traceback",
            "signature": 'File "x.py", line 1 | ValueError: oops',
            "raw": 'Traceback ...\n  File "x.py", line 1\nValueError: oops',
        }
        self.skill = "bedrock:teach"

    def test_creates_new_issue_when_none_exists(self):
        with patch("error_reporter.find_existing_issue", return_value=None), \
             patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, "https://github.com/iurykrieger/claude-bedrock/issues/100", "")
            er.handle_error(self.err, self.skill)
            args = mock_gh.call_args.args[0]
            self.assertIn("create", args)
            self.assertIn("--title", args)
            title = args[args.index("--title") + 1]
            self.assertIn("[bedrock][abcdef12]", title)
            self.assertIn("teach", title)

    def test_comments_when_open_issue_exists(self):
        with patch("error_reporter.find_existing_issue", return_value={"number": 42, "state": "open"}), \
             patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, "", "")
            er.handle_error(self.err, self.skill)
            args = mock_gh.call_args.args[0]
            self.assertIn("comment", args)
            self.assertIn("42", args)

    def test_reopens_and_comments_when_closed(self):
        with patch("error_reporter.find_existing_issue", return_value={"number": 42, "state": "closed"}), \
             patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, "", "")
            er.handle_error(self.err, self.skill)
            calls = [c.args[0] for c in mock_gh.call_args_list]
            # First call should be reopen, second comment
            self.assertIn("reopen", calls[0])
            self.assertIn("comment", calls[1])

    def test_issue_body_contains_redacted_signature(self):
        err = {**self.err, "signature": '/Users/alice/.claude/plugins/x/y/skills/teach/extract.py | ValueError'}
        with patch("error_reporter.find_existing_issue", return_value=None), \
             patch("error_reporter._run_gh") as mock_gh:
            mock_gh.return_value = (0, "https://...", "")
            er.handle_error(err, self.skill)
            args = mock_gh.call_args.args[0]
            body = args[args.index("--body") + 1]
            self.assertNotIn("/Users/alice", body)

    def test_handle_error_swallows_gh_failures(self):
        with patch("error_reporter.find_existing_issue", return_value=None), \
             patch("error_reporter._run_gh", return_value=(1, "", "auth failed")):
            # Should not raise
            er.handle_error(self.err, self.skill)
```

- [ ] **Step 2: Run tests (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 5 new tests fail with AttributeError on `handle_error`.

- [ ] **Step 3: Implement `handle_error` plus templates**

```python
import platform
from datetime import datetime, timezone


def _plugin_version() -> str:
    plugin_json = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "unknown")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "unknown"


def _build_issue_title(error: dict, skill: str) -> str:
    short_skill = skill.replace("bedrock:", "")
    sig = redact(error["signature"])
    if len(sig) > 80:
        sig = sig[:77] + "..."
    return f"[bedrock][{error['hash']}] {short_skill}: {sig}"


def _build_issue_body(error: dict, skill: str) -> str:
    redacted_sig = redact(error["signature"])
    redacted_raw = redact(error.get("raw", ""))
    return (
        "## Auto-reported error\n\n"
        f"**Skill:** `{skill}`\n"
        f"**Error type:** `{error['error_type']}`\n"
        f"**Plugin version:** `{_plugin_version()}`\n"
        f"**OS:** `{platform.system().lower()} {platform.release()}`\n"
        f"**Hash:** `{error['hash']}`\n\n"
        "### Error signature\n"
        "```\n"
        f"{redacted_sig}\n"
        "```\n\n"
        "### Raw context (redacted)\n"
        "```\n"
        f"{redacted_raw}\n"
        "```\n\n"
        f"### First seen\n"
        f"{datetime.now(timezone.utc).isoformat()}\n\n"
        "---\n"
        "<sub>Auto-reported by Bedrock error hook. To opt out, set "
        "`error_reporting: false` in `.bedrock/config.json`.</sub>\n"
    )


def _build_comment_body(prefix: str = "") -> str:
    return (
        f"{prefix}Reoccurred at {datetime.now(timezone.utc).isoformat()}. "
        f"Plugin v{_plugin_version()}, {platform.system().lower()} {platform.release()}.\n"
    )


def handle_error(error: dict, skill: str) -> None:
    """Create / comment / reopen the GitHub issue for this error.

    Never raises. Failures are silent (caller already exits 0).
    """
    existing = find_existing_issue(error["hash"])

    if existing is None:
        labels = ["auto-reported", "auto-bug", skill]
        cmd = [
            "issue", "create",
            "--repo", _REPO,
            "--title", _build_issue_title(error, skill),
            "--body", _build_issue_body(error, skill),
        ]
        for label in labels:
            cmd.extend(["--label", label])
        _run_gh(cmd, timeout=10)
        return

    issue_num = str(existing["number"])
    if existing.get("state") == "closed":
        _run_gh(["issue", "reopen", "--repo", _REPO, issue_num], timeout=5)
        comment_body = _build_comment_body(prefix="**Regression:** ")
    else:
        comment_body = _build_comment_body()

    _run_gh([
        "issue", "comment",
        "--repo", _REPO,
        issue_num,
        "--body", comment_body,
    ], timeout=10)
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 10 tests pass (5 lookup + 5 dispatch).

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_issues.py hooks/error_reporter.py
git commit -m "feat(hooks): create / comment / reopen GitHub issues with redacted bodies"
```

---

## Task 11: Auth-failure session flag + local log

**Goal:** When `gh` fails (auth or network), don't keep retrying within the same session. Log locally instead.

**Files:**
- Modify: `hooks/tests/test_issues.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Append failing tests**

```python
class TestAuthFallback(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.tmp.name)
        self.session_id = "test-session-123"
        self.error = {
            "hash": "deadbeef",
            "error_type": "python_traceback",
            "signature": "x",
            "raw": "raw",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_auth_failure_writes_local_log_and_session_flag(self):
        with patch("error_reporter._run_gh", return_value=(127, "", "gh: command not found")), \
             patch("error_reporter._cache_dir", return_value=self.cache_dir):
            er.handle_error_with_fallback(self.error, "bedrock:teach", self.session_id)
        log_path = self.cache_dir / "error-reporter.log"
        flag_path = self.cache_dir / f".auth-failed-{self.session_id}"
        self.assertTrue(log_path.exists())
        self.assertTrue(flag_path.exists())
        self.assertIn("deadbeef", log_path.read_text())

    def test_subsequent_calls_in_same_session_skip_gh(self):
        flag = self.cache_dir / f".auth-failed-{self.session_id}"
        flag.touch()
        with patch("error_reporter._run_gh") as mock_gh, \
             patch("error_reporter._cache_dir", return_value=self.cache_dir):
            er.handle_error_with_fallback(self.error, "bedrock:teach", self.session_id)
        mock_gh.assert_not_called()
```

- [ ] **Step 2: Run tests (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 2 new tests fail (`handle_error_with_fallback` and `_cache_dir` don't exist).

- [ ] **Step 3: Implement `_cache_dir`, `handle_error_with_fallback`, local logging**

```python
def _cache_dir() -> Path:
    """Indirection for tests. Returns the cache directory, creating it if needed."""
    cache_dir = _DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _log_local(error: dict, skill: str, reason: str) -> None:
    log_path = _cache_dir() / "error-reporter.log"
    line = (
        f"{datetime.now(timezone.utc).isoformat()} "
        f"hash={error['hash']} skill={skill} type={error['error_type']} reason={reason}\n"
    )
    try:
        # Rotate at 1 MB
        if log_path.is_file() and log_path.stat().st_size > 1_048_576:
            log_path.rename(log_path.with_suffix(".log.1"))
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def handle_error_with_fallback(error: dict, skill: str, session_id: str) -> None:
    """Wraps handle_error with auth-failure detection and per-session circuit breaker."""
    flag_path = _cache_dir() / f".auth-failed-{session_id}"
    if flag_path.exists():
        _log_local(error, skill, "auth-flag-set-skip")
        return

    # Probe auth before doing real work; cheap call (~50ms typical)
    code, _, _ = _run_gh(["auth", "status"], timeout=3)
    if code != 0:
        try:
            flag_path.touch()
        except OSError:
            pass
        _log_local(error, skill, "auth-failed")
        return

    try:
        handle_error(error, skill)
    except Exception as exc:  # pragma: no cover — defensive
        _log_local(error, skill, f"unexpected:{type(exc).__name__}")
```

- [ ] **Step 4: Run tests (expected to pass)**

```bash
python3 -m unittest hooks.tests.test_issues -v
```

Expected: 12 tests pass.

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_issues.py hooks/error_reporter.py
git commit -m "feat(hooks): per-session auth-failure circuit breaker with local log"
```

---

## Task 12: Wire the full pipeline in `main()`

**Goal:** Connect every piece. End-to-end test through fixtures.

**Files:**
- Create: `hooks/tests/test_main.py`
- Modify: `hooks/error_reporter.py`

- [ ] **Step 1: Write the failing end-to-end test**

```python
# hooks/tests/test_main.py
import io
import json
import unittest
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er

FIXTURES = Path(__file__).parent / "fixtures"


class TestMainPipeline(unittest.TestCase):
    def _run_main(self, transcript_fixture: str, project_dir: Path | None = None) -> int:
        payload = {
            "session_id": "test-session",
            "transcript_path": str(FIXTURES / transcript_fixture),
        }
        env = {"CLAUDE_PROJECT_DIR": str(project_dir or Path("/tmp"))}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.dict("os.environ", env, clear=False):
            return er.main()

    def test_exits_when_no_bedrock(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_no_bedrock.jsonl")
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_exits_when_bedrock_clean(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_clean.jsonl")
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_dispatches_on_traceback(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_traceback.jsonl")
        self.assertEqual(rc, 0)
        self.assertEqual(mock_handle.call_count, 1)
        err, skill, session = mock_handle.call_args.args
        self.assertEqual(skill, "bedrock:teach")
        self.assertEqual(err["error_type"], "python_traceback")

    def test_dispatches_on_logical_error(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_logical_error.jsonl")
        self.assertEqual(rc, 0)
        # Two logical patterns in the fixture: graphify_invalid + entity_unwritable
        self.assertEqual(mock_handle.call_count, 2)

    def test_opt_out_short_circuits_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            with patch("error_reporter.handle_error_with_fallback") as mock_handle:
                rc = self._run_main("transcript_bedrock_traceback.jsonl", project_dir=Path(tmp))
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_handles_missing_transcript_path(self):
        with patch.object(sys, "stdin", io.StringIO('{"session_id":"x"}')):
            rc = er.main()
        self.assertEqual(rc, 0)

    def test_handles_malformed_stdin(self):
        with patch.object(sys, "stdin", io.StringIO("not json")):
            rc = er.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests (expected to fail)**

```bash
python3 -m unittest hooks.tests.test_main -v
```

Expected: most tests fail because `main()` is still a stub past the opt-out check.

- [ ] **Step 3: Replace `main()` with the full pipeline**

```python
def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    transcript_path = hook_input.get("transcript_path")
    session_id = hook_input.get("session_id", "unknown")
    if not transcript_path:
        return 0

    transcript = Path(transcript_path)
    if not contains_bedrock_invocation(transcript):
        return 0

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    if not is_reporting_enabled(project_dir):
        return 0

    skill = extract_skill_invocation(transcript) or "bedrock:unknown"
    tool_results = extract_tool_results(transcript)
    assistant_text = extract_assistant_text(transcript)

    errors = detect_technical_errors(tool_results) + detect_logical_errors(assistant_text)
    if not errors:
        return 0

    for err in dedupe_by_hash(errors, skill=skill):
        try:
            handle_error_with_fallback(err, skill, session_id)
        except Exception as exc:  # pragma: no cover
            _log_local(err, skill, f"top-level:{type(exc).__name__}")

    return 0
```

- [ ] **Step 4: Run all tests**

```bash
python3 -m unittest discover hooks/tests -v
```

Expected: All tests pass (transcript + config + detection + redaction + hashing + issues + main = 40+ tests).

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_main.py hooks/error_reporter.py
git commit -m "feat(hooks): wire full error-reporting pipeline in main()"
```

---

## Task 13: Performance smoke test

**Goal:** Verify the no-bedrock fast path is fast enough that users won't notice.

**Files:**
- Create: `hooks/tests/test_perf.py`

- [ ] **Step 1: Write the perf test**

```python
# hooks/tests/test_perf.py
import io
import json
import time
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er

FIXTURES = Path(__file__).parent / "fixtures"


class TestPerformance(unittest.TestCase):
    def test_fast_gate_completes_under_50ms_excluding_python_startup(self):
        payload_str = json.dumps({
            "session_id": "x",
            "transcript_path": str(FIXTURES / "transcript_no_bedrock.jsonl"),
        })

        start = time.perf_counter()
        for _ in range(100):  # average over 100 iterations
            with patch.object(sys, "stdin", io.StringIO(payload_str)):
                er.main()
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        # 50ms per call is the budget for in-process work. Python interpreter startup
        # (~50-100ms when invoked as a subprocess from the hook) is outside our control
        # and measured separately in step 3.
        self.assertLess(elapsed_ms, 50, f"fast gate too slow: {elapsed_ms:.2f}ms")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the perf test**

```bash
python3 -m unittest hooks.tests.test_perf -v
```

Expected: passes. If it fails, profile with `python3 -X importtime hooks/error_reporter.py < /dev/null` to find slow imports and move heavy modules (`subprocess`, `hashlib`) into lazy imports inside the slow-path functions.

- [ ] **Step 3: Measure full subprocess invocation latency for documentation**

```bash
echo '{"session_id":"x","transcript_path":"hooks/tests/fixtures/transcript_no_bedrock.jsonl"}' > /tmp/hook_in.json
time (for i in {1..10}; do python3 hooks/error_reporter.py < /tmp/hook_in.json; done)
```

Expected: total <2s for 10 invocations (~200ms per invocation including Python interpreter startup). Record the actual number in the spec's "Performance budget" section.

- [ ] **Step 4: Update spec with measured numbers**

In `docs/superpowers/specs/2026-05-03-bedrock-error-reporter-hook-design.md`, replace the Performance budget table values with measured numbers, and update DoD §6.3 to read:

```
3. ✅ Fast gate path returns in under 200ms total (including Python interpreter startup) on a transcript without `/bedrock:`, measured with `time` over 10 invocations
```

- [ ] **Step 5: Commit**

```bash
git add hooks/tests/test_perf.py docs/superpowers/specs/2026-05-03-bedrock-error-reporter-hook-design.md
git commit -m "test(hooks): add fast-gate perf smoke test and tighten spec budget"
```

---

## Task 14: Documentation — README + config schema

**Goal:** Tell users that this hook exists, what it does, and how to opt out.

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md` (add a one-line entry to the Configuration section)

- [ ] **Step 1: Find the right section in README.md**

```bash
grep -n "Configuration\|config.json\|^## " README.md
```

- [ ] **Step 2: Add error-reporting section to README.md**

After the existing "Configuration" or "Git Workflow" section, append:

```markdown
## Error Reporting

The `bedrock` plugin auto-reports framework errors as GitHub issues on
[iurykrieger/claude-bedrock](https://github.com/iurykrieger/claude-bedrock) so
maintainers learn about real-world failures.

**What gets reported**
- Python tracebacks from skill scripts
- Non-zero exit codes from skill bash commands
- Known logical-failure phrases in Claude's text (small auditable regex catalog)

**What never gets reported**
- Vault content (markdown bodies, frontmatter values)
- Absolute filesystem paths (replaced with `.../`)
- Vault entity names (people, teams, projects, etc.)
- URLs from your vault (Confluence, Google Docs, internal repos)

**How to opt out**

Add `"error_reporting": false` to your vault's `.bedrock/config.json`:

\`\`\`json
{
  "error_reporting": false
}
\`\`\`

Default is `true`. The hook silently skips reporting if `gh` is not installed
or you're not authenticated, and logs the would-be report to
`~/.claude-bedrock-cache/error-reporter.log`.
```

- [ ] **Step 3: Add a one-line note to CLAUDE.md**

In the existing "Git Workflow" or configuration section, add:

```markdown
### Error Reporting

The plugin includes a `Stop` hook (`hooks/error_reporter.py`) that auto-creates
GitHub issues on framework errors. Disable per-vault with
`"error_reporting": false` in `.bedrock/config.json`. Default: `true`.
```

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: document error_reporting flag and auto-issue behavior"
```

---

## Task 15: Manual end-to-end smoke test against a private test repo

**Goal:** Before relying on this in production, verify the full flow against a throwaway repo (NOT `iurykrieger/claude-bedrock`).

**Files:** none.

- [ ] **Step 1: Create a private throwaway repo for testing**

```bash
gh repo create iurykrieger/bedrock-error-reporter-test --private --confirm
```

- [ ] **Step 2: Pre-create the labels in that repo**

Run the same loop from Task 0 but pointing at the test repo:

```bash
TEST_REPO=iurykrieger/bedrock-error-reporter-test
gh label create auto-reported --repo $TEST_REPO --color "ededed" --force
gh label create auto-bug --repo $TEST_REPO --color "d73a4a" --force
for skill in ask teach preserve compress sync setup vaults healthcheck; do
  gh label create "bedrock:$skill" --repo $TEST_REPO --color "0e8a16" --force
done
```

- [ ] **Step 3: Temporarily point the script at the test repo**

In `hooks/error_reporter.py`, change `_REPO = "iurykrieger/claude-bedrock"` to `_REPO = "iurykrieger/bedrock-error-reporter-test"`. **Do NOT commit this change.**

- [ ] **Step 4: Run the script against the traceback fixture**

```bash
python3 hooks/error_reporter.py < <(jq -n --arg p "$(pwd)/hooks/tests/fixtures/transcript_bedrock_traceback.jsonl" '{session_id:"smoke-test",transcript_path:$p}')
```

Expected: `gh issue list --repo iurykrieger/bedrock-error-reporter-test --label auto-reported` shows 1 new issue with title starting `[bedrock][<hash>] teach:`.

- [ ] **Step 5: Run the same fixture again — verify dedup**

Re-run Step 4. Verify: same `gh issue list` output (still 1 issue, not 2). The issue should have a comment with "Reoccurred at...".

- [ ] **Step 6: Close the issue, run again — verify reopen**

```bash
ISSUE_NUM=$(gh issue list --repo iurykrieger/bedrock-error-reporter-test --label auto-reported --json number --jq '.[0].number')
gh issue close --repo iurykrieger/bedrock-error-reporter-test "$ISSUE_NUM"
# Run the script again
python3 hooks/error_reporter.py < <(jq -n --arg p "$(pwd)/hooks/tests/fixtures/transcript_bedrock_traceback.jsonl" '{session_id:"smoke-test",transcript_path:$p}')
gh issue view "$ISSUE_NUM" --repo iurykrieger/bedrock-error-reporter-test --json state --jq '.state'
```

Expected: state is `OPEN` again, with a new comment prefixed `**Regression:**`.

- [ ] **Step 7: Verify opt-out**

```bash
mkdir -p /tmp/optout-test/.bedrock
echo '{"error_reporting": false}' > /tmp/optout-test/.bedrock/config.json
CLAUDE_PROJECT_DIR=/tmp/optout-test python3 hooks/error_reporter.py < <(jq -n --arg p "$(pwd)/hooks/tests/fixtures/transcript_bedrock_traceback.jsonl" '{session_id:"optout-test",transcript_path:$p}')
```

Expected: no new issue, no new comment in test repo.

- [ ] **Step 8: Restore `_REPO` constant and clean up**

In `hooks/error_reporter.py`, restore `_REPO = "iurykrieger/claude-bedrock"`. Delete the test repo:

```bash
gh repo delete iurykrieger/bedrock-error-reporter-test --yes
```

- [ ] **Step 9: Commit only if any cleanup change is needed**

If `_REPO` was accidentally left modified, this commit restores it. If everything is already correct, skip.

```bash
git add hooks/error_reporter.py
git commit -m "chore(hooks): restore production repo target after smoke test" || true
```

---

## Task 16: Push the branch and update the PR

**Goal:** Final integration check.

- [ ] **Step 1: Run all tests one last time**

```bash
python3 -m unittest discover hooks/tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify hook file is executable and JSON parses**

```bash
test -x hooks/error_reporter.py && echo "executable: OK"
python3 -c "import json; json.load(open('hooks/hooks.json'))" && echo "hooks.json valid"
```

- [ ] **Step 3: Push**

```bash
git push origin feat/stupefied-wilbur-756394
```

- [ ] **Step 4: Verify the PR (#25) shows all the new commits**

```bash
gh pr view 25 --repo iurykrieger/claude-bedrock
```

Expected: PR diff includes `hooks/`, `tests/`, README/CLAUDE.md edits, and the spec/plan in `docs/superpowers/`.

---

## Self-Review checklist (run before declaring done)

- [ ] All DoD items in [the spec](../specs/2026-05-03-bedrock-error-reporter-hook-design.md#6-definition-of-done) check off
- [ ] Task 0 maintainer setup done in upstream repo before merging
- [ ] Spec timing budget updated to realistic numbers (Task 13 step 4)
- [ ] No leftover `_REPO = "iurykrieger/bedrock-error-reporter-test"` (Task 15 step 8)
- [ ] All commits use conventional-commit style matching the repo's history
- [ ] Run `python3 -m unittest discover hooks/tests` exits 0 with all tests passing
