#!/usr/bin/env python3
"""
TDD Test Suite for Enhanced Genesis Workflow
"""

import os
import sys
import tempfile
import unittest
import importlib
from itertools import cycle
from unittest.mock import MagicMock, patch

# Import the enhanced genesis functions
sys.path.insert(0, os.path.dirname(__file__))

# Dynamic import to comply with import validation rules
genesis = importlib.import_module('genesis')
cerebras_call = genesis.cerebras_call
enhanced_genesis_workflow = genesis.enhanced_genesis_workflow
execute_codex_command = genesis.execute_codex_command
execute_detailed_b1_to_b5_workflow = genesis.execute_detailed_b1_to_b5_workflow
smart_model_call = genesis.smart_model_call


class TestEnhancedGenesisWorkflow(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.goal = "Build user authentication system"
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.test_tmp_path = self.tmp_dir.name

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.tmp_dir.cleanup()

    @patch('genesis.cerebras_call')
    @patch('subprocess.check_output')
    @patch('os.path.basename')
    @patch('os.makedirs')
    def test_enhanced_genesis_workflow_stage_a1(self, mock_makedirs, mock_basename, mock_check_output, mock_cerebras):
        """Test Stage A1: Enhanced Goal Generation"""
        mock_basename.return_value = "test_repo"
        mock_check_output.return_value = b"test_branch"
        mock_makedirs.return_value = None
        mock_cerebras.return_value = "Enhanced goal specification with milestones"

        result = enhanced_genesis_workflow(self.goal, 1)
        expected_prompt = f"Enhanced Goal Generation: Take this goal and expand it into a comprehensive specification with clear milestones: {self.goal}"

        mock_cerebras.assert_called_once_with(expected_prompt)
        self.assertEqual(result, "Enhanced goal specification with milestones")

    @patch('genesis.cerebras_call')
    @patch('subprocess.check_output')
    @patch('os.path.basename')
    @patch('os.makedirs')
    def test_enhanced_genesis_workflow_stage_a2(self, mock_makedirs, mock_basename, mock_check_output, mock_cerebras):
        """Test Stage A2: Comprehensive TDD Implementation"""
        mock_basename.return_value = "test_repo"
        mock_check_output.return_value = b"test_branch"
        mock_makedirs.return_value = None
        mock_cerebras.return_value = "Complete test suite and implementation"

        previous_output = "Enhanced goal specification with milestones"
        result = enhanced_genesis_workflow(self.goal, 2, previous_output)
        expected_prompt = f"Comprehensive TDD Implementation: Create complete test suite and initial implementation for: {previous_output}"

        mock_cerebras.assert_called_once_with(expected_prompt)
        self.assertEqual(result, "Complete test suite and implementation")

    @patch('genesis.execute_detailed_b1_to_b5_workflow')
    @patch('subprocess.check_output')
    @patch('os.path.basename')
    @patch('os.makedirs')
    def test_enhanced_genesis_workflow_stage_b(self, mock_makedirs, mock_basename, mock_check_output, mock_b1_to_b5):
        """Test Stage B: Detailed workflow execution"""
        mock_basename.return_value = "test_repo"
        mock_check_output.return_value = b"test_branch"
        mock_makedirs.return_value = None
        mock_b1_to_b5.return_value = "B1-B5 workflow result"

        current_suite = "Test suite and implementation code"
        result = enhanced_genesis_workflow(self.goal, 3, current_suite)

        # Check that the detailed workflow was called
        mock_b1_to_b5.assert_called_once_with(current_suite, self.goal, "/tmp/test_repo/test_branch")
        self.assertEqual(result, "B1-B5 workflow result")


class TestDetailedB1ToB5Workflow(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.goal = "Build user authentication system"
        self.current_suite = "Test suite and implementation code"
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = self.tmp_dir.name

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.tmp_dir.cleanup()

    @patch('genesis.smart_model_call')
    def test_b1_integration_testing(self, mock_smart_model):
        """Test B1: Integration & Testing step"""
        # Mock all the workflow calls to avoid infinite execution
        mock_smart_model.side_effect = [
            "Integration tests passed - all tests pass",  # B1
            "Goal validation complete - goal fully implemented"  # B2 (triggers termination)
        ]

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.side_effect = ["Integration tests passed - all tests pass"]

            result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

            # Check that B1 prompt was constructed correctly
            expected_prompt = f"Integration & Testing: Run all relevant tests and integrate changes for goal '{self.goal}': {self.current_suite}"
            calls = mock_smart_model.call_args_list
            self.assertTrue(any(expected_prompt in str(call) for call in calls))

            # Should terminate early due to dual condition being met
            self.assertEqual(result, self.current_suite)

    @patch('genesis.smart_model_call')
    def test_dual_termination_condition(self, mock_smart_model):
        """Test dual termination condition: both goal validation and tests must pass"""
        # Mock B1 output with passing tests
        b1_output = "Integration tests passed - all tests pass"
        # Mock B2 output with completed goal
        b2_output = "Goal validation complete - goal fully implemented"

        mock_smart_model.side_effect = [b1_output, b2_output]

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.side_effect = [b1_output, b2_output]

            result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

            # Should return current suite when both conditions are met
            self.assertEqual(result, self.current_suite)

    @patch('genesis.smart_model_call')
    @patch('genesis.cerebras_call')
    def test_b4_retry_logic(self, mock_cerebras, mock_smart_model):
        """Test B4.3 retry logic when tests fail"""
        # Mock B1 and B2 outputs (not terminating)
        b1_output = "Integration status"
        b2_output = "Goal validation - implementation gaps exist"
        b3_output = "Milestone list"
        b41_output = "Execution plan"
        b42_output = "Generated code"
        b43_fail_output = "Test validation failed - tests failed"
        b43_pass_output = "Test validation passed - all tests pass"
        b5_output = "Code review complete"

        # First B4.3 fails, second passes
        mock_smart_model.side_effect = cycle([
            b1_output, b2_output, b3_output,  # B1, B2, B3
            b41_output, b43_fail_output,       # B4.1, B4.3 (fail)
            b41_output, b43_pass_output,       # B4.1 retry, B4.3 (pass)
            b5_output                          # B5
        ])
        mock_cerebras.side_effect = cycle([b42_output])  # B4.2 calls

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.side_effect = cycle([
                b1_output,    # B2 reads integration status
                b2_output,    # B3 reads goal validation
                b3_output,    # B4.1 reads milestones
                b41_output, b3_output,  # B4.2 reads execution plan and milestones
                b3_output,    # B4.1 retry reads milestones
                b41_output, b3_output   # B4.2 retry reads execution plan and milestones
            ])

            result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

            # Should have retried once and completed B5
            self.assertEqual(result, b5_output)

    @patch('sys.argv', ['test', '--claude'])  # Claude override flag
    @patch('genesis.smart_model_call')
    def test_claude_model_selection(self, mock_smart_model):
        """Test Claude model selection when --claude flag present"""
        genesis.GENESIS_USE_CODEX = None
        genesis._SANITIZED_ARGV = None
        mock_smart_model.return_value = "Claude response"

        # Test Claude-specific prompt construction in B4.1
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.side_effect = cycle([
                "integration status",  # B2 reads
                "goal validation - implementation gaps exist",  # B3 reads
                "milestone list",  # B4.1 reads milestones
                "execution plan", "milestone list"  # B4.2 reads
            ])

            # Mock side effects for the workflow calls - use cycle for infinite responses
            mock_smart_model.side_effect = cycle([
                "integration status",
                "goal validation - implementation gaps exist",
                "milestone list",
                "execution plan",  # B4.1 with Claude
                "all tests pass",  # B4.3 passes
                "code review"      # B5
            ])

            with patch('genesis.cerebras_call', return_value="generated code"):
                result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

                claude_prompts = [args[0] for args, _ in mock_smart_model.call_args_list if args]
                self.assertTrue(
                    any("jleechan_simulation_prompt.md" in prompt for prompt in claude_prompts)
                )

    @patch('sys.argv', ['test'])  # Default Codex path
    @patch('genesis.smart_model_call')
    def test_codex_model_selection(self, mock_smart_model):
        """Test Codex model selection when running with default settings"""
        genesis.GENESIS_USE_CODEX = None
        genesis._SANITIZED_ARGV = None
        mock_smart_model.return_value = "Codex response"

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read.side_effect = cycle([
                "integration status",
                "goal validation - implementation gaps exist",
                "milestone list",
                "execution plan", "milestone list"
            ])

            mock_smart_model.side_effect = cycle([
                "integration status",
                "goal validation - implementation gaps exist",
                "milestone list",
                "execution plan",  # B4.1 with Codex
                "all tests pass",  # B4.3 passes
                "code review"      # B5
            ])

            with patch('genesis.cerebras_call', return_value="generated code"):
                result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

                codex_prompts = [args[0] for args, _ in mock_smart_model.call_args_list if args]
                self.assertTrue(
                    all("jleechan_simulation_prompt.md" not in prompt for prompt in codex_prompts)
                )


class TestHelperFunctions(unittest.TestCase):

    @patch('genesis.execute_claude_command')
    def test_cerebras_call(self, mock_execute):
        """Test cerebras_call wrapper function"""
        mock_execute.return_value = "Cerebras response"

        result = cerebras_call("Test prompt")

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        self.assertEqual(args[0], "Test prompt")
        self.assertTrue(kwargs.get("use_cerebras"))
        self.assertEqual(result, "Cerebras response")

    @patch('genesis.execute_claude_command')
    def test_execute_codex_command(self, mock_execute):
        """Test execute_codex_command wrapper function"""
        mock_execute.return_value = "Codex response"

        result = execute_codex_command("Test prompt")

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        self.assertEqual(args[0], "Test prompt")
        self.assertTrue(kwargs.get("use_codex"))
        self.assertEqual(result, "Codex response")

    @patch('sys.argv', ['test', '--claude'])  # Claude override flag
    @patch('genesis.execute_claude_command')
    def test_smart_model_call_claude(self, mock_execute):
        """Test smart_model_call uses Claude when --claude flag present"""
        genesis.GENESIS_USE_CODEX = None
        genesis._SANITIZED_ARGV = None
        mock_execute.return_value = "Claude response"

        result = smart_model_call("Test prompt")

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        self.assertEqual(args[0], "Test prompt")
        self.assertFalse(kwargs.get("use_cerebras"))
        self.assertEqual(result, "Claude response")

    @patch('sys.argv', ['test'])  # Default Codex path
    @patch('genesis.execute_claude_command')
    def test_smart_model_call_codex(self, mock_execute):
        """Test smart_model_call uses Codex by default"""
        genesis.GENESIS_USE_CODEX = None
        genesis._SANITIZED_ARGV = None
        mock_execute.return_value = "Codex response"

        result = smart_model_call("Test prompt")

        mock_execute.assert_called_once()
        args, kwargs = mock_execute.call_args
        self.assertEqual(args[0], "Test prompt")
        self.assertTrue(kwargs.get("use_codex"))
        self.assertEqual(result, "Codex response")


class TestTmpFileOperations(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = self.tmp_dir.name
        self.goal = "Test goal"
        self.current_suite = "Test suite"

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmp_dir.cleanup()

    @patch('genesis.smart_model_call')
    @patch('genesis.cerebras_call')
    def test_tmp_file_data_flow(self, mock_cerebras, mock_smart_model):
        """Test that data flows correctly through /tmp files"""

        # Create actual temp files to test file operations
        os.makedirs(self.tmp_path, exist_ok=True)

        mock_smart_model.side_effect = cycle([
            "integration status content",
            "goal validation - implementation gaps exist",
            "milestone list content",
            "execution plan content",
            "all tests pass",
            "code review content"
        ])
        mock_cerebras.return_value = "generated code content"

        result = execute_detailed_b1_to_b5_workflow(self.current_suite, self.goal, self.tmp_path)

        # Verify files were created with expected content
        integration_file = os.path.join(self.tmp_path, "genesis_integration_status.txt")
        self.assertTrue(os.path.exists(integration_file))

        goal_validation_file = os.path.join(self.tmp_path, "genesis_goal_validation.txt")
        self.assertTrue(os.path.exists(goal_validation_file))

        milestones_file = os.path.join(self.tmp_path, "genesis_milestones.txt")
        self.assertTrue(os.path.exists(milestones_file))

        execution_plan_file = os.path.join(self.tmp_path, "genesis_execution_plan.txt")
        self.assertTrue(os.path.exists(execution_plan_file))

        test_results_file = os.path.join(self.tmp_path, "genesis_test_results.txt")
        self.assertTrue(os.path.exists(test_results_file))


if __name__ == '__main__':
    unittest.main()
