"""Tests for dirty git repository handling in orchestrated_pr_runner.

This test file validates that ensure_base_clone handles dirty git repositories
correctly by forcing the default branch back to the remote tracking branch.
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
    2. A normal checkout would fail with "local changes would be overwritten"
    3. Fix: Force `git checkout -B main origin/main`
    """
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    owner, repo_name = repo_full.split("/", 1)
    base_dir = base_clone_root / owner / repo_name

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

        # Detect default branch via symbolic-ref
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            return SimpleNamespace(returncode=0, stdout="refs/remotes/origin/main", stderr="")

        if cmd == ["git", "checkout", "--force", "-B", "main", "origin/main"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # All other git commands succeed
        if cmd[0] == "git":
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # Non-git commands
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd)

    # Run ensure_base_clone
    result = runner.ensure_base_clone(repo_full)

    # Verify the fix: force the local default branch back to origin/main directly
    assert result == base_dir

    # Extract just the git commands
    git_cmds = [cmd for cmd in git_commands if cmd[0] == "git"]

    # Verify full command sequence (key parts)
    assert ["git", "clean", "-fdx"] in git_cmds
    assert ["git", "checkout", "--force", "-B", "main", "origin/main"] in git_cmds
    assert ["git", "reset", "--hard"] not in git_cmds
    assert ["git", "checkout", "main"] not in git_cmds


def test_prepare_base_clone_error_message_includes_command(tmp_path, monkeypatch):
    """Test that error messages include the failing git command for debugging.

    With proactive recovery, the first failure triggers a re-clone. Only if
    the reset fails AGAIN after re-clone do we raise the error.
    """
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    owner, repo_name = repo_full.split("/", 1)
    base_dir = base_clone_root / owner / repo_name

    monkeypatch.setattr(runner, "BASE_CLONE_ROOT", base_clone_root)
    monkeypatch.setattr(runner, "get_github_token", lambda: "test-token")

    base_dir.mkdir(parents=True)

    # Track how many times git clean is called
    clean_call_count = [0]

    def mock_run_cmd_fail(cmd, cwd=None, check=True, timeout=None):
        """Mock run_cmd that fails on git clean persistently (even after re-clone)."""
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            return SimpleNamespace(returncode=0, stdout="refs/remotes/origin/main", stderr="")

        if cmd == ["git", "clean", "-fdx"]:
            clean_call_count[0] += 1
            # Fail both times - first attempt AND retry after re-clone
            exc = subprocess.CalledProcessError(
                1, cmd,
                stderr="fatal: not a git repository"
            )
            raise exc

        # git clone succeeds (for re-clone attempt)
        if cmd[0] == "git" and cmd[1] == "clone":
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        # Other commands succeed
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd_fail)

    # Verify error message includes command and stderr (after retry fails)
    with pytest.raises(RuntimeError) as exc_info:
        runner.ensure_base_clone(repo_full)

    error_msg = str(exc_info.value)
    assert "Failed to reset base clone for jleechanorg/test-repo" in error_msg
    assert "even after re-clone" in error_msg  # New: indicates proactive recovery was attempted
    assert "fatal: not a git repository" in error_msg  # stderr should be in error
    # Verify proactive recovery was attempted (clean called twice: initial + retry)
    assert clean_call_count[0] == 2, f"Expected 2 clean attempts, got {clean_call_count[0]}"


def test_prepare_base_clone_handles_detached_head(tmp_path, monkeypatch):
    """Test handling of detached HEAD state (common after automation runs)."""
    base_clone_root = tmp_path / "pr-orch-bases"
    repo_full = "jleechanorg/test-repo"
    owner, repo_name = repo_full.split("/", 1)
    base_dir = base_clone_root / owner / repo_name

    monkeypatch.setattr(runner, "BASE_CLONE_ROOT", base_clone_root)
    monkeypatch.setattr(runner, "get_github_token", lambda: "test-token")

    base_dir.mkdir(parents=True)

    git_commands = []
    is_detached_head = True  # Simulate starting in detached HEAD state

    def mock_run_cmd(cmd, cwd=None, check=True, timeout=None):
        """Mock that simulates detached HEAD state."""
        git_commands.append(cmd)

        # Detect default branch via symbolic-ref
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            return SimpleNamespace(returncode=0, stdout="refs/remotes/origin/main", stderr="")

        if cmd == ["git", "checkout", "--force", "-B", "main", "origin/main"]:
            # Force checkout works even from detached HEAD
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", mock_run_cmd)

    # Should handle detached HEAD gracefully
    result = runner.ensure_base_clone(repo_full)
    assert result == base_dir

    # Verify detached HEAD is resolved with one forced remote checkout
    git_cmds = [cmd for cmd in git_commands if cmd[0] == "git"]
    assert ["git", "checkout", "--force", "-B", "main", "origin/main"] in git_cmds
    assert ["git", "reset", "--hard"] not in git_cmds
