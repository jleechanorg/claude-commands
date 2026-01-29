#!/usr/bin/env python3
"""
Orchestrated PR runner that uses TaskDispatcher (Claude agents) to run /fixpr and /copilot
for recent PRs. Workspaces live under /tmp/{repo}/{branch}.
"""

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests

from orchestration import task_dispatcher
from orchestration.task_dispatcher import TaskDispatcher

import yaml

ORG = "jleechanorg"
BASE_CLONE_ROOT = Path("/tmp/pr-orch-bases")
WORKSPACE_ROOT_BASE = Path("/tmp")
DEFAULT_CUTOFF_HOURS = 24
DEFAULT_MAX_PRS = 5
DEFAULT_TIMEOUT = 30  # baseline timeout per security guideline
TIMEOUT_SECONDS = DEFAULT_TIMEOUT # Alias for backward compatibility (fixes NameError in tests)
CLONE_TIMEOUT = 300
FETCH_TIMEOUT = 120
API_TIMEOUT = 60
WORKTREE_TIMEOUT = 60
LOG_PREFIX = "[orchestrated_pr_runner]"


def log(msg: str) -> None:
    print(f"{LOG_PREFIX} {msg}")


def display_log_viewing_command(session_name: str) -> None:
    """Display formatted log viewing commands for the given session."""
    # Use same path resolution as task_dispatcher (relative to orchestration module)
    script_path = Path(task_dispatcher.__file__).resolve().parent / "stream_logs.sh"

    if script_path.exists():
        log("")
        log("📺 View formatted logs:")
        log(f"   {script_path} {session_name}")
        log("")
        log("   Or use the shorter command:")
        log(f"   ./orchestration/stream_logs.sh {session_name}")
        log("")


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or gh CLI config file (avoids bash/subprocess calls).
    
    Reads token directly from ~/.config/gh/hosts.yml to avoid macOS permission prompts
    that occur when calling 'gh auth token' via subprocess.
    """
    # Try environment first
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        # Basic validation: ensure token is non-empty
        token = token.strip()
        if token and len(token) > 0:
            return token
    
    # Try reading from gh CLI config file directly (avoids subprocess/bash calls)
    try:
        gh_config_path = Path.home() / ".config" / "gh" / "hosts.yml"
        if gh_config_path.exists():
            if yaml is None:
                log("⚠️ PyYAML not available, cannot read gh config file")
            else:
                try:
                    with open(gh_config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)
                    # Extract token from config structure: github.com -> oauth_token
                    if config and "github.com" in config:
                        github_config = config["github.com"]
                        # Try oauth_token at top level first
                        token = github_config.get("oauth_token")
                        if not token and "users" in github_config:
                            # Try user-specific token
                            users = github_config["users"]
                            if users:
                                # Get first user's token
                                first_user = next(iter(users.values()))
                                token = first_user.get("oauth_token")
                        
                        if token:
                            token = str(token).strip()
                            if token and len(token) > 0:
                                log("🔍 Retrieved GitHub token from gh CLI config file")
                                return token
                except Exception as e:
                    log(f"⚠️ Failed to read GitHub token from gh config file: {e}")
    except Exception as e:
        log(f"⚠️ Error accessing gh config file: {e}")
    
    return None


def post_pr_comment_python(repo_full: str, pr_number: int, body: str, in_reply_to: Optional[int] = None) -> bool:
    """Post a comment to a PR using Python GitHub API (avoids bash/macOS permission prompts).
    
    Args:
        repo_full: Repository in format "owner/repo"
        pr_number: PR number
        body: Comment body text
        in_reply_to: Optional comment ID to reply to (creates threaded reply)
    
    Returns:
        True if comment was posted successfully, False otherwise
    """
    token = get_github_token()
    if not token:
        log("⚠️ No GitHub token available for posting comment")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        if in_reply_to:
            # Reply to inline review comment
            url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}/comments"
            data = {
                "body": body,
                "in_reply_to": in_reply_to
            }
        else:
            # General PR comment (issue comment endpoint)
            url = f"https://api.github.com/repos/{repo_full}/issues/{pr_number}/comments"
            data = {"body": body}
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        log(f"✅ Posted comment to {repo_full}#{pr_number}")
        return True
    except requests.exceptions.Timeout as e:
        log(f"⚠️ Timeout while posting comment to {repo_full}#{pr_number}: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else "unknown"
        log(f"⚠️ HTTP error while posting comment to {repo_full}#{pr_number} (status {status_code}): {e}")
        return False
    except requests.exceptions.RequestException as e:
        log(f"⚠️ Network/request error while posting comment to {repo_full}#{pr_number}: {e}")
        return False
    except Exception as e:
        log(f"⚠️ Unexpected error while posting comment to {repo_full}#{pr_number}: {e}")
        return False


def cleanup_pending_reviews_python(repo_full: str, pr_number: int, automation_user: str) -> None:
    """Clean up pending reviews using Python GitHub API (avoids bash/macOS permission prompts).
    
    This function can be called by agents to clean up pending reviews without
    triggering macOS permission dialogs from bash scripts.
    """
    token = get_github_token()
    if not token:
        log("⚠️ No GitHub token available for cleanup")
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Get all reviews
        url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}/reviews"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        reviews = response.json()
        
        # Find pending reviews from automation user
        pending_reviews = [
            r for r in reviews 
            if r.get("state") == "PENDING" and r.get("user", {}).get("login") == automation_user
        ]
        
        if not pending_reviews:
            return
        
        # Delete each pending review
        for review in pending_reviews:
            review_id = review.get("id")
            if review_id:
                delete_url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}/reviews/{review_id}"
                delete_response = requests.delete(delete_url, headers=headers, timeout=30)
                if delete_response.status_code == 204:
                    log(f"✅ Deleted pending review {review_id} for {repo_full}#{pr_number}")
                else:
                    log(f"⚠️ Failed to delete review {review_id}: {delete_response.status_code}")
    except requests.exceptions.Timeout as e:
        log(f"⚠️ Timeout while cleaning up pending reviews for {repo_full}#{pr_number}: {e}")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else "unknown"
        log(f"⚠️ HTTP error while cleaning up pending reviews for {repo_full}#{pr_number} (status {status_code}): {e}")
    except requests.exceptions.RequestException as e:
        log(f"⚠️ Network/request error while cleaning up pending reviews for {repo_full}#{pr_number}: {e}")
    except Exception as e:
        log(f"⚠️ Unexpected error while cleaning up pending reviews for {repo_full}#{pr_number}: {e}")



def run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout or DEFAULT_TIMEOUT,
    )


def query_recent_prs(cutoff_hours: int) -> list[dict]:
    cutoff = datetime.now(UTC) - timedelta(hours=cutoff_hours)
    search_query = f"org:{ORG} is:pr is:open updated:>={cutoff.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    graphql_query = """
    query($searchQuery: String!, $cursor: String) {
      search(type: ISSUE, query: $searchQuery, first: 100, after: $cursor) {
        nodes {
          __typename
          ... on PullRequest {
            number
            title
            headRefName
            headRefOid
            updatedAt
            isDraft
            mergeable
            url
            repository { name nameWithOwner }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
    """

    prs: list[dict] = []
    cursor = None
    while True:
        cmd = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={graphql_query}",
            "-f",
            f"searchQuery={search_query}",
        ]
        if cursor:
            cmd += ["-f", f"cursor={cursor}"]
        result = run_cmd(cmd, check=False, timeout=API_TIMEOUT)
        if result.returncode != 0:
            raise RuntimeError(f"GraphQL search failed: {result.stderr.strip()}")
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response from GitHub API: {e}") from e
        search = data.get("data", {}).get("search") or {}
        for node in search.get("nodes", []):
            if node.get("__typename") != "PullRequest":
                continue
            repo_info = node.get("repository") or {}
            repo_full = repo_info.get("nameWithOwner")
            repo_name = repo_info.get("name")
            branch = node.get("headRefName")
            pr_number = node.get("number")
            if not repo_full or not repo_name or branch is None or pr_number is None:
                log(f"Skipping PR with incomplete data: {node.get('url') or node.get('number')}")
                continue
            prs.append(
                {
                    "repo_full": repo_full,
                    "repo": repo_name,
                    "number": pr_number,
                    "title": node.get("title"),
                    "branch": branch,
                    "head_oid": node.get("headRefOid"),
                    "updatedAt": node.get("updatedAt"),
                    "isDraft": node.get("isDraft"),
                    "mergeable": node.get("mergeable"),
                    "url": node.get("url"),
                }
            )
        page = search.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page.get("endCursor")
        if not cursor:
            break
    prs.sort(key=lambda pr: pr.get("updatedAt", ""), reverse=True)
    return [pr for pr in prs if not pr.get("isDraft")]


def has_failing_checks(repo_full: str, pr_number: int) -> bool:
    """Return True if PR has any failing checks. Uses Python requests instead of gh CLI to avoid bash prompts."""
    try:
        # Use Python requests instead of gh CLI to avoid bash prompts
        token = get_github_token()
        if not token:
            log(f"⚠️ No GitHub token available for checking PR checks: {repo_full}#{pr_number}")
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Fetch PR data to get head SHA
        pr_url = f"https://api.github.com/repos/{repo_full}/pulls/{pr_number}"
        try:
            pr_response = requests.get(pr_url, headers=headers, timeout=API_TIMEOUT)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            head_sha = pr_data.get("head", {}).get("sha")
            if not head_sha:
                log(f"⚠️ Could not get head SHA for {repo_full}#{pr_number}")
                return False
        except requests.exceptions.RequestException as e:
            log(f"Failed to fetch PR data for {repo_full}#{pr_number}: {e}")
            return False

        # Fetch check runs for the head commit
        checks_url = f"https://api.github.com/repos/{repo_full}/commits/{head_sha}/check-runs"
        try:
            checks_response = requests.get(checks_url, headers=headers, timeout=API_TIMEOUT, params={"per_page": 100})
            checks_response.raise_for_status()
            checks_data = checks_response.json()
            checks = checks_data.get("check_runs", [])
        except requests.exceptions.RequestException:
            # Fallback: try statuses endpoint
            statuses_url = f"https://api.github.com/repos/{repo_full}/commits/{head_sha}/statuses"
            try:
                statuses_response = requests.get(statuses_url, headers=headers, timeout=API_TIMEOUT)
                statuses_response.raise_for_status()
                checks = statuses_response.json()
            except requests.exceptions.RequestException:
                checks = []

        if not checks:
            return False
        
        # Check conclusion field (authoritative - indicates final result)
        # Also check state as fallback for checks that haven't completed yet
        failing_conclusions = {"FAILURE", "FAILED", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}
        failing_states = {"FAILED", "FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}
        for check in checks:
            # Check-runs API format: conclusion field
            conclusion = (check.get("conclusion") or "").upper()
            state = (check.get("state") or "").upper()
            # Statuses API format: state field (lowercase)
            if not conclusion and not state:
                status_state = (check.get("state") or "").upper()
                if status_state in failing_states:
                    return True
            # Conclusion is authoritative - if check completed with failure, it's failing
            if conclusion in failing_conclusions:
                return True
            # State fallback - for checks that haven't completed yet but are in failing state
            # Only use state if conclusion is None/empty (check still running)
            if not conclusion and state in failing_states:
                return True
        return False
    except Exception as exc:
        log(f"Error checking PR checks for {repo_full}#{pr_number}: {exc}")
        return False


def ensure_base_clone(repo_full: str) -> Path:
    # Validate repo_full format defensively
    if not re.match(r"^[\w.-]+/[\w.-]+$", repo_full):
        raise ValueError(f"Invalid repository format: {repo_full}")

    github_host = os.environ.get("GH_HOST", "github.com")
    repo_name = repo_full.split("/")[-1]
    base_dir = BASE_CLONE_ROOT / repo_name
    BASE_CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    if not base_dir.exists():
        log(f"Cloning base repo for {repo_full} into {base_dir}")
        run_cmd(
            ["git", "clone", f"https://{github_host}/{repo_full}.git", str(base_dir)],
            timeout=CLONE_TIMEOUT,
        )
    else:
        log(f"Refreshing base repo for {repo_full}")
        try:
            run_cmd(["git", "fetch", "origin", "--prune"], cwd=base_dir, timeout=FETCH_TIMEOUT)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            stderr_msg = getattr(exc, "stderr", "") or str(exc) or "No stderr available"
            log(
                f"Fetch failed for {repo_full} ({exc.__class__.__name__}): {stderr_msg}. "
                "Re-cloning base repo."
            )
            shutil.rmtree(base_dir, ignore_errors=True)
            run_cmd(
                ["git", "clone", f"https://{github_host}/{repo_full}.git", str(base_dir)],
                timeout=CLONE_TIMEOUT,
            )
    # Reset base clone to main to ensure clean worktrees
    try:
        # Ensure we're on main branch (create if doesn't exist locally)
        result = run_cmd(["git", "rev-parse", "--verify", "main"], cwd=base_dir, check=False, timeout=DEFAULT_TIMEOUT)
        if result.returncode != 0:
            # Local main doesn't exist - checkout from remote tracking branch
            run_cmd(["git", "checkout", "-B", "main", "origin/main"], cwd=base_dir, timeout=FETCH_TIMEOUT)
        else:
            # Local main exists - discard local changes first, then switch and reset
            run_cmd(["git", "reset", "--hard"], cwd=base_dir, timeout=FETCH_TIMEOUT)
            run_cmd(["git", "checkout", "main"], cwd=base_dir, timeout=FETCH_TIMEOUT)
            run_cmd(["git", "reset", "--hard", "origin/main"], cwd=base_dir, timeout=FETCH_TIMEOUT)
        run_cmd(["git", "clean", "-fdx"], cwd=base_dir, timeout=FETCH_TIMEOUT)
    except subprocess.CalledProcessError as exc:
        stderr_msg = exc.stderr if exc.stderr else "No stderr available"
        cmd_str = " ".join(exc.cmd) if hasattr(exc, "cmd") else "unknown command"
        raise RuntimeError(
            f"Failed to reset base clone for {repo_full} (command: {cmd_str}): {stderr_msg}"
        ) from exc
    return base_dir


def sanitize_workspace_name(name: str, pr_number: int) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return f"pr-{pr_number}-{sanitized}" if sanitized else f"pr-{pr_number}"


def prepare_workspace_dir(repo: str, workspace_name: str) -> Path:
    target = WORKSPACE_ROOT_BASE / repo / workspace_name
    # Safety: ensure target stays within the configured root
    try:
        target.resolve().relative_to(WORKSPACE_ROOT_BASE.resolve())
    except ValueError:
        raise ValueError(f"Workspace path escapes root: {target}")

    if target.exists():
        git_file = target / ".git"
        if git_file.exists():
            try:
                git_content = git_file.read_text().strip()
                if git_content.startswith("gitdir: "):
                    git_dir_path = Path(git_content.split("gitdir: ", 1)[1].strip())
                    base_repo = git_dir_path.parents[1].parent
                    run_cmd(
                        ["git", "worktree", "remove", str(target), "--force"],
                        cwd=base_repo,
                        check=False,
                        timeout=WORKTREE_TIMEOUT,
                    )
                    run_cmd(
                        ["git", "worktree", "prune"],
                        cwd=base_repo,
                        check=False,
                        timeout=WORKTREE_TIMEOUT,
                    )
            except Exception as exc:
                log(f"Warning: Failed to clean worktree metadata for {target}: {exc}")
        try:
            shutil.rmtree(target)
        except FileNotFoundError:
            # Workspace already gone (external cleanup, reboot, etc.) - nothing to do
            pass
        except OSError as e:
            # Other OS errors (permissions, locks, etc.) are serious
            log(f"Failed to remove existing workspace {target}: {e}")
            raise
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


@contextmanager
def chdir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def kill_tmux_session_if_exists(name: str) -> None:
    """Ensure tmux session name is free; kill existing session if present."""
    try:
        base = name.rstrip(".")
        candidates = [name, f"{name}_", base, f"{base}_"]  # cover trailing dot and suffixed variants
        # First try direct has-session matches
        for candidate in candidates:
            check = run_cmd(["tmux", "has-session", "-t", candidate], check=False, timeout=30)
            if check.returncode == 0:
                log(f"Existing tmux session {candidate} detected; killing to allow reuse")
                run_cmd(["tmux", "kill-session", "-t", candidate], check=False, timeout=30)
        # Fallback: scan tmux ls and kill any sessions containing the base token
        ls = run_cmd(["tmux", "ls"], check=False, timeout=30)
        if ls.returncode == 0:
            base_token = name.rstrip(".")
            pr_token = None
            match = re.search(r"pr-(\d+)", base_token)
            if match:
                pr_token = match.group(0)
            for line in (ls.stdout or "").splitlines():
                session_name = line.split(":", 1)[0]
                # Use word boundary regex to prevent pr-1 from matching pr-10, pr-11, pr-100
                matched = False
                if base_token:
                    # Match base_token with word boundaries
                    base_pattern = rf"\b{re.escape(base_token)}\b"
                    if re.search(base_pattern, session_name):
                        matched = True
                if not matched and pr_token:
                    # Match pr_token with word boundaries (pr-1 should not match pr-10)
                    pr_pattern = rf"\b{re.escape(pr_token)}\b"
                    if re.search(pr_pattern, session_name):
                        matched = True
                if matched:
                    log(f"Killing tmux session {session_name} matched on token {base_token or pr_token}")
                    run_cmd(["tmux", "kill-session", "-t", session_name], check=False, timeout=30)
    except Exception as exc:
        log(f"Warning: unable to check/kill tmux session {name}: {exc}")


def dispatch_agent_for_pr_with_task(
    dispatcher: TaskDispatcher,
    pr: dict,
    task_description: str,
    agent_cli: str = "claude",
    model: str = None,
) -> bool:
    """Dispatch an agent for a PR using a custom task description."""
    repo_full = pr.get("repo_full")
    repo = pr.get("repo")
    pr_number = pr.get("number")
    branch = pr.get("branch")

    if not task_description:
        log("Skipping PR dispatch: missing task description")
        return False

    if not all([repo_full, repo, pr_number is not None, branch]):
        log(f"Skipping PR with missing required fields: {pr}")
        return False
    assert branch is not None and pr_number is not None

    workspace_name = sanitize_workspace_name(branch or f"pr-{pr_number}", pr_number)
    workspace_root = WORKSPACE_ROOT_BASE / repo
    prepare_workspace_dir(repo, workspace_name)

    cli = agent_cli.strip().lower() if isinstance(agent_cli, str) and agent_cli.strip() else "claude"
    agent_specs = dispatcher.analyze_task_and_create_agents(task_description, forced_cli=cli)
    success = False
    for spec in agent_specs:
        agent_spec = {**spec}
        session_name = agent_spec.get("name") or workspace_name
        kill_tmux_session_if_exists(session_name)
        agent_spec.setdefault(
            "workspace_config",
            {
                "workspace_root": str(workspace_root),
                "workspace_name": workspace_name,
            },
        )
        # Inject model parameter for all CLIs in the chain (Gemini, Claude, Cursor, etc.)
        if model:
            raw_model = str(model).strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_model):
                log(f"❌ Invalid model name requested: {raw_model!r}")
                return False
        ok = dispatcher.create_dynamic_agent(agent_spec)
        if ok:
            log(f"Spawned agent for {repo_full}#{pr_number} at /tmp/{repo}/{workspace_name}")
            display_log_viewing_command(session_name)
            success = True
        else:
            log(f"Failed to spawn agent for {repo_full}#{pr_number}")
    return success


def get_automation_user() -> Optional[str]:
    """Detect automation user from environment or gh CLI."""
    automation_user = os.environ.get("GITHUB_ACTOR") or os.environ.get("AUTOMATION_USERNAME")
    if automation_user:
        return automation_user

    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            username = result.stdout.strip()
            # Validate GitHub username: alphanumeric and hyphens, cannot start or end with hyphen, max length 39
            if username and re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username):
                log(f"🔍 Auto-detected automation user from gh CLI: {username}")
                return username
            else:
                log(f"⚠️ Invalid username format from gh CLI: {username!r}")
    except subprocess.TimeoutExpired:
        log("⚠️ Timeout while auto-detecting automation user from gh CLI")
    except subprocess.CalledProcessError as e:
        log(f"⚠️ gh CLI error while auto-detecting automation user: {e}")
    except Exception as e:
        log(f"⚠️ Failed to auto-detect automation user: {type(e).__name__}: {e}")
    
    return None


def dispatch_agent_for_pr(
    dispatcher: TaskDispatcher,
    pr: dict,
    agent_cli: str = "claude",
    model: str | None = None,
) -> bool:
    repo_full = pr.get("repo_full")
    repo = pr.get("repo")
    pr_number = pr.get("number")
    branch = pr.get("branch")

    if not all([repo_full, repo, pr_number is not None, branch]):
        log(f"Skipping PR with missing required fields: {pr}")
        return False
    assert branch is not None and pr_number is not None
    workspace_name = sanitize_workspace_name(branch or f"pr-{pr_number}", pr_number)
    workspace_root = WORKSPACE_ROOT_BASE / repo
    prepare_workspace_dir(repo, workspace_name)

    cli_chain_parts = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
    commit_marker_cli = cli_chain_parts[0] if cli_chain_parts else str(agent_cli).strip().lower() or "claude"

    normalized_model: str | None = None
    if model:
        raw_model = str(model).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_model):
            log(f"❌ Invalid model name requested: {raw_model!r}")
            return False
        normalized_model = raw_model

    # Get automation user for cleanup instructions (before building task description)
    automation_user = get_automation_user()

    task_description = (
        f"FIXPR TASK (SELF-CONTAINED): Update PR #{pr_number} in {repo_full} (branch {branch}). "
        "Goal: resolve merge conflicts FIRST, then fix failing tests. Also review and address any reviewer feedback that is blocking CI or mergeability. "
        f"CLI chain: {agent_cli}. DO NOT wait for additional input—start immediately.\n\n"
        "🚨🚨🚨 PRIORITY 1: MERGE CONFLICT RESOLUTION (DO THIS FIRST - BEFORE ANYTHING ELSE):\n"
        f"   ⚠️⚠️⚠️ MERGE CONFLICTS MUST BE RESOLVED BEFORE FIXING TESTS. CHECK MERGE STATUS IMMEDIATELY:\n\n"
        f"   STEP 1 - Check PR merge status:\n"
        f"   ```bash\n"
        f"   gh pr view {pr_number} --json mergeable,mergeStateStatus\n"
        f"   ```\n\n"
        f"   STEP 2 - If mergeable == \"CONFLICTING\" or mergeStateStatus == \"DIRTY\", resolve conflicts:\n"
        f"   ```bash\n"
        f"   # Ensure you're on the PR branch\n"
        f"   git checkout {branch}\n"
        f"   git status\n\n"
        f"   # Fetch and merge main into the PR branch\n"
        f"   git fetch origin main\n"
        f"   git merge origin/main --no-edit\n"
        f"   ```\n\n"
        f"   STEP 3 - If merge conflicts appear, resolve using these strategies:\n"
        f"   - For `.beads/issues.jsonl`: ALWAYS use ours (keep PR branch version)\n"
        f"     ```bash\n"
        f"     git checkout --ours .beads/issues.jsonl\n"
        f"     ```\n"
        f"   - For test files (mvp_site/tests/*, testing_mcp/lib/*): Usually use theirs (main branch version)\n"
        f"     ```bash\n"
        f"     git checkout --theirs <test_file_path>\n"
        f"     ```\n"
        f"   - For code files (mvp_site/*.py, automation/*.py): Manually resolve, keeping both changes where appropriate\n"
        f"     - Read the conflict markers (<<<<<<< HEAD, =======, >>>>>>> origin/main)\n"
        f"     - Keep changes from both branches that don't conflict\n"
        f"     - Remove conflict markers\n"
        f"   - After resolving all conflicts:\n"
        f"     ```bash\n"
        f"     git add -A\n"
        f"     git commit -m \"[fixpr {automation_user or 'claude'}-automation-commit] Merge main into {branch} to resolve conflicts\"\n"
        f"     git push\n"
        f"     ```\n\n"
        f"   STEP 4 - Verify merge succeeded:\n"
        f"   ```bash\n"
        f"   gh pr view {pr_number} --json mergeable,mergeStateStatus\n"
        f"   # Should now show mergeable: \"MERGEABLE\" or \"UNKNOWN\" (not \"CONFLICTING\")\n"
        f"   ```\n\n"
        f"   ⚠️ DO NOT PROCEED TO TEST FIXES UNTIL MERGE CONFLICTS ARE RESOLVED AND PUSHED.\n\n"
        "🚨🚨🚨 PRE-FLIGHT CHECK - VERIFY TOOL AVAILABILITY (MANDATORY FIRST STEP):\n"
        "   ⚠️⚠️⚠️ BEFORE STARTING ANY WORK, YOU MUST CHECK YOUR AVAILABLE TOOLS:\n"
        "   1. List all available MCP tools (method depends on your CLI)\n"
        "   2. If you see `create_pending_pull_request_review` or `add_comment_to_pending_review` in the tool list:\n"
        "      - DO NOT USE THESE TOOLS - They are FORBIDDEN\n"
        "      - IGNORE them completely - pretend they don't exist\n"
        "      - Use ONLY the allowed methods listed below\n"
        "   3. If these forbidden tools are available, you MUST skip them and use alternative methods\n\n"
        "🚨 CRITICAL - PREVENT PENDING REVIEWS (MANDATORY - READ FIRST):\n"
        "   ⚠️ YOU MUST NEVER CREATE A PENDING REVIEW. Pending reviews clutter PRs and break automation.\n"
        "   ⚠️ IF YOU CREATE A PENDING REVIEW, THE AUTOMATION WILL FAIL AND YOU WILL BE BLOCKED.\n"
        "   ⚠️ THESE TOOLS ARE DISABLED AND WILL NOT WORK - DO NOT ATTEMPT TO USE THEM:\n"
        "   - `create_pending_pull_request_review` MCP tool (DISABLED - will fail if called)\n"
        "   - `add_comment_to_pending_review` MCP tool (DISABLED - will fail if called)\n\n"
        "   ✅✅✅ REQUIRED METHOD - Python (NO bash, NO macOS permission prompts):\n"
        f"   ```python\n"
        f"   from automation.jleechanorg_pr_automation.orchestrated_pr_runner import post_pr_comment_python\n"
        f"   # General PR comment:\n"
        f"   post_pr_comment_python('{repo_full}', {pr_number}, 'Your comment text')\n"
        f"   # Reply to inline review comment:\n"
        f"   post_pr_comment_python('{repo_full}', {pr_number}, 'Your reply', in_reply_to=comment_id)\n"
        f"   ```\n\n"
        "   ❌ FORBIDDEN - Do NOT use bash/gh CLI commands (triggers macOS permission prompts):\n"
        f"   - DO NOT use: `gh api /repos/{repo_full}/pulls/{pr_number}/comments`\n"
        f"   - DO NOT use: `gh pr comment {pr_number} --body '...'`\n"
        f"   - These commands trigger macOS permission dialogs - USE PYTHON FUNCTIONS INSTEAD\n\n"
        "   ❌ FORBIDDEN - These ALWAYS create pending reviews (NEVER USE - TOOLS ARE DISABLED):\n"
        "   - `create_pending_pull_request_review` MCP tool (FORBIDDEN - DISABLED - creates pending review)\n"
        "   - `add_comment_to_pending_review` MCP tool (FORBIDDEN - DISABLED - adds to pending review)\n"
        "   - `POST /repos/.../pulls/.../reviews` endpoint (FORBIDDEN - creates pending review if event missing)\n"
        "   - Any GitHub review workflow that requires 'submit' (FORBIDDEN - creates pending review)\n\n"
        "   ✅ ALLOWED - Verification and Cleanup:\n"
        "   - `GET /repos/.../pulls/.../reviews` (ALLOWED - used to check for pending reviews)\n"
        "   - `DELETE /repos/.../pulls/.../reviews/{review_id}` (ALLOWED - used to clean up pending reviews)\n\n"
        "   ⚠️ VERIFICATION & CLEANUP: After posting ANY comment, you MUST check for and delete pending reviews.\n"
        f"   PREFERRED METHOD (Python - NO bash, NO macOS permission prompts):\n"
        f"   ```python\n"
        f"   from automation.jleechanorg_pr_automation.orchestrated_pr_runner import cleanup_pending_reviews_python\n"
        f"   # Replace 'your-automation-username' with your actual GitHub username\n"
        f"   cleanup_pending_reviews_python('{repo_full}', {pr_number}, 'your-automation-username')\n"
        f"   ```\n"
        "   This cleanup is MANDATORY - pending reviews block PR merges and must be deleted immediately.\n\n"
        "If /fixpr is unavailable, follow these steps explicitly (fallback for all CLIs including Claude):\n"
        f"1) git checkout {branch} (or use git worktree if branch exists elsewhere)\n"
        "2) git status && git branch --show-current\n"
        "3) If checkout fails because the branch exists elsewhere, create worktree:\n"
        f"   git worktree add {workspace_root}/pr-{pr_number}-rerun {pr_number} && cd {workspace_root}/pr-{pr_number}-rerun\n"
        "4) Fetch PR feedback using Python (DO NOT use gh api - triggers macOS prompts):\n"
        f"   ```python\n"
        f"   import requests\n"
        f"   from automation.jleechanorg_pr_automation.orchestrated_pr_runner import get_github_token\n"
        f"   token = get_github_token()\n"
        f"   headers = {{'Authorization': f'Bearer {{token}}', 'Accept': 'application/vnd.github.v3+json'}}\n"
        f"   # Issue comments:\n"
        f"   requests.get('https://api.github.com/repos/{repo_full}/issues/{pr_number}/comments', headers=headers, params={{'per_page': 100}})\n"
        f"   # Review summaries:\n"
        f"   requests.get('https://api.github.com/repos/{repo_full}/pulls/{pr_number}/reviews', headers=headers, params={{'per_page': 100}})\n"
        f"   # Inline review comments:\n"
        f"   requests.get('https://api.github.com/repos/{repo_full}/pulls/{pr_number}/comments', headers=headers, params={{'per_page': 100}})\n"
        f"   ```\n"
        "   Ensure you cover all feedback from all sources.\n"
        "5) Identify failing checks using GitHub API (Python requests, not gh CLI)\n"
        "6) Apply fixes - PRIORITY ORDER:\n"
        "   a) FIRST: Check and resolve merge conflicts (see PRIORITY 1 section above for detailed steps)\n"
        "      - git fetch origin main && git merge origin/main --no-edit\n"
        "      - Resolve any conflicts (.beads/issues.jsonl: use --ours, test files: use --theirs, code: manual)\n"
        "      - git add -A && git commit && git push\n"
        "   b) SECOND: Fix failing tests after merge conflicts are resolved\n"
        "      - Run tests locally to identify failures\n"
        "      - Apply code fixes to make tests pass\n"
        f'7) git add -A && git commit -m "[fixpr {commit_marker_cli}-automation-commit] fix PR #{pr_number}" && git push\n'
        "8) Verify PR status using Python requests (DO NOT use gh pr view)\n"
        f"9) Write completion report to {workspace_root}/{workspace_name}/orchestration_results.json summarizing actions and test results\n\n"
        f"Workspace: --workspace-root {workspace_root} --workspace-name {workspace_name}. "
        "Do not create new PRs or branches. Skip /copilot. Use only the requested CLI chain (in order).\n\n"
        "🚨🚨🚨 ABSOLUTE PROHIBITION - PENDING REVIEWS:\n"
        "   ⚠️⚠️⚠️ YOU ARE FORBIDDEN FROM CREATING PENDING REVIEWS. THIS IS NOT A SUGGESTION - IT IS A HARD REQUIREMENT.\n"
        "   ⚠️⚠️⚠️ IF YOU ATTEMPT TO CREATE A PENDING REVIEW, IT WILL BE IMMEDIATELY DELETED AND YOUR EXECUTION WILL FAIL.\n"
        "   ⚠️⚠️⚠️ THE FOLLOWING TOOLS ARE COMPLETELY DISABLED AND WILL CAUSE IMMEDIATE FAILURE:\n"
        "   - `create_pending_pull_request_review` MCP tool (DISABLED - DO NOT USE)\n"
        "   - `add_comment_to_pending_review` MCP tool (DISABLED - DO NOT USE)\n"
        "   - `POST /repos/.../pulls/.../reviews` endpoint (DISABLED - DO NOT USE)\n"
        "   ⚠️⚠️⚠️ USE ONLY THE ALLOWED METHODS LISTED ABOVE. ANY ATTEMPT TO CREATE A PENDING REVIEW WILL RESULT IN IMMEDIATE TERMINATION.\n"
    )

    # Agent is responsible for cleaning up pending reviews after posting comments
    # No background monitor script needed - eliminates macOS permission prompts
    if automation_user:
        log(f"✅ Agent will handle pending review cleanup for PR #{pr_number} (user: {automation_user})")
    else:
        log("⚠️ GITHUB_ACTOR/AUTOMATION_USERNAME not set; agent cleanup instructions may be incomplete")

    agent_specs = dispatcher.analyze_task_and_create_agents(task_description, forced_cli=agent_cli)
    success = False
    for spec in agent_specs:
        # Preserve the CLI chain emitted by orchestration. Do not overwrite with a single CLI string.
        agent_spec = {**spec}
        # Ensure tmux session name is available for reuse
        session_name = agent_spec.get("name") or workspace_name
        kill_tmux_session_if_exists(session_name)
        agent_spec.setdefault(
            "workspace_config",
            {
                "workspace_root": str(workspace_root),
                "workspace_name": workspace_name,
            },
        )
        if normalized_model:
            agent_spec["model"] = normalized_model
        ok = dispatcher.create_dynamic_agent(agent_spec)
        if ok:
            log(f"Spawned agent for {repo_full}#{pr_number} at /tmp/{repo}/{workspace_name}")
            display_log_viewing_command(session_name)
            success = True
        else:
            log(f"Failed to spawn agent for {repo_full}#{pr_number}")
            # No monitor cleanup needed - agent handles pending review cleanup directly

    return success


def run_fixpr_batch(cutoff_hours: int = DEFAULT_CUTOFF_HOURS, max_prs: int = DEFAULT_MAX_PRS, agent_cli: str = "claude") -> None:
    log(f"Discovering open PRs updated in last {cutoff_hours}h for org {ORG}")
    try:
        prs = query_recent_prs(cutoff_hours)
    except Exception as exc:
        log(f"Failed to discover PRs: {exc}")
        sys.exit(1)

    if not prs:
        log("No recent PRs found")
        return

    # Filter to PRs that need action (merge conflicts or failing checks)
    actionable = []
    for pr in prs:
        repo_full = pr["repo_full"]
        pr_number = pr["number"]
        mergeable = pr.get("mergeable")
        if mergeable == "CONFLICTING":
            actionable.append(pr)
            continue
        if has_failing_checks(repo_full, pr_number):
            actionable.append(pr)

    if not actionable:
        log("No PRs with conflicts or failing checks; skipping run")
        return

    processed = 0
    for pr in actionable:
        if processed >= max_prs:
            break
        repo_full = pr.get("repo_full")
        if not repo_full:
            log(f"Skipping PR with missing repo_full: {pr}")
            continue
        try:
            base_dir = ensure_base_clone(repo_full)
            with chdir(base_dir):
                dispatcher = TaskDispatcher()
                success = dispatch_agent_for_pr(dispatcher, pr, agent_cli=agent_cli)
            if success:
                processed += 1
        except Exception as exc:
            pr_number = pr.get("number", "unknown")
            log(f"Error processing {repo_full}#{pr_number}: {exc}")

    log(f"Completed orchestration dispatch for {processed} PR(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrated PR batch runner (/fixpr-only)")
    parser.add_argument("--cutoff-hours", type=int, default=DEFAULT_CUTOFF_HOURS, help="Lookback window for PR updates")
    parser.add_argument("--max-prs", type=int, default=DEFAULT_MAX_PRS, help="Maximum PRs to process per run")
    args = parser.parse_args()
    run_fixpr_batch(args.cutoff_hours, args.max_prs)
