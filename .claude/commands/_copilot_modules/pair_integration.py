#!/usr/bin/env python3
"""
/pair integration module for /copilot command.

Provides functions to:
- Determine when to trigger /pair
- Generate task specs for /pair agents
- Collect results from /pair sessions
- Enhance responses.json with pair metadata
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional


def load_copilot_config(env: Dict[str, str]) -> Dict:
    """Load copilot configuration from environment variables.

    Args:
        env: Environment variables dict

    Returns:
        Configuration dict with pair integration settings
    """
    return {
        "use_pair": env.get("COPILOT_USE_PAIR", "false").lower() == "true",
        "pair_min_severity": env.get("COPILOT_PAIR_MIN_SEVERITY", "CRITICAL"),
        "pair_important": env.get("COPILOT_PAIR_IMPORTANT", "false").lower() == "true",
        "pair_coder": env.get("COPILOT_PAIR_CODER", "claude"),
        "pair_verifier": env.get("COPILOT_PAIR_VERIFIER", "codex"),
        "pair_timeout": int(env.get("COPILOT_PAIR_TIMEOUT", "600"))
    }


def should_trigger_pair(comment: Dict, env: Dict[str, str]) -> bool:
    """Determine if /pair should be triggered for a comment.

    Args:
        comment: Comment dict with 'category' field
        env: Environment variables

    Returns:
        True if /pair should be triggered, False otherwise
    """
    config = load_copilot_config(env)

    if not config["use_pair"]:
        return False

    category = comment.get("category", "").upper()
    min_severity = config["pair_min_severity"].upper()

    # Severity hierarchy: CRITICAL > BLOCKING > IMPORTANT > ROUTINE
    severity_levels = {"CRITICAL": 4, "BLOCKING": 3, "IMPORTANT": 2, "ROUTINE": 1}
    
    category_level = severity_levels.get(category, 0)
    min_level = severity_levels.get(min_severity, 4)  # Default to CRITICAL if invalid

    # CRITICAL and BLOCKING always trigger when /pair integration is enabled.
    if category in {"CRITICAL", "BLOCKING"}:
        return True

    # IMPORTANT triggers if pair_important is enabled OR if it meets min_severity
    if category == "IMPORTANT":
        return config["pair_important"] or category_level >= min_level

    # Trigger if category meets or exceeds minimum severity
    if category_level >= min_level:
        return True

    return False


def generate_pair_task_spec(comment: Dict, pr_context: Dict) -> str:
    """Generate task specification for /pair agents.

    Args:
        comment: Comment dict with id, category, body, path, line, etc.
        pr_context: PR metadata (number, branch, base, url)

    Returns:
        Markdown task specification string
    """
    comment_id = comment.get("id", "unknown")
    category = comment.get("category", "UNKNOWN")
    body = comment.get("body", "No description")
    path = comment.get("path", "")
    line = comment.get("line", "")

    pr_number = pr_context.get("number", "unknown")
    branch = pr_context.get("branch", "unknown")
    base = pr_context.get("base", "main")
    url = pr_context.get("url", "")

    file_line = f"{path}:{line}" if path and line else path or "unknown"

    task_spec = f"""# Fix PR #{pr_number} Comment #{comment_id}

## Comment Details
**Category:** {category}
**File:** {file_line}
**Reviewer:** {comment.get('author', 'unknown')}

## Issue Description
{body}

## PR Context
- **Branch:** {branch}
- **Base:** {base}
- **PR URL:** {url}

## Acceptance Criteria
- [ ] Issue described in comment is resolved
- [ ] No regressions introduced
- [ ] Tests pass
- [ ] Code follows existing patterns in the codebase

