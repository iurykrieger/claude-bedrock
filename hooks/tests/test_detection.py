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
        content = "stderr: Traceback (most recent call last):\nValueError: oops"
        results = [{"tool_use_id": "x", "is_error": False, "content": content}]
        errors = er.detect_technical_errors(results)
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
