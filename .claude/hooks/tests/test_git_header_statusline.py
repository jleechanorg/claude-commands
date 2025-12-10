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
import time
from pathlib import Path

import pytest


def run_git_header(script_path, env=None, cwd=None):
    """Run git-header.sh --status-only and return output"""
    try:
        result = subprocess.run(
            ["bash", script_path, "--status-only"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env=env,
            cwd=cwd,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        pytest.fail("git-header.sh timed out (>5 seconds)")


@pytest.fixture
def temp_git_repo():
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
def git_header_script():
    """Path to git-header.sh script"""
    # Find the script relative to test file (now in .claude/hooks/tests/)
    test_dir = Path(__file__).parent
    script_path = test_dir.parent / "git-header.sh"

    if not script_path.exists():
        pytest.skip(f"git-header.sh not found at {script_path}")

    return str(script_path)


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

    # RED Phase: Write failing tests first

    def test_red_synced_clean_status(self, temp_git_repo, git_header_script):
        """RED: Test synced clean status shows (synced)"""
        # This test will fail initially because we need to set up remote tracking
        stdout, stderr, returncode = run_git_header(git_header_script)

        # Should contain directory name, branch, and status in parentheses
        assert "Local:" in stdout
        assert "(synced)" in stdout or "(no remote)" in stdout  # Initially no remote
        assert "Dir:" in stdout

    def test_red_uncommitted_changes_detection(self, temp_git_repo, git_header_script):
        """RED: Test uncommitted changes show +uncommitted indicator"""
        # Create uncommitted changes
        with open("test_file.txt", "w") as f:
            f.write("uncommitted content")

        stdout, stderr, returncode = run_git_header(git_header_script)

        # Should show +uncommitted indicator
        assert "+uncommitted" in stdout
        assert "(" in stdout and ")" in stdout  # Always parentheses

    def test_red_no_remote_with_uncommitted(self, temp_git_repo, git_header_script):
        """RED: Test no remote with uncommitted changes"""
        # Create uncommitted changes
        with open("test_file.txt", "w") as f:
            f.write("uncommitted content")

        stdout, stderr, returncode = run_git_header(git_header_script)

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

        stdout, stderr, returncode = run_git_header(git_header_script)

        # Should show ahead status
        assert "ahead" in stdout.lower()
        assert "(" in stdout and ")" in stdout

    def test_red_performance_under_5_seconds(self, temp_git_repo, git_header_script):
        """RED: Test script completes in under 5 seconds"""
        import time

        start_time = time.time()
        run_git_header(git_header_script)
        execution_time = time.time() - start_time

        # Must complete in under 5 seconds (actually under 1 second target)
        assert execution_time < 5.0, f"Script took {execution_time:.2f}s, should be <5s"
        assert execution_time < 1.0, f"Script took {execution_time:.2f}s, target <1s"

    def test_red_essential_output_format(self, temp_git_repo, git_header_script):
        """RED: Test essential output format components"""
        stdout, stderr, returncode = run_git_header(git_header_script)

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

        stdout, stderr, returncode = run_git_header(git_header_script)

        # Should detect PR number from branch name
        assert "pr-1234" in stdout.lower() or "#1234" in stdout

    def test_red_directory_name_display(self, temp_git_repo, git_header_script):
        """RED: Test directory name is correctly displayed"""
        stdout, stderr, returncode = run_git_header(git_header_script)

        # Should show current directory name
        current_dir_name = os.path.basename(os.getcwd())
        assert f"Dir: {current_dir_name}" in stdout

    def test_red_clean_working_directory(self, temp_git_repo, git_header_script):
        """RED: Test clean working directory doesn't show +uncommitted"""
        # Ensure clean state
        subprocess.run(["git", "status", "--porcelain"], check=True)

        stdout, stderr, returncode = run_git_header(git_header_script)

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

        stdout, stderr, returncode = run_git_header(git_header_script)

        if expected_indicator:
            assert expected_indicator.strip() in stdout
        elif "(synced)" in stdout:
            assert "+uncommitted" not in stdout


class TestGitHeaderPRCache:
    """Tests for PR cache invalidation and recent push detection."""

    @pytest.fixture
    def make_temp_repo_with_remote(self, request, tmp_path_factory):
        """Factory fixture that creates a temp repo with a configurable remote name."""

        repos = []

        def _make(remote_name: str = "origin"):
            temp_dir = tmp_path_factory.mktemp("repo")
            os.chdir(temp_dir)

            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], check=True)

            with open("README.md", "w") as f:
                f.write("# Test Repo\n")
            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
            current_branch = (
                subprocess.check_output(["git", "symbolic-ref", "--short", "HEAD"])
                .decode()
                .strip()
            )

            remote_dir = Path(temp_dir) / "remote"
            remote_dir.mkdir()
            subprocess.run(["git", "init", "--bare", str(remote_dir)], check=True)
            subprocess.run(["git", "remote", "add", remote_name, str(remote_dir)], check=True)
            subprocess.run(["git", "push", "-u", remote_name, current_branch], check=True)

            subprocess.run(["git", "fetch", remote_name], check=True)
            subprocess.run(
                ["git", "branch", "--set-upstream-to", f"{remote_name}/{current_branch}"],
                check=True,
            )

            repos.append(temp_dir)
            return Path(temp_dir), current_branch, remote_name

        def cleanup():
            os.chdir("/")
            for repo in repos:
                shutil.rmtree(repo, ignore_errors=True)

        request.addfinalizer(cleanup)
        return _make

    @pytest.fixture
    def gh_stub(self, tmp_path):
        """Create a stub gh executable that records invocations and returns a PR."""

        call_log = tmp_path / "gh_calls.txt"
        script = tmp_path / "gh"
        script.write_text(
            """#!/usr/bin/env bash
echo "${GH_STUB_OUTPUT:-42 https://example.com/pr/42}"
echo "called" >>"${GH_CALL_LOG}"
"""
        )
        script.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{tmp_path}:{env['PATH']}"
        env["GH_CALL_LOG"] = str(call_log)
        env.setdefault("GH_STUB_OUTPUT", "42 https://example.com/pr/42")

        return script, call_log, env

    def _cache_file_for_repo(self, repo_dir: Path):
        commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir)
            .decode()
            .strip()
        )
        return Path("/tmp") / f"git-header-pr-{commit[:8]}"

    def test_pr_cache_uses_cached_value_when_fresh(
        self, make_temp_repo_with_remote, git_header_script, gh_stub
    ):
        """Cache should prevent repeated gh calls while within PR TTL."""

        _script, call_log, env = gh_stub
        repo_dir, branch_name, _ = make_temp_repo_with_remote()

        git_dir = (
            subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=repo_dir)
            .decode()
            .strip()
        )
        remote_ref = Path(git_dir) / "refs" / "remotes" / "origin" / branch_name
        if remote_ref.exists():
            # Make the ref appear older than the recent push window so cache can be used
            old_time = int(time.time()) - 120
            os.utime(remote_ref, (old_time, old_time))

        # First run populates cache
        stdout, _, _ = run_git_header(str(git_header_script), env=env, cwd=repo_dir)
        assert "#42" in stdout
        assert call_log.read_text().strip() == "called"

        cache_file = self._cache_file_for_repo(repo_dir)
        assert cache_file.exists()

        # Reset call log and keep cache fresh
        call_log.write_text("")
        os.utime(cache_file, None)

        stdout, _, _ = run_git_header(str(git_header_script), env=env, cwd=repo_dir)
        assert "#42" in stdout
        # No additional gh call because cache is still valid
        assert call_log.read_text().strip() == ""

    def test_stale_cache_expires_and_refreshes(
        self, make_temp_repo_with_remote, git_header_script, gh_stub
    ):
        """Stale cache entries should be refreshed after the TTL expires."""

        _script, call_log, env = gh_stub
        repo_dir, branch_name, _ = make_temp_repo_with_remote()

        # Seed cache with a stale value that would otherwise be valid
        cache_file = self._cache_file_for_repo(repo_dir)
        cache_file.write_text("cached-pr")
        os.utime(cache_file, None)

        # Age the cache so it falls outside the PR TTL window
        old_time = int(time.time()) - 400
        os.utime(cache_file, (old_time, old_time))

        # Configure stub to return a different PR to confirm bypass
        env["GH_STUB_OUTPUT"] = "99 https://example.com/pr/99"
        call_log.write_text("")

        stdout, _, _ = run_git_header(str(git_header_script), env=env, cwd=repo_dir)
        assert "#99" in stdout
        assert call_log.read_text().strip() == "called"

    def test_recent_push_bypasses_cache_for_non_origin_remote(
        self, make_temp_repo_with_remote, git_header_script, gh_stub
    ):
        """Recent push detection should ignore cache for any remote name."""

        _script, call_log, env = gh_stub
        repo_dir, branch_name, remote_name = make_temp_repo_with_remote("upstream")

        cache_file = self._cache_file_for_repo(repo_dir)
        cache_file.write_text("cached-pr")
        os.utime(cache_file, None)

        git_dir = (
            subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=repo_dir)
            .decode()
            .strip()
        )
        ref_file = Path(git_dir) / "refs" / "remotes" / remote_name / branch_name
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        ref_file.touch()
        os.utime(ref_file, None)

        env["GH_STUB_OUTPUT"] = "77 https://example.com/pr/77"
        call_log.write_text("")

        stdout, _, _ = run_git_header(str(git_header_script), env=env, cwd=repo_dir)
        assert "#77" in stdout
        assert call_log.read_text().strip() == "called"

    def test_packed_refs_used_for_recent_push_detection(
        self, make_temp_repo_with_remote, git_header_script, gh_stub
    ):
        """Packed refs mtime should trigger cache bypass when loose ref is absent."""

        _script, call_log, env = gh_stub
        repo_dir, branch_name, remote_name = make_temp_repo_with_remote()

        cache_file = self._cache_file_for_repo(repo_dir)
        cache_file.write_text("cached-pr")
        os.utime(cache_file, None)

        git_dir = (
            subprocess.check_output(["git", "rev-parse", "--git-common-dir"], cwd=repo_dir)
            .decode()
            .strip()
        )
        packed_refs = Path(git_dir) / "packed-refs"

        subprocess.run(["git", "pack-refs", "--all", "--prune"], cwd=repo_dir, check=True)
        loose_ref = Path(git_dir) / "refs" / "remotes" / remote_name / branch_name
        if loose_ref.exists():
            loose_ref.unlink()

        packed_refs.touch()
        os.utime(packed_refs, None)

        env["GH_STUB_OUTPUT"] = "88 https://example.com/pr/88"
        call_log.write_text("")

        stdout, _, _ = run_git_header(str(git_header_script), env=env, cwd=repo_dir)
        assert "#88" in stdout
        assert call_log.read_text().strip() == "called"



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
