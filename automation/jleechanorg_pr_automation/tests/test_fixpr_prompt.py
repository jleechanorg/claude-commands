#!/usr/bin/env python3
"""Tests for fixpr prompt formatting."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation.jleechanorg_pr_automation import orchestrated_pr_runner as runner


class _FakeDispatcher:
    def __init__(self) -> None:
        self.task_description = None

    def analyze_task_and_create_agents(self, task_description: str, forced_cli: str = "claude"):
        self.task_description = task_description
        return [{"name": "test-agent"}]

    def create_dynamic_agent(self, agent_spec):  # pragma: no cover - simple stub
        return True


class TestFixprPrompt(unittest.TestCase):
    def test_fixpr_commit_message_includes_mode_and_model(self):
        pr_payload = {
            "repo_full": "jleechanorg/worldarchitect.ai",
            "repo": "worldarchitect.ai",
            "number": 123,
            "title": "Test PR",
            "branch": "feature/test-fixpr",
        }

        dispatcher = _FakeDispatcher()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(runner, "WORKSPACE_ROOT_BASE", Path(tmpdir)):
                with patch.object(runner, "kill_tmux_session_if_exists", lambda _: None):
                    ok = runner.dispatch_agent_for_pr(dispatcher, pr_payload, agent_cli="codex")

        self.assertTrue(ok)
        self.assertIsNotNone(dispatcher.task_description)
        self.assertIn(
            "[fixpr codex-automation-commit] fix PR #123",
            dispatcher.task_description,
        )
        # Verify the prompt instructs fetching ALL feedback sources (inline review comments included).
        self.assertIn("/pulls/{pr}/comments", dispatcher.task_description)
        self.assertIn("/pulls/{pr}/reviews", dispatcher.task_description)
        self.assertIn("/issues/{pr}/comments", dispatcher.task_description)
        self.assertIn("--paginate", dispatcher.task_description)


if __name__ == "__main__":
    unittest.main()
