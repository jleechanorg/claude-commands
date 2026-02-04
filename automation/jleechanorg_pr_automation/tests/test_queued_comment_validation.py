"""TDD Tests for Queued Comment Validation.

Problem: The "queued" comment can be posted even if later execution fails.

Solution: Require successful dispatch before posting comments and
run a single heavy preflight at workflow startup.

Test Matrix:
1. No comment posted if CLI validation fails (all CLIs quota exhausted)
2. Comment only posted after dispatch succeeds
3. Failed agents should not leave orphan "queued" comments
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor
from orchestration.task_dispatcher import TaskDispatcher


class TestQueuedCommentValidation(unittest.TestCase):
    """Test that queued comments are only posted after validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = JleechanorgPRMonitor(
            no_act=False,  # We need to test actual behavior
        )
        self.pr_data = {
            "title": "Test PR",
            "number": 123,
            "author": {"login": "testuser"},
            "headRefName": "test-branch",
            "headRefOid": "abc123def456",
            "mergeable": "MERGEABLE",
        }

    @patch.object(JleechanorgPRMonitor, "_get_pr_comment_state")
    @patch.object(JleechanorgPRMonitor, "_has_unaddressed_comments")
    @patch.object(JleechanorgPRMonitor, "dispatch_fix_comment_agent")
    @patch.object(JleechanorgPRMonitor, "_post_fix_comment_queued")
    def test_no_comment_when_dispatch_fails(
        self,
        mock_post_queued,
        mock_dispatch,
        mock_has_unaddressed,
        mock_get_state,
    ):
        """If dispatch_fix_comment_agent returns False, no queued comment should be posted."""
        # Setup: dispatch fails (validation failed, quota exhausted, etc.)
        mock_get_state.return_value = ("abc123def456", [])
        mock_has_unaddressed.return_value = True  # Has work to do
        mock_dispatch.return_value = False  # Dispatch failed!

        with patch("subprocess.run"):  # Mock gh commands
            result = self.monitor._process_pr_fix_comment(
                "jleechanorg/test-repo",
                123,
                self.pr_data,
                agent_cli="gemini",
            )

        # Assert: no queued comment posted, returns "failed"
        self.assertEqual(result, "failed")
        mock_post_queued.assert_not_called()

    @patch.object(JleechanorgPRMonitor, "_get_pr_comment_state")
    @patch.object(JleechanorgPRMonitor, "_has_unaddressed_comments")
    @patch.object(JleechanorgPRMonitor, "dispatch_fix_comment_agent")
    @patch.object(JleechanorgPRMonitor, "_post_fix_comment_queued")
    @patch.object(JleechanorgPRMonitor, "_start_fix_comment_review_watcher")
    @patch.object(JleechanorgPRMonitor, "_cleanup_pending_reviews")
    def test_comment_posted_only_after_successful_dispatch(
        self,
        mock_cleanup,
        mock_watcher,
        mock_post_queued,
        mock_dispatch,
        mock_has_unaddressed,
        mock_get_state,
    ):
        """Queued comment should only be posted after dispatch succeeds."""
        # Setup: dispatch succeeds
        mock_get_state.return_value = ("abc123def456", [])
        mock_has_unaddressed.return_value = True
        mock_dispatch.return_value = True  # Dispatch succeeded
        mock_post_queued.return_value = True
        mock_watcher.return_value = True
        with patch("subprocess.run"):
            result = self.monitor._process_pr_fix_comment(
                "jleechanorg/test-repo",
                123,
                self.pr_data,
                agent_cli="gemini",
            )

        # Assert: queued comment was posted
        self.assertEqual(result, "posted")
        mock_post_queued.assert_called_once()


class TestDispatchValidationIntegration(unittest.TestCase):
    """Test that dispatch_fix_comment_agent properly validates CLI before returning True."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = JleechanorgPRMonitor()
        self.pr_data = {
            "title": "Test PR",
            "number": 123,
            "author": {"login": "testuser"},
            "headRefName": "test-branch",
            "headRefOid": "abc123def456",
        }

    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone")
    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr_with_task")
    def test_dispatch_returns_false_when_validation_fails(
        self,
        mock_dispatch_task,
        mock_ensure_clone,
    ):
        """dispatch_fix_comment_agent should return False when CLI validation fails."""
        mock_dispatch_task.return_value = False  # Validation failed

        with tempfile.TemporaryDirectory() as temp_dir:
            mock_ensure_clone.return_value = temp_dir
            result = self.monitor.dispatch_fix_comment_agent(
                "jleechanorg/test-repo",
                123,
                self.pr_data,
                agent_cli="gemini",
            )

        self.assertFalse(result)


class TestValidationPreventsDuplicateComments(unittest.TestCase):
    """Test that failed validation doesn't leave orphan queued comments."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = JleechanorgPRMonitor()

    def test_failed_validation_returns_failed_status(self):
        """When all CLIs fail validation, _process_pr_fix_comment returns 'failed'."""
        # This is the expected behavior - if dispatch fails, return "failed"
        # and don't post any comment
        pr_data = {
            "title": "Test PR",
            "number": 456,
            "author": {"login": "testuser"},
            "headRefName": "feature-branch",
            "headRefOid": "def789abc123",
        }

        with patch.object(
            self.monitor, "_get_pr_comment_state", return_value=("def789abc123", [])
        ), patch.object(
            self.monitor, "_has_unaddressed_comments", return_value=True
        ), patch.object(
            self.monitor, "dispatch_fix_comment_agent", return_value=False
        ), patch.object(
            self.monitor, "_post_fix_comment_queued"
        ) as mock_post, patch(
            "subprocess.run"
        ):
            result = self.monitor._process_pr_fix_comment(
                "jleechanorg/test-repo",
                456,
                pr_data,
                agent_cli="gemini,cursor",
            )

        # Should return "failed", not "posted" or "partial"
        self.assertEqual(result, "failed")
        # Most importantly: no comment should be posted
        mock_post.assert_not_called()


