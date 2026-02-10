"""
TDD tests for PR monitor feedback loop prevention.

Tests verify that:
1. Draft PRs are always skipped (the primary defense against sub-PR feedback loops)
2. COMMENT_VALIDATION_MARKER_PREFIX is recognized in automation marker detection
"""

from unittest.mock import patch

import pytest

from jleechanorg_pr_automation.automation_utils import AutomationUtils
from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestDraftPRFiltering:
    """Test that draft PRs are always skipped - primary feedback loop defense."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance with mocked GitHub calls."""
        with patch.object(JleechanorgPRMonitor, "_load_branch_history", return_value={}):
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
        with patch.object(JleechanorgPRMonitor, "_load_branch_history", return_value={}):
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


class TestNoDuplicateCommentsPerSHA:
    """Tests that an existing automation comment for a HEAD SHA prevents additional
    automation comments for the same SHA.

    Invariant under test:
    - If an automation comment already exists for a given commit SHA, subsequent
      runs must not post a second automation comment for that SHA, regardless of
      the presence or ordering of other comments (including bot comments).
    """

    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        with patch.object(JleechanorgPRMonitor, "_load_branch_history", return_value={}):
            m = JleechanorgPRMonitor()
            return m

    def test_skip_when_comment_exists_for_sha(self, monitor):
        """Should skip posting if comment already exists for this SHA, even with bot comments."""
        head_sha = "abc123def"
        marker_prefix = monitor.CODEX_COMMIT_MARKER_PREFIX
        marker_suffix = monitor.CODEX_COMMIT_MARKER_SUFFIX

        comments = [
            # Existing automation comment for this SHA
            {
                "body": f"Please address comments\n\n{marker_prefix}{head_sha}{marker_suffix}",
                "author": {"login": "jleechan2015"},
                "createdAt": "2026-02-09T08:00:00Z",
            },
            # Bot comment after automation comment (would trigger "new bot comment" detection)
            {
                "body": "Please fix the SQL injection vulnerability",
                "author": {"login": "coderabbitai[bot]"},
                "createdAt": "2026-02-09T08:05:00Z",
            },
        ]

        # Check if comment exists for this SHA
        has_comment = monitor._has_codex_comment_for_commit(comments, head_sha)
        assert has_comment is True, "Should detect existing comment for this SHA"

        # Verify we would skip even though there's a "new bot comment"
        # (This is the fix - we always check for existing comment regardless of bot comments)

    def test_post_when_no_comment_for_new_sha(self, monitor):
        """Should post when there's no comment for the new SHA, even with bot comments."""
        old_sha = "abc123def"
        new_sha = "xyz789ghi"
        marker_prefix = monitor.CODEX_COMMIT_MARKER_PREFIX
        marker_suffix = monitor.CODEX_COMMIT_MARKER_SUFFIX

        comments = [
            # Automation comment for OLD SHA
            {
                "body": f"Please address comments\n\n{marker_prefix}{old_sha}{marker_suffix}",
                "author": {"login": "jleechan2015"},
                "createdAt": "2026-02-09T08:00:00Z",
            },
            # Bot comment
            {
                "body": "Please fix the issue",
                "author": {"login": "coderabbitai[bot]"},
                "createdAt": "2026-02-09T08:05:00Z",
            },
        ]

        # Check if comment exists for NEW SHA
        has_comment = monitor._has_codex_comment_for_commit(comments, new_sha)
        assert has_comment is False, "Should NOT detect comment for new SHA"

        # Should proceed to post because no comment exists for new_sha

    def test_codex_pr_not_actionable_with_bot_comments(self, monitor):
        """Codex PRs should NOT be marked actionable even when bot comments exist (Option A)."""
        # Mock PR data with Codex branch and bot comments
        pr_data = {
            "number": 5154,
            "state": "OPEN",
            "isDraft": False,
            "headRefOid": "abc123def",
            "repository": "worldarchitect.ai",
            "headRefName": "copilot/auto_comment_loop",  # Codex branch pattern
            "repositoryFullName": "jleechanorg/worldarchitect.ai",
        }

        # Mock _should_skip_pr to indicate PR was already processed (so we hit the bot comment check path)
        # Mock _get_pr_comment_state to return bot comments
        with patch.object(monitor, "_should_skip_pr", return_value=True):
            with patch.object(monitor, "_get_pr_comment_state", return_value=(None, [
                {
                    "body": "Previous automation comment",
                    "author": {"login": "jleechan2015"},
                    "createdAt": "2026-02-09T08:00:00Z",
                },
                {
                    "body": "Bot review feedback",
                    "author": {"login": "coderabbitai[bot]"},
                    "createdAt": "2026-02-09T08:05:00Z",
                },
            ])):
                # Should NOT be actionable (Option A: no re-pinging on bot comments)
                is_actionable = monitor.is_pr_actionable(pr_data)
                assert is_actionable is False, \
                    "Option A: Codex PRs should NOT be actionable even with bot comments"


    def test_all_branches_get_codex_comments_in_default_mode(self, monitor):
        """Comment-only mode posts Codex support comments on ALL non-draft PRs (not just Codex branches)."""
        # Mock PR data with non-Codex branch
        pr_data = {
            "number": 5155,
            "state": "OPEN",
            "isDraft": False,
            "headRefOid": "d318e327",
            "repository": "worldarchitect.ai",
            "headRefName": "docs/automation-orchestration-guide",  # NOT a Codex branch
            "repositoryFullName": "jleechanorg/worldarchitect.ai",
        }

        # Mock to avoid actual GitHub API calls and subprocess calls
        with (
            patch.object(monitor, "_get_pr_comment_state", return_value=("d318e327", [])),
            patch.object(monitor, "_get_head_commit_details", return_value=None),
            patch.object(monitor, "_should_skip_pr", return_value=False),
            patch.object(AutomationUtils, "execute_subprocess_with_timeout", return_value=(0, "", "")),
        ):
            result = monitor.post_codex_instruction_simple("worldarchitect.ai", 5155, pr_data)
            # Should be posted (ALL non-draft PRs get Codex support comments)
            assert result == "posted", \
                f"ALL branches (including non-Codex) should get Codex support comments in comment-only mode, got: {result}"


class TestFilterEligiblePRsIntegration:
    """Integration tests for the full PR filtering pipeline."""

    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        with patch.object(JleechanorgPRMonitor, "_load_branch_history", return_value={}):
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
