#!/usr/bin/env python3
"""
Tests for _cleanup_pending_reviews method and prompt API endpoint verification.

Tests ensure:
1. _cleanup_pending_reviews correctly identifies and deletes pending reviews
2. Prompts contain the correct API endpoint for threaded replies
"""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from automation.jleechanorg_pr_automation import orchestrated_pr_runner as runner
from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCleanupPendingReviews(unittest.TestCase):
    """Test _cleanup_pending_reviews method"""

    def setUp(self):
        """Set up test environment"""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.logger = Mock()

    def test_cleanup_pending_reviews_deletes_pending_reviews(self):
        """Test that pending reviews from automation user are deleted"""
        repo_full = "owner/repo"
        pr_number = 123

        # Mock reviews API response with pending review from automation user
        reviews_response = [
            {
                "id": 1001,
                "state": "PENDING",
                "user": {"login": "test-automation-user"},
            },
            {
                "id": 1002,
                "state": "APPROVED",
                "user": {"login": "test-automation-user"},
            },
            {
                "id": 1003,
                "state": "PENDING",
                "user": {"login": "other-user"},
            },
        ]

        delete_calls = []

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            if "reviews" in " ".join(cmd) and "DELETE" not in cmd:
                # Fetch reviews command
                return SimpleNamespace(
                    returncode=0,
                    stdout="\n".join(json.dumps(r) for r in reviews_response),
                    stderr="",
                )
            elif "DELETE" in cmd:
                # Delete review command
                delete_calls.append(cmd)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        # Should only delete pending review from automation user (id 1001)
        assert len(delete_calls) == 1, f"Expected 1 delete call, got {len(delete_calls)}"
        assert "1001" in " ".join(delete_calls[0]), "Should delete review #1001"
        self.monitor.logger.info.assert_any_call(
            "🧹 Deleted pending review #1001 from test-automation-user on PR #123"
        )
        self.monitor.logger.info.assert_any_call("✅ Cleaned up 1 pending review(s) on PR #123")

    def test_cleanup_pending_reviews_handles_no_pending_reviews(self):
        """Test that method handles case with no pending reviews gracefully"""
        repo_full = "owner/repo"
        pr_number = 123

        # Mock reviews API response with no pending reviews
        reviews_response = [
            {"id": 1001, "state": "APPROVED", "user": {"login": "test-automation-user"}},
            {"id": 1002, "state": "COMMENTED", "user": {"login": "other-user"}},
        ]

        delete_calls = []

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            if "reviews" in " ".join(cmd) and "DELETE" not in cmd:
                return SimpleNamespace(
                    returncode=0,
                    stdout="\n".join(json.dumps(r) for r in reviews_response),
                    stderr="",
                )
            elif "DELETE" in cmd:
                delete_calls.append(cmd)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        # Should not delete anything
        assert len(delete_calls) == 0, "Should not delete any reviews when none are pending"
        # Should not log cleanup success message
        cleanup_logs = [
            call.args[0] for call in self.monitor.logger.info.call_args_list if "Cleaned up" in call.args[0]
        ]
        assert len(cleanup_logs) == 0, "Should not log cleanup when no reviews deleted"

    def test_cleanup_pending_reviews_handles_api_failure(self):
        """Test that method handles API failure gracefully"""
        repo_full = "owner/repo"
        pr_number = 123

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            if "reviews" in " ".join(cmd) and "DELETE" not in cmd:
                # Simulate API failure
                return SimpleNamespace(returncode=1, stdout="", stderr="API error")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            # Should not raise exception
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        self.monitor.logger.debug.assert_called()

    def test_cleanup_pending_reviews_handles_invalid_repo_format(self):
        """Test that method handles invalid repo_full format"""
        repo_full = "invalid-format"
        pr_number = 123

        self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        self.monitor.logger.warning.assert_called_with(
            "Cannot parse repo_full 'invalid-format' for pending review cleanup"
        )

    def test_cleanup_pending_reviews_handles_exception(self):
        """Test that method handles exceptions gracefully"""
        repo_full = "owner/repo"
        pr_number = 123

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            raise Exception("Unexpected error")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            # Should not raise exception
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        self.monitor.logger.debug.assert_called()

    def test_cleanup_pending_reviews_deletes_multiple_pending_reviews(self):
        """Test that multiple pending reviews from automation user are all deleted"""
        repo_full = "owner/repo"
        pr_number = 123

        # Mock reviews API response with multiple pending reviews from automation user
        reviews_response = [
            {"id": 1001, "state": "PENDING", "user": {"login": "test-automation-user"}},
            {"id": 1002, "state": "PENDING", "user": {"login": "test-automation-user"}},
            {"id": 1003, "state": "PENDING", "user": {"login": "other-user"}},
        ]

        delete_calls = []

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            if "reviews" in " ".join(cmd) and "DELETE" not in cmd:
                return SimpleNamespace(
                    returncode=0,
                    stdout="\n".join(json.dumps(r) for r in reviews_response),
                    stderr="",
                )
            elif "DELETE" in cmd:
                delete_calls.append(cmd)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        # Should delete both pending reviews from automation user
        assert len(delete_calls) == 2, f"Expected 2 delete calls, got {len(delete_calls)}"
        self.monitor.logger.info.assert_any_call("✅ Cleaned up 2 pending review(s) on PR #123")

    def test_cleanup_pending_reviews_handles_null_user(self):
        """Test that method handles null user gracefully (prevents AttributeError)"""
        repo_full = "owner/repo"
        pr_number = 123

        # Mock reviews API response with pending review with null user
        reviews_response = [
            {
                "id": 1001,
                "state": "PENDING",
                "user": None,  # API can return null user
            },
            {
                "id": 1002,
                "state": "PENDING",
                "user": {"login": "test-automation-user"},
            },
        ]

        delete_calls = []

        def mock_execute_subprocess(cmd, timeout=None, check=False):
            if "reviews" in " ".join(cmd) and "DELETE" not in cmd:
                return SimpleNamespace(
                    returncode=0,
                    stdout="\n".join(json.dumps(r) for r in reviews_response),
                    stderr="",
                )
            elif "DELETE" in cmd:
                delete_calls.append(cmd)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch(
            "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
            side_effect=mock_execute_subprocess,
        ):
            # Should not raise AttributeError
            self.monitor._cleanup_pending_reviews(repo_full, pr_number)

        # Should only delete pending review from automation user (id 1002), not null user (id 1001)
        assert len(delete_calls) == 1, f"Expected 1 delete call, got {len(delete_calls)}"
        assert "1002" in " ".join(delete_calls[0]), "Should delete review #1002 (with valid user)"
        assert "1001" not in " ".join(delete_calls[0]), "Should NOT delete review #1001 (null user)"