## Verification
Verifier agent must:
1. Review the fix against the comment description
2. Run appropriate tests to verify the fix
3. Verify no regressions in affected modules
4. Confirm code quality matches repository standards
"""

    return task_spec


def collect_pair_results(session_dir: Path) -> Dict:
    """Collect results from /pair session.

    Args:
        session_dir: Path to /pair session directory with result files

    Returns:
        Dict with pair session results (commit, files_modified, status, test_results, etc.)
    """
    results = {
        "session_id": session_dir.name,
        "status": "UNKNOWN",
        "commit": "",
        "files_modified": [],
        "tests_added": [],
        "duration_seconds": 0,
        "test_results": {"passed": 0, "failed": 0, "output": ""}
    }

    # Prefer the current pair monitor artifact.
    status_json_file = session_dir / "status.json"
    if status_json_file.exists():
        try:
            status_data = json.loads(status_json_file.read_text())
            coder_status = str(status_data.get("coder_status") or "").lower()
            verifier_status = str(status_data.get("verifier_status") or "").lower()

            if coder_status == "completed" and verifier_status == "completed":
                results["status"] = "VERIFICATION_COMPLETE"
            elif {"error", "failed"} & {coder_status, verifier_status}:
                results["status"] = "VERIFICATION_FAILED"
            elif "timeout" in {coder_status, verifier_status}:
                results["status"] = "TIMEOUT"
            elif coder_status or verifier_status:
                results["status"] = "IN_PROGRESS"
        except (OSError, json.JSONDecodeError, AttributeError):
            pass

    # Load agent result artifacts from orchestration output within session directory.
    # This ensures we only read artifacts belonging to this specific session.
    artifact_patterns = [
        session_dir.glob("*_results*.json"),
        session_dir.glob("*.result.json"),
    ]
    latest_artifact_ts = -1.0
    for pattern in artifact_patterns:
        for artifact_path in pattern:
            try:
                mtime = artifact_path.stat().st_mtime
                if mtime <= latest_artifact_ts:
                    continue
                artifact_data = json.loads(artifact_path.read_text())
                # Ensure artifact is a dict before using .get()
                if not isinstance(artifact_data, dict):
                    continue
            except (OSError, json.JSONDecodeError, ValueError):
                continue

            latest_artifact_ts = mtime
            if results["status"] == "UNKNOWN":
                artifact_status = str(artifact_data.get("status", "")).lower()
                if artifact_status == "completed":
                    results["status"] = "VERIFICATION_COMPLETE"
                elif artifact_status in {"failed", "error"}:
                    results["status"] = "VERIFICATION_FAILED"

            commit = str(artifact_data.get("commit") or "").strip()
            if commit:
                results["commit"] = commit

            files_modified = artifact_data.get("files_modified") or artifact_data.get("files_changed")
            if isinstance(files_modified, list):
                results["files_modified"] = [str(path) for path in files_modified if str(path).strip()]

            tests_added = artifact_data.get("tests_added")
            if isinstance(tests_added, list):
                results["tests_added"] = [str(path) for path in tests_added if str(path).strip()]

            passed = artifact_data.get("tests_passed")
            failed = artifact_data.get("tests_failed")
            if isinstance(passed, int):
                results["test_results"]["passed"] = passed
            if isinstance(failed, int):
                results["test_results"]["failed"] = failed

            output_text = artifact_data.get("test_output")
            if isinstance(output_text, str) and output_text.strip():
                results["test_results"]["output"] = output_text

            duration = artifact_data.get("duration_seconds")
            if isinstance(duration, int):
                results["duration_seconds"] = duration

    # Backward compatibility for legacy pair_*.txt artifacts.
    status_file = session_dir / "pair_status.txt"
    if results["status"] == "UNKNOWN" and status_file.exists():
        legacy_status = status_file.read_text().strip()
        if legacy_status:
            results["status"] = legacy_status

    commit_file = session_dir / "pair_commit.txt"
    if not results["commit"] and commit_file.exists():
        results["commit"] = commit_file.read_text().strip()

    files_file = session_dir / "pair_files.txt"
    if not results["files_modified"] and files_file.exists():
        files_text = files_file.read_text().strip()
        if files_text:
            results["files_modified"] = files_text.split("\n")

    tests_file = session_dir / "pair_tests.txt"
    if not results["tests_added"] and tests_file.exists():
        tests_text = tests_file.read_text().strip()
        if tests_text:
            results["tests_added"] = tests_text.split("\n")

    test_output_file = session_dir / "pair_test_output.txt"
    if not results["test_results"]["output"] and test_output_file.exists():
        test_output = test_output_file.read_text()
        results["test_results"]["output"] = test_output

        if results["test_results"]["passed"] == 0:
            passed_match = re.search(r'(\d+) passed', test_output)
            if passed_match:
                results["test_results"]["passed"] = int(passed_match.group(1))

        if results["test_results"]["failed"] == 0:
            failed_match = re.search(r'(\d+) failed', test_output)
            if failed_match:
                results["test_results"]["failed"] = int(failed_match.group(1))

    duration_file = session_dir / "pair_duration.txt"
    if results["duration_seconds"] == 0 and duration_file.exists():
        try:
            results["duration_seconds"] = int(duration_file.read_text().strip())
        except ValueError:
            pass

    return results


def enhance_response_with_pair_data(base_response: Dict, pair_results: Dict) -> Dict:
    """Add pair metadata to response object.

    Args:
        base_response: Base response dict (comment_id, category, etc.)
        pair_results: Results from collect_pair_results()

    Returns:
        Enhanced response dict with pair_metadata
    """
    enhanced = base_response.copy()

    # Add top-level fields
    if pair_results.get("commit"):
        enhanced["commit"] = pair_results["commit"]

    if pair_results.get("files_modified"):
        enhanced["files_modified"] = pair_results["files_modified"]

    if pair_results.get("tests_added"):
        enhanced["tests_added"] = pair_results["tests_added"]

    # Add pair_metadata object
    enhanced["pair_metadata"] = {
        "session_id": pair_results.get("session_id", "unknown"),
        "status": pair_results.get("status", "UNKNOWN"),
        "duration_seconds": pair_results.get("duration_seconds", 0),
        "test_results": pair_results.get("test_results", {})
    }

    # Add verification status
    status = pair_results.get("status", "UNKNOWN")
    test_results = pair_results.get("test_results", {})
    passed = test_results.get("passed", 0)
    failed = test_results.get("failed", 0)

    # Check status first - only VERIFICATION_COMPLETE is a success status (allowlist approach)
    if status == "VERIFICATION_COMPLETE":
        # Only approve if status is explicitly VERIFICATION_COMPLETE
        if failed == 0 and passed > 0:
            enhanced["verification"] = f"✅ Tests pass ({passed} passed), verifier approved"
        elif failed > 0:
            enhanced["verification"] = f"⚠️ Tests: {passed} passed, {failed} failed"
        else:
            enhanced["verification"] = "✅ Verifier approved"
    else:
        # Any other status (TIMEOUT, VERIFICATION_FAILED, UNKNOWN, ERROR, etc.) is a failure
        enhanced["verification"] = f"❌ Pair session {status.lower().replace('_', ' ')}"

    return enhanced


if __name__ == "__main__":
    # Quick self-test
    import sys

    # Test config loading
    env = {"COPILOT_USE_PAIR": "true", "COPILOT_PAIR_IMPORTANT": "false"}
    config = load_copilot_config(env)
    assert config["use_pair"] == True
    assert config["pair_coder"] == "claude"
    print("✓ Config loading works")

    # Test trigger logic
    assert should_trigger_pair({"category": "CRITICAL"}, env) == True
    assert should_trigger_pair({"category": "ROUTINE"}, env) == False
    assert should_trigger_pair({"category": "IMPORTANT"}, env) == False
    print("✓ Trigger logic works")

    # Test task spec generation
    comment = {"id": "123", "category": "CRITICAL", "body": "Fix this bug", "path": "src/auth.py", "line": 45}
    pr_context = {"number": "5360", "branch": "fix-branch", "base": "main", "url": "https://github.com/repo/pr/5360"}
    spec = generate_pair_task_spec(comment, pr_context)
    assert "Fix PR #5360 Comment #123" in spec
    assert "CRITICAL" in spec
    print("✓ Task spec generation works")

    print("\n✅ All self-tests passed!")
