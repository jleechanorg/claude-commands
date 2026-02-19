#!/usr/bin/env python3
"""
Test for workspace dispatch when workspace directory doesn't exist.

This tests the critical bug where automation fails when:
1. PR is processed initially (workspace created)
2. Workspace is cleaned up
3. PR gets new commits
4. Automation tries to re-process but fails because workspace is missing

Expected behavior: Create workspace if missing, don't fail
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import from local source, not installed package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from jleechanorg_pr_automation.orchestrated_pr_runner import prepare_workspace_dir


class TestWorkspaceDispatchMissingDirectory(unittest.TestCase):
    """Test that workspace dispatch handles missing directories gracefully."""

    def setUp(self):
        """Set up test workspace directory."""
        self.test_root = Path(tempfile.mkdtemp(prefix="test_workspace_dispatch_"))

    def tearDown(self):
        """Clean up test workspace directory."""
        if self.test_root.exists():
            shutil.rmtree(self.test_root)

    def test_prepare_workspace_ignores_rmtree_filenotfound_race(self):
        """
        Test that prepare_workspace_dir ignores FileNotFoundError from rmtree.

        This can happen if the workspace exists during the initial existence check but
        is removed concurrently (external cleanup, reboot/tmpfs cleanup, etc.) before
        shutil.rmtree() runs.
        """
        repo = "worldarchitect.ai"
        workspace_name = "pr-2915-fix-social-hp-god-tier-enforcement"

        # Workspace exists, but removal races with external cleanup.
        workspace_path = self.test_root / repo / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        with patch("jleechanorg_pr_automation.orchestrated_pr_runner.WORKSPACE_ROOT_BASE", self.test_root):
            with patch(
                "jleechanorg_pr_automation.orchestrated_pr_runner.shutil.rmtree",
                side_effect=FileNotFoundError("[Errno 2] No such file or directory"),
            ) as mock_rmtree:
                result = prepare_workspace_dir(repo, workspace_name)

        self.assertEqual(result, self.test_root / repo / workspace_name)
        self.assertTrue(result.parent.exists(), f"Parent directory {result.parent} should exist after prepare_workspace_dir")
        self.assertEqual(mock_rmtree.call_count, 1, "Expected a single rmtree attempt")

    def test_prepare_workspace_raises_on_non_filenotfound_oserror(self):
        """
        Test that prepare_workspace_dir still raises on serious OS errors.

        Scenario: Workspace exists but rmtree fails (permissions, locks, etc.).
        """
        repo = "worldarchitect.ai"
        workspace_name = "pr-2909-fix-power-absorption-rewards-protocol"

        workspace_path = self.test_root / repo / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        with patch("jleechanorg_pr_automation.orchestrated_pr_runner.WORKSPACE_ROOT_BASE", self.test_root):
            with patch(
                "jleechanorg_pr_automation.orchestrated_pr_runner.shutil.rmtree",
                side_effect=PermissionError("[Errno 13] Permission denied"),
            ):
                with self.assertRaises(PermissionError):
                    prepare_workspace_dir(repo, workspace_name)

    def test_prepare_workspace_with_git_worktree_attempts_cleanup(self):
        """
        Test that prepare_workspace_dir handles git worktrees correctly.

        Scenario: Workspace is a git worktree that was cleaned up
        Expected: Should clean up worktree metadata and proceed
        """
        repo = "worldarchitect.ai"
        workspace_name = "pr-2902-claude-test-and-fix-system-prompt-RiZyM"

        # Create workspace with .git file (worktree marker)
        workspace_path = self.test_root / repo / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)
        git_file = workspace_path / ".git"
        git_file.write_text(
            f"gitdir: {self.test_root / repo / '.git' / 'worktrees' / workspace_name}"
        )

        with patch("jleechanorg_pr_automation.orchestrated_pr_runner.WORKSPACE_ROOT_BASE", self.test_root):
            with patch(
                "jleechanorg_pr_automation.orchestrated_pr_runner.run_cmd",
                return_value=MagicMock(returncode=0, stdout="", stderr=""),
            ) as mock_run_cmd:
                with patch(
                    "jleechanorg_pr_automation.orchestrated_pr_runner.shutil.rmtree",
                    side_effect=FileNotFoundError("[Errno 2] No such file or directory"),
                ):
                    result = prepare_workspace_dir(repo, workspace_name)

        self.assertEqual(result, self.test_root / repo / workspace_name)
        self.assertGreaterEqual(mock_run_cmd.call_count, 2, "Should call git worktree remove and prune")
        self.assertTrue(result.parent.exists(), "Parent directory should exist")


if __name__ == "__main__":
    unittest.main()
