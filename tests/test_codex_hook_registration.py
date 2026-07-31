"""Regression test for the Codex Stop-hook registration configs.

Both `codex_hooks.json` (repo-local) and `.codex/hooks.json` invoke
`cross_cli_status.py` directly via a raw `bash -lc` command rather than
through `.codex/stop-hook-dispatch.sh`. Unlike the dispatch script, that
raw command does not go through a wrapper that sets `HERMES_HOOK_CLI`,
so the env var must be set inline in the command string itself.

Without it, `_detect_cli()` falls through to shape-based detection. A
stale copy of the detector once matched real Codex payloads (which
carry `session_id` + `model` + `transcript_path`) against an older,
looser Claude-detection rule before reaching any Codex-specific check,
silently mislabeling Codex telemetry as "claude". Pinning the env var
in the registration command is what prevents that regardless of which
copy of `cross_cli_status.py` a given install ends up running.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class CodexHookRegistrationTestCase(unittest.TestCase):
    def _stop_commands(self, config_path: Path) -> list[str]:
        config = json.loads(config_path.read_text())
        stop_hooks = config["hooks"]["Stop"]
        commands = []
        for entry in stop_hooks:
            for hook in entry["hooks"]:
                commands.append(hook["command"])
        return commands

    def _assert_cross_cli_command_sets_env(self, config_path: Path) -> None:
        commands = self._stop_commands(config_path)
        cross_cli_commands = [c for c in commands if "cross_cli_status.py" in c]
        self.assertTrue(
            cross_cli_commands,
            f"{config_path} has no Stop command referencing cross_cli_status.py",
        )
        for command in cross_cli_commands:
            self.assertIn(
                "HERMES_HOOK_CLI=codex",
                command,
                f"{config_path}: cross_cli_status.py invocation must pin "
                "HERMES_HOOK_CLI=codex so shape-based detection is never "
                "the only signal for this registration path",
            )

    def test_repo_root_codex_hooks_json_pins_cli(self) -> None:
        self._assert_cross_cli_command_sets_env(REPO_ROOT / "codex_hooks.json")

    def test_dot_codex_hooks_json_pins_cli(self) -> None:
        self._assert_cross_cli_command_sets_env(REPO_ROOT / ".codex" / "hooks.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
