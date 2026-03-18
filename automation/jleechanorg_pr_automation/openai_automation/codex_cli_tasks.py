"""
Codex CLI API — list, status, and diff operations via ``codex cloud`` CLI.

Replaces browser-based automation with direct API calls through the
official OpenAI Codex CLI (authenticated, no Cloudflare).
"""

import atexit
import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from jleechanorg_pr_automation.codex_config import build_automation_commit_marker
from jleechanorg_pr_automation.orchestrated_pr_runner import ensure_base_clone
from jleechanorg_pr_automation.utils import detect_repo_path, resolve_repo_full_from_environment_label, resolve_repo_path

logger = logging.getLogger(__name__)

# Default binary name; overridden in constructor if needed.
_DEFAULT_CODEX_BIN = "codex"

# Maximum items per page (CLI hard limit is 20).
_MAX_PAGE_LIMIT = 20

# Rate limiting for worktree operations to prevent worktree storm
_worktree_last_created = 0
_WORKTREE_MIN_INTERVAL = 2.0  # seconds between worktree creations

# Track active worktrees for cleanup on process exit
_active_worktrees: list[tuple[Path, Optional[Path]]] = []


def _rate_limit_worktree():
    """Rate limit worktree creation to prevent worktree storm."""
    global _worktree_last_created
    elapsed = time.monotonic() - _worktree_last_created
    if elapsed < _WORKTREE_MIN_INTERVAL:
        time.sleep(_WORKTREE_MIN_INTERVAL - elapsed)
    _worktree_last_created = time.monotonic()


def _cleanup_all_worktrees():
    """Clean up all tracked worktrees on process exit."""
    for worktree_path, base_repo_path in _active_worktrees:
        try:
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
        except Exception as exc:
            logger.warning("Failed to clean up worktree %s: %s", worktree_path, exc)


# Register cleanup for worktrees on process exit
atexit.register(_cleanup_all_worktrees)


