#!/usr/bin/env python3
"""Smoke test for validate-browser-mode.sh — ensures it exits 0 when log is clean."""
from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "validate-browser-mode.sh"


class ValidateScriptTests(unittest.TestCase):
    def test_exits_zero_when_log_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = pathlib.Path(tmp) / "gateway.log"
            log.write_text("2026-06-08T10:00:00 INFO   agent started\n2026-06-08T10:00:01 INFO   task complete\n")
            env = dict(os.environ, HERMES_GATEWAY_LOG=str(log))
            result = subprocess.run(  # noqa: S603
                ["bash", str(SCRIPT)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("OK", result.stdout)

    def test_exits_zero_when_log_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, HERMES_GATEWAY_LOG=str(pathlib.Path(tmp) / "missing.log"))
            result = subprocess.run(  # noqa: S603
                ["bash", str(SCRIPT)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            # Missing log should warn but not fail (per script contract).
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)

    def test_exits_nonzero_when_log_shows_headed(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = pathlib.Path(tmp) / "gateway.log"
            log.write_text(
                textwrap.dedent(
                    """\
                    2026-06-08T10:00:00 INFO   agent started
                    2026-06-08T10:00:01 TOOL   chrome_use_browser show_browser=true
                    2026-06-08T10:00:02 INFO   screenshot saved
                    """
                )
            )
            env = dict(os.environ, HERMES_GATEWAY_LOG=str(log))
            result = subprocess.run(  # noqa: S603
                ["bash", str(SCRIPT)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
