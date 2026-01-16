#!/usr/bin/env python3
"""
Test PR targeting functionality for jleechanorg_pr_monitor - Codex Strategy Tests Only
"""

import unittest

from jleechanorg_pr_automation.codex_config import build_comment_intro
from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestPRTargeting(unittest.TestCase):
    """Test PR targeting functionality - Codex Strategy Only"""

    def test_extract_commit_marker(self):
        """Commit markers can be parsed from Codex comments"""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        intro_line = build_comment_intro(
            assistant_mentions=monitor.assistant_mentions
        )
        test_comment = (
            f"{intro_line} Test comment\n\n"
            f"{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        )
        marker = monitor._extract_commit_marker(test_comment)
        self.assertEqual(marker, "abc123")

    def test_fix_comment_marker_detected_for_commit(self):
        """Fix-comment markers should be detected for commit gating."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        test_comment = (
            "Queued\n"
            f"{monitor.FIX_COMMENT_MARKER_PREFIX}abc123"
            f"{monitor.FIX_COMMENT_MARKER_SUFFIX}"
        )

        marker = monitor._extract_fix_comment_marker(test_comment)
        self.assertEqual(marker, "abc123")

    def test_intro_prose_avoids_duplicate_mentions(self):
        """Review assistants should not retain '@' prefixes in prose text."""

        intro_line = build_comment_intro(
            assistant_mentions="@codex @coderabbitai @copilot @cursor"
        )
        _, _, intro_body = intro_line.partition("] ")
        self.assertIn("coderabbitai", intro_body)
        self.assertNotIn("@coderabbitai", intro_body)

    def test_intro_without_mentions_has_no_leading_space(self):
        """Explicitly blank mention lists should not add stray whitespace."""

        intro_line = build_comment_intro(assistant_mentions="")
        self.assertTrue(intro_line.startswith("[AI automation]"))

    def test_detect_pending_codex_commit(self):
        """Codex bot summary comments referencing head commit trigger pending detection."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        head_sha = "abcdef1234567890"
        comments = [
            {
                "body": "**Summary**\nlink https://github.com/org/repo/blob/abcdef1234567890/path/file.py\n",
                "author": {"login": "chatgpt-codex-connector[bot]"},
            }
        ]

        self.assertTrue(monitor._has_pending_codex_commit(comments, head_sha))

    def test_pending_codex_commit_detects_short_sha_references(self):
        """Cursor Bugbot short SHA references should still count as pending commits."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        full_head_sha = "c279655d00dfcab5ac1a2fd9b0f6205ce5cbba12"
        comments = [
            {
                "body": "Written by Cursor Bugbot for commit c279655. This will update automatically on new commits.",
                "author": {"login": "chatgpt-codex-connector[bot]"},
            }
        ]

        self.assertTrue(monitor._has_pending_codex_commit(comments, full_head_sha))

    def test_pending_codex_commit_ignores_short_head_sha(self):
        """Short head SHAs should not match longer Codex summary hashes."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        short_head_sha = "c279655"
        comments = [
            {
                "body": "Written by Cursor Bugbot for commit c279655d00dfcab5ac1a2fd9b0f6205ce5cbba12.",
                "author": {"login": "chatgpt-codex-connector[bot]"},
            }
        ]

        self.assertFalse(monitor._has_pending_codex_commit(comments, short_head_sha))

    def test_pending_codex_commit_requires_codex_author(self):
        """Pending detection ignores non-Codex authors even if commit appears in comment."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        head_sha = "abcdef1234567890"
        comments = [
            {
                "body": "Please review commit https://github.com/org/repo/commit/abcdef1234567890",
                "author": {"login": "reviewer"},
            }
        ]

        self.assertFalse(monitor._has_pending_codex_commit(comments, head_sha))

    def test_codex_comment_includes_detailed_execution_flow(self):
        """Automation comment should summarize the enforced execution flow with numbered steps."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Improve automation summary",
            "author": {"login": "developer"},
            "headRefName": "feature/automation-flow",
        }

        comment_body = monitor._build_codex_comment_body_simple(
            "jleechanorg/worldarchitect.ai",
            42,
            pr_data,
            "abcdef1234567890",
        )

        self.assertIn("**Summary (Execution Flow):**", comment_body)
        self.assertIn("1. Review every outstanding PR comment", comment_body)
        self.assertIn("5. Perform a final self-review", comment_body)

    def test_fix_comment_queued_body_excludes_marker(self):
        """Queued fix-comment notices should not include commit markers."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Queued Fix Comment",
            "author": {"login": "developer"},
            "headRefName": "feature/queued",
        }
        head_sha = "abc123def456"

        comment_body = monitor._build_fix_comment_queued_body(
            "org/repo",
            42,
            pr_data,
            head_sha,
        )

        self.assertNotIn(monitor.FIX_COMMENT_MARKER_PREFIX, comment_body)
        # Queued notices should use the dedicated run marker (not the completion commit marker).
        self.assertIn(monitor.FIX_COMMENT_RUN_MARKER_PREFIX, comment_body)
        self.assertIn(head_sha, comment_body)

    def test_fix_comment_review_body_includes_marker(self):
        """Review requests should include the fix-comment commit marker."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Review Fix Comment",
            "author": {"login": "developer"},
            "headRefName": "feature/review",
        }
        head_sha = "deadbeef1234"

        comment_body = monitor._build_fix_comment_review_body(
            "org/repo",
            42,
            pr_data,
            head_sha,
        )

        self.assertIn(monitor.FIX_COMMENT_MARKER_PREFIX, comment_body)
        self.assertIn(monitor.FIX_COMMENT_MARKER_SUFFIX, comment_body)

    def test_fix_comment_prompt_requires_threaded_replies(self):
        """Fix-comment prompts should require threaded replies via the GitHub API."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        pr_data = {
            "title": "Threaded Replies",
            "author": {"login": "developer"},
            "headRefName": "feature/threaded",
        }

        prompt = monitor._build_fix_comment_prompt_body(
            "org/repo",
            42,
            pr_data,
            "abc123",
            agent_cli="gemini",
        ).lower()

        # Verify prompt includes threading guidance
        self.assertIn("thread", prompt)
        self.assertIn("gh api", prompt)
        self.assertIn("review comments", prompt)
        self.assertIn("issue comments", prompt)
        # After fix for comment #2669657213, prompt clarifies:
        # - Inline review comments use: /pulls/{pr_number}/comments with -F in_reply_to={comment_id}
        # - Issue comments don't support threading (top-level comments only)
        self.assertIn("pulls/42/comments", prompt)  # Updated to match actual PR number in prompt
        self.assertIn("reply individually to each comment", prompt)  # Issue comments clarification

    def test_fix_comment_marker_ignores_queued_comment(self):
        """Queued notices with markers should not satisfy the fix-comment completion check."""
        monitor = JleechanorgPRMonitor(automation_username="test-automation-user")
        head_sha = "feedface1234"
        comment_body = (
            "[AI automation] Fix-comment run queued for this PR. "
            "A review request will follow after updates are pushed.\n\n"
            f"{monitor.FIX_COMMENT_MARKER_PREFIX}{head_sha}{monitor.FIX_COMMENT_MARKER_SUFFIX}"
        )
        comments = [{"body": comment_body}]

        self.assertFalse(monitor._has_fix_comment_comment_for_commit(comments, head_sha))


if __name__ == "__main__":
    unittest.main()
