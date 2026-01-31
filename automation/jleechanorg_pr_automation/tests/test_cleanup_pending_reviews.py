#!/usr/bin/env python3
"""
Tests for _cleanup_pending_reviews method and prompt API endpoint verification.

Tests ensure:
1. _cleanup_pending_reviews correctly identifies and deletes pending reviews
2. Prompts contain the correct API endpoint for threaded replies
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from jleechanorg_pr_automation import orchestrated_pr_runner as runner
from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCleanupPendingReviews(unittest.TestCase):
    """Test _cleanup_pending_reviews method"""

    def setUp(self):
        """Set up test environment"""
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager"):
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
            if "DELETE" in cmd:
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
            if "DELETE" in cmd:
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
            if "DELETE" in cmd:
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
            if "DELETE" in cmd:
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
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager"):
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

        # Should contain correct endpoint: /comments with in_reply_to parameter (Python requests syntax)
        assert "/pulls/123/comments" in prompt or "pulls/123/comments" in prompt, "Prompt should contain /comments endpoint"
        assert "in_reply_to" in prompt, "Prompt should contain in_reply_to parameter"
        # Should use Python requests POST syntax specifically (not just GET)
        assert "post_pr_comment_python" in prompt or "requests.post" in prompt, "Prompt should use Python requests POST for posting comments, not gh CLI"
        
        # Should NOT contain incorrect endpoint
        assert "/comments/{comment_id}/replies" not in prompt, "Prompt should NOT contain incorrect /replies endpoint"


class TestCleanupBeforeEligibilityChecks(unittest.TestCase):
    """Test that cleanup runs before eligibility checks in run_monitoring_cycle"""

    def setUp(self):
        """Set up test environment"""
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager"):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.logger = Mock()

    def test_cleanup_runs_before_eligibility_checks(self):
        """Test that cleanup is called before eligibility checks in run_monitoring_cycle"""
        repo_full = "owner/repo"
        pr_number = 123
        pr = {
            "number": pr_number,
            "repository": "repo",
            "repositoryFullName": repo_full,
            "headRefName": "feature/branch",
            "state": "open",
        }

        # Setup order tracking mock
        manager = Mock()
        manager.attach_mock(self.monitor, "monitor")
        
        # We want to verify that _cleanup_pending_reviews is called before is_pr_actionable
        # in run_monitoring_cycle loop.
        
        with patch.object(self.monitor, "discover_open_prs", return_value=[pr]):
            with patch.object(self.monitor, "is_pr_actionable", return_value=False) as mock_actionable:
                with patch.object(self.monitor, "_cleanup_pending_reviews") as mock_cleanup:
                    # Run monitoring cycle in fixpr mode (which triggers cleanup)
                    # Use sequential mode to maintain test's original behavior
                    self.monitor.run_monitoring_cycle(fixpr=True, parallel=False)
                    
                    # Verify cleanup was called
                    mock_cleanup.assert_called_once_with(repo_full, pr_number)
                    # Verify actionable check was called
                    mock_actionable.assert_called_once()
                    
                    # Verify order using call_args_list or similar if needed, 
                    # but since we mocked both we can check their call order if we patch them on same object
                    
        # Verification of order via a shared mock object
        # Re-run with shared mock to verify order
        with patch.object(self.monitor, "discover_open_prs", return_value=[pr]):
            with patch.object(self.monitor, "is_pr_actionable", return_value=False) as mock_actionable:
                with patch.object(self.monitor, "_cleanup_pending_reviews") as mock_cleanup:
                    # Shared mock to track call order
                    order_mock = Mock()
                    
                    # Define side_effect functions that track calls AND return correct values
                    def cleanup_side_effect(*args, **kwargs):
                        order_mock.cleanup()
                        return None  # _cleanup_pending_reviews returns None
                    
                    def actionable_side_effect(*args, **kwargs):
                        order_mock.actionable()
                        return False  # is_pr_actionable should return False for this test
                    
                    mock_cleanup.side_effect = cleanup_side_effect
                    mock_actionable.side_effect = actionable_side_effect

                    # Use sequential mode to maintain test's original behavior
                    self.monitor.run_monitoring_cycle(fixpr=True, parallel=False)
                    
                    # Check order: cleanup should be before actionable
                    calls = [call[0] for call in order_mock.method_calls]
                    self.assertIn("cleanup", calls)
                    self.assertIn("actionable", calls)
                    self.assertLess(calls.index("cleanup"), calls.index("actionable"))
                    
                    # Verify is_pr_actionable returned False (PR should be skipped)
                    self.assertFalse(mock_actionable.return_value if not mock_actionable.called else mock_actionable.side_effect())


class TestDailyCooldownFiltering(unittest.TestCase):
    """Test daily cooldown filtering for attempts and comments"""

    def setUp(self):
        """Set up test environment"""
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager"):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.logger = Mock()

    def test_count_workflow_comments_filters_by_date(self):
        """Test that _count_workflow_comments only counts today's comments"""
        # Use UTC to match production code (datetime.now(timezone.utc).date().isoformat())
        today = datetime.now(timezone.utc).date().isoformat()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()

        # Create comments with different dates
        comments = [
            {
                "author": {"login": "test-automation-user"},
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR",
                "createdAt": f"{today}T10:00:00Z",
            },
            {
                "author": {"login": "test-automation-user"},
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR yesterday",
                "createdAt": f"{yesterday}T10:00:00Z",
            },
            {
                "author": {"login": "test-automation-user"},
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR today",
                "createdAt": f"{today}T15:00:00Z",
            },
        ]

        count = self.monitor._count_workflow_comments(comments, "fixpr")

        # Should only count today's comments (2), not yesterday's (1)
        self.assertEqual(count, 2, f"Expected 2 today's comments, got {count}")

    def test_count_workflow_comments_handles_utc_timezone(self):
        """Test that _count_workflow_comments handles UTC timestamps correctly"""
        # Use UTC to match production code (datetime.now(timezone.utc).date().isoformat())
        today_utc = datetime.now(timezone.utc).date().isoformat()
        yesterday_utc = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()

        # Create comments with UTC timestamps
        comments = [
            {
                "author": {"login": "test-automation-user"},
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR UTC today",
                "createdAt": f"{today_utc}T23:59:59Z",
            },
            {
                "author": {"login": "test-automation-user"},
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR UTC yesterday",
                "createdAt": f"{yesterday_utc}T00:00:00Z",
            },
        ]

        count = self.monitor._count_workflow_comments(comments, "fixpr")

        # Should only count today's UTC comment (1), not yesterday's
        self.assertEqual(count, 1, f"Expected 1 today's UTC comment, got {count}")

    def test_count_workflow_comments_handles_missing_timestamp(self):
        """Test that _count_workflow_comments handles comments without timestamps"""
        comments = [
            {
                "body": "<!-- fixpr-run-automation-commit:gemini:sha --> Fix PR no timestamp",
                # No createdAt or updatedAt
            },
        ]

        # Should not count if no timestamp is present (cannot verify if from today)
        count = self.monitor._count_workflow_comments(comments, "fixpr")
        self.assertEqual(count, 0)


