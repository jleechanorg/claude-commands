"""TDD Tests for Centralized Automation Marker Detection.

Problem: Multiple one-off fixes for feedback loops because marker detection
is scattered across multiple methods, each manually listing all markers.
When a new marker is added, it's easy to forget to update all locations.

Solution: Centralize ALL_AUTOMATION_MARKER_PREFIXES and provide helper functions
that use this single source of truth.

Test Matrix:
1. ALL_AUTOMATION_MARKER_PREFIXES exists and contains all known markers
2. is_automation_comment() correctly detects all marker types
3. _get_last_codex_automation_comment_time() uses centralized detection
4. _count_workflow_comments() uses centralized detection for fallback
5. Future-proofing: adding a new marker to ALL_AUTOMATION_MARKER_PREFIXES
   automatically makes it work everywhere
"""

import unittest
from unittest.mock import MagicMock

from jleechanorg_pr_automation import codex_config
from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestCentralizedMarkerPrefixesTuple(unittest.TestCase):
    """Test that ALL_AUTOMATION_MARKER_PREFIXES exists and is complete."""

    def test_all_automation_marker_prefixes_exists(self):
        """ALL_AUTOMATION_MARKER_PREFIXES should be defined in codex_config."""
        self.assertTrue(
            hasattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES"),
            "codex_config should define ALL_AUTOMATION_MARKER_PREFIXES tuple",
        )

    def test_all_automation_marker_prefixes_is_tuple(self):
        """ALL_AUTOMATION_MARKER_PREFIXES should be a tuple (immutable)."""
        prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", None)
        self.assertIsInstance(
            prefixes,
            tuple,
            "ALL_AUTOMATION_MARKER_PREFIXES should be a tuple for immutability",
        )

    def test_all_known_markers_are_included(self):
        """All individually-defined marker prefixes should be in the centralized tuple."""
        prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())

        known_markers = [
            codex_config.CODEX_COMMIT_MARKER_PREFIX,
            codex_config.FIX_COMMENT_MARKER_PREFIX,
            codex_config.FIX_COMMENT_RUN_MARKER_PREFIX,
            codex_config.FIXPR_MARKER_PREFIX,
            codex_config.COMMENT_VALIDATION_MARKER_PREFIX,
        ]

        for marker in known_markers:
            with self.subTest(marker=marker):
                self.assertIn(
                    marker,
                    prefixes,
                    f"ALL_AUTOMATION_MARKER_PREFIXES should include {marker}",
                )

    def test_no_duplicates_in_prefixes(self):
        """ALL_AUTOMATION_MARKER_PREFIXES should not have duplicates."""
        prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())
        self.assertEqual(
            len(prefixes),
            len(set(prefixes)),
            "ALL_AUTOMATION_MARKER_PREFIXES should not contain duplicates",
        )