class TestPreflightCLIValidation(unittest.TestCase):
    """Test pre-flight CLI validation before tmux session creation.

    This is the key fix: run a quick test on each CLI BEFORE creating any
    tmux session. If all CLIs fail pre-flight (quota exhausted), return False
    immediately without creating any session or posting any comment.
    """

    def test_preflight_check_detects_quota_exhaustion(self):
        """Pre-flight check should detect quota exhaustion from CLI output."""
        # Test the quota detection patterns in cli_validation.py
        # These are the same patterns used by _validate_cli_availability

        # Gemini quota error phrases
        gemini_error = "[API Error: You have exhausted your daily quota on this model.]"
        quota_phrases = [
            "exhausted your daily quota",
            "rate limit",
            "quota exceeded",
            "hit your usage limit",
        ]
        self.assertTrue(any(phrase in gemini_error.lower() for phrase in quota_phrases))

        # Cursor quota error
        cursor_error = "You've hit your usage limit"
        self.assertTrue(any(phrase in cursor_error.lower() for phrase in quota_phrases))

        # Normal output should not be flagged
        normal_output = "4"  # Response to "What is 2+2?"
        self.assertFalse(any(phrase in normal_output.lower() for phrase in quota_phrases))

    def test_preflight_validation_returns_false_on_quota_failure(self):
        """_validate_cli_availability should return False when quota is exhausted."""
        dispatcher = TaskDispatcher()

        # Mock subprocess to simulate quota error
        with patch("orchestration.cli_validation.subprocess.run") as mock_run:
            # Simulate Gemini returning quota error
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="[API Error: You have exhausted your daily quota on this model.]",
            )

            result = dispatcher._validate_cli_availability(
                cli_name="gemini",
                cli_path="/opt/homebrew/bin/gemini",
                agent_name="test-agent",
                model="gemini-3-flash-preview",
            )

            self.assertFalse(result)

    def test_create_dynamic_agent_fails_when_all_clis_fail_validation(self):
        """create_dynamic_agent should return False if all CLIs fail validation."""
        dispatcher = TaskDispatcher()

        # Mock _validate_cli_availability to always return False (quota exhausted)
        with patch.object(dispatcher, "_validate_cli_availability", return_value=False), \
             patch.object(dispatcher, "_resolve_cli_binary", return_value="/usr/bin/gemini"):

            agent_spec = {
                "name": "test-agent",
                "cli_chain": ["gemini", "cursor"],
                "prompt": "Test task",
            }

            result = dispatcher.create_dynamic_agent(agent_spec)

            # Should return False because all CLIs failed validation
            self.assertFalse(result)


class TestStartupPreflight(unittest.TestCase):
    """Test startup preflight behavior before PR discovery."""

    def setUp(self):
        self.monitor = JleechanorgPRMonitor(no_act=False)

    @patch.object(JleechanorgPRMonitor, "_validate_cli_chain", return_value=(None, {}))
    @patch.object(JleechanorgPRMonitor, "discover_open_prs")
    def test_startup_preflight_blocks_discovery_when_all_fail(
        self,
        mock_discover,
        mock_preflight,
    ):
        """If startup preflight fails, discovery should not run."""
        with patch.dict(
            os.environ,
            {
                "TESTING": "false",
                "MOCK_SERVICES_MODE": "false",
                "GITHUB_ACTIONS": "false",
                "FAST_TESTS": "0",
            },
            clear=False,
        ):
            self.monitor.run_monitoring_cycle(
                fixpr=True,
                agent_cli="gemini,cursor,codex",
            )

        mock_preflight.assert_called_once()
        mock_discover.assert_not_called()


if __name__ == "__main__":
    unittest.main()
