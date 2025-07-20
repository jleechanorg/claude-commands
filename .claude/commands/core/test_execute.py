#!/usr/bin/env python3
"""
Unit tests for the execute command module.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from execute import assess_task_complexity, use_subagents, execute


class TestExecuteModule(unittest.TestCase):
    """Test suite for execute command functionality."""

    def test_assess_task_complexity_simple(self):
        """Test complexity assessment for simple tasks."""
        result = assess_task_complexity("fix button color")
        
        self.assertEqual(result['complexity'], 'Simple')
        self.assertFalse(result['subagent_beneficial'])
        self.assertLess(result['estimated_time'], 30)

    def test_assess_task_complexity_complex(self):
        """Test complexity assessment for complex tasks."""
        result = assess_task_complexity("implement authentication system with database integration and API endpoints")
        
        self.assertEqual(result['complexity'], 'Complex')
        self.assertTrue(result['subagent_beneficial'])
        self.assertGreater(result['estimated_time'], 30)

    def test_use_subagents_decision(self):
        """Test subagent usage decision logic."""
        # Simple task - should not use subagents
        simple_analysis = {'subagent_beneficial': False, 'estimated_time': 10}
        self.assertFalse(use_subagents("fix typo", simple_analysis))
        
        # Complex task - should use subagents
        complex_analysis = {'subagent_beneficial': True, 'estimated_time': 45}
        self.assertTrue(use_subagents("build authentication system", complex_analysis))
        
        # Short complex task - should not use subagents
        short_complex = {'subagent_beneficial': True, 'estimated_time': 15}
        self.assertFalse(use_subagents("quick complex task", short_complex))

    def test_execute_command_dry_run(self):
        """Test execute command in dry-run mode."""
        runner = CliRunner()
        result = runner.invoke(execute, ['test task', '--dry-run'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Dry run complete', result.output)
        self.assertIn('Task Analysis', result.output)

    def test_execute_command_verbose(self):
        """Test execute command with verbose output."""
        runner = CliRunner()
        result = runner.invoke(execute, ['test task', '--dry-run', '--verbose'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Claude Execute Command', result.output)
        self.assertIn('Complexity:', result.output)
        self.assertIn('Strategy:', result.output)

    def test_execute_command_no_subagents(self):
        """Test execute command with subagents disabled."""
        runner = CliRunner()
        result = runner.invoke(execute, ['complex implementation task', '--dry-run', '--no-subagents'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Strategy: Direct execution', result.output)

    @patch('execute.execute_with_subagents')
    def test_execute_with_subagents_called(self, mock_subagents):
        """Test that subagent execution is called for complex tasks."""
        mock_subagents.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(execute, ['implement complex authentication system with database'])
        
        self.assertEqual(result.exit_code, 0)
        mock_subagents.assert_called_once()

    @patch('execute.execute_directly')
    def test_execute_directly_called(self, mock_direct):
        """Test that direct execution is called for simple tasks."""
        mock_direct.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(execute, ['fix typo', '--no-subagents'])
        
        self.assertEqual(result.exit_code, 0)
        mock_direct.assert_called_once()

    def test_complexity_scoring(self):
        """Test complexity scoring algorithm."""
        # Test various complexity indicators
        test_cases = [
            ("fix button", 0, 'Simple'),
            ("implement authentication", 1, 'Complex'),
            ("create system with multiple database integrations", 3, 'Complex'),
            ("simple change to color", 0, 'Simple'),
            ("build architecture for API system", 2, 'Complex')
        ]
        
        for task, expected_min_score, expected_complexity in test_cases:
            result = assess_task_complexity(task)
            self.assertGreaterEqual(result['complexity_score'], expected_min_score)
            self.assertEqual(result['complexity'], expected_complexity)

    def test_timeout_parameter(self):
        """Test timeout parameter handling."""
        runner = CliRunner()
        result = runner.invoke(execute, ['test task', '--dry-run', '--timeout', '600'])
        
        self.assertEqual(result.exit_code, 0)
        # Command should accept timeout parameter without error

    def test_help_output(self):
        """Test help output contains expected information."""
        runner = CliRunner()
        result = runner.invoke(execute, ['--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Execute tasks immediately', result.output)
        self.assertIn('--verbose', result.output)
        self.assertIn('--dry-run', result.output)
        self.assertIn('--no-subagents', result.output)


class TestExecuteIntegration(unittest.TestCase):
    """Integration tests for execute command."""

    def test_end_to_end_simple_task(self):
        """Test end-to-end execution of simple task."""
        runner = CliRunner()
        result = runner.invoke(execute, ['fix spelling error', '--dry-run', '--verbose'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Task Analysis', result.output)
        self.assertIn('Simple', result.output)
        self.assertIn('Direct execution', result.output)

    def test_end_to_end_complex_task(self):
        """Test end-to-end execution of complex task."""
        runner = CliRunner()
        result = runner.invoke(execute, [
            'implement user authentication system with database and API integration',
            '--dry-run', '--verbose'
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Task Analysis', result.output)
        self.assertIn('Complex', result.output)
        # Should suggest subagent coordination for complex tasks


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestExecuteModule))
    suite.addTests(loader.loadTestsFromTestCase(TestExecuteIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)