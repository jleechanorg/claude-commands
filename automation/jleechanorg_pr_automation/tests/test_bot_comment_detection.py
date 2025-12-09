#!/usr/bin/env python3
"""Tests for GitHub bot comment detection since last Codex comment."""

import unittest

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestBotCommentDetection(unittest.TestCase):
    """Validate detection of new GitHub bot comments since last Codex automation comment."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor()

    def test_detects_new_github_actions_bot_comment(self) -> None:
        """Should detect new comment from github-actions[bot] after Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix this {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed: test_something assertion error",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertTrue(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Expected to detect new github-actions[bot] comment after Codex comment",
        )

    def test_detects_new_dependabot_comment(self) -> None:
        """Should detect new comment from dependabot[bot] after Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix issue {self.monitor.CODEX_COMMIT_MARKER_PREFIX}def456{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "dependabot[bot]"},
                "body": "Security vulnerability detected",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertTrue(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Expected to detect new dependabot[bot] comment after Codex comment",
        )

    def test_no_detection_when_bot_comment_before_codex(self) -> None:
        """Should NOT detect bot comments that came BEFORE Codex comment."""
        comments = [
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T09:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should not detect bot comment that came before Codex comment",
        )

    def test_no_detection_when_no_codex_comment_exists(self) -> None:
        """Should return False when there is no Codex automation comment."""
        comments = [
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": "Regular comment without marker",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should return False when no Codex automation comment exists",
        )

    def test_excludes_codex_bot_comments(self) -> None:
        """Should NOT count codex[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "codex[bot]"},
                "body": "Codex summary: fixed the issue",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should NOT count codex[bot] as a new bot requiring action",
        )

    def test_excludes_coderabbitai_bot_comments(self) -> None:
        """Should NOT count coderabbitai[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "coderabbitai[bot]"},
                "body": "Code review completed",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should NOT count coderabbitai[bot] as a new bot requiring action",
        )

    def test_excludes_copilot_bot_comments(self) -> None:
        """Should NOT count copilot[bot] as a new bot comment to process."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "copilot[bot]"},
                "body": "Copilot suggestion",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should NOT count copilot[bot] as a new bot requiring action",
        )

    def test_ignores_human_comments_after_codex(self) -> None:
        """Human comments after Codex should NOT trigger new bot detection."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"@codex fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "reviewer"},
                "body": "LGTM",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Human comments should not be considered bot comments",
        )

    def test_uses_latest_codex_comment_time(self) -> None:
        """Should use the timestamp of the MOST RECENT Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 1 {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI failed",
                "createdAt": "2024-01-01T11:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 2 {self.monitor.CODEX_COMMIT_MARKER_PREFIX}def456{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        # Bot comment at 11:00 is BEFORE latest Codex comment at 12:00
        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should use latest Codex comment time, not the first one",
        )

    def test_detects_bot_comment_after_latest_codex(self) -> None:
        """Should detect bot comment that comes after the latest Codex comment."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 1 {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "author": {"login": "jleechan"},
                "body": f"Fix 2 {self.monitor.CODEX_COMMIT_MARKER_PREFIX}def456{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T11:00:00Z",
            },
            {
                "author": {"login": "github-actions[bot]"},
                "body": "CI still failing",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        self.assertTrue(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should detect bot comment that comes after the latest Codex comment",
        )

    def test_handles_empty_comments_list(self) -> None:
        """Should handle empty comments list gracefully."""
        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex([]),
            "Should return False for empty comments list",
        )

    def test_handles_missing_author(self) -> None:
        """Should handle comments with missing author field."""
        comments = [
            {
                "author": {"login": "jleechan"},
                "body": f"Fix {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "body": "Comment with no author",
                "createdAt": "2024-01-01T11:00:00Z",
            },
        ]

        # Should not crash and should return False (no valid bot comment)
        self.assertFalse(
            self.monitor._has_new_bot_comments_since_codex(comments),
            "Should handle missing author gracefully",
        )


class TestIsGithubBotComment(unittest.TestCase):
    """Validate _is_github_bot_comment method."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor()

    def test_identifies_github_actions_bot(self) -> None:
        comment = {"author": {"login": "github-actions[bot]"}}
        self.assertTrue(self.monitor._is_github_bot_comment(comment))

    def test_identifies_dependabot(self) -> None:
        comment = {"author": {"login": "dependabot[bot]"}}
        self.assertTrue(self.monitor._is_github_bot_comment(comment))

    def test_identifies_renovate_bot(self) -> None:
        comment = {"author": {"login": "renovate[bot]"}}
        self.assertTrue(self.monitor._is_github_bot_comment(comment))

    def test_excludes_codex_bot(self) -> None:
        comment = {"author": {"login": "codex[bot]"}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_excludes_coderabbitai_bot(self) -> None:
        comment = {"author": {"login": "coderabbitai[bot]"}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_excludes_copilot_bot(self) -> None:
        comment = {"author": {"login": "copilot[bot]"}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_excludes_cursor_bot(self) -> None:
        comment = {"author": {"login": "cursor[bot]"}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_excludes_human_user(self) -> None:
        comment = {"author": {"login": "jleechan"}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_handles_user_field_fallback(self) -> None:
        comment = {"user": {"login": "github-actions[bot]"}}
        self.assertTrue(self.monitor._is_github_bot_comment(comment))

    def test_handles_empty_author(self) -> None:
        comment = {"author": {}}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))

    def test_handles_missing_author(self) -> None:
        comment = {"body": "no author"}
        self.assertFalse(self.monitor._is_github_bot_comment(comment))


class TestGetLastCodexAutomationCommentTime(unittest.TestCase):
    """Validate _get_last_codex_automation_comment_time method."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor()

    def test_returns_latest_codex_comment_time(self) -> None:
        comments = [
            {
                "body": f"First {self.monitor.CODEX_COMMIT_MARKER_PREFIX}abc{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T10:00:00Z",
            },
            {
                "body": f"Second {self.monitor.CODEX_COMMIT_MARKER_PREFIX}def{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "createdAt": "2024-01-01T12:00:00Z",
            },
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)
        self.assertEqual(result, "2024-01-01T12:00:00Z")

    def test_returns_none_when_no_codex_comments(self) -> None:
        comments = [
            {"body": "Regular comment", "createdAt": "2024-01-01T10:00:00Z"},
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)
        self.assertIsNone(result)

    def test_returns_none_for_empty_list(self) -> None:
        result = self.monitor._get_last_codex_automation_comment_time([])
        self.assertIsNone(result)

    def test_uses_updated_at_fallback(self) -> None:
        comments = [
            {
                "body": f"Update {self.monitor.CODEX_COMMIT_MARKER_PREFIX}xyz{self.monitor.CODEX_COMMIT_MARKER_SUFFIX}",
                "updatedAt": "2024-01-01T15:00:00Z",
            },
        ]

        result = self.monitor._get_last_codex_automation_comment_time(comments)
        self.assertEqual(result, "2024-01-01T15:00:00Z")


if __name__ == "__main__":
    unittest.main()
