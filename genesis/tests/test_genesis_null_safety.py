#!/usr/bin/env python3
"""Genesis null safety regression tests."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from genesis import genesis
from genesis.common_cli import GenesisUsageError


class TestGenesisNullSafety(unittest.TestCase):
    """Test suite for Genesis null safety - all functions should handle goal_dir=None gracefully"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {
            "learnings": "Test learning content",
            "iteration_num": 1,
            "consensus_response": "Test consensus",
            "iteration_data": {"iteration": 1, "status": "test"}
        }

    def test_update_plan_document_with_none_goal_dir(self):
        """Test update_plan_document handles goal_dir=None without crashing"""
        try:
            result = genesis.update_plan_document(
                goal_dir=None,
                learnings=self.test_data["learnings"],
                iteration_num=self.test_data["iteration_num"],
                use_codex=False
            )
            # Should return empty string when goal_dir is None
            self.assertEqual(result, "")
        except TypeError as e:
            self.fail(f"update_plan_document crashed with TypeError: {e}")

    def test_update_genesis_instructions_with_none_goal_dir(self):
        """Test update_genesis_instructions handles goal_dir=None without crashing"""
        try:
            result = genesis.update_genesis_instructions(
                goal_dir=None,
                learnings=self.test_data["learnings"],
                use_codex=False,
                iteration_num=self.test_data["iteration_num"]
            )
            # Should return None (no crash) when goal_dir is None
            self.assertIsNone(result)
        except TypeError as e:
            self.fail(f"update_genesis_instructions crashed with TypeError: {e}")

    def test_update_progress_file_with_none_goal_dir(self):
        """Test update_progress_file handles goal_dir=None without crashing"""
        try:
            result = genesis.update_progress_file(
                goal_dir=None,
                iteration_data=self.test_data["iteration_data"]
            )
            # Should return None (no crash) when goal_dir is None
            self.assertIsNone(result)
        except TypeError as e:
            self.fail(f"update_progress_file crashed with TypeError: {e}")

    def test_append_genesis_learning_with_none_goal_dir(self):
        """Test append_genesis_learning handles goal_dir=None without crashing"""
        try:
            result = genesis.append_genesis_learning(
                goal_dir=None,
                iteration_num=self.test_data["iteration_num"],
                learning_note="Test learning note"
            )
            # Should return None (no crash) when goal_dir is None
            self.assertIsNone(result)
        except TypeError as e:
            self.fail(f"append_genesis_learning crashed with TypeError: {e}")

    def test_load_goal_from_directory_with_none_goal_dir(self):
        """Test load_goal_from_directory handles goal_dir=None without crashing"""
        try:
            result_goal, result_criteria = genesis.load_goal_from_directory(goal_dir=None)
            # Should return None, None when goal_dir is None
            self.assertIsNone(result_goal)
            self.assertIsNone(result_criteria)
        except TypeError as e:
            self.fail(f"load_goal_from_directory crashed with TypeError: {e}")

    def test_all_path_operations_with_none_goal_dir(self):
        """Comprehensive test of all Path(goal_dir) operations with None"""
        null_safety_functions = [
            (genesis.update_plan_document, {"learnings": "test", "iteration_num": 1}),
            (genesis.update_genesis_instructions, {"learnings": "test", "iteration_num": 1}),
            (genesis.update_progress_file, {"iteration_data": {"test": "data"}}),
            (genesis.append_genesis_learning, {"iteration_num": 1, "learning_note": "test"}),
            (genesis.load_goal_from_directory, {})
        ]

        for func, kwargs in null_safety_functions:
            with self.subTest(function=func.__name__):
                try:
                    # All functions should handle goal_dir=None gracefully
                    result = func(goal_dir=None, **kwargs)
                    # Should not raise TypeError
                    self.assertTrue(True, f"{func.__name__} handled None gracefully")
                except TypeError as e:
                    self.fail(f"{func.__name__} failed null safety test: {e}")


