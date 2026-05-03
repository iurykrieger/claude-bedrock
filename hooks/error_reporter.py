#!/usr/bin/env python3
"""Bedrock error reporter hook — auto-creates GitHub issues for framework errors.

Stop hook entrypoint. Reads transcript via stdin JSON, scans the last turn
for bedrock framework errors (technical + logical), opens deduplicated issues
on iurykrieger/claude-bedrock via the gh CLI.

Never raises, always exits 0. Failures log to ~/.claude-bedrock-cache/error-reporter.log.
"""
import json
import os
import sys
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
