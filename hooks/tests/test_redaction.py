import unittest
from pathlib import Path
import sys

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er


class TestRedaction(unittest.TestCase):
    def test_user_home_path_redacted(self):
        text = '/Users/iury.krieger/Documents/vault/people/alice.md'
        out = er.redact(text)
        self.assertNotIn("/Users/iury.krieger", out)
        self.assertIn(".../", out)

    def test_linux_home_redacted(self):
        text = '/home/dev/.claude/plugins/x/file.py'
        out = er.redact(text)
        self.assertNotIn("/home/dev", out)
        self.assertIn(".../", out)

    def test_plugin_path_preserved_relative_to_plugin_root(self):
        text = '/Users/foo/.claude/plugins/cache/x/skills/teach/scripts/extract.py'
        out = er.redact(text)
        self.assertIn("skills/teach/scripts/extract.py", out)

    def test_session_id_redacted(self):
        text = 'session_id=a1b2c3d4-5678-90ef-1234-567890abcdef failed'
        out = er.redact(text)
        self.assertNotIn("a1b2c3d4-5678", out)
        self.assertIn("<id-redacted>", out)

    def test_url_fully_redacted(self):
        text = 'fetched https://confluence.acme.internal/wiki/spaces/PAY/pages/12345/Spec'
        out = er.redact(text)
        self.assertNotIn("confluence.acme.internal", out)
        self.assertIn("<url-redacted>", out)

    def test_entity_filenames_in_paths_redacted(self):
        text = 'wrote /Users/foo/vault/people/alice-smith.md and teams/squad-payments.md'
        out = er.redact(text)
        self.assertNotIn("alice-smith", out)
        self.assertNotIn("squad-payments", out)

    def test_iso_timestamp_redacted(self):
        text = 'failed at 2026-05-03T14:22:31Z during sync'
        out = er.redact(text)
        self.assertNotIn("2026-05-03T14:22:31Z", out)
        self.assertIn("<ts-redacted>", out)

    def test_idempotent(self):
        text = 'session_id=a1b2c3d4-5678-90ef-1234-567890abcdef'
        once = er.redact(text)
        twice = er.redact(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
