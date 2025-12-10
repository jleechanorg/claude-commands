import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

import automation.jleechanorg_pr_automation.orchestrated_pr_runner as runner


def test_sanitize_workspace_name_includes_pr_number():
    assert runner.sanitize_workspace_name("feature/my-branch", 42) == "pr-42-feature-my-branch"
    assert runner.sanitize_workspace_name("!!!", 7) == "pr-7"


def test_query_recent_prs_invalid_json(monkeypatch):
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout="not json", stderr=""),
    )
    with pytest.raises(RuntimeError):
        runner.query_recent_prs(24)


def test_query_recent_prs_skips_incomplete_data(monkeypatch):
    response = {
        "data": {
            "search": {
                "nodes": [
                    {
                        "__typename": "PullRequest",
                        "number": None,
                        "repository": {"name": "repo", "nameWithOwner": "org/repo"},
                        "headRefName": "branch",
                        "headRefOid": "abc",
                        "updatedAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(response), stderr=""),
    )
    assert runner.query_recent_prs(24) == []


@pytest.mark.parametrize(
    "exc_factory, expected_fragment",
    [
        (
            lambda cmd, timeout: subprocess.CalledProcessError(
                1, cmd, stderr="fetch failed"
            ),
            "fetch failed",
        ),
        (
            subprocess.TimeoutExpired,
            "timed out",
        ),
    ],
)
def test_ensure_base_clone_recovers_from_fetch_failure(monkeypatch, tmp_path, capsys, exc_factory, expected_fragment):
    repo_full = "org/repo"
    runner.BASE_CLONE_ROOT = tmp_path
    base_dir = tmp_path / "repo"
    base_dir.mkdir()
    (base_dir / "stale.txt").write_text("stale")

    def fake_run_cmd(cmd, cwd=None, check=True, timeout=None):
        if cmd[:2] == ["git", "fetch"]:
            raise exc_factory(cmd, timeout)
        if cmd[:2] == ["git", "clone"]:
            base_dir.mkdir(parents=True, exist_ok=True)
            (base_dir / "fresh.txt").write_text("fresh")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)

    result = runner.ensure_base_clone(repo_full)

    assert result == base_dir
    assert not (base_dir / "stale.txt").exists()
    assert (base_dir / "fresh.txt").exists()

    output = capsys.readouterr().out
    assert "Fetch failed for org/repo" in output
    assert expected_fragment in output


def test_prepare_workspace_dir_cleans_worktree(monkeypatch, tmp_path):
    runner.WORKSPACE_ROOT_BASE = tmp_path
    target = tmp_path / "repo" / "ws"
    target.mkdir(parents=True)
    git_dir = tmp_path / "base" / ".git" / "worktrees" / "ws"
    git_dir.mkdir(parents=True)
    git_file = target / ".git"
    git_file.write_text(f"gitdir: {git_dir}")

    calls = []

    def fake_run_cmd(cmd, cwd=None, check=True, timeout=None):
        calls.append({"cmd": cmd, "cwd": cwd, "check": check, "timeout": timeout})
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)

    result = runner.prepare_workspace_dir("repo", "ws")

    assert result == target
    assert any("worktree" in " ".join(call["cmd"]) for call in calls)
    assert not target.exists()


def test_dispatch_agent_for_pr_validates_fields(tmp_path, monkeypatch):
    runner.WORKSPACE_ROOT_BASE = tmp_path

    class FakeDispatcher:
        def analyze_task_and_create_agents(self, _description, forced_cli=None):
            return []

        def create_dynamic_agent(self, _spec):
            return True

    assert runner.dispatch_agent_for_pr(FakeDispatcher(), {"repo_full": None}) is False


def test_dispatch_agent_for_pr_injects_workspace(monkeypatch, tmp_path):
    runner.WORKSPACE_ROOT_BASE = tmp_path

    created_specs = []
    captured_desc = []

    class FakeDispatcher:
        def analyze_task_and_create_agents(self, _description, forced_cli=None):
            captured_desc.append(_description)
            return [{"id": "agent"}]

        def create_dynamic_agent(self, spec):
            created_specs.append(spec)
            return True

    pr = {"repo_full": "org/repo", "repo": "repo", "number": 5, "branch": "feature/x"}
    assert runner.dispatch_agent_for_pr(FakeDispatcher(), pr)
    assert created_specs
    workspace_config = created_specs[0].get("workspace_config")
    assert workspace_config
    assert "pr-5" in workspace_config["workspace_name"]
    # commit prefix guidance should be present in task description with agent CLI
    assert captured_desc and "-automation-commit]" in captured_desc[0]


def test_has_failing_checks_uses_state_only(monkeypatch):
    fake_checks = [{"name": "ci", "state": "FAILED", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_kill_tmux_session_matches_variants(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(returncode=0, stdout="pr-14-foo_: 1 windows", stderr="")
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)

    runner.kill_tmux_session_if_exists("pr-14-foo.")

    assert any(cmd[:2] == ["tmux", "kill-session"] for cmd in calls)


# ============================================================================
# MATRIX TESTS - Phase 1: RED (Failing Tests)
# ============================================================================


# Matrix 1: has_failing_checks() - Additional State Tests
# ========================================================


def test_has_failing_checks_state_failure(monkeypatch):
    """Test FAILURE state (variant of FAILED) triggers True."""
    fake_checks = [{"name": "ci", "state": "FAILURE", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_cancelled(monkeypatch):
    """Test CANCELLED state triggers True."""
    fake_checks = [{"name": "ci", "state": "CANCELLED", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_timed_out(monkeypatch):
    """Test TIMED_OUT state triggers True."""
    fake_checks = [{"name": "ci", "state": "TIMED_OUT", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_action_required(monkeypatch):
    """Test ACTION_REQUIRED state triggers True."""
    fake_checks = [{"name": "ci", "state": "ACTION_REQUIRED", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_success(monkeypatch):
    """Test SUCCESS state returns False."""
    fake_checks = [{"name": "ci", "state": "SUCCESS", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_state_pending(monkeypatch):
    """Test PENDING state returns False."""
    fake_checks = [{"name": "ci", "state": "PENDING", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_empty_state(monkeypatch):
    """Test empty/None state returns False."""
    fake_checks = [{"name": "ci", "state": "", "workflow": "ci.yml"}]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_multiple_all_pass(monkeypatch):
    """Test multiple checks all passing returns False."""
    fake_checks = [
        {"name": "ci", "state": "SUCCESS", "workflow": "ci.yml"},
        {"name": "lint", "state": "SUCCESS", "workflow": "lint.yml"},
        {"name": "test", "state": "SUCCESS", "workflow": "test.yml"},
    ]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_multiple_mixed(monkeypatch):
    """Test multiple checks with one failing returns True."""
    fake_checks = [
        {"name": "ci", "state": "SUCCESS", "workflow": "ci.yml"},
        {"name": "lint", "state": "FAILED", "workflow": "lint.yml"},
        {"name": "test", "state": "SUCCESS", "workflow": "test.yml"},
    ]
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_empty_array(monkeypatch):
    """Test empty checks array returns False."""
    fake_checks = []
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_checks), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_api_error(monkeypatch):
    """Test API error (non-zero returncode) returns False."""
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=1, stdout="", stderr="API error"),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


# Matrix 2: kill_tmux_session_if_exists() - Additional Variant Tests
# ===================================================================


def test_kill_tmux_session_direct_match(monkeypatch):
    """Test direct session name match kills the session."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            # First call matches "pr-14-bar" directly
            if cmd[3] == "pr-14-bar":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)
    runner.kill_tmux_session_if_exists("pr-14-bar")

    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    assert any("pr-14-bar" in cmd for cmd in kill_calls)


def test_kill_tmux_session_underscore_variant(monkeypatch):
    """Test session name with trailing underscore matches."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            # Match "pr-14-baz_" directly
            if cmd[3] == "pr-14-baz_":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)
    runner.kill_tmux_session_if_exists("pr-14-baz_")

    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    assert any("pr-14-baz_" in cmd for cmd in kill_calls)


def test_kill_tmux_session_generic_name(monkeypatch):
    """Test generic session name without pr-prefix."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            # Match "session_" variant
            if cmd[3] == "session_":
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)
    runner.kill_tmux_session_if_exists("session")

    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    assert any("session_" in cmd for cmd in kill_calls)


def test_kill_tmux_session_multiple_pr_matches(monkeypatch):
    """Test multiple sessions with same PR number all get killed."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(
                returncode=0,
                stdout="pr-5-test-alpha: 1 windows\npr-5-test-beta: 1 windows\npr-5-extra: 1 windows",
                stderr="",
            )
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)
    runner.kill_tmux_session_if_exists("pr-5-test")

    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    # Should kill all three pr-5-* sessions
    assert len(kill_calls) >= 3


def test_kill_tmux_session_no_sessions_exist(monkeypatch):
    """Test graceful handling when no sessions exist."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="no server running")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)

    # Should not raise exception
    runner.kill_tmux_session_if_exists("nonexistent")

    # No kill commands should be issued
    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    assert len(kill_calls) == 0


def test_kill_tmux_session_tmux_ls_failure(monkeypatch):
    """Test graceful handling when tmux ls fails."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            raise Exception("tmux command failed")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)

    # Should not raise exception (graceful error handling)
    runner.kill_tmux_session_if_exists("test-session")


def test_kill_tmux_session_no_false_positive_pr_numbers(monkeypatch):
    """Test pr-1 does NOT kill pr-10, pr-11, pr-100 (substring matching bug fix)."""
    calls = []

    def fake_run_cmd(cmd, check=True, timeout=None, cwd=None):
        calls.append(cmd)
        if cmd[:2] == ["tmux", "has-session"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if cmd[:2] == ["tmux", "ls"]:
            # Session list contains pr-1-feature and pr-10-other, pr-100-test
            return SimpleNamespace(
                returncode=0,
                stdout="pr-1-feature: 1 windows\npr-10-other: 1 windows\npr-100-test: 1 windows",
                stderr="",
            )
        if cmd[:2] == ["tmux", "kill-session"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner, "run_cmd", fake_run_cmd)
    runner.kill_tmux_session_if_exists("pr-1-feature")

    kill_calls = [cmd for cmd in calls if cmd[:2] == ["tmux", "kill-session"]]
    killed_sessions = [cmd[3] for cmd in kill_calls if len(cmd) > 3]

    # Should ONLY kill pr-1-feature, NOT pr-10-other or pr-100-test
    assert "pr-1-feature" in killed_sessions, "Should kill pr-1-feature"
    assert "pr-10-other" not in killed_sessions, "Should NOT kill pr-10-other (false positive)"
    assert "pr-100-test" not in killed_sessions, "Should NOT kill pr-100-test (false positive)"


# Matrix 3: dispatch_agent_for_pr() - Additional Validation Tests
# ================================================================


def test_dispatch_agent_for_pr_missing_repo(tmp_path, monkeypatch):
    """Test validation fails when repo is None."""
    runner.WORKSPACE_ROOT_BASE = tmp_path

    class FakeDispatcher:
        def analyze_task_and_create_agents(self, _description, forced_cli=None):
            return []

        def create_dynamic_agent(self, _spec):
            return True

    pr = {"repo_full": "org/repo", "repo": None, "number": 5, "branch": "feature"}
    assert runner.dispatch_agent_for_pr(FakeDispatcher(), pr) is False


def test_dispatch_agent_for_pr_missing_number(tmp_path, monkeypatch):
    """Test validation fails when number is None."""
    runner.WORKSPACE_ROOT_BASE = tmp_path

    class FakeDispatcher:
        def analyze_task_and_create_agents(self, _description, forced_cli=None):
            return []

        def create_dynamic_agent(self, _spec):
            return True

    pr = {"repo_full": "org/repo", "repo": "repo", "number": None, "branch": "feature"}
    assert runner.dispatch_agent_for_pr(FakeDispatcher(), pr) is False


# ============================================================================
# RED PHASE: Test for workspace path collision bug (PR #318 root cause)
# ============================================================================


def test_multiple_repos_same_pr_number_no_collision(tmp_path, monkeypatch):
    """
    Test that PRs with the same number from different repos don't collide on workspace paths.

    BUG REPRODUCTION: dispatch_agent_for_pr() must create distinct workspace_config
    for PRs with same number from different repos.

    Real incident: PR #318 logs showed agent running in wrong repo directory.
    ROOT CAUSE: Need to verify full agent dispatch flow, not just workspace prep.

    This tests the COMPLETE dispatch flow to verify workspace_config uniqueness.
    """
    runner.WORKSPACE_ROOT_BASE = tmp_path

    # Track workspace configs that get passed to agents
    captured_configs = []

    class FakeDispatcher:
        def analyze_task_and_create_agents(self, _description, forced_cli=None):
            return [{"id": "agent-spec"}]

        def create_dynamic_agent(self, spec):
            captured_configs.append(spec.get("workspace_config"))
            return True

    # Mock kill_tmux_session_if_exists to avoid tmux calls in test
    monkeypatch.setattr(runner, "kill_tmux_session_if_exists", lambda name: None)

    # Simulate two PRs with same number from different repos
    pr_worldarchitect = {
        "repo_full": "jleechanorg/worldarchitect.ai",
        "repo": "worldarchitect.ai",
        "number": 318,
        "branch": "fix-doc-size",
        "title": "Fix doc size check"
    }

    pr_ai_universe = {
        "repo_full": "jleechanorg/ai_universe_frontend",
        "repo": "ai_universe_frontend",
        "number": 318,
        "branch": "fix-playwright-tests",
        "title": "Fix playwright tests"
    }

    # Dispatch agents for both PRs
    success1 = runner.dispatch_agent_for_pr(FakeDispatcher(), pr_worldarchitect)
    success2 = runner.dispatch_agent_for_pr(FakeDispatcher(), pr_ai_universe)

    assert success1, "Failed to dispatch agent for worldarchitect.ai PR #318"
    assert success2, "Failed to dispatch agent for ai_universe_frontend PR #318"
    assert len(captured_configs) == 2, f"Expected 2 workspace configs, got {len(captured_configs)}"

    config1 = captured_configs[0]
    config2 = captured_configs[1]

    # CRITICAL: workspace_root must be different for different repos
    assert config1["workspace_root"] != config2["workspace_root"], \
        f"BUG: workspace_root collision! Both: {config1['workspace_root']}"

    # Verify correct repo association
    assert "worldarchitect.ai" in config1["workspace_root"], \
        f"Config1 should contain 'worldarchitect.ai': {config1}"
    assert "ai_universe_frontend" in config2["workspace_root"], \
        f"Config2 should contain 'ai_universe_frontend': {config2}"
