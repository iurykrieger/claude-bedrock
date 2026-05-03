import json
import unittest
from pathlib import Path
import sys
import tempfile

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestOptOut(unittest.TestCase):
    def test_reporting_enabled_default_when_no_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"git": {"strategy": "commit-push"}}))
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_disabled_when_field_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            self.assertFalse(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": True}))
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_walks_up_to_find_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text(json.dumps({"error_reporting": False}))
            nested = Path(tmp) / "sub" / "deep"
            nested.mkdir(parents=True)
            self.assertFalse(er.is_reporting_enabled(nested))

    def test_reporting_enabled_when_config_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text("not json {{{")
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_is_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text('{"error_reporting": null}')
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))

    def test_reporting_enabled_when_field_is_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = Path(tmp) / ".bedrock"
            cfg_dir.mkdir()
            (cfg_dir / "config.json").write_text('{"error_reporting": "false"}')
            self.assertTrue(er.is_reporting_enabled(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
