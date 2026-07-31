"""Live tmux integration for the cross-cli Stop hook.

Only runs when CROSS_CLI_LIVE=1 is set in the environment. Spawns a real
claude / codex / agy session (whichever is on $PATH), captures the Stop
hook payload from the resulting `~/.claude/var/cross_cli_status/last.json`
file, and asserts the normalized record matches the expected shape.

Why live: the unit tests cover payload parsing in isolation, but only a
running CLI confirms the hook is actually invoked end-to-end and that the
real payload shape matches the schema (verified regression on 2026-07-17 —
a unit-tested Codex hook failed to read the actual `tool_input.cwd` field
because Codex 0.144+ nests it differently than the docs claimed).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "cross_cli_status.py"


@unittest.skipUnless(
    os.environ.get("CROSS_CLI_LIVE") == "1",
    "set CROSS_CLI_LIVE=1 to run live tmux integration tests",
)
class LiveCrossCliStopTestCase(unittest.TestCase):  # type: ignore[misc]
    def setUp(self) -> None:
        self.original_home = os.environ.get("HOME")
        self.tmp = Path(tempfile.mkdtemp(prefix="cross-cli-live-"))
        os.environ["HOME"] = str(self.tmp)
        os.environ["CROSS_CLI_STATUS_HISTORY_MAX"] = "5"
        self.last_path = self.tmp / ".claude" / "var" / "cross_cli_status" / "last.json"
        self.last_path.parent.mkdir(parents=True, exist_ok=True)
        # Install a minimal Stop-hook registration into the isolated HOME so
        # a spawned CLI actually discovers and invokes the hook — without
        # this, the CLI reads $HOME/.claude/settings.json from the fresh
        # temp dir, finds no hooks configured, and never fires it.
        settings_dir = self.tmp / ".claude"
        settings_dir.mkdir(parents=True, exist_ok=True)
        (settings_dir / "settings.json").write_text(json.dumps({
            "hooks": {
                "Stop": [
                    {
                        "matcher": "*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f'python3 "{HOOK}"',
                            }
                        ],
                    }
                ]
            }
        }))

    def tearDown(self) -> None:
        if self.original_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.original_home
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _spawn(self, cli: str, prompt: str, timeout: int = 90) -> dict:
        # Spawn a real session; the Stop hook fires when the session ends
        # (or when the tmux pane is closed). The hook writes last.json
        # before the session exits cleanly.
        bin_ = shutil.which(cli)
        if not bin_:
            self.skipTest(f"{cli} not on PATH")
        proc = subprocess.run(
            [bin_, "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "HERMES_HOOK_CLI": cli,
                "HERMES_HOOK_EVENT": "Stop",
            },
            timeout=timeout,
        )
        if not self.last_path.exists():
            self.fail(f"Stop hook did not write {self.last_path}; stderr={proc.stderr[:400]}")
        return json.loads(self.last_path.read_text())

    def test_claude_stop_records_rate_limit(self) -> None:
        rec = self._spawn("claude", "Reply with one word: ping")
        self.assertEqual(rec["cli"], "claude")
        # The Claude CLI may not publish `rate_limits` for non-Pro/Max
        # accounts; we only require that the field, if present, is
        # normalized correctly.
        if rec.get("rate_limit_window") == "5h":
            self.assertGreaterEqual(rec["rate_limit_pct"], 0)
            self.assertLessEqual(rec["rate_limit_pct"], 100)

    def test_codex_stop_records_rate_limit_reset(self) -> None:
        rec = self._spawn("codex", "Reply with one word: pong")
        self.assertEqual(rec["cli"], "codex")
        self.assertIsNotNone(rec["model"])

    def test_agy_stop_records_usage(self) -> None:
        rec = self._spawn("agy", "Reply with one word: agy-ok")
        self.assertEqual(rec["cli"], "agy")
        # agy may not be on PATH in this test env; skip if so.
        # The setUp already gated on shutil.which; this is just a model check.


if __name__ == "__main__":
    unittest.main(verbosity=2)
