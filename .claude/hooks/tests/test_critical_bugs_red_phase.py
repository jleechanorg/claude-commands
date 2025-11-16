#!/usr/bin/env python3
"""
RED PHASE: Tests that expose critical bugs in command output trimmer.
These tests should FAIL initially, then pass after fixes are applied.

Following Red-Green-Refactor methodology:
1. RED: Write failing tests that expose the bugs
2. GREEN: Minimal fixes to make tests pass
3. REFACTOR: Clean up implementation while maintaining tests
"""

import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add the hooks directory (parent of tests) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from command_output_trimmer import Config, OptimizedCommandOutputTrimmer


class TestDictionaryKeyCollisionBug(unittest.TestCase):
    """Test cases that expose the dictionary key collision bug."""

    def setUp(self):
        # Reset singleton for clean testing
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_collision_key_exceeds_length_limit(self):
        """
        BUG 1: Generated collision keys can exceed ARG_LENGTH_LIMIT.

        The current code generates keys like "base_key__dup1" without checking
        if the final key exceeds the length limit, bypassing DoS protection.
        """
        # Create a scenario where collision resolution creates oversized keys
        # Use exactly the limit so that adding "__dup1" exceeds it
        long_base = "x" * Config.ARG_LENGTH_LIMIT

        test_dict = {
            long_base + "extra": "value1",  # This will be trimmed to long_base
            long_base + "more": "value2",   # This will also be trimmed to long_base, causing collision
        }

        result = self.trimmer.trim_args(test_dict)

        # BUG: The collision resolution creates keys like "long_base__dup1"
        # which WILL exceed ARG_LENGTH_LIMIT because long_base is already at the limit
        for key in result.keys():
            key_length = len(str(key))
            if key_length > Config.ARG_LENGTH_LIMIT:
                # This is the bug - collision keys exceed the limit
                self.fail(f"BUG DETECTED: Generated key '{key}' has length {key_length} "
                         f"which exceeds ARG_LENGTH_LIMIT of {Config.ARG_LENGTH_LIMIT}")

    def test_collision_overwrites_existing_key(self):
        """
        BUG 2: Collision handling can silently overwrite existing original keys.

        If an untrimmed key matches a collision-resolved key name, data loss occurs.
        """
        # Create a scenario where collision resolution conflicts with existing key
        base_key = "test_key"
        collision_key = f"{base_key}__dup1"

        test_dict = {
            base_key + "x" * 1000: "original_long_value",  # Will be trimmed to base_key
            collision_key: "existing_value",  # This existing key could be overwritten
        }

        result = self.trimmer.trim_args(test_dict)

        # BUG: The collision resolution might overwrite the existing collision_key
        # Both values should be preserved with different keys
        self.assertEqual(len(result), 2, "Both dictionary entries should be preserved")
        self.assertIn("existing_value", result.values(), "Original collision_key value should be preserved")
        self.assertIn("original_long_value", result.values(), "Trimmed value should be preserved")


class TestArgumentHandlingBug(unittest.TestCase):
    """Test cases that expose the argument handling bug in main()."""

    def setUp(self):
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_main_applies_trim_args_to_sys_argv_incorrectly(self):
        """
        BUG 3: main() incorrectly applies trim_args to sys.argv.

        trim_args is designed for API function arguments, not command-line arguments.
        It can return non-string types which cause TypeError when assigned to sys.argv.
        """
        # Mock sys.argv with mixed types that trim_args might return
        original_argv = sys.argv.copy()

        try:
            # Simulate what happens when trim_args returns non-strings
            with patch('sys.argv', ['script.py', '123', 'long_arg' + 'x' * 1000]):
                with patch('sys.stdin', StringIO("test input")):
                    with patch('sys.stdout', StringIO()):
                        # Import and use the main function
                        from command_output_trimmer import main

                        # BUG: This should not modify sys.argv or should handle it properly
                        # The current code can cause TypeError if trim_args returns non-strings
                        try:
                            main()
                        except TypeError as e:
                            if "list assignment" in str(e) or "can only assign an iterable" in str(e):
                                self.fail(f"main() incorrectly handles sys.argv assignment: {e}")
        finally:
            sys.argv = original_argv

    def test_unicode_input_size_vs_byte_limit_mismatch(self):
        """
        BUG 4: MAX_INPUT_SIZE is byte limit but sys.stdin.read() processes characters.

        This allows larger Unicode input than intended, weakening DoS protection.
        """
        # Create Unicode input that is small in characters but large in bytes
        unicode_char = "🚀"  # 4 bytes in UTF-8
        char_count = Config.MAX_INPUT_SIZE // 2  # Half the limit in characters
        unicode_input = unicode_char * char_count

        # This input is small in character count but large in byte count
        byte_size = len(unicode_input.encode('utf-8'))
        char_size = len(unicode_input)

        self.assertGreater(byte_size, Config.MAX_INPUT_SIZE,
                          "Unicode input should exceed byte limit")
        self.assertLess(char_size, Config.MAX_INPUT_SIZE,
                       "Unicode input should be under character limit")

        # BUG: The current code allows this oversized input through
        with patch('sys.stdin', StringIO(unicode_input)):
            with patch('sys.stdout', StringIO()) as mock_stdout:
                with patch('sys.stderr', StringIO()) as mock_stderr:
                    from command_output_trimmer import main

                    main()

                    # The warning message should reflect the actual issue
                    stderr_output = mock_stderr.getvalue()
                    if "characters" in stderr_output:
                        # BUG: Warning says "characters" but limit is actually bytes
                        self.fail("Warning message incorrectly refers to characters instead of bytes")


class TestTypeValidationBug(unittest.TestCase):
    """Test cases that expose lack of type validation."""

    def setUp(self):
        OptimizedCommandOutputTrimmer._reset_singleton_for_testing()
        self.trimmer = OptimizedCommandOutputTrimmer()

    def test_missing_isinstance_validation(self):
        """
        BUG 5: Missing isinstance() validation allows unsafe operations.

        Methods should validate input types before processing to prevent errors.
        """
        # Test with unexpected input types
        test_cases = [
            None,  # Should be handled gracefully
            42,    # Integer instead of expected types
            3.14,  # Float instead of expected types
        ]

        for invalid_input in test_cases:
            with self.subTest(input_type=type(invalid_input).__name__):
                # BUG: Current code may not handle these gracefully
                try:
                    result = self.trimmer.trim_args(invalid_input)
                    # If it doesn't crash, it should at least return the input unchanged
                    # or handle it appropriately
                except (AttributeError, TypeError) as e:
                    self.fail(f"trim_args should handle {type(invalid_input).__name__} gracefully, got: {e}")


if __name__ == '__main__':
    print("🔴 RED PHASE: Running tests that should FAIL initially...")
    print("These tests expose the critical bugs that need to be fixed.")
    print()

    unittest.main(verbosity=2)
