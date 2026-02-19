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

    def analyze_task_and_create_agents(self, task_description: str, forced_cli: str = "claude", wrap_prompt: bool = False, **kwargs):
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

    def test_fixpr_uses_local_branch_name_not_remote_branch(self):
        """Test that fixpr uses local branch name fixpr_{remote_branch} instead of remote branch directly."""
        pr_payload = {
            "repo_full": "jleechanorg/worldarchitect.ai",
            "repo": "worldarchitect.ai",
            "number": 456,
            "title": "Test PR with feature branch",
            "branch": "feature/add-cool-feature",
        }

        dispatcher = _FakeDispatcher()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(runner, "WORKSPACE_ROOT_BASE", Path(tmpdir)):
                with patch.object(runner, "kill_tmux_session_if_exists", lambda _: None):
                    ok = runner.dispatch_agent_for_pr(dispatcher, pr_payload, agent_cli="claude")

        self.assertTrue(ok)
        self.assertIsNotNone(dispatcher.task_description)

        # Local branch name should be fixpr_feature-add-cool-feature (sanitized)
        expected_local_branch = "fixpr_feature-add-cool-feature"

        # Task description should use local branch for checkout
        self.assertIn(f"git checkout -B {expected_local_branch}", dispatcher.task_description,
                      "Task description should use 'git checkout -B' with local branch name")

        # Should fetch the remote branch
        self.assertIn("git fetch origin feature/add-cool-feature", dispatcher.task_description,
                      "Task description should fetch the remote branch")

        # Should track the remote branch
        self.assertIn("origin/feature/add-cool-feature", dispatcher.task_description,
                      "Task description should reference origin/remote_branch for tracking")

        # Should NOT use plain 'git checkout feature/add-cool-feature'
        self.assertNotIn("git checkout feature/add-cool-feature\n", dispatcher.task_description,
                         "Task description should NOT use direct checkout of remote branch")

    def test_fixpr_local_branch_name_with_special_chars(self):
        """Test that local branch names are properly sanitized from remote branch names."""
        pr_payload = {
            "repo_full": "jleechanorg/worldarchitect.ai",
            "repo": "worldarchitect.ai",
            "number": 789,
            "title": "Test PR with special chars in branch",
            "branch": "fix/bug#123/urgent",
        }

        dispatcher = _FakeDispatcher()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(runner, "WORKSPACE_ROOT_BASE", Path(tmpdir)):
                with patch.object(runner, "kill_tmux_session_if_exists", lambda _: None):
                    ok = runner.dispatch_agent_for_pr(dispatcher, pr_payload, agent_cli="claude")

        self.assertTrue(ok)
        self.assertIsNotNone(dispatcher.task_description)

        # Local branch name should be sanitized: fixpr_fix-bug-123-urgent
        expected_local_branch = "fixpr_fix-bug-123-urgent"

        # Should use local branch name
        self.assertIn(expected_local_branch, dispatcher.task_description,
                      "Task description should contain sanitized local branch name")

        # Should still reference the original remote branch
        self.assertIn("fix/bug#123/urgent", dispatcher.task_description,
                      "Task description should still reference original remote branch name")


if __name__ == "__main__":
    unittest.main()
