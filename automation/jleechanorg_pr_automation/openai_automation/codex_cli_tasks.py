"""
Codex CLI API — list, status, and diff operations via ``codex cloud`` CLI.

Replaces browser-based automation with direct API calls through the
official OpenAI Codex CLI (authenticated, no Cloudflare).
"""

import json
import logging
import re
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# Default binary name; overridden in constructor if needed.
_DEFAULT_CODEX_BIN = "codex"

# Maximum items per page (CLI hard limit is 20).
_MAX_PAGE_LIMIT = 20


class CodexCloudAPI:
    """Wraps ``codex cloud`` CLI subcommands for task management."""

    def __init__(
        self,
        codex_bin: str = _DEFAULT_CODEX_BIN,
        env_id: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Args:
            codex_bin: Path or name of the codex binary.
            env_id: Optional environment filter for list/exec commands.
            timeout: Subprocess timeout in seconds per CLI call.
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
            timeout=self.timeout,
            check=True,
        )
        stdout = result.stdout.strip()
        if parse_json:
            return json.loads(stdout)
        return stdout

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
        """Apply diff from task, commit changes, and push to remote.

        Args:
            task: Task dict with 'id', 'title', 'url' keys.
            attempt: Optional attempt number for codex cloud apply.

        Returns:
            Dict with 'success', 'branch', 'error' keys.
        """
        task_id = task["id"]
        task_title = task.get("title", "Codex task")
        task_url = task.get("url", "")

        try:
            # 1. Apply diff
            logger.info("Applying diff for %s", task_id)
            success, error_msg = self.apply_diff(task_id, attempt=attempt)
            if not success:
                return {
                    "success": False,
                    "error": error_msg or f"Failed to apply diff for {task_id}",
                    "task_id": task_id,
                }

            # 2. Get current branch
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            ).stdout.strip()

            # 3. Git add
            subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # 4. Git commit
            commit_msg = f"""codex: {task_title}

Applied from Codex Cloud task: {task_url}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # 5. Git push
            subprocess.run(
                ["git", "push", "origin", branch],
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

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            error_msg = exc.stderr if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
            logger.error("apply_and_push failed for %s: %s", task_id, error_msg)
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id,
            }

    def _parse_metadata_from_pr(self, pr_number: str) -> Optional[dict]:
        """Parse CODEX_METADATA from PR body and comments.

        Returns dict with task_id, branch, pr_number or None if not found.
        """
        try:
            # Get PR body and comments
            result = subprocess.run(
                ["gh", "pr", "view", pr_number, "--json", "body,comments"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
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

    def _find_existing_pr_by_task_id(self, task_id: str) -> Optional[tuple[str, str]]:
        """Find existing PR by task_id from metadata comments.

        Returns (branch, pr_url) or None.
        """
        try:
            # Get list of open PRs
            result = subprocess.run(
                ["gh", "pr", "list", "--json", "number,headRefName,url", "--limit", "50"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            prs = json.loads(result.stdout)
            for pr in prs:
                pr_number = str(pr["number"])
                metadata = self._parse_metadata_from_pr(pr_number)

                if metadata and metadata["task_id"] == task_id:
                    return (metadata["branch"], pr["url"])

            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            logger.warning("Failed to search PR by task_id: %s", exc)
            return None

    def _find_existing_pr_branch(self, task_title: str, task_id: str = None) -> Optional[tuple[str, str]]:
        """Find existing open PR by task_id (preferred) or title match.

        Args:
            task_title: Task title, may include "Github Mention: " prefix.
            task_id: Optional task ID to search metadata first.

        Returns:
            (branch_name, pr_url) if found, None otherwise.
        """
        # Try task_id match first (most reliable)
        if task_id:
            result = self._find_existing_pr_by_task_id(task_id)
            if result:
                logger.info("Found existing PR by task_id %s", task_id)
                return result

        # Fallback to title match
        search_title = re.sub(r"^GitHub? Mention:\s*", "", task_title, flags=re.IGNORECASE).strip()

        try:
            # Search for open PRs with matching title
            result = subprocess.run(
                ["gh", "pr", "list", "--json", "number,title,headRefName,url", "--limit", "50"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
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
        """Create PR from diff, or update existing PR if one exists with matching title.

        Args:
            task: Task dict with 'id', 'title', 'url' keys.
            attempt: Optional attempt number.

        Returns:
            Dict with 'success', 'pr_url', 'branch', 'has_conflicts', 'error', 'updated_existing' keys.
        """
        task_id = task["id"]
        task_title = task.get("title", "Codex task")
        task_url = task.get("url", "")

        # Clean up any leftover git state from previous failed operations
        try:
            # Try to return to a clean state (main/master) before starting
            # This handles cases where a previous attempt left a commit on a temporary branch
            for main_branch in ["main", "master"]:
                res = subprocess.run(["git", "rev-parse", "--verify", main_branch], capture_output=True, text=True)
                if res.returncode == 0:
                    subprocess.run(["git", "checkout", main_branch], capture_output=True, timeout=self.timeout)
                    subprocess.run(["git", "reset", "--hard", f"origin/{main_branch}"], capture_output=True, timeout=self.timeout)
                    break
            subprocess.run(["git", "clean", "-fd"], capture_output=True, timeout=self.timeout)
        except:
            pass  # Best effort cleanup

        # Check for existing PR first (by task_id from metadata, then by title)
        existing_pr = self._find_existing_pr_branch(task_title, task_id=task_id)
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

        try:
            # Get diff
            diff_text = self.get_diff(task_id, attempt=attempt)
            if not diff_text or "No diff available" in diff_text:
                return {
                    "success": False,
                    "error": "No diff available for this task",
                    "task_id": task_id,
                }

            # Get current branch to return to later
            original_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            ).stdout.strip()

            if updated_existing:
                # Fetch and checkout existing branch
                subprocess.run(
                    ["git", "fetch", "origin", branch],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                )
                subprocess.run(
                    ["git", "checkout", branch],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                )
                # Reset to remote version to start fresh
                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{branch}"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                )
            else:
                # Create and checkout new branch
                subprocess.run(
                    ["git", "checkout", "-b", branch],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
                )

            # Apply diff with 3-way merge (creates conflict markers if needed)
            apply_result = subprocess.run(
                ["git", "apply", "--3way"],
                input=diff_text,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            has_conflicts = apply_result.returncode != 0

            if has_conflicts:
                # When conflicts occur, git apply leaves files in unmerged state
                # Get list of unmerged files and accept incoming changes
                unmerged_result = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=U"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                unmerged_files = unmerged_result.stdout.strip().split("\n")

                # Accept incoming changes for each conflicted file
                for file_path in unmerged_files:
                    if file_path:  # Skip empty lines
                        subprocess.run(
                            ["git", "checkout", "--theirs", file_path],
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                        )

            # Stage all changes (including resolved conflicts)
            subprocess.run(
                ["git", "add", "-A"],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Commit
            conflict_note = " (with conflicts - needs resolution)" if has_conflicts else ""
            commit_msg = f"""codex: {task_title}{conflict_note}

