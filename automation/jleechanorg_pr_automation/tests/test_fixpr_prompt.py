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
        # Verify the prompt instructs fetching ALL feedback sources using Python requests (not gh CLI)
        # Check for Python requests syntax instead of gh CLI syntax
        self.assertIn("requests.get", dispatcher.task_description)
        # Check for API endpoints - the prompt uses full URLs with actual PR number
        self.assertIn("pulls/123/comments", dispatcher.task_description, "Prompt should contain pulls/comments endpoint")
        self.assertIn("pulls/123/reviews", dispatcher.task_description, "Prompt should contain reviews endpoint")
        self.assertIn("issues/123/comments", dispatcher.task_description, "Prompt should contain issues/comments endpoint")
        # Should use Python requests params instead of --paginate
        self.assertIn("params=", dispatcher.task_description, "Prompt should use params= for pagination")


if __name__ == "__main__":
    unittest.main()
