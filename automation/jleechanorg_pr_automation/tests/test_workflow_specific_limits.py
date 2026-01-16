#!/usr/bin/env python3
"""
Test-Driven Development for Workflow-Specific Safety Limits

RED Phase: Tests should FAIL initially (implementation broken)
GREEN Phase: Fix implementation to make tests pass

Tests workflow-specific comment counting and safety limits:
- pr_automation workflow
- fix_comment workflow
- codex_update workflow
- fixpr workflow
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestWorkflowSpecificLimits(unittest.TestCase):
    """Test workflow-specific comment counting and safety limits"""

    def setUp(self):
        """Set up test environment"""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationSafetyManager'):
            # Initialize with explicit test username to avoid environment dependency
            self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
            # Mock safety manager with workflow-specific limits
            self.monitor.safety_manager.pr_automation_limit = 10
            self.monitor.safety_manager.fix_comment_limit = 5
            self.monitor.safety_manager.codex_update_limit = 10
            self.monitor.safety_manager.fixpr_limit = 10
            self.today = datetime.now(timezone.utc).isoformat()

    def _add_timestamps(self, comments):
        """Add today's timestamp to comments if missing"""
        for comment in comments:
            if "createdAt" not in comment and "updatedAt" not in comment:
                comment["createdAt"] = self.today
        return comments

    def test_count_pr_automation_comments(self):
        """Test counting PR automation comments (codex marker, not fix-comment)"""
        comments = [
            {"body": "<!-- codex-automation-commit:abc123 -->"},
            {"body": "<!-- codex-automation-commit:def456 -->"},
            {"body": "<!-- fix-comment-automation-commit:xyz789 -->"},  # Should NOT count
            {"body": "Regular comment"},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "pr_automation")
        self.assertEqual(count, 2, "Should count only codex-automation-commit comments without fix-comment marker")

    def test_count_fix_comment_comments(self):
        """Test counting fix-comment workflow comments"""
        comments = [
            {"body": "<!-- fix-comment-automation-commit:abc123 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- fix-comment-automation-commit:def456 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- codex-automation-commit:xyz789 -->", "author": {"login": "test-automation-user"}},  # Should NOT count
            {"body": "Regular comment", "author": {"login": "test-automation-user"}},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        self.assertEqual(count, 2, "Should count only fix-comment-automation-commit comments")

    def test_count_fix_comment_run_comments(self):
        """Test counting fix-comment queued run markers"""
        comments = [
            {"body": "<!-- fix-comment-run-automation-commit:gemini:abc123 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- fix-comment-run-automation-commit:codex:def456 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- codex-automation-commit:xyz789 -->", "author": {"login": "test-automation-user"}},  # Should NOT count
            {"body": "Regular comment", "author": {"login": "test-automation-user"}},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        self.assertEqual(count, 2, "Should count fix-comment-run-automation-commit comments for fix_comment workflow")

    def test_count_codex_update_comments(self):
        """Test counting codex-update workflow comments (should always be 0)"""
        comments = [
            {"body": "<!-- codex-automation-commit:abc123 -->"},
            {"body": "<!-- fix-comment-automation-commit:def456 -->"},
        ]
        count = self.monitor._count_workflow_comments(comments, "codex_update")
        self.assertEqual(count, 0, "Codex update workflow doesn't post PR comments, should always return 0")

    def test_count_fixpr_comments(self):
        """Test counting fixpr workflow comments"""
        comments = [
            {"body": "<!-- fixpr-run-automation-commit:gemini:abc123 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- fixpr-run-automation-commit:codex:def456 -->", "author": {"login": "test-automation-user"}},
            {"body": "<!-- codex-automation-commit:xyz789 -->", "author": {"login": "test-automation-user"}},  # Should NOT count
            {"body": "<!-- fix-comment-automation-commit:ghi012 -->", "author": {"login": "test-automation-user"}},  # Should NOT count
            {"body": "Regular comment", "author": {"login": "test-automation-user"}},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fixpr")
        self.assertEqual(count, 2, "Should count only fixpr-run-automation-commit comments for fixpr workflow")

    def test_workflow_specific_limit_pr_automation(self):
        """Test that PR automation workflow uses its own limit"""
        comments = [
            {"body": f"<!-- codex-automation-commit:abc{i} -->"} for i in range(10)
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "pr_automation")
        # Should be at limit (10), not blocked yet
        self.assertEqual(count, 10)
        # 11th comment should exceed limit
        comments.append({"body": "<!-- codex-automation-commit:abc11 -->", "createdAt": self.today})
        count = self.monitor._count_workflow_comments(comments, "pr_automation")
        self.assertEqual(count, 11)
        self.assertGreater(count, self.monitor.safety_manager.pr_automation_limit)

    def test_workflow_specific_limit_fix_comment(self):
        """Test that fix-comment workflow uses its own limit (5)"""
        comments = [
            {"body": f"<!-- fix-comment-automation-commit:abc{i} -->", "author": {"login": "test-automation-user"}} for i in range(5)
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        # Should be at limit (5)
        self.assertEqual(count, 5)
        # 6th comment should exceed limit
        comments.append({"body": "<!-- fix-comment-automation-commit:abc6 -->", "author": {"login": "test-automation-user"}, "createdAt": self.today})
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        self.assertEqual(count, 6)
        self.assertGreater(count, self.monitor.safety_manager.fix_comment_limit)

    def test_workflow_specific_limit_independence(self):
        """Test that different workflows have independent limits"""
        # PR automation has 10 comments (at limit)
        pr_automation_comments = [
            {"body": f"<!-- codex-automation-commit:pr{i} -->", "author": {"login": "test-automation-user"}} for i in range(10)
        ]
        # Fix-comment has 2 comments (under limit)
        fix_comment_comments = [
            {"body": f"<!-- fix-comment-automation-commit:fix{i} -->", "author": {"login": "test-automation-user"}} for i in range(2)
        ]

        pr_automation_comments = self._add_timestamps(pr_automation_comments)
        fix_comment_comments = self._add_timestamps(fix_comment_comments)

        pr_count = self.monitor._count_workflow_comments(pr_automation_comments, "pr_automation")
        fix_count = self.monitor._count_workflow_comments(fix_comment_comments, "fix_comment")

        self.assertEqual(pr_count, 10)
        self.assertEqual(fix_count, 2)
        # Fix-comment should still be allowed even though PR automation is at limit
        self.assertLess(fix_count, self.monitor.safety_manager.fix_comment_limit)
        self.assertEqual(pr_count, self.monitor.safety_manager.pr_automation_limit)

    def test_mixed_comments_pr_automation(self):
        """Test PR automation counting with mixed comment types"""
        comments = [
            {"body": "<!-- codex-automation-commit:abc123 -->"},  # Count
            {"body": "<!-- codex-automation-commit:def456 -->"},  # Count
            {"body": "<!-- fix-comment-automation-commit:xyz789 -->"},  # Don't count
            {"body": "<!-- codex-automation-commit:ghi012 -->"},  # Count
            {"body": "Regular comment"},  # Don't count
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "pr_automation")
        self.assertEqual(count, 3, "Should count only codex comments without fix-comment marker")

    def test_mixed_comments_fix_comment(self):
        """Test fix-comment counting with mixed comment types"""
        comments = [
            {"body": "<!-- fix-comment-automation-commit:abc123 -->", "author": {"login": "test-automation-user"}},  # Count
            {"body": "<!-- codex-automation-commit:def456 -->", "author": {"login": "test-automation-user"}},  # Don't count
            {"body": "<!-- fix-comment-automation-commit:xyz789 -->", "author": {"login": "test-automation-user"}},  # Count
            {"body": "Regular comment", "author": {"login": "test-automation-user"}},  # Don't count
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        self.assertEqual(count, 2, "Should count only fix-comment-automation-commit comments")

    def test_empty_comments_list(self):
        """Test counting with empty comments list"""
        comments = []
        for workflow_type in ["pr_automation", "fix_comment", "codex_update", "fixpr"]:
            count = self.monitor._count_workflow_comments(comments, workflow_type)
            self.assertEqual(count, 0, f"Empty list should return 0 for {workflow_type}")

    def test_unknown_workflow_type(self):
        """Test that unknown workflow type falls back to counting all automation comments"""
        comments = [
            {"body": "<!-- codex-automation-commit:abc123 -->"},
            {"body": "<!-- fix-comment-automation-commit:def456 -->"},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "unknown_workflow")
        # Should count all automation comments as fallback
        self.assertEqual(count, 2)

    def test_count_fix_comment_ignores_impostors(self):
        """Test that fix-comment counts ignore comments from other users"""
        comments = [
            # Valid marker but wrong author
            {"body": "<!-- fix-comment-automation-commit:abc123 -->", "author": {"login": "impostor"}},
            # Valid marker and correct author
            {"body": "<!-- fix-comment-automation-commit:def456 -->", "author": {"login": "test-automation-user"}},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fix_comment")
        self.assertEqual(count, 1, "Should ignore comments from impostor users")

    def test_count_fixpr_ignores_impostors(self):
        """Test that fixpr counts ignore comments from other users"""
        comments = [
            # Valid marker but wrong author
            {"body": "<!-- fixpr-run-automation-commit:gemini:abc123 -->", "author": {"login": "impostor"}},
            # Valid marker and correct author
            {"body": "<!-- fixpr-run-automation-commit:codex:def456 -->", "author": {"login": "test-automation-user"}},
        ]
        comments = self._add_timestamps(comments)
        count = self.monitor._count_workflow_comments(comments, "fixpr")
        self.assertEqual(count, 1, "Should ignore comments from impostor users")



if __name__ == "__main__":
    unittest.main()
