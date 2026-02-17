#!/usr/bin/env python3
"""
Copilot Execute - Orchestrated PR Comment Processing

Launches an orchestration agent to handle PR comment analysis, categorization,
fixes, and responses using the /copilot workflow.

Usage:
    python3 scripts/copilot_execute.py [PR_NUMBER]
    python3 scripts/copilot_execute.py --pr 5368
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Use resolved absolute paths
# Script is at .claude/scripts/copilot_execute.py, so parent.parent.parent gets to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ORCHESTRATE_SCRIPT = str(PROJECT_ROOT / "orchestration" / "orchestrate_unified.py")
COPILOT_SKILL = str(PROJECT_ROOT / ".codex" / "skills" / "copilot-pr-processing" / "SKILL.md")

# Prefer PyPI package CLI (`orch`) over local script for portability.
# Falls back to local orchestrate_unified.py when the package isn't installed.
ORCH_CLI = shutil.which("orch")
PAIR_INTEGRATION_MODULE = str(PROJECT_ROOT / ".claude" / "commands" / "_copilot_modules")
PAIR_EXECUTE_SCRIPT = str(PROJECT_ROOT / "scripts" / "pair_execute.py")

# Ensure local copilot modules are importable without inline/dynamic imports.
sys.path.insert(0, PAIR_INTEGRATION_MODULE)
from pair_integration import generate_pair_task_spec, should_trigger_pair


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now(UTC).isoformat()
    print(f"[{timestamp}] {message}", flush=True)


def get_current_pr() -> str | None:
    """Get PR number for current branch."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "--jq", ".number"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_cache_dir() -> Path:
    """Get cache directory for PR comments."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        branch_name = result.stdout.strip() if result.returncode == 0 else "unknown-branch"
        branch_name = "".join(c for c in branch_name if c.isalnum() or c in "._-")

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        repo_path = result.stdout.strip() if result.returncode == 0 else str(PROJECT_ROOT)
        repo_name = Path(repo_path).name
        repo_name = "".join(c for c in repo_name if c.isalnum() or c in "._-")

        return Path(f"/tmp/{repo_name}/{branch_name}")
    except Exception:
        return Path("/tmp/your-project.com/unknown-branch")


def run_pair_integration(pr_number: str) -> None:
    """Execute /pair integration for CRITICAL/BLOCKING comments.

    This function:
    1. Loads comments from /tmp cache
    2. Imports pair_integration module
    3. Checks which comments need /pair (via should_trigger_pair)
    4. Launches /pair sessions for matching comments
    5. Collects results and enhances responses.json

    This is the actual executable integration, not just instructions to the agent.
    """
    # Check if /pair integration is enabled
    if os.environ.get("COPILOT_USE_PAIR", "false").lower() != "true":
        log("ℹ️  /pair integration disabled (COPILOT_USE_PAIR=false)")
        return

    log("🔗 Running /pair integration for CRITICAL/BLOCKING comments")

    # Get cache directory
    cache_dir = get_cache_dir()
    comments_file = cache_dir / "comments.json"

    if not comments_file.exists():
        log(f"⚠️  No comments file found at {comments_file}, skipping /pair integration")
        return

    # Load comments
    try:
        with open(comments_file, "r") as f:
            comments_data = json.load(f)
        comments = comments_data.get("comments", [])
        log(f"📋 Loaded {len(comments)} comments from cache")
    except Exception as e:
        log(f"❌ Failed to load comments: {e}")
        return

    # Get PR context for task specs
    pr_context = {
        "number": pr_number,
        "branch": os.environ.get("GITHUB_HEAD_REF", "unknown"),
        "base": os.environ.get("GITHUB_BASE_REF", "main"),
        "url": f"https://github.com/jleechanorg/your-project.com/pull/{pr_number}",
    }

    # Process comments and launch /pair sessions
    pair_sessions = []
    env = os.environ.copy()

    for comment in comments:
        if should_trigger_pair(comment, env):
            comment_id = comment.get("id", "unknown")
            log(f"🎯 Triggering /pair for comment #{comment_id}")

            # Generate task spec
            task_spec = generate_pair_task_spec(comment, pr_context)

            # Write task spec to temp file
            task_file = cache_dir / f"pair_task_{comment_id}.md"
            with open(task_file, "w") as f:
                f.write(task_spec)

            # Launch /pair session
            coder_cli = os.environ.get("COPILOT_PAIR_CODER", "claude")
            verifier_cli = os.environ.get("COPILOT_PAIR_VERIFIER", "codex")
            timeout = int(os.environ.get("COPILOT_PAIR_TIMEOUT", "600"))

            log(f"🚀 Launching /pair session: coder={coder_cli}, verifier={verifier_cli}")

            try:
                result = subprocess.run(
                    [
                        "python3",
                        PAIR_EXECUTE_SCRIPT,
                        "--coder-cli", coder_cli,
                        "--verifier-cli", verifier_cli,
                        f"Fix PR #{pr_number} Comment #{comment_id}",
                    ],
                    timeout=timeout,
                    check=False,
                )

                if result.returncode == 0:
                    log(f"✅ /pair session completed for comment #{comment_id}")
                    pair_sessions.append({
                        "comment_id": comment_id,
                        "status": "completed",
                    })
                else:
                    log(f"❌ /pair session failed for comment #{comment_id} (exit {result.returncode})")
                    pair_sessions.append({
                        "comment_id": comment_id,
                        "status": "failed",
                        "exit_code": result.returncode,
                    })
            except subprocess.TimeoutExpired:
                log(f"⏱️ /pair session timeout for comment #{comment_id}")
                pair_sessions.append({
                    "comment_id": comment_id,
                    "status": "timeout",
                })

    # Collect results from all sessions
    if pair_sessions:
        log(f"📊 Completed {len(pair_sessions)} /pair sessions")
        # Results will be collected by the orchestration agent in Phase 2.5
    else:
        log("ℹ️  No comments required /pair integration")


def main():
    parser = argparse.ArgumentParser(
        description="Launch orchestrated PR comment processing agent"
    )
    parser.add_argument(
        "pr_number",
        nargs="?",
        help="PR number to process (auto-detected if on PR branch)",
    )
    parser.add_argument(
        "--pr",
        dest="pr_flag",
        help="PR number to process (alternative flag syntax)",
    )

    args = parser.parse_args()

    # Determine PR number
    pr_number = args.pr_number or args.pr_flag
    if not pr_number:
        pr_number = get_current_pr()
        if pr_number:
            log(f"Auto-detected PR #{pr_number} from current branch")
        else:
            log("❌ ERROR: Could not determine PR number")
            log("Usage: python3 scripts/copilot_execute.py [PR_NUMBER]")
            sys.exit(1)

    log(f"🚀 Launching /copilot orchestration for PR #{pr_number}")

    # PHASE 0: Execute /pair integration BEFORE orchestration agent
    # This is actual Python code execution, not instructions to the agent
    run_pair_integration(pr_number)

    # Build task description for orchestration agent
    task_description = f"""Execute /copilot workflow for PR #{pr_number}