class TestGenesisRefineModeFallback(unittest.TestCase):
    """Integration tests for --refine mode fallback scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.test_goal = "Create a test application"
        self.test_iterations = 5

    @patch('genesis.generate_goal_files_fast')
    def test_refine_mode_goal_generation_failure(self, mock_goal_gen):
        """Test --refine mode when goal directory generation fails"""
        # Mock goal generation failure
        mock_goal_gen.return_value = False

        # Test that Genesis handles goal generation failure gracefully
        try:
            # This would normally be called from main() in --refine mode
            # We're testing the specific path where goal_dir becomes None
            goal_dir = None  # Simulates failed goal generation

            # These functions should all handle None gracefully
            genesis.update_plan_document(goal_dir, "test", 1)
            genesis.update_genesis_instructions(goal_dir, "test", iteration_num=1)
            genesis.update_progress_file(goal_dir, {"test": "data"})
            genesis.append_genesis_learning(goal_dir, 1, "test")

            # No TypeError should be raised
            self.assertTrue(True, "All functions handled fallback mode correctly")

        except TypeError as e:
            self.fail(f"Refine mode fallback failed with TypeError: {e}")

    @patch('genesis.execute_claude_command')
    def test_api_failure_fallback_path(self, mock_claude):
        """Test API failure scenarios that lead to goal_dir=None"""
        # Mock API failure that would cause goal directory creation to fail
        mock_claude.side_effect = Exception("API connection failed")

        # Test the code path where API failures cause goal_dir to be None
        try:
            # Simulate the scenario where goal generation fails due to API issues
            goal_dir = None  # This is what happens when generate_goal_files_fast fails

            # All Genesis functions should handle this gracefully
            functions_to_test = [
                lambda: genesis.update_plan_document(goal_dir, "test", 1),
                lambda: genesis.update_genesis_instructions(goal_dir, "test", iteration_num=1),
                lambda: genesis.update_progress_file(goal_dir, {"iteration": 1}),
                lambda: genesis.append_genesis_learning(goal_dir, 1, "test"),
                lambda: genesis.load_goal_from_directory(goal_dir)
            ]

            for test_func in functions_to_test:
                test_func()  # Should not raise TypeError

            self.assertTrue(True, "API failure fallback handled correctly")

        except TypeError as e:
            self.fail(f"API failure fallback test failed: {e}")

    def test_session_mode_fallback(self):
        """Test that session mode works when goal directory is unavailable"""
        # Simulate session mode where goal_dir is None
        goal_dir = None

        try:
            # Test key operations that should work in session mode
            result = genesis.update_plan_document(goal_dir, "session test", 1)
            self.assertEqual(result, "", "Should return empty string in session mode")

            # These should all return gracefully without crashing
            genesis.update_genesis_instructions(goal_dir, "session test", iteration_num=1)
            genesis.update_progress_file(goal_dir, {"session": "mode"})
            genesis.append_genesis_learning(goal_dir, 1, "session learning")

            goal_result, criteria_result = genesis.load_goal_from_directory(goal_dir)
            self.assertIsNone(goal_result, "Should return None for goal in session mode")
            self.assertIsNone(criteria_result, "Should return None for criteria in session mode")

        except TypeError as e:
            self.fail(f"Session mode fallback failed: {e}")


class TestGenesisEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_empty_string_goal_dir(self):
        """Test functions with empty string goal_dir"""
        # Empty string should not cause Path() to crash, but may cause other issues
        empty_goal_dir = ""

        # These functions should handle empty strings gracefully
        try:
            genesis.load_goal_from_directory(empty_goal_dir)
            # May return None,None or handle empty path - just shouldn't crash
        except TypeError as e:
            if "NoneType" in str(e):
                self.fail("Empty string treated as None - indicates missing null check")

    def test_whitespace_goal_dir(self):
        """Test functions with whitespace-only goal_dir"""
        whitespace_goal_dir = "   "

        try:
            genesis.load_goal_from_directory(whitespace_goal_dir)
            # Should handle whitespace gracefully
        except TypeError as e:
            if "NoneType" in str(e):
                self.fail("Whitespace string treated as None - indicates missing null check")

    def test_invalid_path_characters(self):
        """Test functions with invalid path characters"""
        invalid_chars = ["<invalid>", "|pipe|", "*asterisk*"]

        for invalid_char in invalid_chars:
            with self.subTest(invalid_path=invalid_char):
                try:
                    # Should not crash with TypeError about NoneType
                    genesis.load_goal_from_directory(invalid_char)
                except TypeError as e:
                    if "NoneType" in str(e):
                        self.fail(f"Invalid path '{invalid_char}' treated as None")
                except (OSError, ValueError):
                    # These exceptions are acceptable for invalid paths
                    pass


class TestGenesisModelPreference(unittest.TestCase):
    """Unit tests for Genesis model selection helpers."""

    def setUp(self):
        genesis.GENESIS_USE_CODEX = None
        self.addCleanup(lambda: setattr(genesis, "GENESIS_USE_CODEX", None))

    def test_is_codex_enabled_defaults_to_true(self):
        """Without explicit flags Genesis should default to Codex."""

        result = genesis.is_codex_enabled(["genesis.py"])

        self.assertTrue(result)
        self.assertTrue(genesis.GENESIS_USE_CODEX)

    def test_is_codex_enabled_prefers_claude_flag(self):
        """The --claude flag should flip the cached preference."""

        result = genesis.is_codex_enabled(["genesis.py", "--claude"])

        self.assertFalse(result)
        self.assertFalse(genesis.GENESIS_USE_CODEX)

        # Subsequent invocations should reuse the cached preference even if argv changes.
        self.assertFalse(genesis.is_codex_enabled(["genesis.py", "--codex"]))

    def test_is_codex_enabled_rejects_conflicting_flags(self):
        """Conflicting flags should raise a usage error to match CLI validation."""

        with self.assertRaisesRegex(GenesisUsageError, "Cannot specify both --codex and --claude"):
            genesis.is_codex_enabled(["genesis.py", "--codex", "--claude"])


class TestWorkflowStateTokenTracking(unittest.TestCase):
    """Focused coverage for WorkflowState token accounting."""

    def test_add_token_usage_enforces_iteration_limit(self):
        """Exceeding the per-iteration token budget should return False."""

        state = genesis.WorkflowState(max_tokens_per_iteration=100)

        allowed = state.add_token_usage(60, iteration=3)
        self.assertTrue(allowed)
        self.assertEqual(state.total_tokens_used, 60)
        self.assertEqual(state.iteration_tokens[3], 60)

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            blocked = state.add_token_usage(50, iteration=3)
        self.assertFalse(blocked)
        self.assertEqual(state.total_tokens_used, 110)
        self.assertEqual(state.iteration_tokens[3], 110)
        self.assertIn("TOKEN BURN PREVENTION", stdout.getvalue())


class TestSecureFileHandler(unittest.TestCase):
    """Regression tests for secure file IO helpers."""

    def test_write_and_read_with_lock_round_trip(self):
        """Writing and reading with locks should preserve content."""

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "session", "state.json")
            payload = "example contents"

            genesis.SecureFileHandler.write_with_lock(filepath, payload)
            contents = genesis.SecureFileHandler.read_with_lock(filepath)

            self.assertEqual(contents, payload)

    def test_read_with_lock_missing_file(self):
        """Missing files should safely return an empty string."""

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "missing.txt")

            contents = genesis.SecureFileHandler.read_with_lock(filepath)

            self.assertEqual(contents, "")


if __name__ == '__main__':
    # Run the null safety test suite
    unittest.main(verbosity=2)