class TestDailyCooldownAttempts(unittest.TestCase):
    """Test daily cooldown filtering for PR attempts in AutomationSafetyManager"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.safety_manager = AutomationSafetyManager(data_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_can_process_pr_filters_by_date(self):
        """Test that can_process_pr only counts attempts within rolling window (24h)"""

        # Use rolling window logic to match production code
        now = datetime.now(timezone.utc)
        # Recent attempts (inside window)
        recent1 = (now - timedelta(hours=1)).isoformat()
        recent2 = (now - timedelta(hours=2)).isoformat()
        # Old attempt (outside 24h window)
        old = (now - timedelta(hours=25)).isoformat()

        # Create attempts with timestamps
        attempts_data = {
            "r=owner/repo||p=123||b=feature/branch": [
                {"result": "success", "timestamp": recent1},
                {"result": "failure", "timestamp": old},
                {"result": "success", "timestamp": recent2},
            ]
        }

        # Write attempts to file
        attempts_file = os.path.join(self.temp_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(attempts_data, f)

        # Test with limit of 2 (should allow since only 2 attempts in window)
        self.safety_manager.pr_limit = 2
        can_process = self.safety_manager.can_process_pr(123, repo="owner/repo", branch="feature/branch")

        # Should not allow processing when window attempts (2) equal limit (2)
        # total_attempts < effective_limit => 2 < 2 is False
        self.assertFalse(can_process, "Should not allow processing when window attempts equal limit")

        # Test with limit of 3 (should allow since only 2 attempts in window)
        self.safety_manager.pr_limit = 3
        can_process = self.safety_manager.can_process_pr(123, repo="owner/repo", branch="feature/branch")
        self.assertTrue(can_process, "Should allow processing when window attempts < limit")

    def test_get_pr_attempts_filters_by_date(self):
        """Test that get_pr_attempts only counts attempts within rolling window (24h)"""

        # Use rolling window logic to match production code
        now = datetime.now(timezone.utc)
        # Recent attempts (inside window)
        recent1 = (now - timedelta(hours=1)).isoformat()
        recent2 = (now - timedelta(hours=2)).isoformat()
        # Old attempt (outside 24h window)
        old = (now - timedelta(hours=25)).isoformat()

        # Create attempts with timestamps
        attempts_data = {
            "r=owner/repo||p=123||b=feature/branch": [
                {"result": "success", "timestamp": recent1},
                {"result": "failure", "timestamp": old},
                {"result": "success", "timestamp": recent2},
            ]
        }

        # Write attempts to file
        attempts_file = os.path.join(self.temp_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(attempts_data, f)

        count = self.safety_manager.get_pr_attempts(123, repo="owner/repo", branch="feature/branch")

        # Should only count attempts in window (2), not old ones (1)
        self.assertEqual(count, 2, f"Expected 2 attempts in window, got {count}")


if __name__ == "__main__":
    unittest.main()
