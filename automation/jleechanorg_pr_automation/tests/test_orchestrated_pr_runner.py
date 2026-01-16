import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import requests

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


def test_has_failing_checks_uses_conclusion_field(monkeypatch):
    """Test that conclusion field is checked (authoritative checkpoint)."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "FAILURE", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_uses_state_fallback(monkeypatch):
    """Test that state field is used as fallback when conclusion is None."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "FAILED", "conclusion": None, "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
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


def test_has_failing_checks_conclusion_failure(monkeypatch):
    """Test FAILURE conclusion triggers True (authoritative checkpoint)."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "FAILURE", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_failure_fallback(monkeypatch):
    """Test FAILURE state triggers True when conclusion is None (check still running)."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "FAILURE", "conclusion": None, "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_cancelled(monkeypatch):
    """Test CANCELLED state triggers True."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "CANCELLED", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_timed_out(monkeypatch):
    """Test TIMED_OUT conclusion triggers True."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "TIMED_OUT", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_action_required(monkeypatch):
    """Test ACTION_REQUIRED conclusion triggers True."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "ACTION_REQUIRED", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_conclusion_success(monkeypatch):
    """Test SUCCESS conclusion returns False."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_conclusion_neutral(monkeypatch):
    """Test NEUTRAL conclusion returns False (not treated as failure)."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "NEUTRAL", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_state_success_with_failure_conclusion(monkeypatch):
    """Test that conclusion takes precedence over state."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "FAILURE", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_state_pending(monkeypatch):
    """Test PENDING state returns False."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "PENDING", "conclusion": None, "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_empty_state(monkeypatch):
    """Test empty/None conclusion returns False."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "", "workflow": "ci.yml"}
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_multiple_all_pass(monkeypatch):
    """Test multiple checks all passing returns False."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "ci.yml"},
            {"name": "lint", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "lint.yml"},
            {"name": "test", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "test.yml"},
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is False


def test_has_failing_checks_multiple_mixed(monkeypatch):
    """Test multiple checks with one failing returns True."""
    fake_pr_data = {
        "statusCheckRollup": [
            {"name": "ci", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "ci.yml"},
            {"name": "lint", "state": "COMPLETED", "conclusion": "FAILURE", "workflow": "lint.yml"},
            {"name": "test", "state": "COMPLETED", "conclusion": "SUCCESS", "workflow": "test.yml"},
        ]
    }
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
    )
    assert runner.has_failing_checks("org/repo", 1) is True


def test_has_failing_checks_empty_array(monkeypatch):
    """Test empty statusCheckRollup array returns False."""
    fake_pr_data = {"statusCheckRollup": []}
    monkeypatch.setattr(
        runner,
        "run_cmd",
        lambda *_, **__: SimpleNamespace(returncode=0, stdout=json.dumps(fake_pr_data), stderr=""),
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


def test_dispatch_agent_for_pr_accepts_model_for_all_clis(monkeypatch, tmp_path):
    """Test that model parameter is accepted for all CLIs, not just claude."""
    runner.WORKSPACE_ROOT_BASE = tmp_path
    
    captured_model = None
    
    class FakeDispatcher:
        def analyze_task_and_create_agents(self, task_description, forced_cli=None):
            return [{"id": "agent-spec"}]
        
        def create_dynamic_agent(self, spec):
            nonlocal captured_model
            captured_model = spec.get("model")
            return True
    
    monkeypatch.setattr(runner, "kill_tmux_session_if_exists", lambda name: None)
    monkeypatch.setattr(runner, "prepare_workspace_dir", lambda repo, name: None)
    
    pr = {
        "repo_full": "jleechanorg/test-repo",
        "repo": "test-repo",
        "number": 123,
        "branch": "test-branch",
    }
    
    # Test with gemini CLI
    success = runner.dispatch_agent_for_pr(
        FakeDispatcher(),
        pr,
        agent_cli="gemini",
        model="gemini-3-auto"
    )
    
    assert success, "Should succeed with gemini CLI and model parameter"
    assert captured_model == "gemini-3-auto", f"Expected 'gemini-3-auto', got '{captured_model}'"
    
    # Test with codex CLI
    captured_model = None
    success = runner.dispatch_agent_for_pr(
        FakeDispatcher(),
        pr,
        agent_cli="codex",
        model="composer-1"
    )
    
    assert success, "Should succeed with codex CLI and model parameter"
    assert captured_model == "composer-1", f"Expected 'composer-1', got '{captured_model}'"


def test_dispatch_agent_for_pr_rejects_invalid_model(monkeypatch, tmp_path):
    """Test that invalid model names are rejected."""
    runner.WORKSPACE_ROOT_BASE = tmp_path
    
    class FakeDispatcher:
        def analyze_task_and_create_agents(self, task_description, forced_cli=None):
            return [{"id": "agent-spec"}]
        
        def create_dynamic_agent(self, spec):
            return True
    
    monkeypatch.setattr(runner, "kill_tmux_session_if_exists", lambda name: None)
    monkeypatch.setattr(runner, "prepare_workspace_dir", lambda repo, name: None)
    
    pr = {
        "repo_full": "jleechanorg/test-repo",
        "repo": "test-repo",
        "number": 123,
        "branch": "test-branch",
    }
    
    # Test with invalid model name (contains space)
    success = runner.dispatch_agent_for_pr(
        FakeDispatcher(),
        pr,
        agent_cli="gemini",
        model="invalid model name"
    )
    
    assert not success, "Should reject invalid model name with spaces"
    
    # Test with invalid model name (contains special characters)
    success = runner.dispatch_agent_for_pr(
        FakeDispatcher(),
        pr,
        agent_cli="gemini",
        model="model@invalid"
    )
    
    assert not success, "Should reject invalid model name with special characters"


# Tests for Python GitHub API functions (post_pr_comment_python, cleanup_pending_reviews_python, get_github_token)


def test_get_github_token_from_env(monkeypatch):
    """Test get_github_token retrieves token from GITHUB_TOKEN env var."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")
    monkeypatch.setattr(runner, "subprocess", Mock())
    token = runner.get_github_token()
    assert token == "test-token-123"


