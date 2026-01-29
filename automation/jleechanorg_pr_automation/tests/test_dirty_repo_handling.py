"""Tests for dirty git repository handling in orchestrated_pr_runner.

This test file validates that ensure_base_clone handles dirty git repositories
correctly by running `git reset --hard` before attempting to checkout branches.
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch, call

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import automation.jleechanorg_pr_automation.orchestrated_pr_runner as runner
import pytest


def test_prepare_base_clone_handles_dirty_repo(tmp_path, monkeypatch):
    """Test that ensure_base_clone handles dirty working tree correctly.

    Simulates the scenario where:
    1. Base clone exists but has uncommitted changes (detached HEAD state)
    2. `git checkout main` would fail with "local changes would be overwritten"
    3. Fix: Run `git reset --hard` BEFORE `git checkout main`
    """
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    # ensure_base_clone uses only the repo name (last part after /)
    repo_name = repo_full.split("/")[-1]
    base_dir = base_clone_root / repo_name

    # Mock environment
    monkeypatch.setattr(runner, "BASE_CLONE_ROOT", base_clone_root)
    monkeypatch.setattr(runner, "get_github_token", lambda: "test-token")

    # Create base directory structure
    base_dir.mkdir(parents=True)

    # Track all git commands that are run
    git_commands = []

    def mock_run_cmd(cmd, cwd=None, check=True, timeout=None):
        """Mock run_cmd to track git commands and simulate dirty repo scenario."""
        git_commands.append(cmd)

        # Simulate git rev-parse --verify main (main branch exists)
        if cmd == ["git", "rev-parse", "--verify", "main"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # Simulate git checkout main failing on dirty repo (BEFORE the fix)
        # This is what would happen without `git reset --hard` first
        if cmd == ["git", "checkout", "main"]:
            # Check if we ran `git reset --hard` before this
            reset_hard_before_checkout = any(
                c == ["git", "reset", "--hard"]
                for c in git_commands[:-1]  # Check commands before this one
            )

            if not reset_hard_before_checkout:
                # Simulate the error that occurs on dirty repos
                exc = subprocess.CalledProcessError(
                    1, cmd,
                    stderr="error: Your local changes to the following files would be overwritten by checkout:\n\t.beads/beads.base.jsonl\n\t.claude/settings.json\nPlease commit your changes or stash them before you switch branches.\nAborting"
                )
                raise exc
            # After reset --hard, checkout succeeds
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # All other git commands succeed
        if cmd[0] == "git":
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # Non-git commands
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd)

    # Run ensure_base_clone
    result = runner.ensure_base_clone(repo_full)

    # Verify the fix: git reset --hard should run BEFORE git checkout main
    assert result == base_dir

    # Extract just the git commands
    git_cmds = [cmd for cmd in git_commands if cmd[0] == "git"]

    # Find indices of key commands
    reset_hard_idx = None
    checkout_main_idx = None

    for i, cmd in enumerate(git_cmds):
        if cmd == ["git", "reset", "--hard"]:
            reset_hard_idx = i
        elif cmd == ["git", "checkout", "main"]:
            checkout_main_idx = i

    # Verify the fix is in place
    assert reset_hard_idx is not None, "git reset --hard should be called"
    assert checkout_main_idx is not None, "git checkout main should be called"
    assert reset_hard_idx < checkout_main_idx, \
        "git reset --hard must run BEFORE git checkout main to handle dirty repos"

    # Verify full command sequence (key parts)
    assert ["git", "rev-parse", "--verify", "main"] in git_cmds
    assert ["git", "reset", "--hard"] in git_cmds
    assert ["git", "checkout", "main"] in git_cmds
    assert ["git", "reset", "--hard", "origin/main"] in git_cmds
    assert ["git", "clean", "-fdx"] in git_cmds


def test_prepare_base_clone_error_message_includes_command(tmp_path, monkeypatch):
    """Test that error messages include the failing git command for debugging."""
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    repo_name = repo_full.split("/")[-1]
    base_dir = base_clone_root / repo_name

    monkeypatch.setattr(runner, "BASE_CLONE_ROOT", base_clone_root)
    monkeypatch.setattr(runner, "get_github_token", lambda: "test-token")

    base_dir.mkdir(parents=True)

    def mock_run_cmd_fail(cmd, cwd=None, check=True, timeout=None):
        """Mock run_cmd that fails on git clean with detailed error."""
        if cmd == ["git", "rev-parse", "--verify", "main"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        if cmd == ["git", "clean", "-fdx"]:
            exc = subprocess.CalledProcessError(
                1, cmd,
                stderr="fatal: not a git repository"
            )
            raise exc

        # Other commands succeed
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd_fail)

    # Verify error message includes command and stderr
    with pytest.raises(RuntimeError) as exc_info:
        runner.ensure_base_clone(repo_full)

    error_msg = str(exc_info.value)
    assert "Failed to reset base clone for jleechanorg/test-repo" in error_msg
    assert "git clean -fdx" in error_msg  # Command should be in error
    assert "fatal: not a git repository" in error_msg  # stderr should be in error


def test_prepare_base_clone_handles_detached_head(tmp_path, monkeypatch):
    """Test handling of detached HEAD state (common after automation runs)."""
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    repo_name = repo_full.split("/")[-1]
    base_dir = base_clone_root / repo_name

    monkeypatch.setattr(runner, "BASE_CLONE_ROOT", base_clone_root)
    monkeypatch.setattr(runner, "get_github_token", lambda: "test-token")

    base_dir.mkdir(parents=True)

    git_commands = []
    is_detached_head = True  # Simulate starting in detached HEAD state

    def mock_run_cmd(cmd, cwd=None, check=True, timeout=None):
        """Mock that simulates detached HEAD state."""
        git_commands.append(cmd)

        if cmd == ["git", "rev-parse", "--verify", "main"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        if cmd == ["git", "reset", "--hard"]:
            # reset --hard works in detached HEAD
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        if cmd == ["git", "checkout", "main"]:
            # After reset --hard, we can checkout main successfully
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd)

    # Should handle detached HEAD gracefully
    result = runner.ensure_base_clone(repo_full)
    assert result == base_dir

    # Verify reset --hard runs before checkout
    git_cmds = [cmd for cmd in git_commands if cmd[0] == "git"]
    assert ["git", "reset", "--hard"] in git_cmds
    assert ["git", "checkout", "main"] in git_cmds
