import json
import os
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
        old = time.time() - 600
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
            er.handle_error(self.err, self.skill)


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


if __name__ == "__main__":
    unittest.main()