def test_get_github_token_from_gh_cli(monkeypatch):
    """Test get_github_token falls back to gh CLI when env var not set."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    
    mock_result = SimpleNamespace(returncode=0, stdout="gh-token-456\n", stderr="")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: mock_result
    )
    
    token = runner.get_github_token()
    assert token == "gh-token-456"


def test_get_github_token_gh_cli_failure(monkeypatch):
    """Test get_github_token returns None when gh CLI fails."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    
    mock_result = SimpleNamespace(returncode=1, stdout="", stderr="error")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_, **__: mock_result
    )
    
    token = runner.get_github_token()
    assert token is None


def test_get_github_token_gh_cli_timeout(monkeypatch):
    """Test get_github_token handles gh CLI timeout gracefully."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired("gh", 5)
    
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    token = runner.get_github_token()
    assert token is None


def test_post_pr_comment_python_success(monkeypatch):
    """Test post_pr_comment_python successfully posts a comment."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.raise_for_status = Mock()
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.post", return_value=mock_response):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
            result = runner.post_pr_comment_python("owner/repo", 123, "Test comment")
            
            assert result is True
            mock_log.assert_any_call("✅ Posted comment to owner/repo#123")


def test_post_pr_comment_python_reply(monkeypatch):
    """Test post_pr_comment_python posts a threaded reply when in_reply_to is provided."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.raise_for_status = Mock()
    
    post_calls = []
    
    def mock_post(url, json=None, headers=None, timeout=None):
        post_calls.append({"url": url, "json": json, "headers": headers})
        return mock_response
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.post", side_effect=mock_post):
        result = runner.post_pr_comment_python("owner/repo", 123, "Reply comment", in_reply_to=456)
        
        assert result is True
        assert len(post_calls) == 1
        assert "pulls/123/comments" in post_calls[0]["url"]
        assert post_calls[0]["json"]["in_reply_to"] == 456
        assert post_calls[0]["json"]["body"] == "Reply comment"


def test_post_pr_comment_python_no_token(monkeypatch):
    """Test post_pr_comment_python returns False when no token is available."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        runner,
        "get_github_token",
        lambda: None
    )
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
        result = runner.post_pr_comment_python("owner/repo", 123, "Test comment")
        
        assert result is False
        mock_log.assert_any_call("⚠️ No GitHub token available for posting comment")


