#!/usr/bin/env python3
"""
Tests for pr_utils.py shared functionality
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pr_utils


class TestPRUtils(unittest.TestCase):
    def test_parse_scratchpad_summary(self):
        """Test parsing scratchpad content"""
        content = """# Implementation: Test Feature

**Goal**: Add test functionality  
**Status**: In Progress

## Summary

This is a test summary section.

## Implementation

Implementation details here.

## Testing

Test requirements here.
"""

        result = pr_utils.parse_scratchpad_summary(content)

        self.assertEqual(result["goal"], "Add test functionality")
        self.assertIn("test summary section", result["summary"])
        self.assertIn("Implementation details", result["implementation"])
        self.assertIn("Test requirements", result["testing"])

    def test_parse_scratchpad_summary_empty(self):
        """Test parsing empty scratchpad"""
        result = pr_utils.parse_scratchpad_summary("")

        self.assertEqual(result["goal"], "")
        self.assertEqual(result["summary"], "")
        self.assertEqual(result["implementation"], "")
        self.assertEqual(result["testing"], "")

    def test_format_test_results_success(self):
        """Test formatting successful test results"""
        output = "Running tests...\n147 tests passed"
        result = pr_utils.format_test_results(True, output)

        self.assertIn("✅", result)
        self.assertIn("147", result)
        self.assertIn("passing", result)

    def test_format_test_results_failure(self):
        """Test formatting failed test results"""
        result = pr_utils.format_test_results(False, "Some tests failed")

        self.assertIn("❌", result)
        self.assertIn("failing", result)

    @patch("subprocess.run")
    def test_get_current_branch(self, mock_run):
        """Test getting current branch"""
        mock_run.return_value = MagicMock(stdout="feature/test-branch\n")

        result = pr_utils.get_current_branch()

        self.assertEqual(result, "feature/test-branch")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_pr_exists_for_branch(self, mock_run):
        """Test checking if PR exists"""
        mock_run.return_value = MagicMock(
            stdout='[{"number": 123, "url": "https://github.com/test/pr/123", "state": "open", "title": "Test PR"}]'
        )

        result = pr_utils.check_pr_exists_for_branch("test-branch")

        self.assertIsNotNone(result)
        self.assertEqual(result["number"], 123)
        self.assertEqual(result["state"], "open")

    def test_generate_pr_description_basic(self):
        """Test basic PR description generation"""
        result = pr_utils.generate_pr_description(
            title="Test PR",
            branch="test-branch",
            test_success=True,
            test_output="All tests pass",
            is_handoff=False,
        )

        self.assertIn("## Summary", result)
        self.assertIn("test-branch", result)
        self.assertIn("✅", result)
        self.assertIn("🤖 Generated with [Claude Code]", result)

    def test_generate_pr_description_handoff(self):
        """Test handoff PR description generation"""
        result = pr_utils.generate_pr_description(
            title="Handoff Task",
            branch="handoff-test",
            test_success=False,
            test_output="",
            is_handoff=True,
        )

        self.assertIn("Ready for implementation handoff", result)
        self.assertIn("🟡", result)
        self.assertIn("scratchpad_handoff_", result)


if __name__ == "__main__":
    unittest.main()
