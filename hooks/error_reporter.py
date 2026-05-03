#!/usr/bin/env python3
"""Bedrock error reporter hook — auto-creates GitHub issues for framework errors.

Stop hook entrypoint. Reads transcript via stdin JSON, scans the last turn
for bedrock framework errors (technical + logical), opens deduplicated issues
on iurykrieger/claude-bedrock via the gh CLI.

Never raises, always exits 0. Failures log to ~/.claude-bedrock-cache/error-reporter.log.
"""
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


# Keep window small for performance: only the most recent N lines matter,
# since hook fires per turn and older lines are from prior turns.
_TRANSCRIPT_TAIL_LINES = 200

_BEDROCK_INVOCATION_RE = re.compile(r"/bedrock:(\w+)")

_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\):", re.MULTILINE)
_LAST_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+), in (\w+)\n((?!\s*File ")[^\n]*\n)?([A-Z][\w\.]+(?:Error|Exception):.*)', re.MULTILINE)

# Regex catalog. ID -> compiled regex. Keep small to avoid false positives.
_LOGICAL_ERROR_CATALOG = {
    "graphify_invalid": re.compile(r"graphify.{0,40}(returned|gave|produced).{0,20}invalid", re.IGNORECASE),
    "vault_corrupt": re.compile(r"vault\.json.{0,30}corrupt", re.IGNORECASE),
    "skill_failure": re.compile(r"bedrock\s+\w+\s+(skill\s+)?failed", re.IGNORECASE),
    "entity_unwritable": re.compile(r"failed\s+to\s+(write|persist)\s+entity", re.IGNORECASE),
    "sync_unauthorized": re.compile(r"(sync.{0,30}unauthorized|auth(?:entication)?\s+failed.{0,30}sync)", re.IGNORECASE),
}

# Redaction regexes — order matters in redact(). See function docstring.
_HOME_PATH_RE = re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|/root)(?:/[^/\s]+)*?(?=/\.claude/plugins/[^/\s]+/[^/\s]+)")
_GENERIC_HOME_PATH_RE = re.compile(r"(?:/Users/[^/\s]+|/home/[^/\s]+|/root)")
_PLUGIN_PREFIX_RE = re.compile(r"\.claude/plugins/[^/\s]+/[^/\s]+/")
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s'\"<>)]+", re.IGNORECASE)
_ISO_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?")
_VAULT_ENTITY_FILE_RE = re.compile(r"\b(?:people|teams|actors|concepts|topics|discussions|projects|fleeting)/[\w-]+\.md\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_CC_LIKE_RE = re.compile(r"\b\d[\d -]{11,17}\d\b")
_API_KEY_RE = re.compile(r"\b(?:sk_(?:live|test)|ghp|ghs|gho|ghu|ghr|xox[abps]|AKIA|ASIA|GITHUB_TOKEN)[\w_-]{10,}\b", re.IGNORECASE)
_BARE_WIKILINK_RE = re.compile(r"\[\[[\w/-]+\]\]")


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


def _iter_last_turn_lines(transcript_path: Path) -> list[dict]:
    """Return parsed JSON entries from the last turn.

    A turn boundary is defined by a role=user entry containing a type=text content
    block (i.e., a user-typed message, not a tool_result). Returns the last such
    entry and everything after it. If no boundary is found, returns all entries.
    """
    entries = list(_iter_transcript_lines(transcript_path))
    if not entries:
        return []

    # Walk backwards to find the last user-typed message
    last_user_text_idx = None
    for idx in range(len(entries) - 1, -1, -1):
        entry = entries[idx]
        if entry.get("role") != "user":
            continue
        for block in entry.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                last_user_text_idx = idx
                break
        if last_user_text_idx is not None:
            break

    if last_user_text_idx is None:
        return entries  # fallback: scan everything
    return entries[last_user_text_idx:]


def extract_skill_invocation(transcript_path: Path) -> str | None:
    """Return the most recent /bedrock:<skill> reference, e.g. 'bedrock:teach'."""
    last = None
    for entry in _iter_last_turn_lines(transcript_path):
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
    for entry in _iter_last_turn_lines(transcript_path):
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
    for entry in _iter_last_turn_lines(transcript_path):
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
    return "Traceback (no frames extracted)"


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
        # Signature stays generic to avoid leaking user content; raw keeps a short snippet
        # for context but will be aggressively redacted by _build_issue_body.
        start = max(0, match.start() - 20)
        end = min(len(assistant_text), match.end() + 60)
        snippet = assistant_text[start:end].replace("\n", " ").strip()
        errors.append({
            "error_type": f"logical_{pattern_id}",
            "signature": f"matched pattern: {pattern_id}",
            "raw": snippet[:512],
        })
    return errors


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
    text = _EMAIL_RE.sub("<email-redacted>", text)
    text = _API_KEY_RE.sub("<key-redacted>", text)
    text = _UUID_RE.sub("<id-redacted>", text)
    text = _ISO_TIMESTAMP_RE.sub("<ts-redacted>", text)
    text = _CC_LIKE_RE.sub("<digits-redacted>", text)
    text = _VAULT_ENTITY_FILE_RE.sub(lambda m: f"{m.group(0).split('/')[0]}/<entity>.md", text)
    text = _BARE_WIKILINK_RE.sub("[[<entity>]]", text)
    return text


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

    if cache_path.is_file():
        age = time.time() - cache_path.stat().st_mtime
        if age < _CACHE_TTL_SECONDS:
            try:
                payload = json.loads(cache_path.read_text())
                return payload.get("issue")
            except (json.JSONDecodeError, OSError):
                pass

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
    redacted_raw = " ".join(redacted_raw.split())[:256]  # collapse whitespace, hard cap
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


if __name__ == "__main__":
    sys.exit(main())
