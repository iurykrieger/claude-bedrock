import io
import json
import unittest
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er

FIXTURES = Path(__file__).parent / "fixtures"


class TestMainPipeline(unittest.TestCase):
    def _run_main(self, transcript_fixture: str, project_dir: Path | None = None) -> int:
        payload = {
            "session_id": "test-session",
            "transcript_path": str(FIXTURES / transcript_fixture),
        }
        env = {"CLAUDE_PROJECT_DIR": str(project_dir or Path("/tmp"))}
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
             patch.dict("os.environ", env, clear=False):
            return er.main()

    def test_exits_when_no_bedrock(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_no_bedrock.jsonl")
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_exits_when_bedrock_clean(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_clean.jsonl")
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_dispatches_on_traceback(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_traceback.jsonl")
        self.assertEqual(rc, 0)
        self.assertEqual(mock_handle.call_count, 1)
        err, skill, session = mock_handle.call_args.args
        self.assertEqual(skill, "bedrock:teach")
        self.assertEqual(err["error_type"], "python_traceback")

    def test_dispatches_on_logical_error(self):
        with patch("error_reporter.handle_error_with_fallback") as mock_handle:
            rc = self._run_main("transcript_bedrock_logical_error.jsonl")
        self.assertEqual(rc, 0)
        # Two logical patterns in the fixture: graphify_invalid + entity_unwritable
        self.assertEqual(mock_handle.call_count, 2)

    def test_opt_out_short_circuits_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            with patch("error_reporter.handle_error_with_fallback") as mock_handle:
                rc = self._run_main("transcript_bedrock_traceback.jsonl", project_dir=Path(tmp))
        self.assertEqual(rc, 0)
        mock_handle.assert_not_called()

    def test_handles_missing_transcript_path(self):
        with patch.object(sys, "stdin", io.StringIO('{"session_id":"x"}')):
            rc = er.main()
        self.assertEqual(rc, 0)

    def test_handles_malformed_stdin(self):
        with patch.object(sys, "stdin", io.StringIO("not json")):
            rc = er.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
