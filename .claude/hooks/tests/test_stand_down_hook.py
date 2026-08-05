#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile

def run_cmd(cmd, env=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    return res.returncode, res.stdout, res.stderr

def main():
    print("=== Testing Stand-Down Enforcement Hook ===")
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_file = tf.name

    try:
        env = dict(os.environ, STAND_DOWN_FILE=temp_file)

        # 1. Initially no targets
        rc, out, err = run_cmd(f"$HOME/.claude/hooks/set-stand-down.sh list", env=env)
        assert "No active stand-down orders" in out, f"Expected no targets, got: {out}"

        # 2. Test guard on allowed command
        input_json = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push origin main"}})
        proc = subprocess.run(
            ["$HOME/.claude/hooks/stand-down-guard.sh"],
            input=input_json, capture_output=True, text=True, env=env
        )
        assert proc.returncode == 0, f"Expected 0 for allowed command, got {proc.returncode}"
        assert json.loads(proc.stdout).get("decision") == "allow"

        # 3. Add stand-down target
        rc, out, err = run_cmd(f"$HOME/.claude/hooks/set-stand-down.sh add feature-blocked \"Operator explicit stop order\"", env=env)
        assert rc == 0, f"Failed to add target: {err}"
        assert "feature-blocked" in out

        # 4. Test guard on blocked command (pushing to feature-blocked)
        input_json_blocked = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push origin feature-blocked"}})
        proc_blocked = subprocess.run(
            ["$HOME/.claude/hooks/stand-down-guard.sh"],
            input=input_json_blocked, capture_output=True, text=True, env=env
        )
        assert proc_blocked.returncode == 2, f"Expected 2 (blocked) for stand-down target, got {proc_blocked.returncode}"
        res = json.loads(proc_blocked.stdout)
        assert res.get("decision") == "block", f"Expected decision=block, got {res}"
        assert "STAND-DOWN ENFORCEMENT BLOCKED" in res.get("reason", ""), f"Unexpected reason: {res}"
        print("✓ Successfully blocked push to stand-down branch 'feature-blocked'")

        # 5. Test guard on gh pr edit targeting feature-blocked
        input_json_pr = json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh pr edit feature-blocked --body 'update'"}})
        proc_pr = subprocess.run(
            ["$HOME/.claude/hooks/stand-down-guard.sh"],
            input=input_json_pr, capture_output=True, text=True, env=env
        )
        assert proc_pr.returncode == 2, f"Expected 2 (blocked) for gh pr edit, got {proc_pr.returncode}"
        print("✓ Successfully blocked gh pr edit on stand-down target")

        # 6. Remove stand-down target
        rc, out, err = run_cmd(f"$HOME/.claude/hooks/set-stand-down.sh remove feature-blocked", env=env)
        assert rc == 0, f"Failed to remove target: {err}"

        # 7. Verify command is now allowed
        proc_allowed_now = subprocess.run(
            ["$HOME/.claude/hooks/stand-down-guard.sh"],
            input=input_json_blocked, capture_output=True, text=True, env=env
        )
        assert proc_allowed_now.returncode == 0, f"Expected 0 after removal, got {proc_allowed_now.returncode}"
        print("✓ Successfully unblocked command after removing target")

        print("\nALL STAND-DOWN HOOK TESTS PASSED! STARTS CLEAN!")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()
