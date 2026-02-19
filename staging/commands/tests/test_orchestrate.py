#!/usr/bin/env python3
"""
Unit tests for orchestrate.py command.

Tests:
- Configuration constants validation
- Main function redirect functionality
- Module imports
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import orchestrate


class TestOrchestrateModule(unittest.TestCase):
    """Test orchestration module functionality."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    @patch("os.path.exists", return_value=True)
    @patch("orchestrate.subprocess.run")
    def test_main_function_redirect(self, mock_run, mock_exists):
        """Test that main() function redirects to unified orchestration."""
        # Mock successful orchestration script execution
        mock_run.return_value.returncode = 0

        # Test with no arguments (should show usage)
        with patch('sys.argv', ['orchestrate.py']):
            self.assertEqual(orchestrate.main(), 1)  # Returns 1 for usage error

        # Test with task arguments
        with patch('sys.argv', ['orchestrate.py', 'test', 'task']):
            self.assertEqual(orchestrate.main(), 0)

        # Verify subprocess was called for the task
        self.assertTrue(mock_run.called)

    def test_unified_script_path_detection(self):
        """Test that main() can find the unified orchestration script."""
        # Test script directory calculation
        script_dir = os.path.dirname(os.path.abspath(orchestrate.__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        orchestration_dir = os.path.join(project_root, "orchestration")
        unified_script = os.path.join(orchestration_dir, "orchestrate_unified.py")

        # Verify path construction logic
        self.assertTrue(orchestration_dir.endswith("orchestration"))
        self.assertTrue(unified_script.endswith("orchestrate_unified.py"))

    @patch('os.path.exists')
    def test_missing_unified_script_handling(self, mock_exists):
        """Test behavior when unified orchestration script is missing."""
        mock_exists.return_value = False

        with patch('orchestrate.subprocess.run') as mock_run:
            with patch('sys.argv', ['orchestrate.py', 'test', 'task']):
                self.assertEqual(orchestrate.main(), 1)
            mock_run.assert_not_called()

    def test_module_imports_successfully(self):
        """Test that the orchestrate module imports without errors."""
        # Test that the main redirect function is available
        self.assertTrue(callable(orchestrate.main))
        # As a pure redirect module, orchestrate.py no longer contains configuration constants

    def test_usage_message_format(self):
        """Test that usage message is properly formatted."""
        with patch('sys.argv', ['orchestrate.py']):
            with patch('builtins.print') as mock_print:
                self.assertEqual(orchestrate.main(), 1)
                # Verify both usage and example messages were printed
                mock_print.assert_any_call("Usage: /orchestrate [task description]")
                mock_print.assert_any_call("Example: /orchestrate Find security vulnerabilities and create coverage report")
                self.assertEqual(mock_print.call_count, 2)

    @patch('orchestrate.subprocess.run')
    def test_error_handling_on_script_failure(self, mock_run):
        """Test error handling when unified script fails."""
        mock_run.side_effect = Exception("Script execution failed")

        with patch('sys.argv', ['orchestrate.py', 'test', 'task']):
            with patch('os.path.exists', return_value=True):
                self.assertEqual(orchestrate.main(), 1)

    def test_argument_forwarding(self):
        """Test that command line arguments are properly forwarded."""
        test_args = ['orchestrate.py', 'analyze', 'codebase', 'for', 'issues']

        with patch('sys.argv', test_args):
            with patch('subprocess.run') as mock_run:
                with patch('os.path.exists', return_value=True):
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)

                    # Verify subprocess was called with forwarded arguments
                    self.assertTrue(mock_run.called)
                    # Arguments should be forwarded (excluding script name)
                    call_args = mock_run.call_args[0][0]
                    self.assertIn('analyze', ' '.join(call_args))
                    self.assertIn('codebase', ' '.join(call_args))

    def test_redirect_module_purpose(self):
        """Test that orchestrate module serves as pure redirect."""
        # Module already imported at top level

        # Verify main function exists (core redirect functionality)
        self.assertTrue(hasattr(orchestrate, "main"))
        self.assertTrue(callable(orchestrate.main))

        # Verify this is a pure redirect module - no orchestration constants
        # (Constants moved to unified orchestration system)

    def test_redirect_functionality(self):
        """Test that redirect functionality works as expected."""
        # Test that the module correctly redirects to unified orchestration
        # This replaces pattern testing since patterns are now in unified system
        with patch('sys.argv', ['orchestrate.py', 'test_redirect']):
            with patch('os.path.exists', return_value=True):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)
                    self.assertTrue(mock_run.called)

    def test_optional_argument_forwarding(self):
        """Test that optional arguments are properly forwarded to unified orchestration."""
        test_args = [
            'orchestrate.py',
            '--context', '/tmp/context.md',
            '--branch', 'my-branch',
            '--pr', '123',
            '--mcp-agent', 'TestAgent',
            '--bead', 'bead-123',
            '--validate', 'make test',
            '--no-new-pr',
            '--no-new-branch',
            'My task description'
        ]

        with patch('sys.argv', test_args):
            with patch('subprocess.run') as mock_run:
                with patch('os.path.exists', return_value=True):
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)

                    # Verify subprocess was called with all forwarded arguments
                    self.assertTrue(mock_run.called)
                    call_args = mock_run.call_args[0][0]
                    call_str = ' '.join(call_args)

                    # Check all optional arguments are forwarded
                    self.assertIn('--context', call_str)
                    self.assertIn('/tmp/context.md', call_str)
                    self.assertIn('--branch', call_str)
                    self.assertIn('my-branch', call_str)
                    self.assertIn('--pr', call_str)
                    self.assertIn('123', call_str)
                    self.assertIn('--mcp-agent', call_str)
                    self.assertIn('TestAgent', call_str)
                    self.assertIn('--bead', call_str)
                    self.assertIn('bead-123', call_str)
                    self.assertIn('--validate', call_str)
                    self.assertIn('make test', call_str)
                    self.assertIn('--no-new-pr', call_str)
                    self.assertIn('--no-new-branch', call_str)
                    self.assertIn('My task description', call_str)

    def test_partial_optional_arguments(self):
        """Test forwarding with only some optional arguments."""
        test_args = [
            'orchestrate.py',
            '--branch', 'feature-branch',
            '--pr', '456',
            'Update feature'
        ]

        with patch('sys.argv', test_args):
            with patch('subprocess.run') as mock_run:
                with patch('os.path.exists', return_value=True):
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)

                    self.assertTrue(mock_run.called)
                    call_args = mock_run.call_args[0][0]
                    call_str = ' '.join(call_args)

                    # Check partial arguments are forwarded
                    self.assertIn('--branch', call_str)
                    self.assertIn('feature-branch', call_str)
                    self.assertIn('--pr', call_str)
                    self.assertIn('456', call_str)
                    self.assertIn('Update feature', call_str)

    def test_no_new_pr_flag_forwarding(self):
        """Test that --no-new-pr flag is forwarded correctly."""
        test_args = ['orchestrate.py', '--no-new-pr', 'Fix bug']

        with patch('sys.argv', test_args):
            with patch('subprocess.run') as mock_run:
                with patch('os.path.exists', return_value=True):
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)

                    self.assertTrue(mock_run.called)
                    call_args = mock_run.call_args[0][0]
                    self.assertIn('--no-new-pr', call_args)

    def test_no_new_branch_flag_forwarding(self):
        """Test that --no-new-branch flag is forwarded correctly."""
        test_args = ['orchestrate.py', '--no-new-branch', 'Continue work']

        with patch('sys.argv', test_args):
            with patch('subprocess.run') as mock_run:
                with patch('os.path.exists', return_value=True):
                    mock_run.return_value.returncode = 0
                    self.assertEqual(orchestrate.main(), 0)

                    self.assertTrue(mock_run.called)
                    call_args = mock_run.call_args[0][0]
                    self.assertIn('--no-new-branch', call_args)


if __name__ == "__main__":
    unittest.main()
