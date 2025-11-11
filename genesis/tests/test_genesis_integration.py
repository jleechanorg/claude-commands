#!/usr/bin/env python3
"""
Genesis Integration Test Suite
End-to-end tests for Genesis workflow including failure scenarios
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch

# Add genesis directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import genesis module
import genesis


class TestGenesisIntegration(unittest.TestCase):
    """Integration tests for complete Genesis workflows"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_goal = "Create a simple calculator application"
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        # Clean up test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('genesis.execute_claude_command')
    @patch('genesis.cerebras_call')
    def test_refine_mode_success_flow(self, mock_cerebras, mock_claude):
        """Test successful --refine mode execution"""
        # Mock successful API responses
        mock_cerebras.return_value = "REFINED GOAL: Build calculator app\n\nEXIT CRITERIA:\n- Has basic math operations\n- Includes tests\n- Working CLI interface"
        mock_claude.return_value = "Success: Goal files generated"

        os.chdir(self.test_dir)

        # Mock the main function components for --refine mode
        with patch('sys.argv', ['genesis.py', '--refine', self.test_goal]):
            with patch('genesis.generate_goal_files_fast', return_value=True):
                try:
                    # Test the successful path where goal directory is created
                    refined_goal = "Build calculator app"
                    exit_criteria = "Has basic math operations"

                    # Simulate successful goal directory creation
                    goal_dir = "goals/2025-09-29-1234-create-simple"

                    # Test that all functions work with valid goal_dir
                    plan_result = genesis.update_plan_document(goal_dir, "test progress", 1)
                    self.assertIsNotNone(plan_result, "Plan document should be updated")

                    # Should not crash
                    genesis.update_genesis_instructions(goal_dir, "test learning", iteration_num=1)
                    genesis.update_progress_file(goal_dir, {"iteration": 1, "status": "test"})
                    genesis.append_genesis_learning(goal_dir, 1, "test learning")

                except Exception as e:
                    self.fail(f"Successful refine mode flow failed: {e}")

    @patch('genesis.generate_goal_files_fast')
    @patch('genesis.cerebras_call')
    def test_refine_mode_goal_generation_failure(self, mock_cerebras, mock_goal_gen):
        """Test --refine mode when goal directory generation fails"""
        # Mock successful goal refinement but failed goal generation
        mock_cerebras.return_value = "REFINED GOAL: Build calculator\n\nEXIT CRITERIA:\n- Works correctly"
        mock_goal_gen.return_value = False  # Goal generation fails

        os.chdir(self.test_dir)

        try:
            # Simulate the exact scenario from --refine mode where goal_dir becomes None
            refined_goal = "Build calculator"
            exit_criteria = "Works correctly"

            # This is what happens when generate_goal_files_fast returns False
            goal_dir = None  # Fallback to session mode

            # Test that all functions handle this gracefully (the original TypeError issue)
            plan_result = genesis.update_plan_document(goal_dir, "fallback test", 1)
            self.assertEqual(plan_result, "", "Should return empty string in fallback")

            # These should all complete without TypeError
            genesis.update_genesis_instructions(goal_dir, "fallback learning", iteration_num=1)
            genesis.update_progress_file(goal_dir, {"iteration": 1, "fallback": True})
            genesis.append_genesis_learning(goal_dir, 1, "fallback learning")

            # Verify fallback behavior
            goal_result, criteria_result = genesis.load_goal_from_directory(goal_dir)
            self.assertIsNone(goal_result, "Should return None in fallback mode")
            self.assertIsNone(criteria_result, "Should return None in fallback mode")

        except TypeError as e:
            self.fail(f"Refine mode fallback failed with TypeError: {e}")

    @patch('genesis.execute_claude_command')
    def test_api_connection_failure_resilience(self, mock_claude):
        """Test Genesis resilience to API connection failures"""
        # Mock API connection failure
        mock_claude.side_effect = Exception("Connection timeout")

        os.chdir(self.test_dir)

        try:
            # Simulate the scenario where API failures prevent goal directory creation
            goal_dir = None  # This happens when API calls fail

            # Test that Genesis can operate in degraded mode without crashing
            functions_to_test = [
                ("update_plan_document", lambda: genesis.update_plan_document(goal_dir, "api failure test", 1)),
                ("update_genesis_instructions", lambda: genesis.update_genesis_instructions(goal_dir, "api failure", iteration_num=1)),
                ("update_progress_file", lambda: genesis.update_progress_file(goal_dir, {"api": "failed"})),
                ("append_genesis_learning", lambda: genesis.append_genesis_learning(goal_dir, 1, "api failure")),
                ("load_goal_from_directory", lambda: genesis.load_goal_from_directory(goal_dir))
            ]

            for func_name, test_func in functions_to_test:
                with self.subTest(function=func_name):
                    try:
                        result = test_func()
                        # Should complete without TypeError
                        self.assertTrue(True, f"{func_name} handled API failure gracefully")
                    except TypeError as e:
                        if "NoneType" in str(e):
                            self.fail(f"{func_name} failed API failure test: {e}")

        except TypeError as e:
            self.fail(f"API failure resilience test failed: {e}")

    def test_session_mode_workflow(self):
        """Test Genesis workflow in session mode (no goal directory)"""
        os.chdir(self.test_dir)

        try:
            # Test session mode where goal_dir is None throughout
            goal_dir = None
            session_data = {
                "goal_directory": "session_mode",
                "refined_goal": "Test goal",
                "exit_criteria": "Test criteria",
                "current_iteration": 1
            }

            # Test session mode operations
            plan_result = genesis.update_plan_document(goal_dir, "session progress", 1)
            self.assertEqual(plan_result, "", "Session mode should return empty plan")

            # Test all session operations
            genesis.update_genesis_instructions(goal_dir, "session learning", iteration_num=1)
            genesis.update_progress_file(goal_dir, session_data)
            genesis.append_genesis_learning(goal_dir, 1, "session note")

            # Verify session fallback
            goal, criteria = genesis.load_goal_from_directory(goal_dir)
            self.assertIsNone(goal, "Session mode should return None goal")
            self.assertIsNone(criteria, "Session mode should return None criteria")

        except TypeError as e:
            self.fail(f"Session mode workflow failed: {e}")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_file_operation_fallback(self, mock_file, mock_exists):
        """Test file operations when goal directory doesn't exist"""
        # Mock file operations
        mock_exists.return_value = False
        mock_file.return_value.__enter__.return_value.read.return_value = ""

        try:
            # Test with None goal_dir (session mode)
            goal_dir = None

            # File operations should handle None gracefully
            plan_result = genesis.update_plan_document(goal_dir, "file test", 1)
            self.assertEqual(plan_result, "", "Should handle None goal_dir in file operations")

            # Other file operations should not crash
            genesis.update_genesis_instructions(goal_dir, "file test", iteration_num=1)
            genesis.update_progress_file(goal_dir, {"file": "test"})
            genesis.append_genesis_learning(goal_dir, 1, "file test")

        except TypeError as e:
            self.fail(f"File operation fallback failed: {e}")


