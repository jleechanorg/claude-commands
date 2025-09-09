#!/usr/bin/env python3
"""
Test subprocess security vulnerabilities in copilot utils.

Tests the security fix for shell=True usage in check_merge_tree function.
Following TDD approach: test the vulnerability, then verify the fix.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the directory containing the utils module to Python path
# From mvp_site/tests, we need to go up two levels to project root, then to .claude/commands/_copilot_modules
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, os.path.join(project_root, '.claude', 'commands', '_copilot_modules'))

try:
    from utils import GitCommands
    UTILS_AVAILABLE = True
except ImportError:
    GitCommands = None
    UTILS_AVAILABLE = False


class TestSubprocessSecurity(unittest.TestCase):
    """Test subprocess security in GitCommands."""

    def test_check_merge_tree_no_shell_injection(self):
        """Test that check_merge_tree is not vulnerable to shell injection."""

        # Test case 1: Verify secure subprocess usage
        with patch('subprocess.run') as mock_run:
            # Mock successful git operations
            mock_run.side_effect = [
                # First call: git symbolic-ref
                MagicMock(returncode=0, stdout="origin/main\n"),
                # Second call: git merge-base
                MagicMock(returncode=0, stdout="abc123\n"),
                # Third call: git merge-tree
                MagicMock(returncode=0, stdout="no conflicts\n")
            ]

            has_conflicts, output = GitCommands.check_merge_tree("123")

            # Verify no shell=True usage - all calls should use list arguments
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args
                # Verify first argument is a list (not a string for shell=True)
                self.assertIsInstance(args[0], list,
                    f"subprocess.run should use list args, not string. Call: {call_args}")
                # Verify shell is either not set or explicitly False
                shell_value = kwargs.get('shell', False)
                self.assertFalse(shell_value,
                    f"shell should be False or unset. Call: {call_args}")

    def test_check_merge_tree_injection_attempt(self):
        """Test that malicious input cannot be injected through shell."""

        # Simulate a malicious PR number that would be dangerous with shell=True
        malicious_pr = "123; rm -rf /; echo"

        with patch('subprocess.run') as mock_run:
            # Mock git operations
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="origin/main\n"),
                MagicMock(returncode=0, stdout="abc123\n"),
                MagicMock(returncode=0, stdout="no conflicts\n")
            ]

            # This should not execute any shell commands due to list-based args
            GitCommands.check_merge_tree(malicious_pr)

            # Verify that malicious input is safely contained in list arguments
            # The PR number itself isn't directly passed to subprocess, but verify safe usage
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args
                # Verify using list format (secure)
                self.assertIsInstance(args[0], list)
                # Verify no shell interpretation
                self.assertFalse(kwargs.get('shell', False))

    def test_all_git_commands_secure_subprocess(self):
        """Test that all GitCommands methods use secure subprocess calls."""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="test\n")

            # Test all GitCommands methods
            GitCommands.get_current_branch()
            GitCommands.get_merge_conflicts()

            # Verify all subprocess calls are secure
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args
                self.assertIsInstance(args[0], list,
                    "All subprocess calls should use list arguments")
                self.assertFalse(kwargs.get('shell', False),
                    "No subprocess call should use shell=True")

    def test_original_vulnerability_pattern(self):
        """Test that the original vulnerable pattern would fail this test.
        
        This test documents what the vulnerability looked like before the fix.
        If this test passes, it means the vulnerability has been fixed.
        """

        # This test verifies that we're NOT using the old vulnerable pattern:
        # subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="origin/main\n"),
                MagicMock(returncode=0, stdout="abc123\n"),
                MagicMock(returncode=0, stdout="no conflicts\n")
            ]

            GitCommands.check_merge_tree("123")

            # Verify we're NOT using the vulnerable pattern
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args

                # OLD VULNERABLE PATTERN (should NOT be present):
                # - First argument is a string (joined command)
                # - shell=True is set

                # Verify fix: first argument should be list, not string
                self.assertIsInstance(args[0], list,
                    "Fixed code should use list args, not string (vulnerable pattern)")

                # Verify fix: shell should be False/unset, not True
                self.assertFalse(kwargs.get('shell', False),
                    "Fixed code should not use shell=True (vulnerable pattern)")


    def test_merge_tree_uses_remote_tracking_refs(self):
        """Test that merge_tree uses origin/branch for CI/shallow clone reliability.
        
        RED PHASE: This test will fail until we fix the branch reference issue.
        """

        with patch('subprocess.run') as mock_run:
            # Mock git symbolic-ref to return origin/main format
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="origin/main\n"),
                MagicMock(returncode=0, stdout="abc123\n"),
                MagicMock(returncode=0, stdout="no conflicts\n")
            ]

            GitCommands.check_merge_tree("123")

            # Verify that remote tracking refs are used (not local branch names)
            calls = mock_run.call_args_list

            # Second call should be merge-base with remote ref
            merge_base_call = calls[1]
            merge_base_args = merge_base_call[0][0]

            # Should use origin/main, not just main
            self.assertTrue(
                any("origin/" in arg for arg in merge_base_args),
                f"merge-base should use origin/ ref for reliability. Got: {merge_base_args}"
            )

            # Third call should be merge-tree with remote ref
            merge_tree_call = calls[2]
            merge_tree_args = merge_tree_call[0][0]

            # Should use origin/main, not just main
            remote_refs = [arg for arg in merge_tree_args if "origin/" in arg]
            self.assertTrue(
                len(remote_refs) > 0,
                f"merge-tree should use origin/ ref for reliability. Got: {merge_tree_args}"
            )


if __name__ == '__main__':
    # Run with verbose output to see test details
    unittest.main(verbosity=2)
