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

    def test_extraction_scoped_to_last_turn_ignores_old_errors(self):
        # Fixture has an old traceback in turn 1, then a clean turn 2.
        # Extraction should only return the LAST turn's content.
        skill = er.extract_skill_invocation(FIXTURES / "transcript_bedrock_old_turn.jsonl")
        # Last turn is "List my files" — not a /bedrock: invocation
        self.assertIsNone(skill)
        results = er.extract_tool_results(FIXTURES / "transcript_bedrock_old_turn.jsonl")
        # The old traceback in turn 1 must NOT appear in results
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
