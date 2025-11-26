#!/usr/bin/env python3
"""Tests for Codex actor detection heuristics."""

import unittest

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCodexActorMatching(unittest.TestCase):
    """Validate detection of Codex-authored commits."""

    def setUp(self) -> None:
        self.monitor = JleechanorgPRMonitor()

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


if __name__ == "__main__":
    unittest.main()
