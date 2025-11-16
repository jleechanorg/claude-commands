#!/usr/bin/env python3
"""
TDD Tests for git-header.sh statusline functionality

Test-Driven Development (Red → Green → Refactor) for git statusline
Tests the essential functionality: dir, branch, sync status, uncommitted changes

Matrix Coverage:
- Sync states: synced, ahead, behind, diverged, no remote
- Uncommitted changes: clean, uncommitted
- Branch patterns: normal, PR-numbered branches
- Remote states: upstream, no upstream
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestGitHeaderStatusline:
    """
    TDD Test Matrix for git-header statusline

    ## Test Matrix: Git Status × Uncommitted Changes
    | Git Status | Clean | Uncommitted | Expected Output |
    |------------|-------|-------------|-----------------|
    | synced     | ✓     | ❌          | (synced) |
    | synced     | ❌    | ✓           | (synced +uncommitted) |
    | ahead 2    | ✓     | ❌          | (ahead 2) |
    | ahead 2    | ❌    | ✓           | (ahead 2 +uncommitted) |
    | behind 1   | ✓     | ❌          | (behind 1) |
    | behind 1   | ❌    | ✓           | (behind 1 +uncommitted) |
    | diverged   | ✓     | ❌          | (diverged +2 -1) |
    | diverged   | ❌    | ✓           | (diverged +2 -1 +uncommitted) |
    | no remote  | ✓     | ❌          | (no remote) |
    | no remote  | ❌    | ✓           | (no remote +uncommitted) |
    """

    @pytest.fixture
    def temp_git_repo(self):
        """Create temporary git repository for testing"""
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)

        # Create initial commit
        with open("README.md", "w") as f:
            f.write("# Test Repo\n")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

        yield temp_dir

        # Cleanup
        os.chdir("/")
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def git_header_script(self):
        """Path to git-header.sh script"""
        # Find the script relative to test file (now in .claude/hooks/tests/)
        test_dir = Path(__file__).parent
        script_path = test_dir.parent / "git-header.sh"

        if not script_path.exists():
            pytest.skip(f"git-header.sh not found at {script_path}")

        return str(script_path)

    def run_git_header(self, script_path):
        """Run git-header.sh --status-only and return output"""
        try:
            result = subprocess.run(
                ["bash", script_path, "--status-only"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            pytest.fail("git-header.sh timed out (>5 seconds)")

    # RED Phase: Write failing tests first

    def test_red_synced_clean_status(self, temp_git_repo, git_header_script):
        """RED: Test synced clean status shows (synced)"""
        # This test will fail initially because we need to set up remote tracking
        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should contain directory name, branch, and status in parentheses
        assert "Local:" in stdout
        assert "(synced)" in stdout or "(no remote)" in stdout  # Initially no remote
        assert "Dir:" in stdout

    def test_red_uncommitted_changes_detection(self, temp_git_repo, git_header_script):
        """RED: Test uncommitted changes show +uncommitted indicator"""
        # Create uncommitted changes
        with open("test_file.txt", "w") as f:
            f.write("uncommitted content")

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should show +uncommitted indicator
        assert "+uncommitted" in stdout
        assert "(" in stdout and ")" in stdout  # Always parentheses

    def test_red_no_remote_with_uncommitted(self, temp_git_repo, git_header_script):
        """RED: Test no remote with uncommitted changes"""
        # Create uncommitted changes
        with open("test_file.txt", "w") as f:
            f.write("uncommitted content")

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should show both no remote and uncommitted
        assert "(no remote +uncommitted)" in stdout

    def test_red_ahead_commits_status(self, temp_git_repo, git_header_script):
        """RED: Test ahead commits show (ahead N)"""
        # Set up remote tracking
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/test/test.git"],
            check=True,
        )
        subprocess.run(["git", "branch", "--set-upstream-to=origin/main"], check=True)

        # Create local commits ahead of remote (simulate)
        with open("local_commit.txt", "w") as f:
            f.write("local change")
        subprocess.run(["git", "add", "local_commit.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "Local commit"], check=True)

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should show ahead status
        assert "ahead" in stdout.lower()
        assert "(" in stdout and ")" in stdout

    def test_red_performance_under_5_seconds(self, temp_git_repo, git_header_script):
        """RED: Test script completes in under 5 seconds"""
        import time

        start_time = time.time()
        stdout, stderr, returncode = self.run_git_header(git_header_script)
        execution_time = time.time() - start_time

        # Must complete in under 5 seconds (actually under 1 second target)
        assert execution_time < 5.0, f"Script took {execution_time:.2f}s, should be <5s"
        assert execution_time < 1.0, f"Script took {execution_time:.2f}s, target <1s"

    def test_red_essential_output_format(self, temp_git_repo, git_header_script):
        """RED: Test essential output format components"""
        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Must contain all essential components
        assert "Dir:" in stdout
        assert "Local:" in stdout
        assert "Remote:" in stdout
        assert "PR:" in stdout
        assert "(" in stdout and ")" in stdout  # Status always in parentheses

    def test_red_pr_branch_pattern_detection(self, temp_git_repo, git_header_script):
        """RED: Test PR branch pattern detection (pr-123, feature/pr-456)"""
        # Create PR-style branch
        subprocess.run(["git", "checkout", "-b", "pr-1234"], check=True)

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should detect PR number from branch name
        assert "pr-1234" in stdout.lower() or "#1234" in stdout

    def test_red_directory_name_display(self, temp_git_repo, git_header_script):
        """RED: Test directory name is correctly displayed"""
        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should show current directory name
        current_dir_name = os.path.basename(os.getcwd())
        assert f"Dir: {current_dir_name}" in stdout

    def test_red_clean_working_directory(self, temp_git_repo, git_header_script):
        """RED: Test clean working directory doesn't show +uncommitted"""
        # Ensure clean state
        subprocess.run(["git", "status", "--porcelain"], check=True)

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        # Should NOT show +uncommitted when clean
        if "synced" in stdout:
            assert "+uncommitted" not in stdout

    # Matrix test combining all scenarios
    @pytest.mark.parametrize(
        "uncommitted,expected_indicator", [(False, ""), (True, " +uncommitted")]
    )
    def test_red_matrix_uncommitted_scenarios(
        self, temp_git_repo, git_header_script, uncommitted, expected_indicator
    ):
        """RED: Matrix test for uncommitted change scenarios"""
        if uncommitted:
            with open("uncommitted.txt", "w") as f:
                f.write("test")

        stdout, stderr, returncode = self.run_git_header(git_header_script)

        if expected_indicator:
            assert expected_indicator.strip() in stdout
        elif "(synced)" in stdout:
            assert "+uncommitted" not in stdout


# Integration test for real script behavior
class TestGitHeaderIntegration:
    """Integration tests running actual git-header.sh script"""

    def test_red_script_exists_and_executable(self):
        """RED: Test git-header.sh script exists and is executable"""
        test_dir = Path(__file__).parent
        script_path = test_dir.parent / "git-header.sh"

        assert script_path.exists(), f"git-header.sh not found at {script_path}"
        assert os.access(
            script_path, os.X_OK
        ), f"git-header.sh not executable at {script_path}"

    def test_red_status_only_flag_supported(self):
        """RED: Test --status-only flag is supported"""
        test_dir = Path(__file__).parent
        script_path = test_dir.parent / "git-header.sh"

        if script_path.exists():
            result = subprocess.run(
                ["bash", str(script_path), "--status-only"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # Should not error out
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            assert result.stdout.strip(), "No output from --status-only"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
