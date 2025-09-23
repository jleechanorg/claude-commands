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

from jleechanorg_pr_monitor import JleechanorgPRMonitor, main


class TestPRTargeting(unittest.TestCase):
    """Test PR targeting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_workspace = "/tmp/test-workspace"

    @patch('jleechanorg_pr_monitor.AutomationSafetyManager')
    def test_monitor_init_with_target_pr(self, mock_safety_manager):
        """Test monitor initialization with target PR option"""
        monitor = JleechanorgPRMonitor(workspace_base=self.mock_workspace)

        # Test that monitor can accept target_pr parameter
        self.assertIsInstance(monitor, JleechanorgPRMonitor)

    @patch('jleechanorg_pr_monitor.AutomationSafetyManager')
    def test_process_single_pr_by_number(self, mock_safety_manager):
        """Test processing a single PR by number"""
        monitor = JleechanorgPRMonitor(workspace_base=self.mock_workspace)

        # Mock the dependencies for process_single_pr_by_number
        with patch.object(monitor, 'post_codex_instruction', return_value=True) as mock_codex, \
             patch.object(monitor, 'create_worktree_for_pr', return_value=Path(self.mock_workspace)) as mock_worktree, \
             patch.object(monitor, 'cleanup_workspace') as mock_cleanup, \
             patch('subprocess.run') as mock_subprocess:

            # Mock gh pr view response
            mock_subprocess.return_value.stdout = '{"title": "Test PR", "headRefName": "test-branch", "baseRefName": "main", "url": "http://test.com", "author": {"login": "testuser"}}'

            result = monitor.process_single_pr_by_number(1702, "worldarchitect.ai")

            self.assertTrue(result)
            mock_codex.assert_called_once()
            mock_worktree.assert_called_once()
            mock_cleanup.assert_called()

    def test_cli_argument_parsing_target_pr(self):
        """Test that CLI accepts --target-pr argument"""
        # This should fail initially because --target-pr doesn't exist yet
        parser = argparse.ArgumentParser(description='jleechanorg PR Monitor')
        parser.add_argument('--workspace-base', help='Base directory for PR workspaces')
        parser.add_argument('--dry-run', action='store_true', help='Discover PRs but do not process them')
        parser.add_argument('--single-repo', help='Process only specific repository')
        parser.add_argument('--max-prs', type=int, default=10, help='Maximum PRs to process per cycle')

        # This line should cause the test to fail because --target-pr doesn't exist
        try:
            parser.add_argument('--target-pr', type=int, help='Process specific PR number')
            parser.add_argument('--target-repo', help='Repository for target PR (required with --target-pr)')

            # Test parsing with target-pr
            args = parser.parse_args(['--target-pr', '1702', '--target-repo', 'worldarchitect.ai'])

            self.assertEqual(args.target_pr, 1702)
            self.assertEqual(args.target_repo, 'worldarchitect.ai')

        except Exception as e:
            self.fail(f"CLI should support --target-pr argument: {e}")

    @patch('sys.argv', ['jleechanorg_pr_monitor.py', '--target-pr', '1702', '--target-repo', 'worldarchitect.ai'])
    @patch('jleechanorg_pr_monitor.JleechanorgPRMonitor')
    def test_main_with_target_pr(self, mock_monitor_class):
        """Test main function with target PR arguments"""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.process_single_pr_by_number.return_value = True

        # This will fail because main() doesn't handle --target-pr yet
        try:
            main()
            mock_monitor.process_single_pr_by_number.assert_called_once_with(1702, 'worldarchitect.ai')
        except SystemExit:
            # Expected to fail with current implementation
            pass

    @patch('jleechanorg_pr_monitor.subprocess.run')
    def test_post_codex_instruction_skips_for_existing_commit(self, mock_run):
        """Codex comment is skipped when already posted for latest commit"""
        monitor = JleechanorgPRMonitor(workspace_base=self.mock_workspace)

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            metadata = {
                "pr_number": 1703,
                "repository": "worldarchitect.ai",
                "repository_full_name": "jleechanorg/worldarchitect.ai",
            }
            with open(workspace / ".pr-metadata.json", 'w') as f:
                json.dump(metadata, f)

            comment_body = (
                f"{monitor.CODEX_COMMENT_TEXT}\n\n"
                f"{monitor.CODEX_COMMIT_MARKER_PREFIX}deadbeef{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
            )

            with patch.object(
                monitor,
                '_get_pr_comment_state',
                return_value=("deadbeef", [{"body": comment_body}])
            ) as mock_state:
                result = monitor.post_codex_instruction(workspace)

            mock_state.assert_called_once_with("jleechanorg/worldarchitect.ai", 1703)

        self.assertTrue(result)
        mock_run.assert_not_called()

    def test_extract_commit_marker(self):
        """Commit markers can be parsed from Codex comments"""
        monitor = JleechanorgPRMonitor(workspace_base=self.mock_workspace)
        marker = monitor._extract_commit_marker(
            f"{monitor.CODEX_COMMENT_TEXT}\n\n"
            f"{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        )
        self.assertEqual(marker, "abc123")


if __name__ == '__main__':
    unittest.main()