class CodexCloudAPI:
    """Wraps ``codex cloud`` CLI subcommands for task management."""

    def __init__(
        self,
        codex_bin: str = _DEFAULT_CODEX_BIN,
        env_id: Optional[str] = None,
        timeout: int = 30,
        repo_path: Optional[str] = None,
    ):
        """
        Args:
            codex_bin: Path or name of the codex binary.
            env_id: Optional environment filter for list/exec commands.
            timeout: Subprocess timeout in seconds per CLI call.
            repo_path: Path to the main git repository (for creating worktrees).
                      If None, attempts to find from ~/.config/worldarchitect/repo_path
        """
        # Validate required binaries
        for bin_name in [codex_bin, "git", "gh"]:
            resolved = shutil.which(bin_name)
            if resolved is None:
                if bin_name == codex_bin:
                    msg = f"codex binary not found: {bin_name!r}. Install with: npm i -g @openai/codex"
                else:
                    msg = f"required binary not found: {bin_name!r}. Please install it."
                raise FileNotFoundError(msg)
            if bin_name == codex_bin:
                self.codex_bin = resolved

        self.env_id = env_id
        self.timeout = timeout

        # Determine repository path via shared automation utility.
        self.repo_path = resolve_repo_path(repo_path, logger=logger)

    def _codex_cli_timeout(self) -> int:
        """Return a launchd-safe timeout for codex CLI subprocesses."""
        return max(self.timeout, 120)

    def _resolve_repo_full(self, task: dict) -> Optional[str]:
        """Resolve owner/repo from task metadata."""
        return resolve_repo_full_from_environment_label(task)

    def _resolve_base_repo_path(self, task: dict) -> Path:
        """Resolve git base repo path for worktree operations.

        Uses task's environment_label to determine the correct repository,
        falling back to local repo_path only when task provides no repository context.
        """
        repo_full = self._resolve_repo_full(task)
        
        # If task specifies a repository, use that (ensures correct repo for multi-repo tasks)
        if repo_full:
            try:
                return ensure_base_clone(repo_full)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                logger.warning("Failed to ensure base clone for %s: %s", repo_full, exc)
                raise RuntimeError(
                    f"Failed to resolve base repo for {repo_full}; refusing local fallback to avoid cross-repo push"
                ) from exc
        
        # Fallback to configured repo_path only when task has no repo context
        if self.repo_path:
            return self.repo_path

        raise RuntimeError(
            "No git repository context available: missing local repo_path and "
            "task.environment_label owner/repo"
        )

    # ------------------------------------------------------------------
    # Repository and worktree management
    # ------------------------------------------------------------------

    def _detect_repo_path(self) -> Optional[str]:
        """Backward-compatible wrapper for tests and legacy callers."""
        detected = detect_repo_path()
        return str(detected) if detected is not None else None

    def _worktree_add(
        self,
        base_repo_path: Path,
        worktree_dir: Path,
        base_branch: str,
        force: bool = True,
    ) -> None:
        """Run ``git worktree add`` without checkout to avoid internal reset hangs."""
        cmd = ["git", "-C", str(base_repo_path), "worktree", "add", "--detach", "--no-checkout"]
        if force:
            cmd.extend(["-f", "-f"])
        cmd.extend([str(worktree_dir), base_branch])
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=max(self.timeout, 120),
        )

    def _create_worktree(self, branch_name: str, base_repo_path: Path) -> tuple[Path, str]:
        """Create a temporary worktree for the given branch.

        Args:
            branch_name: Name of the branch for the worktree

        Returns:
            Tuple of (worktree_dir, base_branch_name)

        Raises:
            RuntimeError: If worktree creation fails
        """
        # Rate limit worktree creation to prevent worktree storm
        _rate_limit_worktree()

        # Create worktree directory in /tmp (sanitize branch name for directory)
        safe_branch_name = branch_name.replace("/", "_")
        worktree_dir = Path(tempfile.mkdtemp(prefix=f"codex_{safe_branch_name}_", dir="/tmp"))
        
        # Remove the directory so git worktree add can create it
        shutil.rmtree(worktree_dir)

        try:
            # Detect the actual default branch from remote HEAD
            result = subprocess.run(
                ["git", "-C", str(base_repo_path), "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode == 0:
                # Output is like "refs/remotes/origin/main" or "refs/remotes/origin/release/main"
                # Extract everything after "refs/remotes/origin/"
                ref_output = result.stdout.strip()
                prefix = "refs/remotes/origin/"
                if ref_output.startswith(prefix):
                    base_branch = ref_output[len(prefix):]
                else:
                    # Fallback to last segment if format is unexpected
                    base_branch = ref_output.split("/")[-1]
            else:
                result = subprocess.run(
                    ["git", "-C", str(base_repo_path), "remote", "show", "origin"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        if line.startswith("HEAD branch:"):
                            base_branch = line.split(":", 1)[1].strip()
                            break
                    else:
                        base_branch = None
                else:
                    base_branch = None

                if base_branch:
                    result = subprocess.run(
                        ["git", "-C", str(base_repo_path), "rev-parse", "--verify", f"origin/{base_branch}"],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                    if result.returncode != 0:
                        base_branch = None

                # Fallback to common defaults if symbolic-ref fails
                if not base_branch:
                    for base_branch in ["main", "master"]:
                        result = subprocess.run(
                            ["git", "-C", str(base_repo_path), "rev-parse", "--verify", base_branch],
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                        )
                        if result.returncode == 0:
                            break
                    else:
                        base_branch = None

                if not base_branch:
                    # Last-resort fallback: choose first available remote branch.
                    refs_result = subprocess.run(
                        [
                            "git",
                            "-C",
                            str(base_repo_path),
                            "for-each-ref",
                            "--format=%(refname:short)",
                            "refs/remotes/origin",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                    if refs_result.returncode != 0:
                        raise RuntimeError("Could not detect default branch")

                    candidates = []
                    for ref_name in refs_result.stdout.splitlines():
                        ref_name = ref_name.strip()
                        if not ref_name or ref_name == "origin/HEAD":
                            continue
                        if ref_name.startswith("origin/"):
                            candidates.append(ref_name)

                    if not candidates:
                        raise RuntimeError("Could not detect default branch")
                    
                    # Sort candidates to prefer common default branch names
                    def branch_priority(ref):
                        branch_name = ref.split("/", 1)[1] if "/" in ref else ref
                        if branch_name == "main":
                            return 0
                        elif branch_name == "master":
                            return 1
                        elif branch_name == "develop":
                            return 2
                        elif branch_name == "dev":
                            return 3
                        elif branch_name == "staging":
                            return 4
                        elif branch_name.startswith("release/"):
                            return 5
                        else:
                            return 6
                    
                    candidates.sort(key=branch_priority)
                    base_branch = candidates[0]

            self._prune_stale_worktrees(base_repo_path)
            # Clean up any stale local branch with the same name to avoid
            # "branch already exists" errors from previous incomplete runs
            try:
                subprocess.run(
                    ["git", "-C", str(base_repo_path), "branch", "-D", branch_name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass  # Branch didn't exist, which is fine

            try:
                self._worktree_add(base_repo_path, worktree_dir, base_branch)
            except subprocess.CalledProcessError as exc:
                self._prune_stale_worktrees(base_repo_path)
                self._worktree_add(base_repo_path, worktree_dir, base_branch, force=True)
            except subprocess.TimeoutExpired:
                self._prune_stale_worktrees(base_repo_path)
                self._worktree_add(base_repo_path, worktree_dir, base_branch, force=True)
            logger.info("Created worktree at %s from %s", worktree_dir, base_branch)
            # Track worktree for cleanup on process exit
            _active_worktrees.append((worktree_dir, base_repo_path))
            return worktree_dir, base_branch
        except Exception as exc:
            # Clean up on failure
            if worktree_dir.exists():
                shutil.rmtree(worktree_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to create worktree: {exc}") from exc

    def _cleanup_worktree(self, worktree_path: Path, base_repo_path: Optional[Path]):
        """Remove a worktree and its directory.

        Args:
            worktree_path: Path to the worktree to remove
        """
        if not base_repo_path:
            return

        removed_temp_dir = False
        try:
            # These codex temp worktrees are throwaway scratch dirs under /tmp.
            # Removing the directory first and pruning metadata is faster and
            # avoids launchd-visible hangs in `git worktree remove --force`.
            is_temp_codex_worktree = (
                worktree_path.is_absolute()
                and worktree_path.parent == Path("/tmp")
                and worktree_path.name.startswith("codex_")
            )
            if is_temp_codex_worktree:
                if worktree_path.exists():
                    shutil.rmtree(worktree_path, ignore_errors=True)
                    removed_temp_dir = True
                logger.info("Cleaned up temp worktree at %s", worktree_path)
            else:
                subprocess.run(
                    ["git", "-C", str(base_repo_path), "worktree", "remove", str(worktree_path), "--force"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=max(self.timeout, 120),
                )
                logger.info("Cleaned up worktree at %s", worktree_path)
        except Exception as exc:
            logger.warning("Failed to clean up worktree %s: %s", worktree_path, exc)
        finally:
            # Always attempt filesystem cleanup, even if git worktree remove failed
            if not removed_temp_dir and worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            # Remove from tracking list to prevent unbounded growth
            _active_worktrees[:] = [(wp, br) for wp, br in _active_worktrees if wp != worktree_path]
            # Best-effort prune - don't let cleanup errors override successful apply/push
            if base_repo_path:
                try:
                    self._prune_stale_worktrees(base_repo_path)
                except Exception as prune_exc:
                    logger.warning("Worktree prune failed (best-effort): %s", prune_exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: list[str], *, parse_json: bool = False) -> str | dict:
        """Execute a codex CLI command and return stdout.

        Args:
            args: Arguments after ``codex``.
            parse_json: If True, parse stdout as JSON and return a dict.

        Returns:
            Raw stdout string, or parsed JSON dict when *parse_json* is True.

        Raises:
            subprocess.CalledProcessError: Non-zero exit.
            subprocess.TimeoutExpired: Command exceeded *self.timeout*.
            json.JSONDecodeError: *parse_json* is True but output is invalid.
        """
        cmd = [self.codex_bin, *args]
        logger.debug("Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self._codex_cli_timeout(),
            check=True,
        )
        stdout = result.stdout.strip()
        if parse_json:
            return json.loads(stdout)
        return stdout

    def _remote_branch_exists(self, worktree_str: str, branch: str) -> bool:
        """Return True when the branch already exists on origin."""
        result = subprocess.run(
            ["git", "-C", worktree_str, "ls-remote", "--heads", "origin", branch],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "git ls-remote failed"
            raise RuntimeError(f"Failed to query remote branch {branch!r}: {error_msg}")
        return result.stdout.strip() != ""

    def _prune_stale_worktrees(self, base_repo_path: Path) -> None:
        """Remove stale worktree metadata left behind by interrupted runs."""
        self._remove_initializing_worktree_metadata(base_repo_path)
        result = subprocess.run(
            ["git", "-C", str(base_repo_path), "worktree", "prune", "--verbose"],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if result.returncode != 0:
            logger.warning("git worktree prune failed: %s", result.stderr)

    def _remove_initializing_worktree_metadata(self, base_repo_path: Path) -> None:
        """Drop stale ``locked initializing`` metadata whose worktree path is gone."""
        worktrees_dir = base_repo_path / ".git" / "worktrees"
        if not worktrees_dir.exists():
            return

        for metadata_dir in worktrees_dir.iterdir():
            if not metadata_dir.is_dir():
                continue
            locked_file = metadata_dir / "locked"
            gitdir_file = metadata_dir / "gitdir"
            if not locked_file.exists() or not gitdir_file.exists():
                continue
            lock_reason = locked_file.read_text(encoding="utf-8", errors="ignore").strip().lower()
            if "initializing" not in lock_reason:
                continue
            gitdir_path = Path(gitdir_file.read_text(encoding="utf-8", errors="ignore").strip())
            worktree_path = gitdir_path.parent
            if worktree_path.exists():
                continue
            shutil.rmtree(metadata_dir, ignore_errors=True)
            logger.warning("Removed stale initializing worktree metadata: %s", metadata_dir)

    def _checkout_branch_at_target(self, worktree_str: str, branch: str, reset_target: str) -> None:
        """Create or reset a branch to a known target in one git operation.

        Uses -B (force) to handle cases where branch already exists.
        If that fails due to existing branch, try to delete and recreate.
        """
        result = subprocess.run(
            ["git", "-C", worktree_str, "checkout", "-B", branch, reset_target],
            capture_output=True,
            text=True,
            timeout=max(self.timeout, 120),
        )
        if result.returncode != 0:
            # If -B fails (e.g., branch exists), try deleting and recreating
            if "already exists" in result.stderr:
                subprocess.run(
                    ["git", "-C", worktree_str, "branch", "-D", branch],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                subprocess.run(
                    ["git", "-C", worktree_str, "checkout", "-b", branch, reset_target],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=max(self.timeout, 120),
                )
            else:
                # Re-raise for other errors
                raise subprocess.CalledProcessError(result.returncode, "git checkout", result.stderr)

    def _checkout_detached_target(self, worktree_str: str, reset_target: str) -> None:
        """Check out a target commit/ref in detached HEAD mode."""
        # Prefer `switch --detach <ref>` to avoid checkout argument parsing quirks
        # with remote branch names that include slash-separated path segments.
        switch_result = subprocess.run(
            ["git", "-C", worktree_str, "switch", "--detach", reset_target],
            capture_output=True,
            text=True,
            timeout=max(self.timeout, 120),
        )
        if switch_result.returncode == 0:
            return

        # Fallback for older git versions that may not support `switch`.
        subprocess.run(
            ["git", "-C", worktree_str, "checkout", "--detach", reset_target],
            capture_output=True,
            text=True,
            check=True,
            timeout=max(self.timeout, 120),
        )

    # ------------------------------------------------------------------
    # List / paginate
    # ------------------------------------------------------------------

    def list_tasks(
        self,
        limit: int = _MAX_PAGE_LIMIT,
        cursor: Optional[str] = None,
    ) -> dict:
        """Run ``codex cloud list --json`` and return parsed JSON.

        Returns:
            ``{"tasks": [...], "cursor": "..."}``
        """
        args = ["cloud", "list", "--json", "--limit", str(min(limit, _MAX_PAGE_LIMIT))]
        if self.env_id is not None:
            args.extend(["--env", self.env_id])
        if cursor is not None:
            args.extend(["--cursor", cursor])
        return self._run(args, parse_json=True)

    def list_all_tasks(self, max_pages: int = 10) -> list[dict]:
        """Paginate through tasks using cursor, up to *max_pages* pages.

        Returns:
            Flat list of task dicts.
        """
        all_tasks: list[dict] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            page = self.list_tasks(cursor=cursor)
            tasks = page.get("tasks", [])
            if not tasks:
                break
            all_tasks.extend(tasks)
            cursor = page.get("cursor")
            if not cursor:
                break
        return all_tasks

    # ------------------------------------------------------------------
    # Single-task operations
    # ------------------------------------------------------------------

    def get_status(self, task_id: str) -> str:
        """Run ``codex cloud status <TASK_ID>`` and return raw output."""
        return self._run(["cloud", "status", task_id])

    def get_diff(self, task_id: str, attempt: Optional[int] = None) -> str:
        """Run ``codex cloud diff <TASK_ID>`` and return unified diff."""
        args = ["cloud", "diff", task_id]
        if attempt is not None:
            args.extend(["--attempt", str(attempt)])
        return self._run(args)

    def apply_diff(self, task_id: str, attempt: Optional[int] = None) -> tuple[bool, str]:
        """Run ``codex cloud apply <TASK_ID>``.

        Returns:
            Tuple of (success, error_message). error_message is empty string on success.
        """
        args = ["cloud", "apply", task_id]
        if attempt is not None:
            args.extend(["--attempt", str(attempt)])
        try:
            self._run(args)
            return (True, "")
        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr or str(exc)
            logger.warning("apply failed for %s: %s", task_id, error_msg)
            return (False, error_msg)
        except subprocess.TimeoutExpired as exc:
            error_msg = str(exc)
            logger.warning("apply timed out for %s: %s", task_id, error_msg)
            return (False, error_msg)

    # ------------------------------------------------------------------
    # Apply and push workflow
    # ------------------------------------------------------------------

    def apply_and_push(self, task: dict, attempt: Optional[int] = None) -> dict:
        """Apply diff from task using worktree, commit changes, and push to remote.

        Args:
            task: Task dict with 'id', 'title', 'url' keys.
            attempt: Optional attempt number for codex cloud apply.

        Returns:
            Dict with 'success', 'branch', 'error' keys.
        """
        task_id = task["id"]
        task_title = task.get("title", "Codex task")
        task_url = task.get("url", "")
        branch = f"codex/{task_id[-8:]}"

        worktree_path = None
        base_repo_path = None
        try:
            base_repo_path = self._resolve_base_repo_path(task)
            # Create worktree
            worktree_path, base_branch = self._create_worktree(branch, base_repo_path)
            worktree_str = str(worktree_path)

            # Check if branch exists remotely first to handle rerun scenarios
            remote_branch_exists = self._remote_branch_exists(worktree_str, branch)

            if remote_branch_exists:
                # Remote branch exists, fetch and operate from detached remote HEAD.
                subprocess.run(
                    [
                        "git",
                        "-C",
                        worktree_str,
                        "fetch",
                        "origin",
                        f"+{branch}:refs/remotes/origin/{branch}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                )
                self._checkout_detached_target(worktree_str, f"origin/{branch}")
            else:
                # Avoid attaching a local branch in scratch worktrees: branch names may
                # already be active in sibling worktrees from prior runs.
                # Normalize base_branch to avoid "origin/origin/..." paths
                normalized_branch = base_branch[7:] if base_branch.startswith("origin/") else base_branch
                self._checkout_detached_target(worktree_str, f"origin/{normalized_branch}")

            # Get diff
            diff_text = self.get_diff(task_id, attempt=attempt)
            # FIX: Codex Cloud diff may not end with newline, causing "corrupt patch" error
            # Ensure diff ends with newline before applying
            if diff_text and not diff_text.endswith("\n"):
                diff_text = diff_text + "\n"
            if not diff_text or "No diff available" in diff_text:
                return {
                    "success": False,
                    "error": "No diff available for this task",
                    "task_id": task_id,
                }

            # Apply diff in worktree
            logger.info("Applying diff for %s", task_id)
            apply_result = subprocess.run(
                ["git", "-C", worktree_str, "apply", "--3way"],
                input=diff_text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if apply_result.returncode != 0:
                error_msg = apply_result.stderr or "Failed to apply diff"
                # DEBUG: Log first 500 chars of diff to diagnose corrupt patch
                logger.debug("Diff preview (first 500 chars) for %s: %s", task_id, diff_text[:500] if diff_text else "EMPTY")
                # Check for stale patch - target repo has changed since diff was generated
                # "patch does not apply" means the diff is outdated, not corrupt
                is_stale_patch = "patch does not apply" in error_msg.lower() or "does not exist in index" in error_msg.lower() or "corrupt patch" in error_msg.lower()
                # Retry without --3way if corrupt patch - sometimes Codex Cloud generates diffs
                # that work with plain apply but fail with 3-way merge
                if "corrupt patch" in error_msg.lower():
                    logger.info("Retrying apply without --3way for %s", task_id)
                    apply_result = subprocess.run(
                        ["git", "-C", worktree_str, "apply"],
                        input=diff_text,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                    if apply_result.returncode == 0:
                        logger.info("Retry succeeded for %s", task_id)
                    else:
                        error_msg = apply_result.stderr or "Failed to apply diff (retry)"
                        # DEBUG: Log diff preview on retry failure too
                        logger.debug("Retry diff preview (first 500 chars) for %s: %s", task_id, diff_text[:500] if diff_text else "EMPTY")
                        logger.debug("Retry stderr for %s: %s", task_id, error_msg)
                        is_stale_patch = is_stale_patch or ("patch does not apply" in error_msg.lower())
                if apply_result.returncode != 0:
                    logger.warning("Failed to apply diff for %s: %s", task_id, error_msg)
                    # Don't fallback to PR for stale patches - they won't apply anyway
                    allow_pr_fallback = not is_stale_patch and "corrupt patch" not in (error_msg or "").lower()
                    return {
                        "success": False,
                        "error": error_msg,
                        "task_id": task_id,
                        "fallback_to_pr": allow_pr_fallback,
                    }

            # Git add
            subprocess.run(
                ["git", "-C", worktree_str, "add", "."],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Git commit
            commit_msg = f"""{build_automation_commit_marker("codex-api")} codex: {task_title}

Applied from Codex Cloud task: {task_url}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""
            subprocess.run(
                ["git", "-C", worktree_str, "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Git push - use force to handle cases where remote branch already exists
            # (e.g., from previous failed runs where push succeeded but PR creation failed)
            if remote_branch_exists:
                # Use HEAD:{branch} for existing branch
                push_cmd = ["git", "-C", worktree_str, "push", "origin", "--force-with-lease", f"HEAD:{branch}"]
            else:
                # Worktree stays detached for scratch safety; push detached HEAD explicitly.
                push_cmd = ["git", "-C", worktree_str, "push", "origin", "--force", f"HEAD:{branch}"]
            subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            logger.info("Successfully pushed %s to branch %s", task_id, branch)
            return {
                "success": True,
                "branch": branch,
                "task_id": task_id,
            }

        except Exception as exc:
            error_msg = exc.stderr if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
            logger.error("apply_and_push failed for %s: %s", task_id, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id,
                "fallback_to_pr": True,
            }
        finally:
            # Always clean up the worktree
            if worktree_path:
                self._cleanup_worktree(worktree_path, base_repo_path)

    def _parse_metadata_from_pr(self, pr_number: str, repo_full: Optional[str] = None) -> Optional[dict]:
        """Parse CODEX_METADATA from PR body and comments.

        Returns dict with task_id, branch, pr_number or None if not found.
        """
        try:
            # Get PR body and comments
            cmd = ["gh", "pr", "view", pr_number, "--json", "body,comments"]
            if repo_full:
                cmd.extend(["--repo", repo_full])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
                cwd=str(self.repo_path) if self.repo_path and not repo_full else None,
            )

            data = json.loads(result.stdout)
            body = data.get("body", "")
            comments = data.get("comments", [])

            # Search in body first, then comments
            all_text = [body] + [c.get("body", "") for c in comments]

            for text in all_text:
                # Look for <!-- CODEX_METADATA ... --> blocks
                match = re.search(
                    r"<!--\s*CODEX_METADATA\s*\nTask:\s*(\S+)\s*\nPR:\s*#(\d+)\s*\nBranch:\s*(\S+)",
                    text,
                    re.MULTILINE
                )
                if match:
                    return {
                        "task_id": match.group(1),
                        "pr_number": match.group(2),
                        "branch": match.group(3),
                    }

            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            logger.debug("Failed to parse metadata from PR %s: %s", pr_number, exc)
            return None

    def _find_existing_pr_by_task_id(self, task_id: str, repo_full: Optional[str] = None) -> Optional[tuple[str, str]]:
        """Find existing PR by the deterministic task branch name.

        Returns (branch, pr_url) or None.
        """
        try:
            branch = f"codex/{task_id[-8:]}"
            cmd = ["gh", "pr", "list", "--json", "number,headRefName,url", "--limit", "50", "--head", branch]
            if repo_full:
                cmd.extend(["--repo", repo_full])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
                cwd=str(self.repo_path) if self.repo_path and not repo_full else None,
            )

            prs = json.loads(result.stdout)
            for pr in prs:
                if pr.get("headRefName") == branch:
                    return (branch, pr["url"])

            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to search PR by task_id: %s", exc)
            return None

    def _find_existing_pr_branch(
        self,
        task_title: str,
        task_id: str = None,
        repo_full: Optional[str] = None,
    ) -> Optional[tuple[str, str]]:
        """Find existing open PR by task_id (preferred) or title match.

        Args:
            task_title: Task title, may include "Github Mention: " prefix.
            task_id: Optional task ID to search metadata first.

        Returns:
            (branch_name, pr_url) if found, None otherwise.
        """
        # Try task_id match first (most reliable)
        if task_id:
            result = self._find_existing_pr_by_task_id(task_id, repo_full=repo_full)
            if result:
                logger.info("Found existing PR by task_id %s", task_id)
                return result

        # Fallback to title match
        search_title = re.sub(r"^GitHub? Mention:\s*", "", task_title, flags=re.IGNORECASE).strip()

        try:
            # Search for open PRs with matching title
            cmd = ["gh", "pr", "list", "--json", "number,title,headRefName,url", "--limit", "50"]
            if repo_full:
                cmd.extend(["--repo", repo_full])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
                cwd=str(self.repo_path) if self.repo_path and not repo_full else None,
            )

            prs = json.loads(result.stdout)
            for pr in prs:
                pr_title = pr.get("title", "")
                # Check if titles match (case-insensitive, ignore GitHub Mention prefix)
                pr_title_clean = re.sub(r"^GitHub? Mention:\s*", "", pr_title, flags=re.IGNORECASE).strip()
                if pr_title_clean.lower() == search_title.lower():
                    logger.info("Found existing PR by title match")
                    return (pr["headRefName"], pr["url"])

            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to search for existing PR: %s", exc)
            return None

    def create_pr_from_diff(self, task: dict, attempt: Optional[int] = None) -> dict:
        """Create PR from diff using a temporary worktree.

        Args:
            task: Task dict with 'id', 'title', 'url' keys.
            attempt: Optional attempt number.

        Returns:
            Dict with 'success', 'pr_url', 'branch', 'has_conflicts', 'error', 'updated_existing' keys.
        """
        task_id = task["id"]
        task_title = task.get("title", "Codex task")
        task_url = task.get("url", "")

        repo_full = self._resolve_repo_full(task)

        # Check for existing PR first (by task_id from metadata, then by title)
        existing_pr = self._find_existing_pr_branch(task_title, task_id=task_id, repo_full=repo_full)
        if existing_pr:
            branch, pr_url = existing_pr
            logger.info("Found existing PR for task %s: %s (branch: %s)", task_id, pr_url, branch)
            updated_existing = True
        else:
            # Generate new branch name from task ID
            branch = f"codex/{task_id[-8:]}"
            pr_url = None
            updated_existing = False
            logger.info("No existing PR found for task %s, will create new PR", task_id)

        # Create worktree
        worktree_path = None
        base_repo_path = None
        try:
            base_repo_path = self._resolve_base_repo_path(task)
            worktree_path, base_branch = self._create_worktree(branch, base_repo_path)
            worktree_str = str(worktree_path)

            # Get diff
            diff_text = self.get_diff(task_id, attempt=attempt)
            # FIX: Codex Cloud diff may not end with newline, causing "corrupt patch" error
            # Ensure diff ends with newline before applying
            if diff_text and not diff_text.endswith("\n"):
                diff_text = diff_text + "\n"
            if not diff_text or "No diff available" in diff_text:
                return {
                    "success": False,
                    "error": "No diff available for this task",
                    "task_id": task_id,
                }

            checked_out_detached = False
            if updated_existing:
                # Fetch and checkout existing branch
                try:
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            worktree_str,
                            "fetch",
                            "origin",
                            f"+{branch}:refs/remotes/origin/{branch}",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=self.timeout,
                    )
                    self._checkout_detached_target(worktree_str, f"origin/{branch}")
                    checked_out_detached = True
                except subprocess.CalledProcessError as e:
                    error_msg = (e.stderr or str(e)).strip()
                    logger.error(
                        "Failed to fetch existing PR branch %s for task %s: %s",
                        branch,
                        task_id,
                        error_msg,
                    )
                    return {
                        "success": False,
                        "error": f"Failed to update existing PR branch {branch}: {error_msg}",
                        "task_id": task_id,
                    }
            else:
                # Check if branch already exists on remote (from previous failed run)
                remote_exists = self._remote_branch_exists(worktree_str, branch)
                if remote_exists:
                    # Fetch and update existing branch
                    try:
                        subprocess.run(
                            [
                                "git",
                                "-C",
                                worktree_str,
                                "fetch",
                                "origin",
                                f"+{branch}:refs/remotes/origin/{branch}",
                            ],
                            capture_output=True,
                            text=True,
                            check=True,
                            timeout=self.timeout,
                        )
                        self._checkout_detached_target(worktree_str, f"origin/{branch}")
                        checked_out_detached = True
                    except Exception as e:
                        # Branch may have been deleted or force-pushed after _remote_branch_exists check
                        # Fall back to treating as new branch
                        logger.warning("Failed to checkout existing branch %s: %s", branch, e)
                        logger.info("Falling back to new branch for task %s", task_id)
                        normalized_base = base_branch[7:] if base_branch.startswith("origin/") else base_branch
                        self._checkout_branch_at_target(worktree_str, branch, f"origin/{normalized_base}")
                        checked_out_detached = False
                else:
                    self._checkout_branch_at_target(worktree_str, branch, base_branch)
                    checked_out_detached = False

            # Apply diff with 3-way merge (creates conflict markers if needed)
            apply_result = subprocess.run(
                ["git", "-C", worktree_str, "apply", "--3way"],
                input=diff_text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            has_conflicts = apply_result.returncode != 0
            apply_stderr = (apply_result.stderr or "").strip()

            if has_conflicts:
                # Check for stale patch - target repo has changed since diff was generated
                # "patch does not apply" or "does not exist in index" means diff is stale
                is_stale_patch = "patch does not apply" in apply_stderr.lower() or "does not exist in index" in apply_stderr.lower() or "corrupt patch" in apply_stderr.lower()

                # Retry without --3way if corrupt patch - sometimes Codex Cloud generates diffs
                # that work with plain apply but fail with 3-way merge
                if "corrupt patch" in apply_stderr.lower():
                    logger.info("Retrying apply without --3way for %s", task_id)
                    apply_result = subprocess.run(
                        ["git", "-C", worktree_str, "apply"],
                        input=diff_text,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                    )
                    if apply_result.returncode == 0:
                        logger.info("Retry succeeded for %s", task_id)
                        has_conflicts = False
                        apply_stderr = ""
                    else:
                        # Check if retry also failed with stale patch
                        is_stale_patch = is_stale_patch or ("patch does not apply" in (apply_result.stderr or "").lower())
                        if is_stale_patch:
                            logger.warning("Stale diff - patch does not apply to current repo state for %s", task_id)
                            return {
                                "success": False,
                                "error": "Stale diff - target repo has changed since task was created",
                                "task_id": task_id,
                            }
                        return {
                            "success": False,
                            "error": apply_result.stderr or "Failed to apply diff (retry)",
                            "task_id": task_id,
                        }
                # If it's a stale patch that wasn't caught above, fail early
                if is_stale_patch and has_conflicts:
                    logger.warning("Stale diff - patch does not apply to current repo state for %s", task_id)
                    return {
                        "success": False,
                        "error": "Stale diff - target repo has changed since task was created",
                        "task_id": task_id,
                    }
                # When conflicts occur, git apply leaves files in unmerged state
                # Get list of unmerged files and accept incoming changes
                unmerged_result = subprocess.run(
                    ["git", "-C", worktree_str, "diff", "--name-only", "--diff-filter=U"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                unmerged_files = unmerged_result.stdout.strip().split("\n")

                # Accept incoming changes for each conflicted file
                for file_path in unmerged_files:
                    if file_path:  # Skip empty lines
                        subprocess.run(
                            ["git", "-C", worktree_str, "checkout", "--theirs", file_path],
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                        )

            # Stage all changes (including resolved conflicts)
            subprocess.run(
                ["git", "-C", worktree_str, "add", "-A"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            staged_changes = subprocess.run(
                ["git", "-C", worktree_str, "diff", "--cached", "--quiet"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            # Only returncode 0 means no staged changes; returncode 1 means changes staged
            # Any other returncode (e.g., 2 for errors) should be treated as an error
            if staged_changes.returncode == 0:
                return {
                    "success": False,
                    "error": "no staged changes after fallback apply",
                    "task_id": task_id,
                }
            elif staged_changes.returncode > 1:
                return {
                    "success": False,
                    "error": f"git diff --cached failed with code {staged_changes.returncode}: {staged_changes.stderr}",
                    "task_id": task_id,
                }

            # Commit
            conflict_note = " (with conflicts - needs resolution)" if has_conflicts else ""
            commit_msg = f"""{build_automation_commit_marker("codex-api")} codex: {task_title}{conflict_note}

Applied from Codex Cloud task: {task_url}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""
            commit_result = subprocess.run(
                ["git", "-C", worktree_str, "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if commit_result.returncode != 0:
                logger.warning("Commit failed for %s: %s", task_id, commit_result.stderr)
                if "nothing to commit" in commit_result.stderr.lower():
                    logger.info("Nothing to commit for %s, checking for existing changes", task_id)
                    status_result = subprocess.run(
                        ["git", "-C", worktree_str, "status", "--porcelain"],
                        capture_output=True, text=True, timeout=30,
                    )
                    logger.warning("Git status for %s: %s", task_id, status_result.stdout)
                    return {
                        "success": False,
                        "error": f"nothing to commit: {status_result.stdout[:200]}",
                        "task_id": task_id,
                    }
                # Any other commit failure should not fall through to push
                error_msg = (commit_result.stderr or commit_result.stdout or "git commit failed").strip()
                return {
                    "success": False,
                    "error": error_msg,
                    "task_id": task_id,
                }
            else:
                logger.info("Committed changes for %s", task_id)

            # Push branch - use force-with-lease for safety (not --force which negates it)
            # Use HEAD:{branch} when in detached HEAD mode (remote_exists but no local branch)
            # But first verify the branch exists on remote to avoid "not a full refname" error
            try:
                branch_on_remote = self._remote_branch_exists(worktree_str, branch)
            except Exception:
                branch_on_remote = False  # If we can't check, assume new branch

            if branch_on_remote:
                if updated_existing:
                    # Updating known existing PR/branch: keep lease protection.
                    push_cmd = ["git", "-C", worktree_str, "push", "origin", "--force-with-lease", f"HEAD:{branch}"]
                else:
                    # We fell back to treating this as a new branch but remote may still
                    # exist; lease checks can be stale in that path, so force-update.
                    push_cmd = ["git", "-C", worktree_str, "push", "origin", "--force", f"HEAD:{branch}"]
            else:
                if checked_out_detached:
                    # Existing branch may have disappeared after checkout; detached HEAD cannot
                    # push local branch names, so push explicit HEAD ref.
                    push_cmd = ["git", "-C", worktree_str, "push", "origin", f"HEAD:{branch}"]
                else:
                    # Use -u for new local branch
                    push_cmd = ["git", "-C", worktree_str, "push", "-u", "origin", branch]

            subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Create PR only if this is a new branch
            if not updated_existing:
                summary = task.get("summary", {})
                conflict_warning = "\n\n⚠️ **This PR contains merge conflicts that need to be resolved.**" if has_conflicts else ""
                pr_body = f"""Applied from Codex Cloud task: {task_url}

## Changes
{summary.get("files_changed", 0)} files changed: +{summary.get("lines_added", 0)}/-{summary.get("lines_removed", 0)}{conflict_warning}

🤖 Generated with Codex Cloud via CLI API
"""
                result = subprocess.run(
                    ["gh", "pr", "create", "--head", branch, "--title", task_title, "--body", pr_body]
                    + (["--repo", repo_full] if repo_full else []),
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                    cwd=worktree_str,
                )
                pr_url = result.stdout.strip()

                # Extract PR number from URL (e.g., https://github.com/owner/repo/pull/123 -> 123)
                pr_number = pr_url.rstrip('/').split('/')[-1]

                # Post metadata comment for future parsing
                metadata_comment = f"""<!-- CODEX_METADATA
Task: {task_id}
PR: #{pr_number}
Branch: {branch}
Task URL: {task_url}
-->
✅ Applied changes from [Codex Cloud task {task_id}]({task_url})
📋 **Metadata:** PR #{pr_number} | Branch: `{branch}`"""

                comment_result = subprocess.run(
                    ["gh", "pr", "comment", pr_number, "--body", metadata_comment]
                    + (["--repo", repo_full] if repo_full else []),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=worktree_str,
                )
                if comment_result.returncode != 0:
                    logger.warning("Failed to post metadata comment: %s", comment_result.stderr)

                logger.info("Created PR for %s: %s (conflicts: %s)", task_id, pr_url, has_conflicts)
            else:
                # Post update comment to existing PR
                pr_number = pr_url.rstrip('/').split('/')[-1]
                update_comment = f"""<!-- CODEX_METADATA
Task: {task_id}
PR: #{pr_number}
Branch: {branch}
Task URL: {task_url}
-->
🔄 Updated from [Codex Cloud task {task_id}]({task_url})
📋 **Metadata:** PR #{pr_number} | Branch: `{branch}`"""

                comment_result = subprocess.run(
                    ["gh", "pr", "comment", pr_number, "--body", update_comment]
                    + (["--repo", repo_full] if repo_full else []),
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=worktree_str,
                )
                if comment_result.returncode != 0:
                    logger.warning("Failed to post update comment: %s", comment_result.stderr)

                logger.info("Updated existing PR %s for %s (conflicts: %s)", pr_url, task_id, has_conflicts)

            return {
                "success": True,
                "pr_url": pr_url,
                "branch": branch,
                "has_conflicts": has_conflicts,
                "updated_existing": updated_existing,
                "task_id": task_id,
            }

        except Exception as exc:
            error_msg = str(exc)
            if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
                error_msg = exc.stderr
            logger.error("create_pr_from_diff failed for %s: %s", task_id, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id,
            }
        finally:
            # Always clean up the worktree
            if worktree_path:
                self._cleanup_worktree(worktree_path, base_repo_path)

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    @staticmethod
    def filter_github_mentions(tasks: list[dict]) -> list[dict]:
        """Return tasks whose title starts with ``GitHub Mention:`` (case-insensitive)."""
        return [
            t
            for t in tasks
            if t.get("title", "").lower().startswith("github mention:")
        ]

    @staticmethod
    def filter_by_status(tasks: list[dict], status: str) -> list[dict]:
        """Return tasks matching *status* (ready, pending, running, etc)."""
        return [t for t in tasks if t.get("status") == status]

    @staticmethod
    def filter_has_changes(tasks: list[dict]) -> list[dict]:
        """Return tasks that have file changes (files_changed > 0)."""
        return [t for t in tasks if (t.get("summary") or {}).get("files_changed", 0) > 0]
