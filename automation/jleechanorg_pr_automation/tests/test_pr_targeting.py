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
        monitor = JleechanorgPRMonitor()
        intro_line = build_comment_intro(
            assistant_mentions=monitor.assistant_mentions
        )
        test_comment = (
            f"{intro_line} Test comment\n\n"
            f"{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        )
        marker = monitor._extract_commit_marker(test_comment)
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
        monitor = JleechanorgPRMonitor()
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
        monitor = JleechanorgPRMonitor()
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
        monitor = JleechanorgPRMonitor()
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
        monitor = JleechanorgPRMonitor()
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
        monitor = JleechanorgPRMonitor()
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


if __name__ == "__main__":
    unittest.main()
