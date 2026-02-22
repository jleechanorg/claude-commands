"""
Test for merge conflict detection in fixpr mode.

GitHub API returns mergeable as Boolean (false = conflicts), not string.
This test verifies the fix correctly handles Boolean mergeable values.
"""

import unittest
from unittest.mock import Mock, patch

from automation.jleechanorg_pr_automation import jleechanorg_pr_monitor as mon


class TestMergeableConflictDetection(unittest.TestCase):
    """Test that fixpr correctly detects merge conflicts from GitHub API."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = mon.JleechanorgPRMonitor(automation_username="test-automation-user")

    @patch.object(mon, "has_failing_checks", return_value=False)
    def test_pr_with_mergeable_false_is_actionable(self, mock_failing):
        """PR with mergeable=false (conflicts) should be marked actionable."""
        # GitHub API returns mergeable as Boolean false when there are conflicts
        sample_prs = [
            {"repository": "repo/a", "number": 1, "title": "has conflicts", "mergeable": False},
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should be actionable because mergeable=False means conflicts
        self.assertEqual(len(actionable), 1)
        self.assertEqual(actionable[0]["number"], 1)

    @patch.object(mon, "has_failing_checks", return_value=False)
    def test_pr_with_mergeable_true_is_not_actionable(self, mock_failing):
        """PR with mergeable=true (clean) should NOT be marked actionable."""
        sample_prs = [
            {"repository": "repo/a", "number": 2, "title": "clean PR", "mergeable": True},
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should NOT be actionable because mergeable=True means clean
        self.assertEqual(len(actionable), 0)

    @patch.object(mon, "has_failing_checks", return_value=False)
    def test_pr_with_mergeable_null_is_not_actionable(self, mock_failing):
        """PR with mergeable=null (unknown) should NOT be marked actionable."""
        sample_prs = [
            {"repository": "repo/a", "number": 3, "title": "unknown state", "mergeable": None},
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should NOT be actionable because mergeable=None means unknown
        self.assertEqual(len(actionable), 0)

    @patch.object(mon, "has_failing_checks", return_value=True)
    def test_pr_with_failing_checks_is_actionable(self, mock_failing):
        """PR with failing checks should be marked actionable regardless of mergeable."""
        sample_prs = [
            {"repository": "repo/a", "number": 4, "title": "failing checks", "mergeable": True},
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should be actionable because has failing checks
        self.assertEqual(len(actionable), 1)
        self.assertEqual(actionable[0]["number"], 4)

    @patch.object(mon, "has_failing_checks", return_value=False)
    def test_pr_with_mergeable_dirty_state_is_actionable(self, mock_failing):
        """PR with mergeableState='dirty' should be marked actionable."""
        # GitHub REST API can also return mergeableState as string "dirty"
        sample_prs = [
            {"repository": "repo/a", "number": 5, "title": "dirty state", "mergeableState": "dirty"},
        ]

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should be actionable because mergeableState="dirty" means conflicts
        self.assertEqual(len(actionable), 1)
        self.assertEqual(actionable[0]["number"], 5)

    @patch.object(mon, "has_failing_checks", return_value=False)
    def test_mixed_prs_filtered_correctly(self, mock_failing):
        """Test that mixed PRs are filtered correctly."""
        sample_prs = [
            {"repository": "repo/a", "number": 1, "title": "conflicts", "mergeable": False},
            {"repository": "repo/b", "number": 2, "title": "clean", "mergeable": True},
            {"repository": "repo/c", "number": 3, "title": "failing", "mergeable": True},  # will have failing checks
            {"repository": "repo/d", "number": 4, "title": "unknown", "mergeable": None},
        ]

        def fake_failing_checks(repo: str, pr_num: int) -> bool:
            return pr_num == 3

        with patch.object(self.monitor, "discover_open_prs", return_value=sample_prs), \
             patch.object(mon, "has_failing_checks", fake_failing_checks):
            actionable = self.monitor.list_actionable_prs(max_prs=10)

        # Should have 2: #1 (conflicts) and #3 (failing checks)
        self.assertEqual(len(actionable), 2)
        self.assertEqual({pr["number"] for pr in actionable}, {1, 3})


if __name__ == "__main__":
    unittest.main()
