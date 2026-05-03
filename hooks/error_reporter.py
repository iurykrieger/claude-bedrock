#!/usr/bin/env python3
"""Bedrock error reporter hook — auto-creates GitHub issues for framework errors.

Stop hook entrypoint. Reads transcript via stdin JSON, scans the last turn
for bedrock framework errors (technical + logical), opens deduplicated issues
on iurykrieger/claude-bedrock via the gh CLI.

Never raises, always exits 0. Failures log to ~/.claude-bedrock-cache/error-reporter.log.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable


# Keep window small for performance: only the most recent N lines matter,
# since hook fires per turn and older lines are from prior turns.
_TRANSCRIPT_TAIL_LINES = 200

_BEDROCK_INVOCATION_RE = re.compile(r"/bedrock:(\w+)")

_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\):", re.MULTILINE)
_LAST_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+), in (\w+)\n((?!\s*File ")[^\n]*\n)?([A-Z][\w\.]+(?:Error|Exception):.*)', re.MULTILINE)


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

    Intentionally a substring check, not JSON parsing — optimized for the 99% case
    where the answer is no. False positives (e.g., the substring quoted in an
    assistant message) only cost an extra slow-path traversal in the next stage;
    false negatives would mean lost error reports, which is the worse failure mode.
    """
    tail = _read_transcript_tail(Path(transcript_path))
    return "/bedrock:" in tail


def is_reporting_enabled(start_dir: Path) -> bool:
    """Walk up from start_dir looking for .bedrock/config.json.

    Returns True (default) if no config found, config malformed, or field missing.
    Returns False only if config explicitly sets error_reporting to the JSON `false`
    boolean — null, "false" strings, 0, etc. all default-on. Opt-out must be
    well-formed and intentional.
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
            val = cfg.get("error_reporting", True)
            return val if isinstance(val, bool) else True
    return True


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
    lines = [ln for ln in content.splitlines() if ln.strip()]
    return lines[-1] if lines else "Traceback (no frames extracted)"


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


if __name__ == "__main__":
    sys.exit(main())
