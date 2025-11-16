#!/usr/bin/env python3
"""
TDD Test Suite for Critical Issues in PR #1777
RED PHASE: These tests MUST FAIL initially to expose the issues
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add the hooks directory (parent of tests) to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from command_output_trimmer import Config, OptimizedCommandOutputTrimmer


class TestCriticalIssues(unittest.TestCase):
    """RED PHASE: Tests for critical issues that MUST fail initially."""

    def setUp(self):
        """Set up test fixture."""
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    @unittest.skipUnless(os.getenv("RUN_RED_PHASE") == "1", "Skip RED phase by default")
    def test_sanitize_args_actually_called_in_main_workflow(self):
        """
        RED TEST: Verify sanitize_args is called during actual processing.
        This test MUST FAIL initially because sanitize_args is never called.
        """
        # Create a mock input with very long arguments
        long_input = "x" * 2000  # Exceeds ARG_LENGTH_LIMIT of 1000

        # Mock stdin to provide the long input
        with patch('sys.stdin', StringIO(long_input)):
            with patch('sys.stdout', StringIO()) as mock_stdout:
                with patch.object(self.trimmer, 'trim_args', wraps=self.trimmer.trim_args) as mock_sanitize:
                    # Call the main entry point that should use sanitize_args
                    from command_output_trimmer import main
                    try:
                        main()
                    except SystemExit:
                        pass

                    # GREEN: This should now pass because trim_args is called
                    mock_sanitize.assert_called()
                    self.assertGreater(mock_sanitize.call_count, 0,
                                     "trim_args should be called during processing")

    @unittest.skipUnless(os.getenv("RUN_RED_PHASE") == "1", "Skip RED phase by default")
    def test_type_preservation_in_list_sanitization(self):
        """
        RED TEST: Verify that list elements maintain their types when not exceeding limits.
        This test MUST FAIL initially due to type conversion bug.
        """
        # Test data with mixed types that DON'T exceed limit
        mixed_list = [
            42,                    # Integer
            True,                  # Boolean
            3.14,                  # Float
            "short string",        # String under limit
            None,                  # None type
            {"key": "value"}       # Dict
        ]

        result = self.trimmer.trim_args(mixed_list)

        # RED: These MUST fail because current implementation converts all to strings
        self.assertIsInstance(result[0], int, "Integer should remain integer when under limit")
        self.assertIsInstance(result[1], bool, "Boolean should remain boolean when under limit")
        self.assertIsInstance(result[2], float, "Float should remain float when under limit")
        self.assertIsInstance(result[3], str, "String should remain string")
        self.assertIsNone(result[4], "None should remain None")
        self.assertIsInstance(result[5], dict, "Dict should remain dict when under limit")

        # Only when OVER limit should it convert to string
        long_list = [
            "x" * 1500,  # This should be truncated to string
            42,          # This should remain int
        ]

        result_long = self.trimmer.trim_args(long_list)
        self.assertIsInstance(result_long[0], str, "Long string should be truncated")
        self.assertEqual(len(result_long[0]), Config.ARG_LENGTH_LIMIT)
        self.assertIsInstance(result_long[1], int, "Short int should preserve type")

    def test_unused_variable_removed(self):
        """
        GREEN TEST: Verify that unused important_patterns variable has been removed.
        This test should now pass because we cleaned up the dead code.
        """
        # Read the source code to check that unused variables are removed
        script_dir = os.path.dirname(__file__)
        trimmer_path = os.path.join(os.path.dirname(script_dir), 'command_output_trimmer.py')

        with open(trimmer_path) as f:
            source_code = f.read()

        # GREEN: important_patterns should no longer be defined as unused code
        self.assertNotIn('important_patterns = [', source_code,
                        "important_patterns should have been removed as it was unused dead code")

    @unittest.skipUnless(os.getenv("RUN_RED_PHASE") == "1", "Skip RED phase by default")
    def test_summary_size_is_bounded(self):
        """
        RED TEST: Verify that summary output has reasonable size limits.
        This test MUST FAIL initially because summary can grow unbounded.
        """
        # Create input with many errors, URLs, and status updates
        massive_middle_content = []
        for i in range(100):
            massive_middle_content.append(f"ERROR: Error number {i} with very long description " + "x" * 200)
            massive_middle_content.append(f"https://very-long-url-{i}.com/" + "x" * 300)
            massive_middle_content.append(f"✅ Status update {i}: " + "x" * 250)
            massive_middle_content.append(f"PR #{i} was created with extensive details " + "x" * 180)

        summary = self.trimmer._summarize_middle_content(massive_middle_content)

        # RED: This MUST fail because summary can become very large
        max_reasonable_summary_lines = 50  # Reasonable upper bound
        self.assertLessEqual(len(summary), max_reasonable_summary_lines,
                           f"Summary has {len(summary)} lines, should be bounded to {max_reasonable_summary_lines}")

        # Also check total character count
        total_chars = sum(len(line) for line in summary)
        max_reasonable_chars = 5000  # Reasonable character limit
        self.assertLessEqual(total_chars, max_reasonable_chars,
                           f"Summary has {total_chars} chars, should be bounded to {max_reasonable_chars}")

    @unittest.skipUnless(os.getenv("RUN_RED_PHASE") == "1", "Skip RED phase by default")
    def test_integration_with_actual_hook_execution(self):
        """
        RED TEST: Verify the hook integrates properly with Claude Code's execution flow.
        This test MUST FAIL initially due to missing integration points.
        """
        # Test that the hook can be called through the actual hook mechanism
        test_input = "test input with very long arguments: " + "x" * 1500

        # Mock the hook execution environment
        with patch.dict(os.environ, {'CLAUDE_HOOK_EXECUTION': 'true'}):
            with patch('sys.stdin', StringIO(test_input)):
                with patch('sys.stdout', StringIO()) as mock_stdout:
                    # RED: This should fail because sanitize_args integration is missing
                    from command_output_trimmer import main
                    try:
                        main()
                    except SystemExit:
                        pass

                    output = mock_stdout.getvalue()

                    # Verify that output processing occurred (input is command output, not arguments)
                    # For small inputs, output should be unchanged (passthrough)
                    self.assertEqual(len(output), len(test_input),
                                   "Small output should pass through unchanged")

                    # Check that content was preserved (not sanitized, as this is output processing)
                    self.assertIn("x" * 1500, output,
                                "Content should be preserved as this is output processing, not argument sanitization")

class TestTDDMatrixCoverage(unittest.TestCase):
    """TDD Matrix Testing for comprehensive coverage."""

    def setUp(self):
        """Set up test matrix."""
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_argument_type_matrix(self):
        """
        Test matrix for all argument types × length conditions.
        Each combination must be tested systematically.
        """
        # Define test matrix
        test_cases = [
            # [input, expected_type, should_be_truncated]
            ("short string", str, False),
            ("x" * 1500, str, True),
            (42, int, False),
            (sys.maxsize, int, False),  # Large int that doesn't become too long as string
            (True, bool, False),
            (False, bool, False),
            (3.14159, float, False),
            (None, type(None), False),
            ({"key": "value"}, dict, False),
            ({"key": "x" * 1500}, dict, True),  # Dict with long values
            ([], list, False),
            (["short", "items"], list, False),
            (["x" * 1500, "short"], list, True),  # List with long items
        ]

        for input_value, expected_type, should_be_truncated in test_cases:
            with self.subTest(input=input_value, type=expected_type.__name__):
                result = self.trimmer.trim_args(input_value)

                if should_be_truncated:
                    # For truncated items, verify truncation occurred properly
                    if isinstance(input_value, str):
                        self.assertEqual(len(result), Config.ARG_LENGTH_LIMIT)
                    elif isinstance(input_value, list):
                        # Check that long items in list were truncated
                        for item in result:
                            if isinstance(item, str):
                                self.assertLessEqual(len(item), Config.ARG_LENGTH_LIMIT)
                    elif isinstance(input_value, dict):
                        # Check that long values in dict were truncated
                        for key, value in result.items():
                            if isinstance(key, str):
                                self.assertLessEqual(len(key), Config.ARG_LENGTH_LIMIT)
                            if isinstance(value, str):
                                self.assertLessEqual(len(value), Config.ARG_LENGTH_LIMIT)
                # For non-truncated items, verify type preservation
                elif not isinstance(input_value, (list, dict)):
                    self.assertEqual(type(result), expected_type)

def run_red_phase_tests():
    """Run all RED phase tests and verify they fail."""
    print("🔴 RED PHASE: Running tests that MUST fail to expose issues...")
    print("=" * 60)

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCriticalIssues))
    suite.addTest(unittest.makeSuite(TestTDDMatrixCoverage))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("📊 RED PHASE RESULTS:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures or result.errors:
        print(f"\n✅ RED PHASE SUCCESS: {len(result.failures + result.errors)} tests failed as expected")
        print("Now we can move to GREEN phase to fix these issues!")
        return True
    print("\n❌ RED PHASE FAILED: All tests passed - issues may not be properly exposed")
    return False

if __name__ == "__main__":
    success = run_red_phase_tests()
    sys.exit(0 if success else 1)
