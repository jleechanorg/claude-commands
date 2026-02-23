#!/usr/bin/env python3
"""
Unit tests for automation marker generation and parsing functions.

Tests build_automation_marker() and parse_automation_marker() helper functions
added to support enhanced automation markers with workflow:agent:commit format.
"""

import unittest

from jleechanorg_pr_automation.codex_config import (
    FIX_COMMENT_RUN_MARKER_PREFIX,
    FIXPR_MARKER_PREFIX,
    build_automation_commit_marker,
    build_automation_marker,
    build_default_comment,
    is_automation_commit_message,
    parse_automation_marker,
)


class TestBuildAutomationMarker(unittest.TestCase):
    """Test build_automation_marker() function"""

    def test_basic_marker_generation(self):
        """Test basic marker generation with all parameters"""
        marker = build_automation_marker("fix-comment-run", "gemini", "abc1234")
        expected = "<!-- fix-comment-run-automation-commit:gemini:abc1234-->"
        self.assertEqual(marker, expected)

    def test_fixpr_workflow(self):
        """Test marker generation for fixpr workflow"""
        marker = build_automation_marker("fixpr-run", "codex", "def5678")
        expected = "<!-- fixpr-run-automation-commit:codex:def5678-->"
        self.assertEqual(marker, expected)

    def test_different_agents(self):
        """Test marker generation with different agent names"""
        agents = ["gemini", "codex", "claude"]
        for agent in agents:
            marker = build_automation_marker("fix-comment-run", agent, "sha123")
            self.assertIn(f":{agent}:", marker)
            self.assertTrue(marker.startswith("<!-- fix-comment-run-automation-commit:"))
            self.assertTrue(marker.endswith("-->"))

    def test_build_automation_commit_marker_matrix(self):
        """Matrix test for workflow + optional actor commit marker generation."""
        matrix = [
            ("codex", None),
            ("codex", "claude"),
            ("codex-api", None),
            ("fixpr", None),
            ("fixpr", "codex"),
            ("fixcomment", None),
            ("fixcomment", "claude"),
            ("fix-comment", "minimax"),
            ("comment-validation", "copilot"),
        ]

        expected = {
            ("codex", None): "[codex-automation-commit]",
            ("codex", "claude"): "[codex claude-automation-commit]",
            ("codex-api", None): "[codex-api-automation-commit]",
            ("fixpr", None): "[fixpr-automation-commit]",
            ("fixpr", "codex"): "[fixpr codex-automation-commit]",
            ("fixcomment", None): "[fixcomment-automation-commit]",
            ("fixcomment", "claude"): "[fixcomment claude-automation-commit]",
            ("fix-comment", "minimax"): "[fix-comment minimax-automation-commit]",
            ("comment-validation", "copilot"): "[comment-validation copilot-automation-commit]",
        }

        for workflow, actor in matrix:
            marker = build_automation_commit_marker(workflow, actor)
            self.assertEqual(marker, expected[(workflow, actor)])

    def test_short_commit_sha(self):
        """Test marker generation with short commit SHA"""
        marker = build_automation_marker("fix-comment-run", "gemini", "abc")
        expected = "<!-- fix-comment-run-automation-commit:gemini:abc-->"
        self.assertEqual(marker, expected)

    def test_long_commit_sha(self):
        """Test marker generation with full 40-character commit SHA"""
        full_sha = "a" * 40
        marker = build_automation_marker("fix-comment-run", "gemini", full_sha)
        expected = f"<!-- fix-comment-run-automation-commit:gemini:{full_sha}-->"
        self.assertEqual(marker, expected)

    def test_unknown_commit_fallback(self):
        """Test marker generation with 'unknown' commit value"""
        marker = build_automation_marker("fix-comment-run", "gemini", "unknown")
        expected = "<!-- fix-comment-run-automation-commit:gemini:unknown-->"
        self.assertEqual(marker, expected)

    def test_marker_format_consistency(self):
        """Test that marker format matches prefix constants"""
        # Fix-comment marker should match FIX_COMMENT_RUN_MARKER_PREFIX
        marker = build_automation_marker("fix-comment-run", "gemini", "abc123")
        self.assertTrue(marker.startswith(FIX_COMMENT_RUN_MARKER_PREFIX))

        # FixPR marker should match FIXPR_MARKER_PREFIX
        marker = build_automation_marker("fixpr-run", "codex", "def456")
        self.assertTrue(marker.startswith(FIXPR_MARKER_PREFIX))


