#!/usr/bin/env python3
"""
Test comment validation functionality for jleechanorg_pr_monitor
"""

import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCommentValidation(unittest.TestCase):
    """Test comment validation functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        self.monitor.history_storage_path = self.temp_dir

    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_extract_comment_validation_marker(self):
        """Comment validation markers can be parsed from comments"""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        test_comment = (
            "Please review this PR\n\n"
            f"{monitor.COMMENT_VALIDATION_MARKER_PREFIX}abc123{monitor.COMMENT_VALIDATION_MARKER_SUFFIX}"
        )
        marker = monitor._extract_comment_validation_marker(test_comment)
        self.assertEqual(marker, "abc123")

    def test_has_comment_validation_comment_for_commit(self):
        """Comment validation comments should be detected for commit gating."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        head_sha = "abc123def456"
        comments = [
            {
                "body": (
                    "Please review this PR\n\n"
                    f"{monitor.COMMENT_VALIDATION_MARKER_PREFIX}{head_sha}"
                    f"{monitor.COMMENT_VALIDATION_MARKER_SUFFIX}"
                )
            }
        ]

        self.assertTrue(monitor._has_comment_validation_comment_for_commit(comments, head_sha))

    def test_has_comment_validation_comment_ignores_other_markers(self):
        """Comment validation detection should ignore Codex markers."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        head_sha = "abc123def456"
        comments = [
            {
                "body": (
                    "Codex comment\n\n"
                    f"{monitor.CODEX_COMMIT_MARKER_PREFIX}{head_sha}"
                    f"{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
                )
            }
        ]

        self.assertFalse(monitor._has_comment_validation_comment_for_commit(comments, head_sha))

    def test_build_comment_validation_body_includes_marker(self):
        """Comment validation body should include the commit marker."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Test PR",
            "author": {"login": "developer"},
            "headRefName": "feature/test",
        }
        head_sha = "abc123def456"

        comment_body = monitor._build_comment_validation_body(
            "org/repo",
            42,
            pr_data,
            head_sha,
        )

        self.assertIn(monitor.COMMENT_VALIDATION_MARKER_PREFIX, comment_body)
        self.assertIn(monitor.COMMENT_VALIDATION_MARKER_SUFFIX, comment_body)
        self.assertIn(head_sha, comment_body)
        self.assertIn("@coderabbit-ai", comment_body)
        self.assertIn("@greptileai", comment_body)
        self.assertIn("@bugbot", comment_body)
        self.assertIn("@copilot", comment_body)
        # Should NOT include Codex
        self.assertNotIn("@codex", comment_body.lower())

    def test_build_comment_validation_body_includes_review_instructions(self):
        """Comment validation body should include review instructions."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Test PR",
            "author": {"login": "developer"},
            "headRefName": "feature/test",
        }

        comment_body = monitor._build_comment_validation_body(
            "org/repo",
            42,
            pr_data,
            "abc123",
        )

        self.assertIn("review flow", comment_body.lower())
        self.assertIn("verify", comment_body.lower())
        self.assertIn("check for bugs", comment_body.lower())
        self.assertIn("done/not done", comment_body.lower())

    def test_comment_validation_posting_returns_posted_on_success(self):
        """Comment validation posting should return 'posted' when successful"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_comment_validation_comment_for_commit") as mock_has_comment, \
             patch.object(self.monitor, "_build_comment_validation_body") as mock_build_body, \
             patch.object(self.monitor, "_record_processed_pr") as mock_record, \
             patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout") as mock_subprocess:

            # Setup: PR not skipped, no existing comment, successful command
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = False
            mock_build_body.return_value = "Test comment body"
            mock_subprocess.return_value = Mock(returncode=0, stdout="success", stderr="")

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_comment_validation_request("org/repo", 123, pr_data)
            self.assertEqual(result, "posted")
            mock_record.assert_called_once()

    def test_comment_validation_posting_returns_skipped_when_already_processed(self):
        """Comment validation posting should return 'skipped' when PR already processed"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip:

            # Setup: PR should be skipped
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = True

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_comment_validation_request("org/repo", 123, pr_data)
            self.assertEqual(result, "skipped")

    def test_comment_validation_posting_returns_skipped_when_comment_exists(self):
        """Comment validation posting should return 'skipped' when comment already exists for commit"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_comment_validation_comment_for_commit") as mock_has_comment:

            # Setup: PR not skipped but has existing comment
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = True

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_comment_validation_request("org/repo", 123, pr_data)
            self.assertEqual(result, "skipped")

    def test_comment_validation_posting_returns_failed_on_error(self):
        """Comment validation posting should return 'failed' on subprocess error"""
        with patch.object(self.monitor, "_get_pr_comment_state") as mock_state, \
             patch.object(self.monitor, "_should_skip_pr") as mock_skip, \
             patch.object(self.monitor, "_has_comment_validation_comment_for_commit") as mock_has_comment, \
             patch.object(self.monitor, "_build_comment_validation_body") as mock_build_body, \
             patch("jleechanorg_pr_automation.automation_utils.AutomationUtils.execute_subprocess_with_timeout") as mock_subprocess:

            # Setup: PR not skipped, no existing comment, but command fails
            mock_state.return_value = ("sha123", [])
            mock_skip.return_value = False
            mock_has_comment.return_value = False
            mock_build_body.return_value = "Test comment body"
            mock_subprocess.side_effect = subprocess.CalledProcessError(1, "gh", stderr="Error")

            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }

            result = self.monitor.post_comment_validation_request("org/repo", 123, pr_data)
            self.assertEqual(result, "failed")

    def test_comment_validation_shares_common_code(self):
        """Comment validation should use the shared _post_pr_comment_common method"""
        # Verify that post_comment_validation_request calls _post_pr_comment_common
        with patch.object(self.monitor, "_post_pr_comment_common") as mock_common:
            mock_common.return_value = "posted"
            
            pr_data = {
                "repositoryFullName": "org/repo",
                "headRefName": "feature"
            }
            
            result = self.monitor.post_comment_validation_request("org/repo", 123, pr_data)
            
            # Verify _post_pr_comment_common was called with correct parameters
            mock_common.assert_called_once()
            call_kwargs = mock_common.call_args[1]
            self.assertEqual(call_kwargs["repository"], "org/repo")
            self.assertEqual(call_kwargs["pr_number"], 123)
            self.assertEqual(call_kwargs["pr_data"], pr_data)
            self.assertEqual(call_kwargs["log_prefix"], "comment validation")
            self.assertIsNone(call_kwargs["skip_checks_fn"])  # No special skip checks
            self.assertEqual(result, "posted")


if __name__ == "__main__":
    unittest.main()
