#!/usr/bin/env python3
"""
Orchestrated PR runner that uses TaskDispatcher (Claude agents) to run /fixpr and /copilot
for recent PRs. Workspaces live under /tmp/{repo}/{branch}.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from orchestration.task_dispatcher import TaskDispatcher

ORG = "jleechanorg"
BASE_CLONE_ROOT = Path("/tmp/pr-orch-bases")
WORKSPACE_ROOT_BASE = Path("/tmp")
DEFAULT_CUTOFF_HOURS = 24
DEFAULT_MAX_PRS = 5
DEFAULT_TIMEOUT = 30  # baseline timeout per security guideline
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
    try:
        import orchestration.task_dispatcher
        script_path = Path(orchestration.task_dispatcher.__file__).resolve().parent / "stream_logs.sh"
    except (ImportError, AttributeError):
        # Fallback to relative path if orchestration module not available
        script_path = Path(__file__).resolve().parent.parent.parent / "orchestration" / "stream_logs.sh"

    if script_path.exists():
        log("")
        log("📺 View formatted logs:")
        log(f"   {script_path} {session_name}")
        log("")
        log("   Or use the shorter command:")
        log(f"   ./orchestration/stream_logs.sh {session_name}")
        log("")


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout or DEFAULT_TIMEOUT,
    )


def query_recent_prs(cutoff_hours: int) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)
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

    prs: List[Dict] = []
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
    """Return True if PR has any failing checks."""
    try:
        result = run_cmd(
            ["gh", "pr", "checks", str(pr_number), "--repo", repo_full, "--json", "name,state,workflow"],
            check=False,
            timeout=API_TIMEOUT,
        )
        if result.returncode != 0:
            log(f"Failed to fetch checks for {repo_full}#{pr_number}: {result.stderr.strip()}")
            return False
        data = json.loads(result.stdout or "[]")
        failing_states = {"FAILED", "FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}
        for check in data:
            state = (check.get("state") or "").upper()
            if state in failing_states:
                return True
        return False
    except Exception as exc:
        log(f"Error checking PR checks for {repo_full}#{pr_number}: {exc}")
        return False


def ensure_base_clone(repo_full: str) -> Path:
    # Validate repo_full format defensively
    if not re.match(r"^[\w.-]+/[\w.-]+$", repo_full):
        raise ValueError(f"Invalid repository format: {repo_full}")

    github_host = os.environ.get('GH_HOST', 'github.com')
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
            # Local main exists - switch to it and reset
            run_cmd(["git", "checkout", "main"], cwd=base_dir, timeout=FETCH_TIMEOUT)
            run_cmd(["git", "reset", "--hard", "origin/main"], cwd=base_dir, timeout=FETCH_TIMEOUT)
        run_cmd(["git", "clean", "-fdx"], cwd=base_dir, timeout=FETCH_TIMEOUT)
    except subprocess.CalledProcessError as exc:
        stderr_msg = exc.stderr if exc.stderr else "No stderr available"
        raise RuntimeError(f"Failed to reset base clone for {repo_full}: {stderr_msg}") from exc
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
    pr: Dict,
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


def dispatch_agent_for_pr(
    dispatcher: TaskDispatcher,
    pr: Dict,
    agent_cli: str = "claude",
    model: Optional[str] = None,
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

    normalized_model: Optional[str] = None
    if model:
        raw_model = str(model).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_model):
            log(f"❌ Invalid model name requested: {raw_model!r}")
            return False
        normalized_model = raw_model

    task_description = (
        f"FIXPR TASK (SELF-CONTAINED): Update PR #{pr_number} in {repo_full} (branch {branch}). "
        "Goal: resolve merge conflicts and failing checks. Also review and address any reviewer feedback that is blocking CI or mergeability. "
        f"CLI chain: {agent_cli}. DO NOT wait for additional input—start immediately.\n\n"
        "🚨 CRITICAL - PREVENT PENDING REVIEWS (MANDATORY - READ FIRST):\n"
        "   ⚠️ YOU MUST NEVER CREATE A PENDING REVIEW. Pending reviews clutter PRs and break automation.\n"
        "   ⚠️ IF YOU CREATE A PENDING REVIEW, THE AUTOMATION WILL FAIL AND YOU WILL BE BLOCKED.\n\n"
        "   ✅ CORRECT METHOD - Reply to inline review comments (ONLY USE THIS):\n"
        f"   `gh api /repos/{repo_full}/pulls/{pr_number}/comments -f body='...' -F in_reply_to={{comment_id}}`\n"
        "   This `/comments` endpoint with `in_reply_to` creates a threaded reply WITHOUT starting a review.\n"
        "   ⚠️ Use `-f` for body (string) and `-F` for in_reply_to (numeric comment ID).\n\n"
        "   ✅ CORRECT METHOD - General PR comments (not line-specific):\n"
        f"   `gh pr comment {pr_number} --body '...'` or `gh api /repos/{repo_full}/issues/{pr_number}/comments -f body='...'`\n\n"
        "   ❌ FORBIDDEN - These ALWAYS create pending reviews (NEVER USE):\n"
        "   - `create_pending_pull_request_review` MCP tool (FORBIDDEN - creates pending review)\n"
        "   - `add_comment_to_pending_review` MCP tool (FORBIDDEN - adds to pending review)\n"
        "   - `POST /repos/.../pulls/.../reviews` endpoint (FORBIDDEN - creates pending review if event missing)\n"
        "   - Any GitHub review workflow that requires 'submit' (FORBIDDEN - creates pending review)\n\n"
        "   ✅ ALLOWED - Verification and Cleanup:\n"
        "   - `GET /repos/.../pulls/.../reviews` (ALLOWED - used to check for pending reviews)\n"
        "   - `DELETE /repos/.../pulls/.../reviews/{review_id}` (ALLOWED - used to clean up pending reviews)\n\n"
        "   ⚠️ VERIFICATION: After replying, verify NO pending review was created:\n"
        f"   `gh api /repos/{repo_full}/pulls/{pr_number}/reviews --jq '.[] | select(.state==\"PENDING\")'`\n"
        "   If any pending reviews exist from your user, DELETE THEM IMMEDIATELY.\n\n"
        "If /fixpr is unavailable, follow these steps explicitly (fallback for all CLIs including Claude):\n"
        f"1) gh pr checkout {pr_number}\n"
        "2) git status && git branch --show-current\n"
        "3) If checkout fails because the branch exists elsewhere, create worktree:\n"
        f"   git worktree add {workspace_root}/pr-{pr_number}-rerun {pr_number} && cd {workspace_root}/pr-{pr_number}-rerun\n"
        "4) Fetch PR feedback from ALL sources (pagination-safe):\n"
        "   - Issue comments: gh api \"/repos/{owner}/{repo}/issues/{pr}/comments\" --paginate -F per_page=100\n"
        "   - Review summaries: gh api \"/repos/{owner}/{repo}/pulls/{pr}/reviews\" --paginate -F per_page=100\n"
        "   - Inline review comments: gh api \"/repos/{owner}/{repo}/pulls/{pr}/comments\" --paginate -F per_page=100\n"
        "   Ensure you cover all feedback; do not assume `gh pr view --json comments` includes inline review comments.\n"
        "5) Identify failing checks (gh pr view --json statusCheckRollup) and reproduce locally (tests/linters as needed)\n"
        "6) Apply fixes (prefer a deterministic branch sync strategy: merge base into branch; avoid rebases unless required by policy)\n"
        f'7) git add -A && git commit -m "[fixpr {commit_marker_cli}-automation-commit] fix PR #{pr_number}" && git push\n'
        f"8) gh pr view {pr_number} --json mergeable,mergeStateStatus,statusCheckRollup\n"
        f"9) Write completion report to {workspace_root}/{workspace_name}/orchestration_results.json summarizing actions and test results\n\n"
        f"Workspace: --workspace-root {workspace_root} --workspace-name {workspace_name}. "
        "Do not create new PRs or branches. Skip /copilot. Use only the requested CLI chain (in order)."
    )

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
