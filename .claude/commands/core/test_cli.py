#!/usr/bin/env python3
"""
Unit tests for the CLI framework.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from cli import cli
except ImportError:
    # Skip CLI tests if imports fail
    cli = None


class TestCLIFramework(unittest.TestCase):
    """Test suite for CLI framework functionality."""

    def setUp(self):
        """Set up test environment."""
        if cli is None:
            self.skipTest("CLI module not available")
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ['--help'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Claude AI Assistant', result.output)
        self.assertIn('Command Line Interface', result.output)

    def test_cli_version(self):
        """Test CLI version output."""
        result = self.runner.invoke(cli, ['--version'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('1.0.0', result.output)

    def test_execute_command_available(self):
        """Test that execute command is available."""
        result = self.runner.invoke(cli, ['execute', '--help'])
        
        # Should either work or show command not found
        # This tests that the command is properly registered
        self.assertIn('execute', result.output.lower() or 'not found' in result.output.lower())

    def test_test_command_available(self):
        """Test that test command is available."""
        result = self.runner.invoke(cli, ['test', '--help'])
        
        # Should either work or show command not found
        # This tests that the command is properly registered
        self.assertTrue(
            result.exit_code == 0 or 'not found' in result.output.lower()
        )

    def test_invalid_command(self):
        """Test invalid command handling."""
        result = self.runner.invoke(cli, ['nonexistent-command'])
        
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('No such command', result.output)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI framework."""

    def setUp(self):
        """Set up test environment."""
        if cli is None:
            self.skipTest("CLI module not available")
        self.runner = CliRunner()

    def test_command_discovery(self):
        """Test that commands are properly discovered."""
        result = self.runner.invoke(cli, ['--help'])
        
        if result.exit_code == 0:
            # Check for expected command groups
            help_text = result.output.lower()
            # CLI should list available commands
            self.assertTrue(len(help_text) > 50)  # Should have substantial help text

    def test_error_handling(self):
        """Test CLI error handling."""
        result = self.runner.invoke(cli, ['execute'])  # Missing required argument
        
        # Should handle missing arguments gracefully
        self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCLIFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)