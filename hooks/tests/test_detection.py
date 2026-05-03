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

    def test_signature_includes_pattern_id(self):
        text = "graphify returned an invalid structure here"
        errors = er.detect_logical_errors(text)
        self.assertEqual(errors[0]["signature"], "matched pattern: graphify_invalid")


class TestLogicalSignatureRedaction(unittest.TestCase):
    def test_logical_signature_does_not_leak_user_content(self):
        text = "graphify returned invalid output for customer acme-fintech-acquisition"
        errors = er.detect_logical_errors(text)
        self.assertEqual(len(errors), 1)
        self.assertNotIn("acme-fintech", errors[0]["signature"])
        self.assertEqual(errors[0]["signature"], "matched pattern: graphify_invalid")


if __name__ == "__main__":
    unittest.main()
