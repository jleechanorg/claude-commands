#!/usr/bin/env python3
"""Tests for Codex actor detection heuristics."""

import unittest

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCodexActorMatching(unittest.TestCase):
    """Validate detection of Codex-authored commits."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_detects_codex_via_actor_fields(self) -> None:
        commit_details = {
            "author_login": "codex-bot",
            "author_email": "codex@example.com",
            "author_name": "Codex Bot",
            "committer_login": None,
            "committer_email": None,
            "committer_name": None,
            "message_headline": "Refactor subsystem",
            "message": "Refactor subsystem",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected Codex detection when actor fields include Codex token",
        )

    def test_detects_codex_via_message_marker(self) -> None:
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": (
                f"Address review feedback {self.monitor.CODEX_COMMIT_MESSAGE_MARKER}"
            ),
            "message": "Address review feedback and add tests",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected Codex detection from commit message marker",
        )

    def test_detects_codex_via_message_body_marker_case_insensitive(self) -> None:
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "Address review feedback",
            "message": "Add docs [CODEX-AUTOMATION-COMMIT] and clean up",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected Codex detection from commit body marker",
        )

    def test_returns_false_when_no_codex_tokens_found(self) -> None:
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "reviewer",
            "committer_email": "reviewer@example.com",
            "committer_name": "Helpful Reviewer",
            "message_headline": "Refactor subsystem",
            "message": "Improve code coverage",
        }

        self.assertFalse(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected no Codex detection when no markers are present",
        )

    def test_handles_non_string_actor_fields(self) -> None:
        """Type safety: should not crash when actor fields contain non-string values"""
        commit_details = {
            "author_login": {"nested": "value"},  # Invalid type
            "author_email": 12345,  # Invalid type
            "author_name": None,
            "committer_login": ["list", "value"],  # Invalid type
            "committer_email": None,
            "committer_name": None,
            "message_headline": "Normal message",
            "message": "Normal body",
        }

        # Should not raise TypeError and should return False
        result = self.monitor._is_head_commit_from_codex(commit_details)
        self.assertFalse(result, "Should handle non-string fields gracefully")

    def test_handles_non_string_message_fields(self) -> None:
        """Type safety: should not crash when message fields contain non-string values"""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": None,
            "committer_email": None,
            "committer_name": None,
            "message_headline": {"nested": "object"},  # Invalid type
            "message": 12345,  # Invalid type
        }

        # Should not raise TypeError and should return False
        result = self.monitor._is_head_commit_from_codex(commit_details)
        self.assertFalse(result, "Should handle non-string message fields gracefully")

    def test_handles_empty_string_fields(self) -> None:
        """Should handle empty strings correctly"""
        commit_details = {
            "author_login": "",
            "author_email": "",
            "author_name": "",
            "committer_login": "",
            "committer_email": "",
            "committer_name": "",
            "message_headline": "",
            "message": "",
        }

        result = self.monitor._is_head_commit_from_codex(commit_details)
        self.assertFalse(result, "Should treat empty strings as no Codex markers")

    # =========================================================================
    # Tests for centralized workflow detection (fixcomment, fixpr, codex, etc.)
    # These tests verify that ALL automation workflows are detected via commit messages
    # =========================================================================

    def test_detects_fixcomment_via_message_marker(self) -> None:
        """Test that fixcomment workflow commits are detected via message marker."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "[fixcomment-automation-commit] Fix PR review comments",
            "message": "Fix PR review comments and address feedback",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected fixcomment detection from commit message marker",
        )

    def test_detects_fixcomment_with_actor_via_message_marker(self) -> None:
        """Test that fixcomment workflow commits with actor are detected."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "claude-bot",
            "committer_email": "claude@example.com",
            "committer_name": "Claude Bot",
            "message_headline": "[fixcomment claude-automation-commit] Fix PR review comments",
            "message": "Fix PR review comments",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected fixcomment with actor detection from commit message marker",
        )

    def test_detects_fixpr_with_gemini_actor_via_message_marker(self) -> None:
        """Test that fixpr workflow commits with gemini actor are detected."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "gemini-bot",
            "committer_email": "gemini@example.com",
            "committer_name": "Gemini Bot",
            "message_headline": "[fixpr gemini-automation-commit] Resolve conflicts",
            "message": "Merge main to resolve conflicts",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected fixpr with gemini actor detection from commit message marker",
        )

    def test_detects_codex_with_cursor_actor_via_message_marker(self) -> None:
        """Test that codex workflow commits with cursor actor are detected."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "cursor-bot",
            "committer_email": "cursor@example.com",
            "committer_name": "Cursor Bot",
            "message_headline": "[codex cursor-automation-commit] Update tests",
            "message": "Update tests for new functionality",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected codex with cursor actor detection from commit message marker",
        )

    def test_detects_comment_validation_via_message_marker(self) -> None:
        """Test that comment-validation workflow commits are detected via message marker."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "[comment-validation-automation-commit] Request reviews",
            "message": "Request AI bot reviews on PR",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected comment-validation detection from commit message marker",
        )

    def test_detects_automation_via_message_body_not_headline(self) -> None:
        """Test that automation markers in message body (not just headline) are detected."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "Update functionality",
            "message": "Update functionality and fix issues [fixcomment-automation-commit]",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected detection from commit body marker",
        )

    def test_detects_coderabbitai_legacy_marker(self) -> None:
        """Legacy compatibility: coderabbitai automation markers should still be recognized."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "[coderabbitai-automation-commit] Apply review fixes",
            "message": "Apply review fixes",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected coderabbitai legacy marker detection",
        )

    def test_detects_fixpr_coderabbit_legacy_marker(self) -> None:
        """Legacy compatibility: fixpr + coderabbit markers should still be recognized."""
        commit_details = {
            "author_login": "regular-user",
            "author_email": "dev@example.com",
            "author_name": "Regular User",
            "committer_login": "regular-user",
            "committer_email": "dev@example.com",
            "committer_name": "Regular User",
            "message_headline": "[fixpr coderabbit-automation-commit] Resolve conflicts",
            "message": "Resolve conflicts",
        }

        self.assertTrue(
            self.monitor._is_head_commit_from_codex(commit_details),
            "Expected fixpr coderabbit legacy marker detection",
        )


if __name__ == "__main__":
    unittest.main()
