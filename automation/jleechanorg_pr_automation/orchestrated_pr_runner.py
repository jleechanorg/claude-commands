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

    repo_name = repo_full.split("/")[-1]
    base_dir = BASE_CLONE_ROOT / repo_name
    BASE_CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    if not base_dir.exists():
        log(f"Cloning base repo for {repo_full} into {base_dir}")
        run_cmd(
            ["git", "clone", f"https://github.com/{repo_full}.git", str(base_dir)],
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
                ["git", "clone", f"https://github.com/{repo_full}.git", str(base_dir)],
                timeout=CLONE_TIMEOUT,
            )
    # Reset base clone to main to ensure clean worktrees
    try:
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
        except OSError as e:
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


def dispatch_agent_for_pr(dispatcher: TaskDispatcher, pr: Dict, agent_cli: str = "claude") -> bool:
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

    task_description = (
        f"FIXPR TASK (SELF-CONTAINED): Update PR #{pr_number} in {repo_full} (branch {branch}). "
        "Goal: resolve merge conflicts and failing checks. "
        f"CLI chain: {agent_cli}. DO NOT wait for additional input—start immediately.\n\n"
        "If /fixpr is unavailable, follow these steps explicitly (fallback for all CLIs including Claude):\n"
        f"1) gh pr checkout {pr_number}\n"
        "2) git status && git branch --show-current\n"
        "3) If checkout fails because the branch exists elsewhere, create worktree:\n"
        f"   git worktree add {workspace_root}/pr-{pr_number}-rerun {pr_number} && cd {workspace_root}/pr-{pr_number}-rerun\n"
        "4) Identify failing checks (gh pr view --json statusCheckRollup) and reproduce locally (tests/linters as needed)\n"
        "5) Apply fixes\n"
        f'6) git add -A && git commit -m "[{commit_marker_cli}-automation-commit] fix PR #{pr_number}" && git push\n'
        f"7) gh pr view {pr_number} --json mergeable,mergeStateStatus,statusCheckRollup\n"
        "8) Write completion report to /tmp/orchestration_results/pr-{pr_number}._results.json summarizing actions and test results\n\n"
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
        ok = dispatcher.create_dynamic_agent(agent_spec)
        if ok:
            log(f"Spawned agent for {repo_full}#{pr_number} at /tmp/{repo}/{workspace_name}")
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