ORCHESTRATION MODE: You are an autonomous orchestration agent.
Execute the complete /copilot workflow by running these commands:

Phase 0: Fetch and analyze PR comments
/commentfetch {pr_number}
/gstatus

Phase 1: Categorize comments and identify issues
- Analyze all comments from /tmp cache
- Categorize as CRITICAL/BLOCKING/IMPORTANT/ROUTINE
- Identify fixes needed

Phase 2: Generate responses for ALL comments
- Create responses.json with ACTION_ACCOUNTABILITY protocol
- For each comment: analyze issue, determine action, document in response
- If COPILOT_USE_PAIR=true: Collect /pair session results and enhance responses.json with pair_metadata
  (Note: /pair sessions already launched by copilot_execute.py before this agent started)

Phase 3: Post consolidated response
/commentreply jleechanorg your-project.com {pr_number}

Phase 4: Verify coverage
/commentcheck {pr_number}

Phase 5: Push changes if needed
/pushl

IMPORTANT:
- Run ALL phases autonomously without stopping
- Do not ask user questions - execute the workflow
- Follow .codex/skills/copilot-pr-processing/SKILL.md for detailed instructions
- Use existing slash commands (/commentfetch, /commentreply, /commentcheck, /pushl)
- Post consolidated summary comment (not individual responses per comment)

COMMENT URL TRACKING (MANDATORY):
- When making code fixes, include PR comment URL in commit message
- Format: "Comment: https://github.com/jleechanorg/your-project.com/pull/{pr_number}#discussion_r{{comment_id}}"
- Extract html_url from comments.json for the comment that triggered the fix
- Example commit message:
  Fix: Address CodeRabbit security concern

  Comment: https://github.com/jleechanorg/your-project.com/pull/{pr_number}#discussion_r123456

  Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"""

    # Launch orchestration agent
    log("📋 Creating orchestration agent with copilot task...")

    # Use configurable CLI with fallback chain
    agent_cli = os.environ.get("COPILOT_AGENT_CLI", "codex")
    log(f"🤖 Using agent CLI: {agent_cli}")

    # Prefer PyPI `orch` CLI; fall back to local script for development
    if ORCH_CLI:
        cmd = [
            ORCH_CLI, "run",
            "--agent-cli", agent_cli,
            "--no-worktree",
            task_description,
        ]
        log(f"🔧 Using PyPI package: {ORCH_CLI}")
    else:
        cmd = [
            "python3",
            ORCHESTRATE_SCRIPT,
            "--agent-cli", agent_cli,
            "--no-worktree",
            task_description,
        ]
        log(f"🔧 Falling back to local script: {ORCHESTRATE_SCRIPT}")

    log(f"🔧 Command: {' '.join(cmd[:4])}... [task truncated]")

    try:
        result = subprocess.run(
            cmd,
            timeout=1800,  # 30 minute timeout for full workflow
            check=False,
        )

        if result.returncode == 0:
            log(f"✅ /copilot workflow completed successfully for PR #{pr_number}")
            sys.exit(0)
        else:
            log(f"❌ /copilot workflow failed with exit code {result.returncode}")
            sys.exit(result.returncode)

    except subprocess.TimeoutExpired:
        log("❌ /copilot workflow timed out after 30 minutes")
        sys.exit(124)
    except KeyboardInterrupt:
        log("⚠️ /copilot workflow interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