def test_post_pr_comment_python_api_error(monkeypatch):
    """Test post_pr_comment_python handles API errors gracefully."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.post", return_value=mock_response):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
            result = runner.post_pr_comment_python("owner/repo", 123, "Test comment")
            
            assert result is False
            mock_log.assert_any_call("⚠️ Failed to post comment: API Error")


def test_cleanup_pending_reviews_python_success(monkeypatch):
    """Test cleanup_pending_reviews_python successfully deletes pending reviews."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    # Mock reviews response
    reviews_response = [
        {
            "id": 1001,
            "state": "PENDING",
            "user": {"login": "automation-user"},
        },
        {
            "id": 1002,
            "state": "APPROVED",
            "user": {"login": "automation-user"},
        },
        {
            "id": 1003,
            "state": "PENDING",
            "user": {"login": "other-user"},
        },
        {
            "id": 1004,
            "state": "PENDING",
            "user": {"login": "automation-user"},
        },
    ]
    
    mock_get_response = Mock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = reviews_response
    mock_get_response.raise_for_status = Mock()
    
    mock_delete_response = Mock()
    mock_delete_response.status_code = 204
    
    get_calls = []
    delete_calls = []
    
    def mock_get(url, headers=None, timeout=None):
        get_calls.append({"url": url, "headers": headers})
        return mock_get_response
    
    def mock_delete(url, headers=None, timeout=None):
        delete_calls.append({"url": url, "headers": headers})
        return mock_delete_response
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.get", side_effect=mock_get):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.delete", side_effect=mock_delete):
            with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
                runner.cleanup_pending_reviews_python("owner/repo", 123, "automation-user")
                
                # Should fetch reviews once
                assert len(get_calls) == 1
                assert "pulls/123/reviews" in get_calls[0]["url"]
                
                # Should delete only pending reviews from automation-user (1001 and 1004)
                assert len(delete_calls) == 2
                assert "reviews/1001" in delete_calls[0]["url"] or "reviews/1001" in delete_calls[1]["url"]
                assert "reviews/1004" in delete_calls[0]["url"] or "reviews/1004" in delete_calls[1]["url"]
                
                mock_log.assert_any_call("✅ Deleted pending review 1001 for owner/repo#123")
                mock_log.assert_any_call("✅ Deleted pending review 1004 for owner/repo#123")


def test_cleanup_pending_reviews_python_no_pending(monkeypatch):
    """Test cleanup_pending_reviews_python handles no pending reviews gracefully."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    # Mock reviews response with no pending reviews from automation user
    reviews_response = [
        {
            "id": 1001,
            "state": "APPROVED",
            "user": {"login": "automation-user"},
        },
        {
            "id": 1002,
            "state": "PENDING",
            "user": {"login": "other-user"},
        },
    ]
    
    mock_get_response = Mock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = reviews_response
    mock_get_response.raise_for_status = Mock()
    
    delete_calls = []
    
    def mock_get(url, headers=None, timeout=None):
        return mock_get_response
    
    def mock_delete(url, headers=None, timeout=None):
        delete_calls.append(url)
        return Mock(status_code=204)
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.get", side_effect=mock_get):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.delete", side_effect=mock_delete):
            runner.cleanup_pending_reviews_python("owner/repo", 123, "automation-user")
            
            # Should not delete anything
            assert len(delete_calls) == 0


def test_cleanup_pending_reviews_python_no_token(monkeypatch):
    """Test cleanup_pending_reviews_python handles missing token gracefully."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        runner,
        "get_github_token",
        lambda: None
    )
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
        runner.cleanup_pending_reviews_python("owner/repo", 123, "automation-user")
        
        mock_log.assert_any_call("⚠️ No GitHub token available for cleanup")


def test_cleanup_pending_reviews_python_api_error(monkeypatch):
    """Test cleanup_pending_reviews_python handles API errors gracefully."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.get", return_value=mock_response):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
            runner.cleanup_pending_reviews_python("owner/repo", 123, "automation-user")
            
            mock_log.assert_any_call("Error cleaning up pending reviews: API Error")


def test_cleanup_pending_reviews_python_delete_failure(monkeypatch):
    """Test cleanup_pending_reviews_python handles delete failures gracefully."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    
    reviews_response = [
        {
            "id": 1001,
            "state": "PENDING",
            "user": {"login": "automation-user"},
        },
    ]
    
    mock_get_response = Mock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = reviews_response
    mock_get_response.raise_for_status = Mock()
    
    mock_delete_response = Mock()
    mock_delete_response.status_code = 500  # Server error
    
    with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.get", return_value=mock_get_response):
        with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.requests.delete", return_value=mock_delete_response):
            with patch("automation.jleechanorg_pr_automation.orchestrated_pr_runner.log") as mock_log:
                runner.cleanup_pending_reviews_python("owner/repo", 123, "automation-user")
                
                mock_log.assert_any_call("⚠️ Failed to delete review 1001: 500")