Applied from Codex Cloud task: {task_url}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Push branch (force-with-lease for existing branches)
            push_cmd = ["git", "push", "origin"]
            if updated_existing:
                push_cmd.append("--force-with-lease")
            else:
                push_cmd.append("-u")
            push_cmd.append(branch)

            subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.timeout,
            )

            # Return to original branch
            subprocess.run(
                ["git", "checkout", original_branch],
                capture_output=True,
                text=True,
                check=False,  # Don't fail if this doesn't work
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
                    ["gh", "pr", "create", "--head", branch, "--title", task_title, "--body", pr_body],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self.timeout,
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

                subprocess.run(
                    ["gh", "pr", "comment", pr_number, "--body", metadata_comment],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

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

                subprocess.run(
                    ["gh", "pr", "comment", pr_number, "--body", update_comment],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                logger.info("Updated existing PR %s for %s (conflicts: %s)", pr_url, task_id, has_conflicts)
            return {
                "success": True,
                "pr_url": pr_url,
                "branch": branch,
                "has_conflicts": has_conflicts,
                "updated_existing": updated_existing,
                "task_id": task_id,
            }

        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr if exc.stderr else str(exc)
            logger.error("create_pr_from_diff failed for %s: %s", task_id, error_msg)
            # Try to return to original branch on error
            try:
                subprocess.run(["git", "checkout", original_branch], capture_output=True, timeout=self.timeout)
                # Delete the failed branch
                subprocess.run(["git", "branch", "-D", branch], capture_output=True, timeout=self.timeout)
            except:
                pass
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id,
            }

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
