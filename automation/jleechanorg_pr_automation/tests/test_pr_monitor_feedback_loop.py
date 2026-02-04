"""
TDD tests for PR monitor feedback loop prevention.

Tests verify that:
1. Draft PRs are always skipped (the primary defense against sub-PR feedback loops)
2. COMMENT_VALIDATION_MARKER_PREFIX is recognized in automation marker detection
"""

import pytest
from unittest.mock import patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestDraftPRFiltering:
    """Test that draft PRs are always skipped - primary feedback loop defense."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance with mocked GitHub calls."""
        with patch.object(JleechanorgPRMonitor, '_load_branch_history', return_value={}):
            m = JleechanorgPRMonitor()
            return m

    def test_draft_pr_not_actionable(self, monitor):
        """Draft PRs should never be actionable."""
        pr_data = {
            "number": 100,
            "state": "OPEN",
            "isDraft": True,
            "headRefOid": "abc123",
            "repository": "test_repo",
            "headRefName": "feature/test",
        }
        assert monitor.is_pr_actionable(pr_data) is False

    def test_draft_sub_pr_not_actionable(self, monitor):
        """Draft automation sub-PRs (copilot/sub-pr-*) are skipped via draft filter."""
        pr_data = {
            "number": 420,
            "state": "OPEN",
            "isDraft": True,
            "headRefOid": "xyz789",
            "repository": "ai_universe_frontend",
            "headRefName": "copilot/sub-pr-383-latest",
        }
        assert monitor.is_pr_actionable(pr_data) is False

    def test_non_draft_pr_is_actionable(self, monitor):
        """Non-draft open PRs with commits should be actionable."""
        pr_data = {
            "number": 383,
            "state": "OPEN",
            "isDraft": False,
            "headRefOid": "commit123",
            "repository": "ai_universe_frontend",
            "headRefName": "codex/try-installing-in-codex-web-containers",
        }
        assert monitor.is_pr_actionable(pr_data) is True


class TestCommentValidationMarkerRecognition:
    """Test that COMMENT_VALIDATION_MARKER_PREFIX is recognized to prevent feedback loops."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        with patch.object(JleechanorgPRMonitor, '_load_branch_history', return_value={}):
            m = JleechanorgPRMonitor()
            return m

    def test_comment_validation_marker_recognized_as_automation_time(self, monitor):
        """CRITICAL: comment-validation markers must be recognized in _get_last_codex_automation_comment_time.

        This is the root cause of the feedback loop - if comment_validation comments
        aren't recognized, bot comments after them will trigger infinite reprocessing.
        """
        # Use actual marker from the monitor constants
        marker_prefix = monitor.COMMENT_VALIDATION_MARKER_PREFIX
        marker_suffix = monitor.COMMENT_VALIDATION_MARKER_SUFFIX

        comments = [
            {
                "body": f"{marker_prefix}abc123{marker_suffix}\n📝 Requesting reviews",
                "author": {"login": "jleechan"},
                "createdAt": "2026-01-31T10:00:00Z",
            }
        ]
        # This MUST return a timestamp, otherwise bot comments will trigger reprocessing
        result = monitor._get_last_codex_automation_comment_time(comments)
        assert result == "2026-01-31T10:00:00Z", \
            f"comment_validation marker not recognized! Got {result}. This causes feedback loops."

    def test_all_automation_markers_recognized(self, monitor):
        """All workflow markers should be recognized by _get_last_codex_automation_comment_time."""
        test_cases = [
            ("CODEX_COMMIT_MARKER_PREFIX", monitor.CODEX_COMMIT_MARKER_PREFIX),
            ("FIX_COMMENT_MARKER_PREFIX", monitor.FIX_COMMENT_MARKER_PREFIX),
            ("FIX_COMMENT_RUN_MARKER_PREFIX", monitor.FIX_COMMENT_RUN_MARKER_PREFIX),
            ("FIXPR_MARKER_PREFIX", monitor.FIXPR_MARKER_PREFIX),
            ("COMMENT_VALIDATION_MARKER_PREFIX", monitor.COMMENT_VALIDATION_MARKER_PREFIX),
        ]

        for marker_name, marker_prefix in test_cases:
            comments = [
                {
                    "body": f"{marker_prefix}test123-->\nAutomation comment",
                    "author": {"login": "automation"},
                    "createdAt": "2026-01-31T12:00:00Z",
                }
            ]
            result = monitor._get_last_codex_automation_comment_time(comments)
            assert result == "2026-01-31T12:00:00Z", \
                f"{marker_name} not recognized! Got {result}"


class TestFilterEligiblePRsIntegration:
    """Integration tests for the full PR filtering pipeline."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        with patch.object(JleechanorgPRMonitor, '_load_branch_history', return_value={}):
            m = JleechanorgPRMonitor()
            return m

    def test_mixed_pr_list_filtering(self, monitor):
        """Filter should correctly handle a mix of regular, draft, and closed PRs."""
        pr_list = [
            # Regular PR - should be actionable
            {
                "number": 383,
                "state": "OPEN",
                "isDraft": False,
                "headRefOid": "commit1",
                "repository": "ai_universe_frontend",
                "headRefName": "codex/try-installing-in-codex-web-containers",
            },
            # Draft sub-PR - should NOT be actionable (draft filter)
            {
                "number": 398,
                "state": "OPEN",
                "isDraft": True,
                "headRefOid": "commit2",
                "repository": "ai_universe_frontend",
                "headRefName": "copilot/sub-pr-383-6d22ba3d",
            },
            # Closed PR - should NOT be actionable
            {
                "number": 300,
                "state": "CLOSED",
                "isDraft": False,
                "headRefOid": "commit4",
                "repository": "ai_universe_frontend",
                "headRefName": "feature/old",
            },
        ]

        eligible = monitor.filter_eligible_prs(pr_list)

        # Only PR #383 should be eligible
        assert len(eligible) == 1
        assert eligible[0]["number"] == 383
