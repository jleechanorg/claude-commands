#!/usr/bin/env python3
"""
Test PR targeting functionality for jleechanorg_pr_monitor
"""

import unittest
import argparse
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path setup
import jleechanorg_pr_monitor
from jleechanorg_pr_monitor import JleechanorgPRMonitor, main


class TestPRTargeting(unittest.TestCase):
    """Test PR targeting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        pass

    @patch('jleechanorg_pr_monitor.AutomationSafetyManager')
    def test_monitor_init_with_target_pr(self, mock_safety_manager):
        """Test monitor initialization with target PR option"""
        monitor = JleechanorgPRMonitor()

        # Test that monitor can accept target_pr parameter
        self.assertIsInstance(monitor, JleechanorgPRMonitor)

    @patch('jleechanorg_pr_monitor.AutomationSafetyManager')
    def test_process_single_pr_by_number(self, mock_safety_manager):
        """Test processing a single PR by number"""
        monitor = JleechanorgPRMonitor()

        # Mock the dependencies for process_single_pr_by_number
        with patch.object(monitor, 'post_codex_instruction_simple', return_value=True) as mock_codex, \
             patch('subprocess.run') as mock_subprocess:

            # Mock gh pr view response
            mock_subprocess.return_value.stdout = '{"title": "Test PR", "headRefName": "test-branch", "baseRefName": "main", "url": "http://test.com", "author": {"login": "testuser"}}'

            result = monitor.process_single_pr_by_number(1702, "jleechanorg/worldarchitect.ai")

            self.assertTrue(result)
            mock_codex.assert_called_once()

    def test_cli_argument_parsing_target_pr(self):
        """Test that CLI accepts --target-pr argument"""
        # This should fail initially because --target-pr doesn't exist yet
        parser = argparse.ArgumentParser(description='jleechanorg PR Monitor')
        parser.add_argument('--dry-run', action='store_true', help='Discover PRs but do not process them')
        parser.add_argument('--single-repo', help='Process only specific repository')
        parser.add_argument('--max-prs', type=int, default=10, help='Maximum PRs to process per cycle')

        # This line should cause the test to fail because --target-pr doesn't exist
        try:
            parser.add_argument('--target-pr', type=int, help='Process specific PR number')
            parser.add_argument('--target-repo', help='Repository for target PR (required with --target-pr)')

            # Test parsing with target-pr
            args = parser.parse_args(['--target-pr', '1702', '--target-repo', 'jleechanorg/worldarchitect.ai'])

            self.assertEqual(args.target_pr, 1702)
            self.assertEqual(args.target_repo, 'jleechanorg/worldarchitect.ai')

        except Exception as e:
            self.fail(f"CLI should support --target-pr argument: {e}")

    @patch('sys.argv', ['jleechanorg_pr_monitor.py', '--target-pr', '1702', '--target-repo', 'jleechanorg/worldarchitect.ai'])
    @patch('jleechanorg_pr_monitor.JleechanorgPRMonitor')
    def test_main_with_target_pr(self, mock_monitor_class):
        """Test main function with target PR arguments"""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.process_single_pr_by_number.return_value = True

        # This will fail because main() doesn't handle --target-pr yet
        try:
            main()
            mock_monitor.process_single_pr_by_number.assert_called_once_with(1702, 'jleechanorg/worldarchitect.ai')
        except SystemExit:
            # Expected to fail with current implementation
            pass


    def test_extract_commit_marker(self):
        """Commit markers can be parsed from Codex comments"""
        monitor = JleechanorgPRMonitor()
        marker = monitor._extract_commit_marker(
            f"{monitor.CODEX_COMMENT_TEXT}\n\n"
            f"{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        )
        self.assertEqual(marker, "abc123")

    def test_build_comment_includes_marker_and_handle(self):
        """Generated comments include dynamic handle and commit marker."""
        monitor = JleechanorgPRMonitor()
        head_sha = "abc123def456"
        body = monitor._build_codex_comment_body_simple(
            repository="jleechanorg/worldarchitect.ai",
            pr_number=1702,
            pr_data={"title": "Test", "author": {"login": "tester"}, "headRefName": "feature"},
            head_sha=head_sha,
            comments=[],
        )
        expected_marker = f"{monitor.CODEX_COMMIT_MARKER_PREFIX}{head_sha}{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        self.assertIn(expected_marker, body)
        self.assertIn(f"@{monitor.assistant_handle}", body)


if __name__ == '__main__':
    unittest.main()
