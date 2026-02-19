import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.jleechanorg_pr_automation import orchestrated_pr_runner

def test_dispatch_agent_includes_worktree_fix_and_push_refspec(tmp_path, monkeypatch):
    """Verify that worktree fallback uses -b and git push uses refspec."""
    orchestrated_pr_runner.WORKSPACE_ROOT_BASE = tmp_path
    
    # Mock dependencies
    monkeypatch.setattr(orchestrated_pr_runner, "kill_tmux_session_if_exists", lambda name: None)
    monkeypatch.setattr(orchestrated_pr_runner, "prepare_workspace_dir", lambda repo, name: None)
    monkeypatch.setattr(orchestrated_pr_runner, "get_automation_user", lambda: "test-user")
    
    # Capture task description
    captured_desc = []
    
    class FakeDispatcher:
        def analyze_task_and_create_agents(self, description, forced_cli=None, wrap_prompt: bool = False, **kwargs):
            captured_desc.append(description)
            return [{"id": "agent-spec", "name": "test-agent"}]
            
        def create_dynamic_agent(self, spec):
            return True
            
    pr = {
        "repo_full": "org/repo",
        "repo": "repo",
        "number": 123,
        "branch": "feature/test",
    }
    
    # Run
    orchestrated_pr_runner.dispatch_agent_for_pr(FakeDispatcher(), pr)
    
    assert len(captured_desc) == 1
    desc = captured_desc[0]
    local_branch = "fixpr_feature-test"
    remote_branch = "feature/test"
    workspace_root = str(tmp_path / "repo")
    
    # Bug #1: Worktree fallback must create the local branch with -b
    # Expected: "git worktree add -b {local_branch} {workspace_root}/pr-{pr_number}-rerun origin/{branch}"
    # Current (Buggy): "git worktree add {workspace_root}/pr-{pr_number}-rerun origin/{branch}"
    expected_worktree_cmd = f"git worktree add -b {local_branch} {workspace_root}/pr-123-rerun origin/{remote_branch}"
    
    if expected_worktree_cmd not in desc:
        print("\n=== DEBUG: Generated Task Description Snippet (Worktree) ===")
        for line in desc.splitlines():
            if "git worktree" in line:
                print(line)
        pytest.fail(f"Bug #1 Reproduction: 'git worktree add' command missing '-b {local_branch}'")

    # Bug #2: Merge conflict resolution must use explicit refspec in git push
    # Expected: "git add -A && git commit && git push origin {local_branch}:{branch}"
    # Current (Buggy): "git add -A && git commit && git push"
    
    expected_push_refspec = f"git push origin {local_branch}:{remote_branch}"
    
    # We need to find the push in the merge conflict section (STEP 6a or similar)
    # The description text has multiple steps. 
    # We want to ensure NO bare "git push" exists.
    
    if "&& git push\n" in desc:
         pytest.fail("Bug #2 Reproduction: Bare 'git push' detected (likely in merge resolution step).")
    
    # Also ensure the correct push IS present
    if expected_push_refspec not in desc:
        pytest.fail(f"Bug #2 Reproduction: Explicit refspec push '{expected_push_refspec}' not found.")
