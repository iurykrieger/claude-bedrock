import io
import json
import time
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import error_reporter as er

FIXTURES = Path(__file__).parent / "fixtures"


class TestPerformance(unittest.TestCase):
    def test_fast_gate_completes_under_50ms_excluding_python_startup(self):
        payload_str = json.dumps({
            "session_id": "x",
            "transcript_path": str(FIXTURES / "transcript_no_bedrock.jsonl"),
        })

        start = time.perf_counter()
        for _ in range(100):  # average over 100 iterations
            with patch.object(sys, "stdin", io.StringIO(payload_str)):
                er.main()
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        # 50ms per call is the budget for in-process work. Python interpreter startup
        # (~50-100ms when invoked as a subprocess from the hook) is outside our control
        # and measured separately in step 3.
        self.assertLess(elapsed_ms, 50, f"fast gate too slow: {elapsed_ms:.2f}ms")


if __name__ == "__main__":
    unittest.main()
