#!/usr/bin/env python3
"""
Test for fixpr workflow return value handling.

Regression test for cursor[bot] bug report (Comment ID 2674134633):
"FixPR workflow ignores queued comment posting failure"

Tests that _process_pr_fixpr correctly captures and handles the return value
from _post_fixpr_queued, matching the behavior of _process_pr_fix_comment.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestFixprReturnValue(unittest.TestCase):
    """Test fixpr workflow return value handling"""

    def setUp(self):
        """Set up test environment with comprehensive mocking"""
        # Patch AutomationSafetyManager during JleechanorgPRMonitor initialization
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor()
            self.monitor.safety_manager.fixpr_limit = 10

        # Mock logger to avoid logging issues
        self.monitor.logger = MagicMock()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_returns_partial_when_queued_comment_fails(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
    ):
        """
        Test that _process_pr_fixpr returns 'partial' when _post_fixpr_queued fails.

        Regression test for cursor[bot] bug: Method was ignoring return value and
        always returning 'posted' even when comment posting failed.
        """
        # Setup mocks
        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True  # Agent dispatch succeeds

        pr_data = {
            "number": 1234,
            "title": "Test PR",
            "headRefName": "test-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/1234",
            "headRepository": {"owner": {"login": "test"}},
            "headRefOid": "abc123",
            "statusCheckRollup": [],
            "mergeable": "MERGEABLE",
        }

        # Comprehensive mocking to avoid all side effects
        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123", [])):
                with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                    with patch.object(self.monitor, '_count_workflow_comments', return_value=5):  # Under limit
                        with patch.object(self.monitor, '_post_fixpr_queued', return_value=False) as mock_post_queued:  # FAILS
                            with patch.object(self.monitor, '_record_processed_pr'):
                                result = self.monitor._process_pr_fixpr(
                                    repository="test/repo",
                                    pr_number=1234,
                                    pr_data=pr_data,
                                )

        # CRITICAL: Should return "partial" when queued comment fails
        self.assertEqual(
            result,
            "partial",
            "REGRESSION BUG: _process_pr_fixpr should return 'partial' when _post_fixpr_queued fails, "
            "not ignore the return value. This causes failed marker posts to not count against fixpr_limit."
        )
        # Verify _post_fixpr_queued was called
        mock_post_queued.assert_called_once()

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher')
    def test_fixpr_returns_posted_when_queued_comment_succeeds(
        self,
        mock_dispatcher,
        mock_chdir,
        mock_clone,
        mock_dispatch_agent,
    ):
        """
        Test that _process_pr_fixpr returns 'posted' when _post_fixpr_queued succeeds.

        This is the happy path - verifies correct behavior when comment posting works.
        """
        # Setup mocks
        mock_clone.return_value = "/tmp/fake/repo"
        mock_dispatch_agent.return_value = True  # Agent dispatch succeeds

        pr_data = {
            "number": 1234,
            "title": "Test PR",
            "headRefName": "test-branch",
            "baseRefName": "main",
            "url": "https://github.com/test/repo/pull/1234",
            "headRepository": {"owner": {"login": "test"}},
            "headRefOid": "abc123",
            "statusCheckRollup": [],
            "mergeable": "MERGEABLE",
        }

        # Comprehensive mocking to avoid all side effects
        with patch.object(self.monitor, '_normalize_repository_name', return_value="test/repo"):
            with patch.object(self.monitor, '_get_pr_comment_state', return_value=("abc123", [])):
                with patch.object(self.monitor, '_should_skip_pr', return_value=False):
                    with patch.object(self.monitor, '_count_workflow_comments', return_value=5):  # Under limit
                        with patch.object(self.monitor, '_post_fixpr_queued', return_value=True) as mock_post_queued:  # SUCCEEDS
                            with patch.object(self.monitor, '_record_processed_pr'):
                                result = self.monitor._process_pr_fixpr(
                                    repository="test/repo",
                                    pr_number=1234,
                                    pr_data=pr_data,
                                )

        # Should return "posted" when everything succeeds
        self.assertEqual(result, "posted")
        # Verify _post_fixpr_queued was called
        mock_post_queued.assert_called_once()



if __name__ == "__main__":
    unittest.main()
