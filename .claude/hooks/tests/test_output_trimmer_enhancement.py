#!/usr/bin/env python3
"""
Test suite for the enhanced command_output_trimmer.py
Tests the new argument sanitization functionality.
"""

import sys
import os
import unittest
from unittest.mock import patch, mock_open

# Add the hooks directory (parent of tests) to the path so we can import the trimmer
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from command_output_trimmer import OptimizedCommandOutputTrimmer, Config

class TestArgumentSanitization(unittest.TestCase):
    """Test the new argument sanitization functionality."""

    def setUp(self):
        """Set up test fixture."""
        # Reset singleton for clean testing
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_sanitize_string_under_limit(self):
        """Test string argument under length limit."""
        short_string = "short argument"
        result = self.trimmer.trim_args(short_string)
        self.assertEqual(result, short_string)

    def test_sanitize_string_over_limit(self):
        """Test string argument over length limit."""
        long_string = "x" * (Config.ARG_LENGTH_LIMIT + 100)
        result = self.trimmer.trim_args(long_string)
        self.assertEqual(len(result), Config.ARG_LENGTH_LIMIT)
        self.assertEqual(result, "x" * Config.ARG_LENGTH_LIMIT)

    def test_sanitize_list_under_limit(self):
        """Test list with all elements under length limit."""
        test_list = ["short", "arguments", "here"]
        result = self.trimmer.trim_args(test_list)
        self.assertEqual(result, test_list)

    def test_sanitize_list_over_limit(self):
        """Test list with some elements over length limit."""
        long_arg = "x" * (Config.ARG_LENGTH_LIMIT + 50)
        test_list = ["short", long_arg, "normal"]
        result = self.trimmer.trim_args(test_list)
        expected = ["short", "x" * Config.ARG_LENGTH_LIMIT, "normal"]
        self.assertEqual(result, expected)

    def test_sanitize_dict_under_limit(self):
        """Test dictionary with all values under length limit."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = self.trimmer.trim_args(test_dict)
        self.assertEqual(result, test_dict)

    def test_sanitize_dict_over_limit(self):
        """Test dictionary with keys/values over length limit."""
        long_key = "k" * (Config.ARG_LENGTH_LIMIT + 10)
        long_value = "v" * (Config.ARG_LENGTH_LIMIT + 20)
        test_dict = {"short_key": "short_value", long_key: long_value}
        result = self.trimmer.trim_args(test_dict)

        expected = {
            "short_key": "short_value",
            "k" * Config.ARG_LENGTH_LIMIT: "v" * Config.ARG_LENGTH_LIMIT
        }
        self.assertEqual(result, expected)

    def test_sanitize_integer(self):
        """Test non-string argument (integer)."""
        test_int = 12345
        result = self.trimmer.trim_args(test_int)
        self.assertEqual(result, test_int)

    def test_sanitize_large_integer(self):
        """Test very large integer that becomes long when converted to string."""
        # Create a number that when converted to string exceeds the limit
        large_int = int("9" * (Config.ARG_LENGTH_LIMIT + 50))
        result = self.trimmer.trim_args(large_int)
        # Should be trimmed to string representation limit
        expected = "9" * Config.ARG_LENGTH_LIMIT
        self.assertEqual(result, expected)

    def test_sanitize_mixed_list(self):
        """Test list with mixed data types."""
        mixed_list = [
            "short_string",
            "x" * (Config.ARG_LENGTH_LIMIT + 10),
            123,
            {"key": "value"}
        ]
        result = self.trimmer.trim_args(mixed_list)
        expected = [
            "short_string",
            "x" * Config.ARG_LENGTH_LIMIT,
            123,  # Type preserved when under limit
            {"key": "value"}  # Type preserved when under limit
        ]
        self.assertEqual(result, expected)

    def test_sanitize_empty_list(self):
        """Test empty list."""
        empty_list = []
        result = self.trimmer.trim_args(empty_list)
        self.assertEqual(result, empty_list)

    def test_sanitize_empty_string(self):
        """Test empty string."""
        empty_string = ""
        result = self.trimmer.trim_args(empty_string)
        self.assertEqual(result, empty_string)

    def test_sanitize_none(self):
        """Test None value."""
        result = self.trimmer.trim_args(None)
        self.assertEqual(result, None)

class TestOutputTrimmingIntegration(unittest.TestCase):
    """Test that existing output trimming functionality still works."""

    def setUp(self):
        """Set up test fixture."""
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_small_output_passthrough(self):
        """Test that small outputs pass through unchanged."""
        small_output = "Small output\nJust a few lines\nNothing to trim"
        result = self.trimmer.process_output(small_output)
        self.assertEqual(result, small_output)

    def test_large_output_trimming(self):
        """Test that large outputs get trimmed."""
        # Create output with many lines
        lines = [f"Line {i}: Some content here" for i in range(200)]
        large_output = "\n".join(lines)

        result = self.trimmer.process_output(large_output)
        result_lines = result.split('\n')

        # Should be significantly fewer lines
        self.assertLess(len(result_lines), len(lines))
        # Should contain summary indicator (new behavior)
        self.assertTrue(any("SUMMARY" in line for line in result_lines))

    def test_bypass_markers(self):
        """Test that bypass markers prevent trimming."""
        large_output_with_marker = "[claude:no-trim]\n" + "\n".join([f"Line {i}" for i in range(200)])
        result = self.trimmer.process_output(large_output_with_marker)

        # Should not be trimmed due to marker
        self.assertEqual(result, large_output_with_marker)

    def test_intelligent_summarization(self):
        """Test that middle content gets intelligently summarized."""
        # Create output with errors, URLs, and status updates
        lines = [
            "Starting process...",
            "Loading configuration...",
            "ERROR: Something failed",
            "Warning: Check this",
            "Processing item 1",
            "Processing item 2",
            "✅ Step completed successfully",
            "Visit https://github.com/example/repo",
            "❌ Another step failed",
            "PR #123 was merged",
            "Final result: completed"
        ]

        # Add enough lines to trigger trimming
        test_lines = lines[:2]  # First 2
        test_lines.extend([f"Middle line {i}" for i in range(100)])  # Many middle lines
        test_lines.extend(["ERROR: Critical issue", "https://example.com"])  # More middle content
        test_lines.extend([f"More middle {i}" for i in range(100)])  # Even more middle
        test_lines.extend(lines[-2:])  # Last 2

        large_output = "\n".join(test_lines)
        result = self.trimmer.process_output(large_output)
        result_lines = result.split('\n')

        # Should contain summary
        self.assertTrue(any("SUMMARY" in line for line in result_lines))
        # Should contain extracted errors
        self.assertTrue(any("ERROR: Critical issue" in line for line in result_lines))
        # Should contain extracted URLs
        self.assertTrue(any("https://example.com" in line for line in result_lines))

def run_comprehensive_tests():
    """Run all tests and provide detailed results."""
    print("🧪 Running Enhanced Output Trimmer Tests...")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTest(unittest.makeSuite(TestArgumentSanitization))
    suite.addTest(unittest.makeSuite(TestOutputTrimmingIntegration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")

    if result.errors:
        print(f"\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")

    if not result.failures and not result.errors:
        print(f"\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ Some tests failed. See details above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