class TestIsAutomationCommentHelper(unittest.TestCase):
    """Test the centralized is_automation_comment() helper function."""

    def test_is_automation_comment_exists(self):
        """is_automation_comment() should be defined in codex_config."""
        self.assertTrue(
            hasattr(codex_config, "is_automation_comment"),
            "codex_config should define is_automation_comment() function",
        )

    def test_detects_codex_commit_marker(self):
        """is_automation_comment() should detect CODEX_COMMIT_MARKER_PREFIX."""
        body = f"Some text {codex_config.CODEX_COMMIT_MARKER_PREFIX}abc123-->"
        result = codex_config.is_automation_comment(body)
        self.assertTrue(result, "Should detect CODEX_COMMIT_MARKER_PREFIX")

    def test_detects_fix_comment_marker(self):
        """is_automation_comment() should detect FIX_COMMENT_MARKER_PREFIX."""
        body = f"Some text {codex_config.FIX_COMMENT_MARKER_PREFIX}abc123-->"
        result = codex_config.is_automation_comment(body)
        self.assertTrue(result, "Should detect FIX_COMMENT_MARKER_PREFIX")

    def test_detects_fix_comment_run_marker(self):
        """is_automation_comment() should detect FIX_COMMENT_RUN_MARKER_PREFIX."""
        body = f"Some text {codex_config.FIX_COMMENT_RUN_MARKER_PREFIX}abc123-->"
        result = codex_config.is_automation_comment(body)
        self.assertTrue(result, "Should detect FIX_COMMENT_RUN_MARKER_PREFIX")

    def test_detects_fixpr_marker(self):
        """is_automation_comment() should detect FIXPR_MARKER_PREFIX."""
        body = f"Some text {codex_config.FIXPR_MARKER_PREFIX}abc123-->"
        result = codex_config.is_automation_comment(body)
        self.assertTrue(result, "Should detect FIXPR_MARKER_PREFIX")

    def test_detects_comment_validation_marker(self):
        """is_automation_comment() should detect COMMENT_VALIDATION_MARKER_PREFIX."""
        body = f"Some text {codex_config.COMMENT_VALIDATION_MARKER_PREFIX}abc123-->"
        result = codex_config.is_automation_comment(body)
        self.assertTrue(result, "Should detect COMMENT_VALIDATION_MARKER_PREFIX")

    def test_returns_false_for_regular_comment(self):
        """is_automation_comment() should return False for non-automation comments."""
        body = "This is a regular PR comment without any automation markers."
        result = codex_config.is_automation_comment(body)
        self.assertFalse(result, "Should return False for regular comments")

    def test_returns_false_for_empty_body(self):
        """is_automation_comment() should return False for empty string."""
        result = codex_config.is_automation_comment("")
        self.assertFalse(result, "Should return False for empty string")

    def test_returns_false_for_none(self):
        """is_automation_comment() should handle None gracefully."""
        result = codex_config.is_automation_comment(None)
        self.assertFalse(result, "Should return False for None")


class TestJleechanorgPRMonitorUsesCentralizedDetection(unittest.TestCase):
    """Test that JleechanorgPRMonitor uses centralized marker detection."""

    def setUp(self):
        """Create JleechanorgPRMonitor instance for testing."""
        self.monitor = JleechanorgPRMonitor.__new__(JleechanorgPRMonitor)
        self.monitor.logger = MagicMock()

    def test_get_last_codex_automation_comment_time_uses_centralized(self):
        """_get_last_codex_automation_comment_time should use is_automation_comment()."""
        # Create comments with each marker type
        all_prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())

        for i, prefix in enumerate(all_prefixes):
            with self.subTest(prefix=prefix):
                comments = [
                    {
                        "body": f"Automation {prefix}sha123-->",
                        "createdAt": f"2026-01-{20+i:02d}T12:00:00Z",
                    }
                ]
                result = self.monitor._get_last_codex_automation_comment_time(comments)
                self.assertIsNotNone(
                    result,
                    f"Should recognize comment with {prefix} as automation comment",
                )

    def test_new_marker_automatically_detected(self):
        """Adding a marker to ALL_AUTOMATION_MARKER_PREFIXES should automatically work.

        This is the key benefit of centralization: no code changes needed
        in JleechanorgPRMonitor when a new marker is added to the central tuple.
        """
        # Verify all prefixes in tuple are detected
        all_prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())

        for prefix in all_prefixes:
            body = f"Test {prefix}test123-->"
            # Use the centralized function (which JleechanorgPRMonitor should use internally)
            result = codex_config.is_automation_comment(body)
            self.assertTrue(
                result,
                f"Marker {prefix} from ALL_AUTOMATION_MARKER_PREFIXES should be auto-detected",
            )


class TestFutureProofing(unittest.TestCase):
    """Test that the centralized approach is future-proof."""

    def test_marker_count_matches_expected(self):
        """Verify we have exactly 5 automation marker prefixes currently.

        If this test fails after adding a new marker, update the count
        and add the new marker to ALL_AUTOMATION_MARKER_PREFIXES.
        """
        prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())
        expected_count = 5  # Update when adding new markers

        self.assertEqual(
            len(prefixes),
            expected_count,
            f"Expected {expected_count} marker prefixes. If you added a new marker, "
            "update this test and ensure it's in ALL_AUTOMATION_MARKER_PREFIXES.",
        )

    def test_all_prefixes_start_with_html_comment(self):
        """All marker prefixes should start with '<!--' (HTML comment)."""
        prefixes = getattr(codex_config, "ALL_AUTOMATION_MARKER_PREFIXES", ())

        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    prefix.startswith("<!--"),
                    f"Marker prefix should start with '<!--': {prefix}",
                )


if __name__ == "__main__":
    unittest.main()