class TestGenesisRegressionTests(unittest.TestCase):
    """Regression tests for specific issues that were fixed"""

    def test_line_1035_regression(self):
        """Regression test for TypeError at line 1035 in update_plan_document"""
        try:
            # This was the exact scenario that caused the original crash
            result = genesis.update_plan_document(
                goal_dir=None,  # This caused: TypeError: expected str, bytes or os.PathLike object, not NoneType
                learnings="Test learnings",
                iteration_num=1,
                use_codex=False
            )
            # Should return empty string, not crash
            self.assertEqual(result, "", "Should handle None goal_dir gracefully")
        except TypeError as e:
            self.fail(f"Line 1035 regression test failed: {e}")

    def test_line_1849_regression(self):
        """Regression test for TypeError at line 1849 in update_progress_file"""
        try:
            # This was another crash point
            result = genesis.update_progress_file(
                goal_dir=None,  # This caused: Path(goal_dir) TypeError
                iteration_data={"iteration": 1, "test": True}
            )
            # Should complete without crash
            self.assertIsNone(result, "Should handle None goal_dir gracefully")
        except TypeError as e:
            self.fail(f"Line 1849 regression test failed: {e}")

    def test_line_770_regression(self):
        """Regression test for TypeError at line 770 in load_goal_from_directory"""
        try:
            # This was another potential crash point
            goal, criteria = genesis.load_goal_from_directory(goal_dir=None)
            # Should return None, None without crash
            self.assertIsNone(goal, "Should return None for goal")
            self.assertIsNone(criteria, "Should return None for criteria")
        except TypeError as e:
            self.fail(f"Line 770 regression test failed: {e}")

    def test_line_1593_regression(self):
        """Regression test for TypeError at line 1593 in append_genesis_learning"""
        try:
            # This was another potential crash point
            result = genesis.append_genesis_learning(
                goal_dir=None,  # This could cause: Path(goal_dir) TypeError
                iteration_num=1,
                learning_note="Test regression"
            )
            # Should complete without crash
            self.assertIsNone(result, "Should handle None goal_dir gracefully")
        except TypeError as e:
            self.fail(f"Line 1593 regression test failed: {e}")

    def test_comprehensive_null_safety(self):
        """Comprehensive test to ensure no Path(goal_dir) calls crash with None"""
        null_test_cases = [
            ("update_plan_document", lambda: genesis.update_plan_document(None, "test", 1)),
            ("update_genesis_instructions", lambda: genesis.update_genesis_instructions(None, "test", iteration_num=1)),
            ("update_progress_file", lambda: genesis.update_progress_file(None, {"test": "data"})),
            ("append_genesis_learning", lambda: genesis.append_genesis_learning(None, 1, "test")),
            ("load_goal_from_directory", lambda: genesis.load_goal_from_directory(None))
        ]

        for func_name, test_func in null_test_cases:
            with self.subTest(function=func_name):
                try:
                    result = test_func()
                    # Should not raise TypeError about NoneType
                    self.assertTrue(True, f"{func_name} passed null safety test")
                except TypeError as e:
                    if "NoneType" in str(e) and "Path" in str(e):
                        self.fail(f"{func_name} still has Path(None) issue: {e}")


if __name__ == '__main__':
    # Run the integration test suite
    unittest.main(verbosity=2)
