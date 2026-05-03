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
