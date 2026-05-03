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


if __name__ == "__main__":
    unittest.main()
