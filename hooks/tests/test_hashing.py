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


if __name__ == "__main__":
    unittest.main()