class TestParseAutomationMarker(unittest.TestCase):
    """Test parse_automation_marker() function"""

    def test_parse_new_format_with_agent(self):
        """Test parsing new format marker with agent"""
        marker = "<!-- fix-comment-run-automation-commit:gemini:abc123-->"
        result = parse_automation_marker(marker)

        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], "fix-comment-run")
        self.assertEqual(result["agent"], "gemini")
        self.assertEqual(result["commit"], "abc123")

    def test_parse_fixpr_marker(self):
        """Test parsing fixpr-run marker"""
        marker = "<!-- fixpr-run-automation-commit:codex:def456-->"
        result = parse_automation_marker(marker)

        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], "fixpr-run")
        self.assertEqual(result["agent"], "codex")
        self.assertEqual(result["commit"], "def456")

    def test_parse_legacy_format_without_agent(self):
        """Test parsing legacy format marker without agent"""
        marker = "<!-- fix-comment-automation-commit:abc123-->"
        result = parse_automation_marker(marker)

        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], "fix-comment")
        self.assertEqual(result["agent"], "unknown")
        self.assertEqual(result["commit"], "abc123")

    def test_parse_legacy_fixpr_marker(self):
        """Test parsing legacy fixpr marker without agent"""
        marker = "<!-- fixpr-automation-commit:ghi789-->"
        result = parse_automation_marker(marker)

        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], "fixpr")
        self.assertEqual(result["agent"], "unknown")
        self.assertEqual(result["commit"], "ghi789")

    def test_parse_invalid_marker_missing_html_comment(self):
        """Test parsing invalid marker missing HTML comment markers"""
        marker = "fix-comment-run-automation-commit:gemini:abc123"
        result = parse_automation_marker(marker)
        self.assertIsNone(result)

    def test_parse_invalid_marker_wrong_format(self):
        """Test parsing invalid marker with wrong format"""
        marker = "<!-- some random comment -->"
        result = parse_automation_marker(marker)
        self.assertIsNone(result)

    def test_parse_invalid_marker_too_many_colons(self):
        """Test parsing marker with too many colons"""
        marker = "<!-- fix-comment-run-automation-commit:gemini:abc123:extra-->"
        result = parse_automation_marker(marker)
        # Should return None for invalid format (3 colons instead of 2)
        self.assertIsNone(result)

    def test_parse_marker_with_whitespace(self):
        """Test parsing marker with extra whitespace"""
        marker = "<!-- fix-comment-run-automation-commit:gemini:abc123 -->"
        result = parse_automation_marker(marker)

        # Parser should handle trailing whitespace gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], "fix-comment-run")

    def test_roundtrip_consistency(self):
        """Test that building and parsing a marker gives consistent results"""
        workflow = "fix-comment-run"
        agent = "gemini"
        commit = "abc1234"

        # Build marker
        marker = build_automation_marker(workflow, agent, commit)

        # Parse it back
        result = parse_automation_marker(marker)

        # Verify roundtrip consistency
        self.assertIsNotNone(result)
        self.assertEqual(result["workflow"], workflow)
        self.assertEqual(result["agent"], agent)
        self.assertEqual(result["commit"], commit)

    def test_parse_with_different_workflows(self):
        """Test parsing markers with different workflow types"""
        workflows = ["fix-comment-run", "fixpr-run", "codex", "pr-automation", "codex-api"]

        for workflow in workflows:
            marker = build_automation_marker(workflow, "gemini", "abc123")
            result = parse_automation_marker(marker)

            self.assertIsNotNone(result)
            self.assertEqual(result["workflow"], workflow)


class TestCodexDefaultCommentTracking(unittest.TestCase):
    """Test Codex default comment tracking requirements."""

    def test_default_comment_mentions_html_url_tracking(self):
        """Default comment should require html_url tracking metadata."""
        comment = build_default_comment()
        self.assertIn("include html_url", comment)

    def test_default_comment_mentions_fixed_and_considered_tracking(self):
        """Default comment should require fixed/considered URL bucketing."""
        comment = build_default_comment()
        self.assertIn("FIXED vs CONSIDERED", comment)
        self.assertIn("[codex-api-automation-commit]", comment)

    def test_matrix_commit_marker_strings_are_detected(self):
        """Long-marker matrix values should still match the automation detector."""
        commit_shas = ["123423432432432", "234329473243234334"]

        for sha in commit_shas:
            marker = build_automation_commit_marker("codex-api")
            commit_message = f"{marker} codex: test workflow update\\n\\n{sha}"
            self.assertTrue(is_automation_commit_message(commit_message))


if __name__ == "__main__":
    unittest.main()