class TestPromptAPIEndpoint(unittest.TestCase):
    """Test that prompts contain correct API endpoint"""

    def setUp(self):
        """Set up test environment"""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_fix_comment_prompt_contains_correct_endpoint(self):
        """Test that fix-comment prompt contains correct API endpoint"""
        repository = "owner/repo"
        pr_number = 123
        pr_data = {"headRefName": "feature/branch"}
        head_sha = "abc123def456"

        prompt = self.monitor._build_fix_comment_prompt_body(
            repository, pr_number, pr_data, head_sha, agent_cli="claude"
        )

        # Should contain correct endpoint: /comments with in_reply_to parameter
        assert "/pulls/123/comments" in prompt, "Prompt should contain /comments endpoint"
        assert "in_reply_to" in prompt, "Prompt should contain in_reply_to parameter"
        assert "-F in_reply_to" in prompt, "Prompt should use -F flag for numeric parameter"
        assert "-f body" in prompt, "Prompt should use -f flag for string parameter"

        # Should NOT contain incorrect endpoint
        assert "/comments/{comment_id}/replies" not in prompt, "Prompt should NOT contain incorrect /replies endpoint"

    def test_orchestrated_pr_runner_prompt_contains_correct_endpoint(self):
        """Test that orchestrated_pr_runner prompt contains correct API endpoint"""
        repo_full = "owner/repo"
        pr_number = 123
        branch = "feature/branch"
        agent_cli = "claude"

        # Get the task description from dispatch_agent_for_pr
        class FakeDispatcher:
            def __init__(self):
                self.task_description = None

            def analyze_task_and_create_agents(self, task_description, forced_cli=None):
                self.task_description = task_description
                return [{"id": "agent"}]

            def create_dynamic_agent(self, spec):
                return True

        dispatcher = FakeDispatcher()
        pr = {"repo_full": repo_full, "repo": "repo", "number": pr_number, "branch": branch}

        with patch.object(runner, "WORKSPACE_ROOT_BASE", Path("/tmp")):
            with patch.object(runner, "kill_tmux_session_if_exists", lambda _: None):
                with patch.object(runner, "prepare_workspace_dir", lambda repo, name: None):
                    runner.dispatch_agent_for_pr(dispatcher, pr, agent_cli=agent_cli)

        assert dispatcher.task_description is not None, "Task description should be set"
        prompt = dispatcher.task_description

        # Should contain correct endpoint: /comments with in_reply_to parameter
        assert "/pulls/123/comments" in prompt, "Prompt should contain /comments endpoint"
        assert "in_reply_to" in prompt, "Prompt should contain in_reply_to parameter"
        assert "-F in_reply_to" in prompt, "Prompt should use -F flag for numeric parameter"
        assert "-f body" in prompt, "Prompt should use -f flag for string parameter"

        # Should NOT contain incorrect endpoint
        assert "/comments/{comment_id}/replies" not in prompt, "Prompt should NOT contain incorrect /replies endpoint"


if __name__ == "__main__":
    unittest.main()
