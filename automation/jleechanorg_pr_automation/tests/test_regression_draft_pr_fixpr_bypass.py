#!/usr/bin/env python3
"""
Regression test for draft PR bypass bug in fixpr workflow.

BUG: Draft PRs with conflicts bypass isDraft filter in fixpr workflow
Location: jleechanorg_pr_monitor.py:3931-3936

When a PR has conflicts, the fixpr workflow bypasses is_pr_actionable() check
which contains the draft filter. This causes draft PRs to be processed when
they should be skipped.

Evidence:
- PR #4979 (isDraft: true) was processed and received automation commits
- PR #4984 (isDraft: true) was processed and received automation commits

Expected: Draft PRs should ALWAYS be skipped regardless of conflicts/failing checks
Actual: Draft PRs with conflicts bypass the draft filter
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch, MagicMock

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestRegressionDraftPRFixprBypass(unittest.TestCase):
    """Test that draft PRs are skipped by fixpr even when they have conflicts"""

    def setUp(self):
        """Set up test environment"""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            self.monitor.safety_manager.fixpr_limit = 10

        self.monitor.logger = MagicMock()
        self.monitor.no_act = False

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    def test_regression_draft_pr_with_conflicts_should_be_skipped(
        self,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        RED: Draft PR with merge conflicts should be skipped by fixpr workflow

        This reproduces the bug where draft PRs #4979 and #4984 were processed
        despite being drafts, because they had conflicts which bypassed the
        is_pr_actionable check.
        """
        # Set up draft PR with conflicts
        pr_data = {
            "number": 4979,
            "title": "Fix arithmetic errors",
            "state": "open",
            "isDraft": True,  # THIS IS A DRAFT
            "headRefName": "copilot/sub-pr-4978",
            "repository": "worldarchitect.ai",
            "repositoryFullName": "jleechanorg/worldarchitect.ai",
            "headRefOid": "abc123"
        }

        # Mock PR has conflicts (this triggers the bypass logic)
        mock_subprocess.return_value = SimpleNamespace(
            returncode=0,
            stdout='{"mergeable": "CONFLICTING"}',
            stderr=""
        )
        mock_has_failing_checks.return_value = False

        # Mock comment state (no existing automation comments)
        self.monitor._get_pr_comment_state = Mock(return_value=("abc123", []))

        # Call _process_pr_fixpr
        result = self.monitor._process_pr_fixpr(
            repository="worldarchitect.ai",
            pr_number=4979,
            pr_data=pr_data,
            agent_cli="gemini"
        )

        # EXPECTED: Should return "skipped" because PR is draft
        # ACTUAL (before fix): Returns "posted" - PR was processed!
        self.assertEqual(
            result,
            "skipped",
            "Draft PR with conflicts should be skipped, not processed. "
            "Bug: Conflict detection bypasses isDraft filter at line 3931-3936"
        )

        # Verify logger shows draft skip message
        skip_log_found = any(
            "draft" in str(call).lower() and "skip" in str(call).lower()
            for call in self.monitor.logger.info.call_args_list
        )
        self.assertTrue(
            skip_log_found,
            "Should log that draft PR is being skipped"
        )

    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks')
    @patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout')
    def test_regression_draft_pr_with_failing_checks_should_be_skipped(
        self,
        mock_subprocess,
        mock_has_failing_checks,
    ):
        """
        RED: Draft PR with failing checks should also be skipped by fixpr workflow
        """
        pr_data = {
            "number": 4984,
            "title": "Review PR #4978",
            "state": "open",
            "isDraft": True,  # THIS IS A DRAFT
            "headRefName": "copilot/sub-pr-4978-yet-again",
            "repository": "worldarchitect.ai",
            "repositoryFullName": "jleechanorg/worldarchitect.ai",
            "headRefOid": "def456"
        }

        # Mock PR has failing checks (no conflicts)
        mock_subprocess.return_value = SimpleNamespace(
            returncode=0,
            stdout='{"mergeable": "MERGEABLE"}',
            stderr=""
        )
        mock_has_failing_checks.return_value = True  # HAS FAILING CHECKS

        # Mock comment state
        self.monitor._get_pr_comment_state = Mock(return_value=("def456", []))

        result = self.monitor._process_pr_fixpr(
            repository="worldarchitect.ai",
            pr_number=4984,
            pr_data=pr_data,
            agent_cli="gemini"
        )

        # Draft PRs should be skipped even with failing checks
        self.assertEqual(
            result,
            "skipped",
            "Draft PR with failing checks should be skipped. "
            "Bug: Failing checks bypass isDraft filter"
        )

    def test_non_draft_pr_with_conflicts_should_be_processed(self):
        """
        Sanity check: Non-draft PRs with conflicts should still be processed
        """
        pr_data = {
            "number": 5000,
            "title": "Real PR",
            "state": "open",
            "isDraft": False,  # NOT A DRAFT
            "headRefName": "feature-branch",
            "repository": "worldarchitect.ai",
            "repositoryFullName": "jleechanorg/worldarchitect.ai",
            "headRefOid": "xyz789"
        }

        # This PR should pass is_pr_actionable since it's not a draft
        result = self.monitor.is_pr_actionable(pr_data)
        self.assertTrue(result, "Non-draft PR should be actionable")


if __name__ == "__main__":
    unittest.main()
