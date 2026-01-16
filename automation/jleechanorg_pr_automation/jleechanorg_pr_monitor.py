#!/usr/bin/env python3
"""
jleechanorg PR Monitor - Cross-Organization Automation

Discovers and processes open PRs across the jleechanorg organization by
posting configurable automation comments with safety limits integration.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from collections import Counter
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Threshold for detecting stale queued comments (hours)
# Comments older than this threshold without a completion marker are considered stale
# and allow re-running the fix-comment agent (handles cases where agent failed silently)
STALE_QUEUE_THRESHOLD_HOURS = 1.0

from orchestration.task_dispatcher import CLI_PROFILES, TaskDispatcher

from .automation_safety_manager import AutomationSafetyManager
from .automation_utils import AutomationUtils
from .codex_config import (
    CODEX_COMMIT_MARKER_PREFIX as SHARED_MARKER_PREFIX,
)
from .codex_config import (
    CODEX_COMMIT_MARKER_SUFFIX as SHARED_MARKER_SUFFIX,
)
from .codex_config import (
    FIX_COMMENT_MARKER_PREFIX as SHARED_FIX_COMMENT_PREFIX,
)
from .codex_config import (
    FIX_COMMENT_MARKER_SUFFIX as SHARED_FIX_COMMENT_SUFFIX,
)
from .codex_config import (
    FIX_COMMENT_RUN_MARKER_PREFIX as SHARED_FIX_COMMENT_RUN_PREFIX,
)
from .codex_config import (
    FIX_COMMENT_RUN_MARKER_SUFFIX as SHARED_FIX_COMMENT_RUN_SUFFIX,
)
from .codex_config import (
    FIXPR_MARKER_PREFIX as SHARED_FIXPR_PREFIX,
)
from .codex_config import (
    FIXPR_MARKER_SUFFIX as SHARED_FIXPR_SUFFIX,
)
from .codex_config import (
    build_automation_marker,
    build_comment_intro,
)
from .orchestrated_pr_runner import (
    chdir,
    dispatch_agent_for_pr,
    dispatch_agent_for_pr_with_task,
    ensure_base_clone,
    has_failing_checks,
)
from .utils import json_manager, setup_logging


def _parse_fixpr_agent_chain(value: str) -> str:
    """Parse comma-separated CLI chain for --fixpr-agent (e.g., 'gemini,codex')."""
    if not isinstance(value, str) or not value.strip():
        raise argparse.ArgumentTypeError("--fixpr-agent must be a non-empty string")

    parts = [part.strip().lower() for part in value.split(",")]
    chain = [part for part in parts if part]
    if not chain:
        raise argparse.ArgumentTypeError("--fixpr-agent chain is empty")

    invalid = [cli for cli in chain if cli not in CLI_PROFILES]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Invalid --fixpr-agent CLI(s): {invalid}. Must be subset of {list(CLI_PROFILES.keys())}"
        )

    # De-duplicate while preserving order
    seen = set()
    ordered = []
    for cli in chain:
        if cli not in seen:
            ordered.append(cli)
            seen.add(cli)
    return ",".join(ordered)


def _positive_int_arg(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"Expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"Value must be >= 1, got {parsed}")
    return parsed


def _normalize_model(model: str | None) -> str | None:
    """Return a sanitized model value compatible with orchestration/TaskDispatcher.

    Rejects values that fail TaskDispatcher's model regex.
    """
    if model is None:
        return None

    raw = str(model).strip()
    if not raw:
        return None

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw):
        raise argparse.ArgumentTypeError(
            f"Invalid --model value {raw!r}. Allowed: letters, numbers, '.', '_', '-'."
        )

    return raw


class JleechanorgPRMonitor:
    """Cross-organization PR monitoring with Codex automation comments"""

    def _determine_workflow_type(self, fix_comment: bool, fixpr: bool = False) -> str:
        """Determine workflow type from execution context"""
        if fix_comment:
            return "fix_comment"
        if fixpr:
            return "fixpr"
        return "pr_automation"

    def _redact_email(self, email: str | None) -> str | None:
        """Redact email for logging while preserving domain for debugging"""
        if not email or "@" not in email:
            return email
        user, domain = email.rsplit("@", 1)
        if len(user) <= 2:
            return f"***@{domain}"
        return f"{user[:2]}***@{domain}"

    CODEX_COMMIT_MARKER_PREFIX = SHARED_MARKER_PREFIX
    CODEX_COMMIT_MARKER_SUFFIX = SHARED_MARKER_SUFFIX
    FIX_COMMENT_MARKER_PREFIX = SHARED_FIX_COMMENT_PREFIX
    FIX_COMMENT_MARKER_SUFFIX = SHARED_FIX_COMMENT_SUFFIX
    FIX_COMMENT_RUN_MARKER_PREFIX = SHARED_FIX_COMMENT_RUN_PREFIX
    FIX_COMMENT_RUN_MARKER_SUFFIX = SHARED_FIX_COMMENT_RUN_SUFFIX
    FIXPR_MARKER_PREFIX = SHARED_FIXPR_PREFIX
    FIXPR_MARKER_SUFFIX = SHARED_FIXPR_SUFFIX
    CODEX_COMMIT_MESSAGE_MARKER = "[codex-automation-commit]"
    CODEX_BOT_IDENTIFIER = "codex"
    FIX_COMMENT_COMPLETION_MARKER = "Fix-comment automation complete"
    # GitHub short SHAs display with a minimum of 7 characters, while full SHAs are 40 characters.
    CODEX_COMMIT_SHA_LENGTH_RANGE: tuple[int, int] = (7, 40)
    CODEX_SUMMARY_COMMIT_PATTERNS = [
        re.compile(
            rf"/blob/([0-9a-fA-F]{{{CODEX_COMMIT_SHA_LENGTH_RANGE[0]},{CODEX_COMMIT_SHA_LENGTH_RANGE[1]}}})/"
        ),
        re.compile(
            rf"/commit/([0-9a-fA-F]{{{CODEX_COMMIT_SHA_LENGTH_RANGE[0]},{CODEX_COMMIT_SHA_LENGTH_RANGE[1]}}})"
        ),
        # Cursor Bugbot summaries reference the pending Codex commit in prose, e.g.
        # "Written by Cursor Bugbot for commit c279655."
        re.compile(
            rf"\bcommit\b[^0-9a-fA-F]{{0,5}}([0-9a-fA-F]{{{CODEX_COMMIT_SHA_LENGTH_RANGE[0]},{CODEX_COMMIT_SHA_LENGTH_RANGE[1]}}})",
            re.IGNORECASE,
        ),
    ]

    _HEAD_COMMIT_DETAILS_QUERY = """
        query($owner: String!, $name: String!, $prNumber: Int!) {
          repository(owner: $owner, name: $name) {
            pullRequest(number: $prNumber) {
              headRefOid
              commits(last: 1) {
                nodes {
                  commit {
                    oid
                    messageHeadline
                    message
                    author {
                      email
                      name
                      user { login }
                    }
                    committer {
                      email
                      name
                      user { login }
                    }
                  }
                }
              }
            }
          }
        }
        """

    _codex_actor_keywords = [
        "codex",
        "coderabbitai",
        "coderabbit",
        "copilot",
        "cursor",
    ]
    _codex_actor_patterns = [
        re.compile(rf"\b{keyword}\b", re.IGNORECASE)
        for keyword in _codex_actor_keywords
    ]
    _codex_commit_message_pattern_str = (
        r"\[(?:fixpr\s+)?(?:" + "|".join(_codex_actor_keywords) + r")-automation-commit\]"
    )
    _codex_commit_message_pattern = re.compile(
        _codex_commit_message_pattern_str,
        re.IGNORECASE,
    )

    # Known GitHub review bots that may appear without [bot] suffix in API responses.
    # Note: Some bots (e.g., "coderabbitai", "copilot") appear in both this list and
    # _codex_actor_keywords. This is intentional:
    # - KNOWN_GITHUB_BOTS: Detects the review service (e.g., "coderabbitai" or "coderabbitai[bot]")
    #   whose comments should trigger PR re-processing.
    # - _codex_actor_keywords: Used to exclude our own automation bots from being
    #   treated as external review bots when they have the [bot] suffix.
    # The detection order in _is_github_bot_comment() ensures known bots are detected first.
    KNOWN_GITHUB_BOTS = frozenset({
        "github-actions",
        "coderabbitai",
        "copilot-swe-agent",
        "dependabot",
        "renovate",
        "codecov",
        "sonarcloud",
    })

    @staticmethod
    def _extract_actor_fields(
        actor: dict | None,
    ) -> tuple[str | None, str | None, str | None]:
        if not isinstance(actor, dict):
            return (None, None, None)

        user_info = actor.get("user")
        login = user_info.get("login") if isinstance(user_info, dict) else None
        email = actor.get("email")
        name = actor.get("name")
        return (login, email, name)

    def __init__(self, *, safety_limits: dict[str, int] | None = None, no_act: bool = False, automation_username: str | None = None):
        self.logger = setup_logging(__name__)
        self._explicit_automation_username = automation_username

        self.assistant_mentions = os.environ.get(
            "AI_ASSISTANT_MENTIONS",
            "@codex @coderabbitai @copilot @cursor",
        )

        self.wrapper_managed = os.environ.get("AUTOMATION_SAFETY_WRAPPER") == "1"
        self.no_act = bool(no_act)

        # Processing history persisted to permanent location
        self.history_base_dir = Path.home() / "Library" / "Logs" / "worldarchitect-automation" / "pr_history"
        self.history_base_dir.mkdir(parents=True, exist_ok=True)

        # Organization settings
        self.organization = "jleechanorg"
        self.base_project_dir = Path.home() / "projects"

        safety_data_dir = os.environ.get("AUTOMATION_SAFETY_DATA_DIR")
        if not safety_data_dir:
            default_dir = Path.home() / "Library" / "Application Support" / "worldarchitect-automation"
            default_dir.mkdir(parents=True, exist_ok=True)
            safety_data_dir = str(default_dir)

        self.safety_manager = AutomationSafetyManager(safety_data_dir, limits=safety_limits)

        # Resolve automation username (CLI > Env > Dynamic)
        # Note: CLI arg is passed via __init__ if we update signature, but for now we'll handle it
        # by checking if it was set after init or passing it in.
        # Actually, let's update __init__ signature to accept it.
        self.automation_username = self._resolve_automation_username()

        self.logger.info("🏢 Initialized jleechanorg PR monitor")
        self.logger.info(f"📁 History storage: {self.history_base_dir}")
        self.logger.info("💬 Comment-only automation mode")
    def _get_history_file(self, repo_name: str, branch_name: str) -> Path:
        """Get history file path for specific repo/branch"""
        repo_dir = self.history_base_dir / repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Replace slashes in branch names to avoid creating nested directories
        safe_branch_name = branch_name.replace("/", "_")
        return repo_dir / f"{safe_branch_name}.json"

    def _load_branch_history(self, repo_name: str, branch_name: str) -> dict[str, str]:
        """Load processed PRs for a specific repo/branch"""
        history_file = self._get_history_file(repo_name, branch_name)
        return json_manager.read_json(str(history_file), {})

    def _save_branch_history(self, repo_name: str, branch_name: str, history: dict[str, str]) -> None:
        """Save processed PRs for a specific repo/branch"""
        history_file = self._get_history_file(repo_name, branch_name)
        if not json_manager.write_json(str(history_file), history):
            self.logger.error(f"❌ Error saving history for {repo_name}/{branch_name}: write failed")

    def _should_skip_pr(self, repo_name: str, branch_name: str, pr_number: int, current_commit: str) -> bool:
        """Check if PR should be skipped based on recent processing"""
        history = self._load_branch_history(repo_name, branch_name)
        pr_key = str(pr_number)

        # If we haven't processed this PR before, don't skip
        if pr_key not in history:
            return False

        # If commit has changed since we processed it, don't skip
        last_processed_commit = history[pr_key]
        if last_processed_commit != current_commit:
            self.logger.info(f"🔄 PR {repo_name}/{branch_name}#{pr_number} has new commit ({current_commit[:8]} vs {last_processed_commit[:8]})")
            return False

        # We processed this PR with this exact commit, skip it
        self.logger.info(f"⏭️ Skipping PR {repo_name}/{branch_name}#{pr_number} - already processed commit {current_commit[:8]}")
        return True

    def _resolve_automation_username(self) -> str:
        """Resolve the automation username from multiple sources."""
        # 1. Explicitly passed (CLI)
        if self._explicit_automation_username:
            self.logger.debug(f"👤 Using explicit automation username: {self._explicit_automation_username}")
            return self._explicit_automation_username

        # 2. Environment variable
        env_user = os.environ.get("AUTOMATION_USERNAME")
        if env_user:
            self.logger.debug(f"👤 Using environment automation username: {env_user}")
            return env_user

        # 3. Dynamic discovery from GitHub CLI
        try:
            result = AutomationUtils.execute_subprocess_with_timeout(
                ["gh", "api", "user", "--jq", ".login"],
                timeout=10,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                user = result.stdout.strip()
                self.logger.debug(f"👤 Discovered current GitHub user: {user}")
                return user
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to discover GitHub user: {e}")

        # Fallback (should ideally not happen in real usage, but safe default)
        self.logger.warning("⚠️ Could not resolve automation username, defaulting to 'unknown'")
        return "unknown"

    def _record_processed_pr(self, repo_name: str, branch_name: str, pr_number: int, commit_sha: str) -> None:
        """Record that we've processed a PR with a specific commit"""
        history = self._load_branch_history(repo_name, branch_name)
        pr_key = str(pr_number)
        history[pr_key] = commit_sha
        self._save_branch_history(repo_name, branch_name, history)
        self.logger.debug(f"📝 Recorded processing of PR {repo_name}/{branch_name}#{pr_number} with commit {commit_sha[:8]}")

    # TDD GREEN: Implement methods for PR filtering and actionable counting
    def _record_pr_processing(self, repo_name: str, branch_name: str, pr_number: int, commit_sha: str) -> None:
        """Record that a PR has been processed (alias for compatibility)"""
        self._record_processed_pr(repo_name, branch_name, pr_number, commit_sha)

    def _normalize_repository_name(self, repository: str) -> str:
        """Return full owner/repo identifier for GitHub CLI operations."""

        if not repository:
            return repository

        if "/" in repository:
            return repository

        return f"{self.organization}/{repository}"

    def is_pr_actionable(self, pr_data: dict) -> bool:
        """Determine if a PR is actionable (should be processed)"""
        # Closed PRs are not actionable
        if pr_data.get("state", "").lower() != "open":
            return False

        # Draft PRs are not actionable for automation
        if pr_data.get("isDraft"):
            return False

        # PRs with no commits are not actionable
        head_ref_oid = pr_data.get("headRefOid")
        if not head_ref_oid:
            return False

        # Check if already processed with this commit
        repo_name = pr_data.get("repository", "")
        branch_name = pr_data.get("headRefName", "")
        pr_number = pr_data.get("number", 0)

        if self._should_skip_pr(repo_name, branch_name, pr_number, head_ref_oid):
            # Even if commit was processed, check for new bot comments that need attention
            repo_full = pr_data.get("repositoryFullName") or ""

            if not repo_full:
                if repo_name:
                    repo_full = self._normalize_repository_name(repo_name)
                else:
                    self.logger.warning(
                        "Skipping PR comment state check: missing repository information "
                        f"(pr_number={pr_number})"
                    )
                    return False

            owner_repo = repo_full.split("/", 1)
            if len(owner_repo) != 2 or not owner_repo[0].strip() or not owner_repo[1].strip():
                self.logger.warning(
                    "Skipping PR comment state check due to invalid repository identifier "
                    f"repo_full='{repo_full}' (pr_number={pr_number})"
                )
                return False
            _, comments = self._get_pr_comment_state(repo_full, pr_number)
            # Handle API failures: treat None as empty list (assume no new bot comments on failure)
            if comments is None:
                comments = []
            if self._has_new_bot_comments_since_codex(comments):
                self.logger.info(
                    f"🤖 PR {repo_name}#{pr_number} has new bot comments since last processing - marking actionable"
                )
                return True
            return False

        # Open non-draft PRs with new commits are actionable
        return True

    def filter_eligible_prs(self, pr_list: list[dict]) -> list[dict]:
        """Filter list to return only actionable PRs"""
        eligible = []
        for pr in pr_list:
            if self.is_pr_actionable(pr):
                eligible.append(pr)
        return eligible

    def process_actionable_prs(self, pr_list: list[dict], target_count: int) -> int:
        """Process up to target_count actionable PRs, returning count processed"""
        processed = 0
        for pr in pr_list:
            if processed >= target_count:
                break
            if self.is_pr_actionable(pr):
                # Simulate processing (for testing)
                processed += 1
        return processed

    def filter_and_process_prs(self, pr_list: list[dict], target_actionable_count: int) -> int:
        """Filter PRs to actionable ones and process up to target count"""
        eligible_prs = self.filter_eligible_prs(pr_list)
        return self.process_actionable_prs(eligible_prs, target_actionable_count)

    def find_eligible_prs(self, limit: int = 10) -> list[dict]:
        """Find eligible PRs from live GitHub data"""
        all_prs = self.discover_open_prs()
        eligible_prs = self.filter_eligible_prs(all_prs)
        return eligible_prs[:limit]

    def list_actionable_prs(self, cutoff_hours: int = 24, max_prs: int = 20, mode: str = "fixpr", single_repo: str | None = None) -> list[dict]:
        """
        Return PRs that would be processed for fixpr (merge conflicts or failing checks).
        """
        try:
            prs = self.discover_open_prs(cutoff_hours=cutoff_hours)
        except TypeError:
            # Backwards-compatible with older stubs/mocks that don't accept cutoff_hours.
            prs = self.discover_open_prs()
        if single_repo:
            prs = [pr for pr in prs if pr.get("repository") == single_repo]

        actionable = []
        for pr in prs:
            repo = pr.get("repository")
            owner = pr.get("owner", "jleechanorg")
            pr_number = pr.get("number")
            if not repo or pr_number is None:
                continue
            repo_full = f"{owner}/{repo}"

            mergeable = pr.get("mergeable")
            if mergeable is None:
                try:
                    result = AutomationUtils.execute_subprocess_with_timeout(
                        ["gh", "pr", "view", str(pr_number), "--repo", repo_full, "--json", "mergeable"],
                        timeout=30,
                        check=False,
                    )
                    if result.returncode == 0:
                        data = json.loads(result.stdout or "{}")
                        mergeable = data.get("mergeable")
                except Exception:
                    mergeable = None

            if mergeable == "CONFLICTING":
                actionable.append({**pr, "repo_full": repo_full})
                continue

            try:
                if has_failing_checks(repo_full, pr_number):
                    actionable.append({**pr, "repo_full": repo_full})
            except Exception:
                # Skip on error to avoid blocking listing
                continue

        actionable = actionable[:max_prs]
        print(f"🔎 Eligible for fixpr: {len(actionable)}")
        for pr in actionable:
            print(f"  • {pr.get('repository')} PR #{pr.get('number')}: {pr.get('title')}")
        return actionable

    def run_monitoring_cycle_with_actionable_count(self, target_actionable_count: int = 20) -> dict:
        """Enhanced monitoring cycle that processes exactly target actionable PRs"""
        all_prs = self.discover_open_prs()

        # Sort by most recently updated first
        all_prs.sort(key=lambda pr: pr.get("updatedAt", ""), reverse=True)

        actionable_processed = 0
        skipped_count = 0
        processing_failures = 0

        # Count ALL non-actionable PRs as skipped, not just those we encounter before target
        for pr in all_prs:
            if not self.is_pr_actionable(pr):
                skipped_count += 1

        # Process actionable PRs up to target
        for pr in all_prs:
            if actionable_processed >= target_actionable_count:
                break

            if not self.is_pr_actionable(pr):
                continue  # Already counted in skipped above

            # Attempt to process the PR
            repo_name = pr.get("repository", "")
            pr_number = pr.get("number", 0)
            repo_full = pr.get("repositoryFullName", f"jleechanorg/{repo_name}")

            # Reserve a processing slot for this PR
            if not self.safety_manager.try_process_pr(pr_number, repo=repo_full):
                self.logger.info(f"⚠️ PR {repo_full}#{pr_number} blocked by safety manager - consecutive failures or rate limit")
                processing_failures += 1
                continue

            try:
                success = self._process_pr_comment(repo_name, pr_number, pr)
                if success:
                    actionable_processed += 1
                else:
                    processing_failures += 1
            except Exception as e:
                self.logger.error(f"Error processing PR {repo_name}#{pr_number}: {e}")
                processing_failures += 1
            finally:
                # Always release the processing slot
                self.safety_manager.release_pr_slot(pr_number, repo=repo_full)

        return {
            "actionable_processed": actionable_processed,
            "total_discovered": len(all_prs),
            "skipped_count": skipped_count,
            "processing_failures": processing_failures
        }

    def _process_pr_comment(self, repo_name: str, pr_number: int, pr_data: dict) -> bool:
        """Process a PR by posting a comment (used by tests and enhanced monitoring)"""
        try:
            # Use the existing comment posting method
            repo_full_name = pr_data.get("repositoryFullName", f"jleechanorg/{repo_name}")
            result = self.post_codex_instruction_simple(repo_full_name, pr_number, pr_data)
            # Return True only if comment was actually posted
            return result == "posted"
        except Exception as e:
            self.logger.error(f"Error processing comment for PR {repo_name}#{pr_number}: {e}")
            return False

    def discover_open_prs(self, cutoff_hours: int = 24) -> list[dict]:
        """Discover open PRs updated in the last specified hours across the organization."""

        self.logger.info(f"🔍 Discovering open PRs in {self.organization} organization (last {cutoff_hours} hours)")

        now = datetime.now(UTC)
        one_day_ago = now - timedelta(hours=cutoff_hours)
        self.logger.info("📅 Filtering PRs updated since: %s UTC", one_day_ago.strftime("%Y-%m-%d %H:%M:%S"))

        graphql_query = """
        query($searchQuery: String!, $cursor: String) {
          search(type: ISSUE, query: $searchQuery, first: 100, after: $cursor) {
            nodes {
              __typename
              ... on PullRequest {
                number
                title
                headRefName
                baseRefName
                updatedAt
                url
                author { login resourcePath url }
                headRefOid
                state
                isDraft
                repository { name nameWithOwner }
              }
            }
            pageInfo { hasNextPage endCursor }
          }
        }
        """

        search_query = f"org:{self.organization} is:pr is:open"
        cursor: str | None = None
        recent_prs: list[dict] = []

        while True:
            gh_api_cmd = [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={graphql_query}",
                "-f",
                f"searchQuery={search_query}",
            ]
            if cursor:
                gh_api_cmd.extend(["-f", f"cursor={cursor}"])

            api_result = AutomationUtils.execute_subprocess_with_timeout(gh_api_cmd, timeout=60, check=False)
            if api_result.returncode != 0:
                raise RuntimeError(f"GraphQL search failed: {api_result.stderr.strip()}")

            try:
                api_data = json.loads(api_result.stdout)
            except json.JSONDecodeError as exc:
                self.logger.error("❌ Failed to parse GraphQL response: %s", exc)
                raise

            search_data = api_data.get("data", {}).get("search")
            if not search_data:
                break

            nodes = search_data.get("nodes", [])
            for node in nodes:
                if node.get("__typename") != "PullRequest":
                    continue

                updated_str = node.get("updatedAt")
                if not updated_str:
                    continue

                try:
                    # Parse ISO format and ensure timezone-aware (UTC)
                    updated_time = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    if updated_time.tzinfo is None:
                        updated_time = updated_time.replace(tzinfo=UTC)
                except ValueError:
                    self.logger.debug(
                        "⚠️ Invalid date format for PR %s: %s", node.get("number"), updated_str
                    )
                    continue

                if updated_time < one_day_ago:
                    continue

                repo_info = node.get("repository") or {}
                author_info = node.get("author") or {}
                if "login" not in author_info:
                    author_info = {**author_info, "login": author_info.get("login")}

                normalized = {
                    "number": node.get("number"),
                    "title": node.get("title"),
                    "headRefName": node.get("headRefName"),
                    "baseRefName": node.get("baseRefName"),
                    "updatedAt": updated_str,
                    "url": node.get("url"),
                    "author": author_info,
                    "headRefOid": node.get("headRefOid"),
                    "state": node.get("state"),
                    "isDraft": node.get("isDraft"),
                    "repository": repo_info.get("name"),
                    "repositoryFullName": repo_info.get("nameWithOwner"),
                    "updated_datetime": updated_time,
                }
                recent_prs.append(normalized)

            page_info = search_data.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break

            cursor = page_info.get("endCursor")
            if not cursor:
                break

        if not recent_prs:
            self.logger.info("📭 No recent open PRs discovered")
            return []

        # Use timezone-aware minimum datetime for safe comparison with aware datetimes
        datetime_min_utc = datetime.min.replace(tzinfo=UTC)
        recent_prs.sort(key=lambda x: x.get("updated_datetime", datetime_min_utc), reverse=True)

        repo_counter = Counter(pr.get("repository") for pr in recent_prs if pr.get("repository"))
        for repo_name, count in repo_counter.items():
            self.logger.info("📋 %s: %s recent PRs", repo_name, count)

        self.logger.info("🎯 Total recent PRs discovered (last 24 hours): %s", len(recent_prs))

        self.logger.info("📊 Most recently updated PRs:")
        for i, pr in enumerate(recent_prs[:5], 1):
            updated_str = pr["updated_datetime"].strftime("%Y-%m-%d %H:%M")
            self.logger.info("  %s. %s #%s - %s", i, pr["repositoryFullName"], pr["number"], updated_str)

        return recent_prs


    def _find_local_repository(self, repo_name: str) -> Path | None:
        """Find local repository path for given repo name"""

        def is_git_repository(path: Path) -> bool:
            """Check if path is a git repository"""
            git_path = path / ".git"
            return git_path.exists()

        # Check current working directory first
        current_dir = Path.cwd()
        if is_git_repository(current_dir):
            # Check if this is related to the target repository
            if repo_name.lower() in current_dir.name.lower() or "worldarchitect" in current_dir.name.lower():
                self.logger.debug(f"🎯 Found local repo (current dir): {current_dir}")
                return current_dir

        # Common patterns for local repositories
        search_paths = [
            # Standard patterns in ~/projects/
            self.base_project_dir / repo_name,
            self.base_project_dir / f"{repo_name}_worker",
            self.base_project_dir / f"{repo_name}_worker1",
            self.base_project_dir / f"{repo_name}_worker2",
            # Project patterns in home directory
            Path.home() / f"project_{repo_name}",
            Path.home() / f"project_{repo_name}" / repo_name,
            # Nested repository patterns
            Path.home() / f"project_{repo_name}_frontend" / f"{repo_name}_frontend",
        ]

        for path in search_paths:
            if path.exists() and is_git_repository(path):
                self.logger.debug(f"🎯 Found local repo: {path}")
                return path

        # Search for any directory containing the repo name in ~/projects/
        if self.base_project_dir.exists():
            for path in self.base_project_dir.iterdir():
                if path.is_dir() and repo_name.lower() in path.name.lower():
                    if is_git_repository(path):
                        self.logger.debug(f"🎯 Found local repo (fuzzy): {path}")
                        return path

        # Search for project_* patterns in home directory
        home_dir = Path.home()
        for path in home_dir.iterdir():
            if path.is_dir() and path.name.startswith(f"project_{repo_name}"):
                # Check if it's a direct repo
                if is_git_repository(path):
                    self.logger.debug(f"🎯 Found local repo (home): {path}")
                    return path
                # Check if repo is nested inside
                nested_repo = path / repo_name
                if nested_repo.exists() and is_git_repository(nested_repo):
                    self.logger.debug(f"🎯 Found local repo (nested): {nested_repo}")
                    return nested_repo

        return None

    def _cleanup_pending_reviews(self, repo_full: str, pr_number: int) -> None:
        """Delete any pending reviews for the current automation user to prevent review clutter.

        This is a safety measure to clean up pending reviews that may have been left behind
        by agents that use MCP tools (create_pending_pull_request_review) without submitting.
        """
        try:
            # Extract owner and repo from repo_full
            parts = repo_full.split("/")
            if len(parts) != 2:
                self.logger.warning(f"Cannot parse repo_full '{repo_full}' for pending review cleanup")
                return

            owner, repo = parts

            # Fetch all reviews for the PR
            reviews_cmd = [
                "gh", "api",
                f"repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                "--paginate", "-q", ".[]",
            ]
            result = AutomationUtils.execute_subprocess_with_timeout(
                reviews_cmd, timeout=30, check=False
            )

            if result.returncode != 0:
                self.logger.debug(f"Could not fetch reviews for pending cleanup: {result.stderr}")
                return

            # Parse reviews and find pending ones from automation user
            pending_deleted = 0
            for line in (result.stdout or "").splitlines():
                if not line.strip():
                    continue
                try:
                    review = json.loads(line)
                    if review.get("state") == "PENDING":
                        user_info = review.get("user")
                        if isinstance(user_info, dict):
                            review_user = user_info.get("login", "")
                        else:
                            review_user = ""
                        if review_user == self.automation_username:
                            review_id = review.get("id")
                            if review_id:
                                delete_cmd = [
                                    "gh", "api",
                                    f"repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}",
                                    "-X", "DELETE",
                                ]
                                delete_result = AutomationUtils.execute_subprocess_with_timeout(
                                    delete_cmd, timeout=30, check=False
                                )
                                if delete_result.returncode == 0:
                                    self.logger.info(
                                        f"🧹 Deleted pending review #{review_id} from {review_user} on PR #{pr_number}"
                                    )
                                    pending_deleted += 1
                                else:
                                    self.logger.debug(
                                        f"Could not delete pending review #{review_id}: {delete_result.stderr}"
                                    )
                except json.JSONDecodeError:
                    continue

            if pending_deleted > 0:
                self.logger.info(f"✅ Cleaned up {pending_deleted} pending review(s) on PR #{pr_number}")

        except Exception as exc:
            self.logger.debug(f"Pending review cleanup failed for PR #{pr_number}: {exc}")
            # Non-fatal - continue with the workflow

    def post_codex_instruction_simple(self, repository: str, pr_number: int, pr_data: dict) -> str:
        """Post codex instruction comment to PR"""
        repo_full = self._normalize_repository_name(repository)
        self.logger.info(f"💬 Requesting Codex support for {repo_full} PR #{pr_number}")

        if self.no_act:
            self.logger.info("🧪 --no-act enabled: skipping comment post for %s #%s", repo_full, pr_number)
            return "skipped"

        # Extract repo name and branch from PR data
        repo_name = repo_full.split("/")[-1]
        branch_name = pr_data.get("headRefName", "unknown")

        # Get current PR state including commit SHA
        head_sha, comments = self._get_pr_comment_state(repo_full, pr_number)
        # Handle API failures: treat None as empty list
        if comments is None:
            comments = []
        head_commit_details = None
        # Flag to bypass skip checks when new bot comments require attention
        force_process_due_to_bot_comments = False

        if head_sha:
            head_commit_details = self._get_head_commit_details(repo_full, pr_number, head_sha)
            if head_commit_details and self._is_head_commit_from_codex(head_commit_details):
                # Check if there are new bot comments that need attention
                if self._has_new_bot_comments_since_codex(comments):
                    self.logger.info(
                        "🤖 Head commit %s for %s#%s is from Codex, but new bot comments detected - forcing re-run",
                        head_sha[:8],
                        repo_full,
                        pr_number,
                    )
                    force_process_due_to_bot_comments = True
                else:
                    self.logger.debug(
                        "🆔 Head commit %s for %s#%s already attributed to Codex",
                        head_sha[:8],
                        repo_full,
                        pr_number,
                    )
                    self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)
                    return "skipped"

        if not head_sha:
            self.logger.warning(
                f"⚠️ Could not determine commit SHA for PR #{pr_number}; proceeding without marker gating"
            )
        elif not force_process_due_to_bot_comments:
            # Only apply skip checks if we're not forcing a re-run due to new bot comments
            # Check if we should skip this PR based on commit-based tracking
            if self._should_skip_pr(repo_name, branch_name, pr_number, head_sha):
                self.logger.info(f"⏭️ Skipping PR #{pr_number} - already processed this commit")
                return "skipped"

            if self._has_codex_comment_for_commit(comments, head_sha):
                self.logger.info(
                    f"♻️ Codex instruction already posted for commit {head_sha[:8]} on PR #{pr_number}, skipping"
                )
                self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)
                return "skipped"

            if self._has_pending_codex_commit(comments, head_sha):
                self.logger.info(
                    f"⏳ Pending Codex automation commit {head_sha[:8]} detected on PR #{pr_number}; skipping re-run"
                )
                self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)
                return "skipped"

        # Build comment body that tells Codex to fix PR comments and failing tests
        comment_body = self._build_codex_comment_body_simple(
            repo_full,
            pr_number,
            pr_data,
            head_sha,
        )

        # Post the comment
        try:
            comment_cmd = [
                "gh", "pr", "comment", str(pr_number),
                "--repo", repo_full,
                "--body", comment_body
            ]

            AutomationUtils.execute_subprocess_with_timeout(
                comment_cmd,
                timeout=30,
                retry_attempts=5,
                retry_backoff_seconds=1.0,
                retry_backoff_multiplier=2.0,
                retry_on_stderr_substrings=(
                    "was submitted too quickly",
                    "secondary rate limit",
                    "API rate limit exceeded",
                ),
            )

            self.logger.info(f"✅ Posted Codex instruction comment on PR #{pr_number} ({repo_full})")
            time.sleep(2.0)

            # Record that we've processed this PR with this commit when available
            if head_sha:
                self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)

            return "posted"

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to post comment on PR #{pr_number}: {e.stderr}")
            return "failed"
        except Exception as e:
            self.logger.error(f"💥 Unexpected error posting comment: {e}")
            return "failed"











    def _are_tests_passing(self, repository: str, pr_number: int) -> bool:
        """Check if tests are passing on the PR"""
        try:
            # Get PR status checks
            result = AutomationUtils.execute_subprocess_with_timeout([
                "gh", "pr", "view", str(pr_number),
                "--repo", repository,
                "--json", "statusCheckRollup"
            ], timeout=30)

            pr_status = json.loads(result.stdout or "{}")
            status_checks = pr_status.get("statusCheckRollup", [])

            # If no status checks are configured, assume tests are failing
            if not status_checks:
                self.logger.debug(f"⚠️ No status checks configured for PR #{pr_number}, assuming failing")
                return False

            # Check if all status checks are successful
            for check in status_checks:
                if check.get("state") not in ["SUCCESS", "NEUTRAL"]:
                    self.logger.debug(f"❌ Status check failed: {check.get('name')} - {check.get('state')}")
                    return False

            self.logger.debug(f"✅ All {len(status_checks)} status checks passing for PR #{pr_number}")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Could not check test status for PR #{pr_number}: {e}")
            return False  # Assume tests are failing if we can't check

    def _build_codex_comment_body_simple(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str,
    ) -> str:
        """Build comment body that tells all AI assistants to fix PR comments, tests, and merge conflicts"""

        intro_line = build_comment_intro(assistant_mentions=self.assistant_mentions)
        comment_body = f"""{intro_line}

**Summary (Execution Flow):**
1. Review every outstanding PR comment to understand required fixes and clarifications.
2. Implement code or configuration updates that address each comment, then reply with explicit DONE/NOT DONE outcomes plus context.
3. Run the relevant test suites locally and in CI, repairing any failures until the checks report success.
4. Rebase or merge with the base branch to clear conflicts, then push the updated commits to this PR.
5. Perform a final self-review to confirm linting, formatting, and documentation standards are met before handoff.

**PR Details:**
- Title: {pr_data.get('title', 'Unknown')}
- Author: {pr_data.get('author', {}).get('login', 'unknown')}
- Branch: {pr_data.get('headRefName', 'unknown')}
- Commit: {head_sha[:8] if head_sha else 'unknown'} ({head_sha or 'unknown'})

**Instructions:**
Use your judgment to fix comments from everyone or explain why it should not be fixed. Follow binary response protocol - every comment needs "DONE" or "NOT DONE" classification explicitly with an explanation. Address all comments on this PR. Fix any failing tests and resolve merge conflicts. Push any commits needed to remote so the PR is updated.

**Tasks:**
1. **Address all comments** - Review and implement ALL feedback from reviewers
2. **Fix failing tests** - Review test failures and implement fixes
3. **Resolve merge conflicts** - Handle any conflicts with the base branch
4. **Ensure code quality** - Follow project standards and best practices

**Automation Markers:**
- Leave the hidden comment marker `<!-- codex-automation-commit:... -->` in this thread so we only re-ping you after new commits.
- Include `{self.CODEX_COMMIT_MESSAGE_MARKER}` in the commit message of your next push so we can confirm Codex authored it (even if the author/committer metadata already shows Codex).
"""

        if head_sha:
            comment_body += (
                f"\n\n{self.CODEX_COMMIT_MARKER_PREFIX}{head_sha}"
                f"{self.CODEX_COMMIT_MARKER_SUFFIX}"
            )

        return comment_body

    def _compose_fix_comment_mentions(self) -> str:
        mentions = [
            token for token in (self.assistant_mentions or "").split() if token.startswith("@")
        ]
        lower_mentions = {token.lower() for token in mentions}
        if "@greptile" not in lower_mentions:
            mentions.append("@greptile")
        return " ".join(mentions)

    def _build_fix_comment_prompt_body(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str,
    ) -> str:
        cli_chain = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
        commit_marker_cli = cli_chain[0] if cli_chain else "claude"

        return (
            f"FIX-COMMENT TASK (SELF-CONTAINED): Update PR #{pr_number} in {repository} "
            f"(branch {pr_data.get('headRefName', 'unknown')}).\n"
            "Goal: address all review comments with explicit action-based replies, "
            "fix failing tests, and resolve merge conflicts.\n\n"
            f"CLI chain: {agent_cli}. Start immediately.\n\n"
            "🚨🚨🚨 PRE-FLIGHT CHECK - VERIFY TOOL AVAILABILITY (MANDATORY FIRST STEP):\n"
            "   ⚠️⚠️⚠️ BEFORE STARTING ANY WORK, YOU MUST CHECK YOUR AVAILABLE TOOLS:\n"
            "   1. List all available MCP tools (method depends on your CLI)\n"
            "   2. If you see `create_pending_pull_request_review` or `add_comment_to_pending_review` in the tool list:\n"
            "      - DO NOT USE THESE TOOLS - They are FORBIDDEN\n"
            "      - IGNORE them completely - pretend they don't exist\n"
            "      - Use ONLY the allowed methods listed below\n"
            "   3. If these forbidden tools are available, you MUST skip them and use alternative methods\n\n"
            "🚨🚨🚨 CRITICAL - PREVENT PENDING REVIEWS (MANDATORY - READ FIRST - NO EXCEPTIONS):\n"
            "   ⚠️⚠️⚠️ YOU MUST NEVER CREATE A PENDING REVIEW. Pending reviews clutter PRs and break automation.\n"
            "   ⚠️⚠️⚠️ IF YOU CREATE A PENDING REVIEW, THE AUTOMATION WILL FAIL AND YOU WILL BE BLOCKED.\n"
            "   ⚠️⚠️⚠️ THESE TOOLS ARE FORBIDDEN AND WILL CAUSE AUTOMATION FAILURE:\n"
            "   - `create_pending_pull_request_review` MCP tool (FORBIDDEN - DO NOT USE)\n"
            "   - `add_comment_to_pending_review` MCP tool (FORBIDDEN - DO NOT USE)\n"
            "   - `POST /repos/.../pulls/.../reviews` endpoint (FORBIDDEN - DO NOT USE)\n"
            "   - Any GitHub review workflow that requires 'submit' (FORBIDDEN - DO NOT USE)\n\n"
            "   ✅✅✅ CORRECT METHOD - Reply to inline review comments (ONLY USE THIS):\n"
            f"   `gh api /repos/{repository}/pulls/{pr_number}/comments -f body='...' -F in_reply_to={{comment_id}}`\n"
            "   This `/comments` endpoint with `in_reply_to` creates a threaded reply WITHOUT starting a review.\n"
            "   ⚠️ Use `-f` for body (string) and `-F` for in_reply_to (numeric comment ID).\n\n"
            "   ✅✅✅ CORRECT METHOD - General PR comments (not line-specific):\n"
            f"   `gh pr comment {pr_number} --body '...'` or `gh api /repos/{repository}/issues/{pr_number}/comments -f body='...'`\n\n"
            "   ✅ ALLOWED - Verification and Cleanup:\n"
            "   - `GET /repos/.../pulls/.../reviews` (ALLOWED - used to check for pending reviews)\n"
            "   - `DELETE /repos/.../pulls/.../reviews/{review_id}` (ALLOWED - used to clean up pending reviews)\n\n"
            "   ⚠️ VERIFICATION: After replying, verify NO pending review was created:\n"
            f"   `gh api /repos/{repository}/pulls/{pr_number}/reviews --jq '.[] | select(.state==\"PENDING\")'`\n"
            "   If any pending reviews exist from your user, DELETE THEM IMMEDIATELY.\n\n"
            "🚨🚨🚨 ABSOLUTE PROHIBITION - PENDING REVIEWS:\n"
            "   ⚠️⚠️⚠️ YOU ARE FORBIDDEN FROM CREATING PENDING REVIEWS. THIS IS NOT A SUGGESTION - IT IS A HARD REQUIREMENT.\n"
            "   ⚠️⚠️⚠️ IF YOU ATTEMPT TO CREATE A PENDING REVIEW, IT WILL BE IMMEDIATELY DELETED AND YOUR EXECUTION WILL FAIL.\n"
            "   ⚠️⚠️⚠️ THE FOLLOWING TOOLS ARE COMPLETELY DISABLED AND WILL CAUSE IMMEDIATE FAILURE:\n"
            "   - `create_pending_pull_request_review` MCP tool (DISABLED - DO NOT USE)\n"
            "   - `add_comment_to_pending_review` MCP tool (DISABLED - DO NOT USE)\n"
            "   - `POST /repos/.../pulls/.../reviews` endpoint (DISABLED - DO NOT USE)\n"
            "   ⚠️⚠️⚠️ USE ONLY THE ALLOWED METHODS LISTED ABOVE. ANY ATTEMPT TO CREATE A PENDING REVIEW WILL RESULT IN IMMEDIATE TERMINATION.\n\n"
            "Steps:\n"
            f"1) gh pr checkout {pr_number}\n\n"
            "2) Fetch ALL PR feedback sources (pagination-safe) using correct GitHub API endpoints:\n"
            f"   - Issue comments: `gh api /repos/{repository}/issues/{pr_number}/comments --paginate -F per_page=100`\n"
            f"   - Review summaries: `gh api /repos/{repository}/pulls/{pr_number}/reviews --paginate -F per_page=100`\n"
            f"   - Inline review comments: `gh api /repos/{repository}/pulls/{pr_number}/comments --paginate -F per_page=100`\n"
            "   ⚠️ WARNING: `gh pr view --json comments` ONLY fetches issue comments, NOT inline review comments.\n\n"
            "3) Apply code changes to address feedback, then reply to **100%** of comments INDIVIDUALLY.\n"
            "   Threading rules:\n"
            "   - Inline review comments MUST use threaded replies via the GitHub API.\n"
            "   - Issue/PR comments do not support threading (they are top-level only).\n\n"
            "   **Response Protocol** (use ONE of these categories for EACH comment):\n"
            "   - **FIXED**: Issue implemented with working code → include files modified, tests added, verification\n"
            "   - **DEFERRED**: Created issue for future work → include issue URL and reason\n"
            "   - **ACKNOWLEDGED**: Noted but not actionable → include explanation\n"
            "   - **NOT DONE**: Cannot implement → include specific technical reason\n\n"
            "   **Reply Methods (ONLY use these - no pending reviews!):**\n"
            f"   - Inline review comments: `gh api /repos/{repository}/pulls/{pr_number}/comments -f body='[Response]' -F in_reply_to={{comment_id}}`\n"
            f"   - Issue/PR comments: `gh pr comment {pr_number} --body '[Response]'`\n"
            "   - Do NOT post mega-comments consolidating multiple responses; reply individually to each comment.\n\n"
            "4) Run tests and fix failures (block completion on critical/blocking test failures)\n\n"
            "5) Resolve merge conflicts (prefer merge over rebase)\n\n"
            f'6) git add -A && git commit -m "[{commit_marker_cli}-automation-commit] fix PR #{pr_number} review feedback" && git push\n\n'
            f"7) Write completion report to /tmp/orchestration_results/pr-{pr_number}_results.json "
            "with comments addressed, files modified, tests run, and remaining issues\n\n"
            "**PR Details:**\n"
            f"- Title: {pr_data.get('title', 'Unknown')}\n"
            f"- Author: {pr_data.get('author', {}).get('login', 'unknown')}\n"
            f"- Branch: {pr_data.get('headRefName', 'unknown')}\n"
            f"- Commit: {head_sha[:8] if head_sha else 'unknown'} ({head_sha or 'unknown'})\n"
        )

    def _build_fix_comment_queued_body(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> str:
        comment_body = (
            f"[AI automation - {agent_cli}] Fix-comment run queued for this PR. "
            "A review request will follow after updates are pushed.\n\n"
            "**PR Details:**\n"
            f"- Title: {pr_data.get('title', 'Unknown')}\n"
            f"- Author: {pr_data.get('author', {}).get('login', 'unknown')}\n"
            f"- Branch: {pr_data.get('headRefName', 'unknown')}\n"
            f"- Commit: {head_sha[:8] if head_sha else 'unknown'} ({head_sha or 'unknown'})\n"
            f"- Agent: {agent_cli}"
        )

        # Always add marker for limit counting, even when head_sha is unavailable.
        # Use enhanced format: workflow:agent:commit
        sha_value = head_sha or "unknown"
        # Extract first CLI from chain (e.g., "gemini,codex" -> "gemini")
        cli_chain = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
        marker_cli = cli_chain[0] if cli_chain else "claude"
        marker = build_automation_marker("fix-comment-run", marker_cli, sha_value)
        comment_body += f"\n\n{marker}"

        return comment_body

    def _build_fixpr_queued_body(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> str:
        full_sha = head_sha or "unknown"
        short_sha = head_sha[:8] if head_sha else "unknown"
        comment_body = (
            f"[AI automation - {agent_cli}] FixPR run queued for this PR.\n\n"
            "**PR Details:**\n"
            f"- Title: {pr_data.get('title', 'Unknown')}\n"
            f"- Author: {pr_data.get('author', {}).get('login', 'unknown')}\n"
            f"- Branch: {pr_data.get('headRefName', 'unknown')}\n"
            f"- Commit: {short_sha} ({full_sha})\n"
            f"- Agent: {agent_cli}"
        )

        # Always add marker for limit counting, even when head_sha is unavailable
        # Use enhanced format: workflow:agent:commit
        sha_value = head_sha or "unknown"
        # Extract first CLI from chain (e.g., "gemini,codex" -> "gemini")
        cli_chain = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
        marker_cli = cli_chain[0] if cli_chain else "claude"
        marker = build_automation_marker("fixpr-run", marker_cli, sha_value)
        comment_body += f"\n\n{marker}"

        return comment_body

    def _build_fix_comment_review_body(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> str:
        mentions = self._compose_fix_comment_mentions()
        intro = f"{mentions} [AI automation] {self.FIX_COMMENT_COMPLETION_MARKER}. Please review the updates."

        comment_body = (
            f"{intro}\n\n"
            "**Review Request:**\n"
            "Please review the latest changes, leave feedback, and flag any remaining issues. "
            "If further fixes are needed, add explicit DONE/NOT DONE guidance.\n\n"
            "**PR Details:**\n"
            f"- Title: {pr_data.get('title', 'Unknown')}\n"
            f"- Author: {pr_data.get('author', {}).get('login', 'unknown')}\n"
            f"- Branch: {pr_data.get('headRefName', 'unknown')}\n"
            f"- Commit: {head_sha[:8] if head_sha else 'unknown'} ({head_sha or 'unknown'})\n"
        )

        if head_sha:
            # Extract first CLI from chain (e.g., "gemini,codex" -> "gemini")
            cli_chain = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
            marker_cli = cli_chain[0] if cli_chain else "claude"
            marker = build_automation_marker("fix-comment", marker_cli, head_sha)
            comment_body += f"\n{marker}"

        return comment_body

    def _get_fix_comment_watch_state(
        self,
        repo_full: str,
        pr_number: int,
    ) -> tuple[dict, str | None, list[dict], list[str]]:
        view_cmd = [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo_full,
            "--json",
            "title,headRefName,headRefOid,author,comments,commits",
        ]
        result = AutomationUtils.execute_subprocess_with_timeout(view_cmd, timeout=30, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or f"gh pr view failed for {repo_full}#{pr_number}")

        pr_data = json.loads(result.stdout or "{}")
        head_sha = pr_data.get("headRefOid")

        comments_data = pr_data.get("comments", [])
        if isinstance(comments_data, dict):
            comments = comments_data.get("nodes", [])
        elif isinstance(comments_data, list):
            comments = comments_data
        else:
            comments = []

        commits_data = pr_data.get("commits", [])
        if isinstance(commits_data, dict):
            commit_nodes = commits_data.get("nodes", [])
        elif isinstance(commits_data, list):
            commit_nodes = commits_data
        else:
            commit_nodes = []

        headlines = []
        for node in commit_nodes:
            # Handle both nested 'commit' node structure and flat structure
            commit_obj = node.get("commit") if isinstance(node, dict) and "commit" in node else node
            headline = commit_obj.get("messageHeadline") if isinstance(commit_obj, dict) else None
            if headline:
                headlines.append(headline)

        return pr_data, head_sha, comments, headlines

    def _post_fix_comment_review(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        comment_body = self._build_fix_comment_review_body(
            repo_full,
            pr_number,
            pr_data,
            head_sha,
            agent_cli,
        )

        try:
            comment_cmd = [
                "gh",
                "pr",
                "comment",
                str(pr_number),
                "--repo",
                repo_full,
                "--body",
                comment_body,
            ]
            AutomationUtils.execute_subprocess_with_timeout(
                comment_cmd,
                timeout=30,
                retry_attempts=5,
                retry_backoff_seconds=1.0,
                retry_backoff_multiplier=2.0,
                retry_on_stderr_substrings=(
                    "was submitted too quickly",
                    "secondary rate limit",
                    "API rate limit exceeded",
                ),
            )
            self.logger.info(
                "✅ Posted fix-comment review request on PR #%s (%s)",
                pr_number,
                repo_full,
            )
            time.sleep(2.0)
            return True
        except Exception as exc:
            self.logger.error(
                "❌ Failed to post fix-comment review request on PR #%s: %s",
                pr_number,
                exc,
            )
            return False

    def _post_fix_comment_queued(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        comment_body = self._build_fix_comment_queued_body(
            repo_full,
            pr_number,
            pr_data,
            head_sha,
            agent_cli=agent_cli,
        )

        try:
            queued_cmd = [
                "gh",
                "pr",
                "comment",
                str(pr_number),
                "--repo",
                repo_full,
                "--body",
                comment_body,
            ]
            AutomationUtils.execute_subprocess_with_timeout(
                queued_cmd,
                timeout=30,
                retry_attempts=5,
                retry_backoff_seconds=1.0,
                retry_backoff_multiplier=2.0,
                retry_on_stderr_substrings=(
                    "was submitted too quickly",
                    "secondary rate limit",
                    "API rate limit exceeded",
                ),
            )
            self.logger.info(
                "✅ Posted fix-comment queued notice on PR #%s (%s)",
                pr_number,
                repo_full,
            )
            time.sleep(2.0)
            return True
        except Exception as exc:
            self.logger.error(
                "❌ Failed to post fix-comment queued notice on PR #%s: %s",
                pr_number,
                exc,
            )
            return False

    def _post_fixpr_queued(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        head_sha: str | None,
        agent_cli: str = "claude",
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        comment_body = self._build_fixpr_queued_body(
            repo_full,
            pr_number,
            pr_data,
            head_sha,
            agent_cli=agent_cli,
        )

        try:
            queued_cmd = [
                "gh",
                "pr",
                "comment",
                str(pr_number),
                "--repo",
                repo_full,
                "--body",
                comment_body,
            ]
            AutomationUtils.execute_subprocess_with_timeout(
                queued_cmd,
                timeout=30,
                retry_attempts=5,
                retry_backoff_seconds=1.0,
                retry_backoff_multiplier=2.0,
                retry_on_stderr_substrings=(
                    "was submitted too quickly",
                    "secondary rate limit",
                    "API rate limit exceeded",
                ),
            )
            self.logger.info(
                "✅ Posted fixpr queued notice on PR #%s (%s)",
                pr_number,
                repo_full,
            )
            time.sleep(2.0)
            return True
        except Exception as exc:
            self.logger.error(
                "❌ Failed to post fixpr queued notice on PR #%s: %s",
                pr_number,
                exc,
            )
            return False

    def _start_fix_comment_review_watcher(
        self,
        repository: str,
        pr_number: int,
        agent_cli: str,
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        env = os.environ.copy()
        pythonpath_parts = [str(ROOT_DIR), str(ROOT_DIR / "automation")]
        if env.get("PYTHONPATH"):
            pythonpath_parts.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = ":".join(pythonpath_parts)

        cmd = [
            sys.executable,
            "-m",
            "jleechanorg_pr_automation.jleechanorg_pr_monitor",
            "--fix-comment-watch",
            "--target-pr",
            str(pr_number),
            "--target-repo",
            repo_full,
            "--fixpr-agent",
            agent_cli,
        ]
        try:
            subprocess.Popen(
                cmd,
                cwd=str(ROOT_DIR),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.logger.info(
                "🧭 Started fix-comment review watcher for PR #%s (%s)",
                pr_number,
                repo_full,
            )
            return True
        except Exception as exc:
            self.logger.error(
                "❌ Failed to start fix-comment review watcher for PR #%s: %s",
                pr_number,
                exc,
            )
            return False

    def run_fix_comment_review_watcher(
        self,
        pr_number: int,
        repository: str,
        agent_cli: str = "claude",
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        cli_chain = [part.strip().lower() for part in str(agent_cli).split(",") if part.strip()]
        commit_marker_cli = cli_chain[0] if cli_chain else "claude"
        commit_marker = f"[{commit_marker_cli}-automation-commit]"
        timeout_seconds = int(os.environ.get("FIX_COMMENT_WATCH_TIMEOUT", "3600"))
        poll_interval = float(os.environ.get("FIX_COMMENT_WATCH_POLL", "30"))
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            try:
                pr_data, head_sha, comments, headlines = self._get_fix_comment_watch_state(
                    repo_full,
                    pr_number,
                )
            except Exception as exc:
                self.logger.warning(
                    "⚠️ Fix-comment watcher failed to fetch PR state for #%s: %s",
                    pr_number,
                    exc,
                )
                time.sleep(poll_interval)
                continue

            if head_sha and self._has_fix_comment_comment_for_commit(comments, head_sha):
                self.logger.info(
                    "✅ Fix-comment review already posted for PR #%s",
                    pr_number,
                )
                return True

            if any(commit_marker in headline for headline in headlines):
                if self._post_fix_comment_review(repo_full, pr_number, pr_data, head_sha, agent_cli):
                    return True
                return False

            time.sleep(poll_interval)

        self.logger.warning(
            "⏳ Fix-comment watcher timed out for PR #%s after %ss",
            pr_number,
            timeout_seconds,
        )
        return False

    def dispatch_fix_comment_agent(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        agent_cli: str = "claude",
        model: str = None,
    ) -> bool:
        repo_full = self._normalize_repository_name(repository)
        repo_name = repo_full.split("/")[-1]
        branch = pr_data.get("headRefName", "")
        if not branch:
            branch = f"pr-{pr_number}"

        head_sha = pr_data.get("headRefOid")
        task_description = self._build_fix_comment_prompt_body(
            repo_full,
            pr_number,
            pr_data,
            head_sha,
            agent_cli,
        )

        pr_payload = {
            "repo_full": repo_full,
            "repo": repo_name,
            "number": pr_number,
            "branch": branch,
        }

        try:
            base_dir = ensure_base_clone(repo_full)
            with chdir(base_dir):
                dispatcher = TaskDispatcher()
                return dispatch_agent_for_pr_with_task(
                    dispatcher,
                    pr_payload,
                    task_description,
                    agent_cli=agent_cli,
                    model=model,
                )
        except Exception as exc:
            self.logger.error(
                "❌ Failed to dispatch fix-comment agent for %s #%s: %s",
                repo_full,
                pr_number,
                exc,
            )
            return False

    def _process_pr_fix_comment(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        agent_cli: str = "claude",
        model: str = None,
    ) -> str:
        repo_full = self._normalize_repository_name(repository)
        repo_name = repo_full.split("/")[-1]
        branch_name = pr_data.get("headRefName", "unknown")

        if self.no_act:
            self.logger.info("🧪 --no-act enabled: skipping fix-comment dispatch for %s #%s", repo_full, pr_number)
            return "skipped"

        head_sha, comments = self._get_pr_comment_state(repo_full, pr_number)
        # Handle API failures: treat None as empty list
        if comments is None:
            comments = []
        if head_sha and pr_data.get("headRefOid") != head_sha:
            pr_data = {**pr_data, "headRefOid": head_sha}

        # Check workflow-specific safety limits for fix-comment
        fix_comment_count = self._count_workflow_comments(comments, "fix_comment")
        if fix_comment_count >= self.safety_manager.fix_comment_limit:
            self.logger.info(
                f"🚫 Safety limits exceeded for PR {repo_full} #{pr_number} (fix-comment); "
                f"{fix_comment_count}/{self.safety_manager.fix_comment_limit} fix-comment automation comments"
            )
            return "skipped"

        # Check completion marker FIRST (authoritative checkpoint)
        # This is the real indicator that fix-comment actually completed for this commit
        has_completion_marker = False
        if head_sha:
            has_completion_marker = self._has_fix_comment_comment_for_commit(comments, head_sha)
        
        # Cache unaddressed comments check (expensive API call, avoid redundant calls)
        has_unaddressed = self._has_unaddressed_comments(repo_full, pr_number)
        
        # If completion marker exists, check if there are unaddressed comments
        # If no unaddressed comments, skip (work was completed successfully)
        if has_completion_marker:
            if not has_unaddressed:
                self.logger.info(
                    "✅ Fix-comment automation completed for commit %s on PR #%s with no unaddressed comments - skipping",
                    head_sha[:8] if head_sha else "unknown",
                    pr_number,
                )
                return "skipped"
            # Completion marker exists but there are unaddressed comments - reprocess
            self.logger.info(
                "🔄 Fix-comment completed for commit %s on PR #%s, but unaddressed comments exist - reprocessing",
                head_sha[:8] if head_sha else "unknown",
                pr_number,
            )
            # Continue to process unaddressed comments (skip history check since completion marker already decided)
        
        # If no completion marker, check commit history as fallback
        # History might be stale (recorded after queuing but before completion)
        elif head_sha and self._should_skip_pr(repo_name, branch_name, pr_number, head_sha):
            # No completion marker but commit in history - check unaddressed comments to decide
            if not has_unaddressed:
                self.logger.info(
                    "⏭️ Skipping PR #%s - commit %s in history and no unaddressed comments",
                    pr_number,
                    head_sha[:8],
                )
                return "skipped"
            # Commit in history but no completion marker AND unaddressed comments exist
            # This indicates a previous run didn't complete - reprocess
            self.logger.info(
                "🔄 PR #%s commit %s in history but no completion marker and unaddressed comments exist - reprocessing",
                pr_number,
                head_sha[:8],
            )
            # Continue to process unaddressed comments
        
        # Final check: if no completion marker and not in history, check for unaddressed comments
        elif not has_unaddressed:
            self.logger.info(
                "⏭️ Skipping PR #%s - no unaddressed comments found",
                pr_number,
            )
            return "skipped"

        # Race condition fix: Check if a queued comment already exists for this commit
        # This prevents duplicate agent dispatches during the window between when
        # a fix-comment run is queued and when the completion marker is posted
        # NOTE: Only check for queued markers if NO completion marker exists.
        # If completion marker exists, any queued marker is stale and should be ignored
        # (allows legitimate reprocessing when completion marker + unaddressed comments exist)
        if not has_completion_marker and head_sha:
            queued_info = self._get_fix_comment_queued_info(comments, head_sha)
            if queued_info:
                # Check if queued comment is stale (older than threshold with no completion)
                # This handles cases where agent failed silently and never posted completion marker
                queued_age_hours = queued_info.get("age_hours", 0)
                if queued_age_hours > STALE_QUEUE_THRESHOLD_HOURS:
                    self.logger.warning(
                        "⚠️ PR #%s has stale queued comment (%.1f hours old, no completion) - allowing re-run",
                        pr_number,
                        queued_age_hours,
                    )
                    # Allow re-run - agent likely failed
                else:
                    self.logger.info(
                        "⏭️ Skipping PR #%s - fix-comment run already queued for commit %s (%.1f hours ago)",
                        pr_number,
                        head_sha[:8],
                        queued_age_hours,
                    )
                    return "skipped"

        # Cleanup any pending reviews left behind by previous automation runs
        self._cleanup_pending_reviews(repo_full, pr_number)

        agent_success = self.dispatch_fix_comment_agent(repo_full, pr_number, pr_data, agent_cli=agent_cli, model=model)

        # Cleanup any pending reviews created by the agent during execution
        # This catches reviews created despite the warnings in the prompt
        self._cleanup_pending_reviews(repo_full, pr_number)

        if not agent_success:
            return "failed"

        queued_posted = self._post_fix_comment_queued(repo_full, pr_number, pr_data, head_sha, agent_cli=agent_cli)

        # NOTE: Do NOT record in history here - only record after completion marker is posted
        # The completion marker is the authoritative checkpoint, history is just a cache
        # Recording here causes stale history when runs are queued but don't complete

        if not self._start_fix_comment_review_watcher(
            repo_full,
            pr_number,
            agent_cli=agent_cli,
        ):
            self.logger.warning(
                "⚠️ Failed to start review watcher for PR #%s, but agent is dispatched",
                pr_number,
            )
            return "failed"

        if not queued_posted:
            self.logger.warning(
                "⚠️ Queued comment failed for PR #%s, but agent and watcher are running",
                pr_number,
            )
            return "partial"

        return "posted"

    def _process_pr_fixpr(
        self,
        repository: str,
        pr_number: int,
        pr_data: dict,
        agent_cli: str = "claude",
        model: str | None = None,
    ) -> str:
        repo_full = self._normalize_repository_name(repository)
        repo_name = repo_full.split("/")[-1]
        branch_name = pr_data.get("headRefName", "unknown")

        if self.no_act:
            self.logger.info("🧪 --no-act enabled: skipping fixpr dispatch for %s #%s", repo_full, pr_number)
            return "skipped"

        head_sha, comments = self._get_pr_comment_state(repo_full, pr_number)
        # Handle API failures: treat None as empty list
        if comments is None:
            comments = []
        if head_sha and pr_data.get("headRefOid") != head_sha:
            pr_data = {**pr_data, "headRefOid": head_sha}

        # Check workflow-specific safety limits for fixpr
        fixpr_count = self._count_workflow_comments(comments, "fixpr")
        if fixpr_count >= self.safety_manager.fixpr_limit:
            self.logger.info(
                f"🚫 Safety limits exceeded for PR {repo_full} #{pr_number} (fixpr); "
                f"{fixpr_count}/{self.safety_manager.fixpr_limit} fixpr automation comments"
            )
            return "skipped"

        # Check for conflicts or failing checks BEFORE skip check
        # If PR has issues, reprocess even if commit was already processed
        is_conflicting = False
        is_failing = False

        try:
            # Fetch mergeable status
            result = AutomationUtils.execute_subprocess_with_timeout(
                ["gh", "pr", "view", str(pr_number), "--repo", repo_full, "--json", "mergeable"],
                timeout=30, check=False
            )
            if result.returncode == 0:
                data = json.loads(result.stdout or "{}")
                if data.get("mergeable") == "CONFLICTING":
                    is_conflicting = True

            # Check for failing checks
            is_failing = has_failing_checks(repo_full, pr_number)
        except Exception as e:
            self.logger.warning(f"⚠️ Error checking PR status for #{pr_number} ({type(e).__name__}): {e}")
            # Continue with skip check if status check fails

        # Only skip if PR has no issues (no conflicts, no failing checks)
        # If PR has conflicts or failing checks, reprocess even if commit was already processed
        if head_sha and self._should_skip_pr(repo_name, branch_name, pr_number, head_sha):
            if not (is_conflicting or is_failing):
                self.logger.info(
                    "⏭️ Skipping PR #%s - already processed commit %s (no conflicts or failing checks)",
                    pr_number,
                    head_sha[:8],
                )
                return "skipped"
            self.logger.info(
                "🔄 Reprocessing PR #%s (commit %s) - has conflicts or failing checks",
                pr_number,
                head_sha[:8],
            )
                # Continue processing despite skip check

        # Cleanup any pending reviews left behind by previous automation runs
        self._cleanup_pending_reviews(repo_full, pr_number)

        # Dispatch agent for fixpr
        try:
            base_dir = ensure_base_clone(repo_full)
            with chdir(base_dir):
                dispatcher = TaskDispatcher()
                # Prepare PR dict for dispatch_agent_for_pr
                pr_info = {
                    "repo_full": repo_full,
                    "repo": repo_name,
                    "number": pr_number,
                    "branch": branch_name,
                }
                success = dispatch_agent_for_pr(dispatcher, pr_info, agent_cli=agent_cli, model=model)

                # Cleanup any pending reviews created by the agent during execution
                # This catches reviews created despite the warnings in the prompt
                self._cleanup_pending_reviews(repo_full, pr_number)

                if success:
                    queued_posted = self._post_fixpr_queued(repo_full, pr_number, pr_data, head_sha, agent_cli=agent_cli)
                    # Record processing so we don't loop
                    if head_sha:
                        self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)

                    if not queued_posted:
                        self.logger.warning(
                            "⚠️ Queued comment failed for PR #%s, but agent is dispatched",
                            pr_number,
                        )
                        return "partial"

                    return "posted" # "posted" means action taken
                return "failed"
        except Exception as exc:
            self.logger.error(
                "❌ Failed to dispatch fixpr agent for %s #%s: %s",
                repo_full,
                pr_number,
                exc,
            )
            return "failed"

    def _get_pr_comment_state(self, repo_full_name: str, pr_number: int) -> tuple[str | None, list[dict] | None]:
        """Fetch PR comment data needed for Codex comment gating.
        
        Returns:
            Tuple of (head_sha, comments). If API call fails, returns (None, None) to
            distinguish from "no comments" case (None, []). Callers should check for
            None comments and treat as "unknown" rather than skipping.
        """
        view_cmd = [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo_full_name,
            "--json",
            "headRefOid,comments",
        ]

        try:
            result = AutomationUtils.execute_subprocess_with_timeout(
                view_cmd,
                timeout=30,
                check=False
            )
            # Check return code to distinguish API failures from empty results
            if result.returncode != 0:
                error_message = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
                self.logger.warning(
                    f"⚠️ Failed to fetch PR comment state for PR #{pr_number}: {error_message}"
                )
                # Return sentinel value to indicate API failure (distinct from "no comments")
                # Caller should treat this as "unknown" rather than "no comments"
                return None, None

            pr_data = json.loads(result.stdout or "{}")
            head_sha = pr_data.get("headRefOid")

            # Handle different comment structures from GitHub API
            comments_data = pr_data.get("comments", [])
            if isinstance(comments_data, dict):
                comments = comments_data.get("nodes", [])
            elif isinstance(comments_data, list):
                comments = comments_data
            else:
                comments = []

            # Ensure comments are sorted by creation time (oldest first)
            # GitHub API should return them sorted, but let's be explicit
            comments.sort(
                key=lambda c: (c.get("createdAt") or c.get("updatedAt") or "")
            )

            return head_sha, comments
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip() if e.stderr else str(e)
            self.logger.warning(
                f"⚠️ Failed to fetch PR comment state for PR #{pr_number}: {error_message}"
            )
            # Return sentinel value to indicate API failure
            return None, None
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"⚠️ Failed to parse PR comment state for PR #{pr_number}: {e}"
            )
            # Return sentinel value to indicate parse failure
            return None, None

    def _get_head_commit_details(
        self,
        repo_full_name: str,
        pr_number: int,
        expected_sha: str | None = None,
    ) -> dict[str, str | None] | None:
        """Fetch metadata for the PR head commit using the GitHub GraphQL API."""

        if "/" not in repo_full_name:
            self.logger.debug(
                "⚠️ Cannot fetch commit details for %s - invalid repo format",
                repo_full_name,
            )
            return None

        owner, name = repo_full_name.split("/", 1)

        # Validate GitHub naming constraints (alphanumeric, hyphens, periods, underscores, max 100 chars)
        github_name_pattern = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\._]{0,98}[a-zA-Z0-9])?$")
        if not github_name_pattern.match(owner) or not github_name_pattern.match(name):
            self.logger.warning(
                "⚠️ Invalid GitHub identifiers: owner='%s', name='%s'",
                owner,
                name,
            )
            return None

        # Validate PR number is positive integer
        if not isinstance(pr_number, int) or pr_number <= 0:
            self.logger.warning("⚠️ Invalid PR number: %s", pr_number)
            return None

        cmd = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={self._HEAD_COMMIT_DETAILS_QUERY}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={name}",
            "-F",
            f"prNumber={pr_number}",
        ]

        try:
            result = AutomationUtils.execute_subprocess_with_timeout(cmd, timeout=30)
        except subprocess.CalledProcessError as exc:
            self.logger.debug(
                "⚠️ Failed to fetch head commit details for %s#%s: %s",
                repo_full_name,
                pr_number,
                exc.stderr or exc,
            )
            return None
        except Exception as exc:
            self.logger.debug(
                "⚠️ Error executing head commit lookup for %s#%s: %s",
                repo_full_name,
                pr_number,
                exc,
            )
            return None

        try:
            data = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            self.logger.debug(
                "⚠️ Failed to decode commit details for %s#%s: %s",
                repo_full_name,
                pr_number,
                exc,
            )
            return None

        pr_data = (
            data.get("data", {})
            .get("repository", {})
            .get("pullRequest", {})
        )
        commits_data = pr_data.get("commits") or {}
        commit_nodes = commits_data.get("nodes") if isinstance(commits_data, dict) else None
        if not commit_nodes or not isinstance(commit_nodes, list):
            return None

        commit_info = commit_nodes[-1].get("commit") if commit_nodes else None
        if not commit_info:
            return None

        commit_sha = commit_info.get("oid")
        if expected_sha and commit_sha and commit_sha != expected_sha:
            # If GitHub served stale data, ignore it to avoid mismatched metadata.
            return None

        author_info = commit_info.get("author") or {}
        committer_info = commit_info.get("committer") or {}

        author_login, author_email, author_name = self._extract_actor_fields(author_info)
        committer_login, committer_email, committer_name = self._extract_actor_fields(committer_info)

        # Log commit detection with redacted emails for privacy
        self.logger.debug(
            "📧 Commit %s: author=%s (%s), committer=%s (%s)",
            commit_sha[:8] if commit_sha else "unknown",
            author_login or "unknown",
            self._redact_email(author_email) if author_email else "no-email",
            committer_login or "unknown",
            self._redact_email(committer_email) if committer_email else "no-email",
        )

        return {
            "sha": commit_sha,
            "author_login": author_login,
            "author_email": author_email,
            "author_name": author_name,
            "committer_login": committer_login,
            "committer_email": committer_email,
            "committer_name": committer_name,
            "message_headline": commit_info.get("messageHeadline"),
            "message": commit_info.get("message"),
        }

    def _extract_commit_marker(self, comment_body: str) -> str | None:
        """Extract commit marker from Codex automation comment"""
        if not comment_body:
            return None

        prefix_index = comment_body.find(self.CODEX_COMMIT_MARKER_PREFIX)
        if prefix_index == -1:
            return None

        start_index = prefix_index + len(self.CODEX_COMMIT_MARKER_PREFIX)
        end_index = comment_body.find(self.CODEX_COMMIT_MARKER_SUFFIX, start_index)
        if end_index == -1:
            return None

        return comment_body[start_index:end_index].strip()

    def _extract_fix_comment_marker(self, comment_body: str) -> str | None:
        """Extract commit SHA from fix-comment automation comments.
        
        Handles both old format (SHA) and new format (SHA:cli).
        Returns just the SHA portion for comparison.
        """
        if not comment_body:
            return None

        prefix_index = comment_body.find(self.FIX_COMMENT_MARKER_PREFIX)
        if prefix_index == -1:
            return None

        start_index = prefix_index + len(self.FIX_COMMENT_MARKER_PREFIX)
        end_index = comment_body.find(self.FIX_COMMENT_MARKER_SUFFIX, start_index)
        if end_index == -1:
            return None

        marker_content = comment_body[start_index:end_index].strip()
        # Handle new format: SHA:cli -> extract just SHA
        # Also handles old format: SHA (no colon)
        if ":" in marker_content:
            marker_content = marker_content.split(":")[0]

        return marker_content

    def _extract_fix_comment_run_marker(self, comment_body: str) -> str | None:
        """Extract commit SHA from fix-comment queued run markers.
        
        Handles format: <!-- fix-comment-run-automation-commit:agent:sha -->
        Returns just the SHA portion for comparison.
        """
        if not comment_body:
            return None

        prefix_index = comment_body.find(self.FIX_COMMENT_RUN_MARKER_PREFIX)
        if prefix_index == -1:
            return None

        start_index = prefix_index + len(self.FIX_COMMENT_RUN_MARKER_PREFIX)
        end_index = comment_body.find(self.FIX_COMMENT_RUN_MARKER_SUFFIX, start_index)
        if end_index == -1:
            return None

        marker_content = comment_body[start_index:end_index].strip()
        # Format is agent:sha, extract just SHA (last part after colon)
        if ":" in marker_content:
            marker_content = marker_content.split(":")[-1]

        return marker_content

    def _has_codex_comment_for_commit(self, comments: list[dict], head_sha: str) -> bool:
        """Determine if Codex instruction already exists for the latest commit"""
        if not head_sha:
            return False

        for comment in comments:
            body = comment.get("body", "")
            marker_sha = self._extract_commit_marker(body)
            if marker_sha and marker_sha == head_sha:
                return True

        return False

    def _has_fix_comment_comment_for_commit(self, comments: list[dict], head_sha: str) -> bool:
        """Determine if fix-comment automation already ran for the latest commit."""
        if not head_sha:
            return False

        for comment in comments:
            body = comment.get("body", "")
            marker_sha = self._extract_fix_comment_marker(body)
            if marker_sha and marker_sha == head_sha and self.FIX_COMMENT_COMPLETION_MARKER in body:
                return True

        return False

    def _has_fix_comment_queued_for_commit(self, comments: list[dict], head_sha: str) -> bool:
        """Determine if a fix-comment run is already queued for the latest commit.
        
        This prevents duplicate agent dispatches during the window between when
        a fix-comment run is queued and when the completion marker is posted.
        """
        return self._get_fix_comment_queued_info(comments, head_sha) is not None

    def _get_fix_comment_queued_info(self, comments: list[dict], head_sha: str) -> dict | None:
        """Get info about queued fix-comment comment for a commit, including age.
        
        Returns dict with 'age_hours' and 'created_at' if found, None otherwise.
        This allows checking if a queued comment is stale (agent failed silently).
        """
        if not head_sha:
            return None

        for comment in comments:
            body = comment.get("body", "")
            # Check for queued run marker (FIX_COMMENT_RUN_MARKER_PREFIX)
            marker_sha = self._extract_fix_comment_run_marker(body)
            if marker_sha and marker_sha == head_sha:
                # Verify this is from automation user (not a bot echo)
                author = self._get_comment_author_login(comment)
                if author == self.automation_username:
                    # GitHub API returns timestamps in camelCase (createdAt)
                    created_at_str = comment.get("createdAt") or comment.get("created_at", "")
                    if created_at_str:
                        try:
                            # Normalize ISO 8601 timestamp: replace 'Z' with '+00:00' for consistent parsing
                            # (defensive normalization - Python 3.11+ supports 'Z' directly, but this ensures compatibility)
                            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                            # Ensure timezone-aware datetime (handle edge case where fromisoformat returns naive)
                            if created_at.tzinfo is None:
                                created_at = created_at.replace(tzinfo=timezone.utc)
                            now = datetime.now(timezone.utc)
                            age_hours = (now - created_at).total_seconds() / 3600
                            return {
                                "age_hours": age_hours,
                                "created_at": created_at_str,
                            }
                        except (ValueError, AttributeError, TypeError):
                            # If we can't parse date or compare (naive vs aware), assume it's recent (conservative)
                            return {"age_hours": 0.0, "created_at": created_at_str}
                    return {"age_hours": 0.0, "created_at": ""}

        return None

    def _is_head_commit_from_codex(
        self, commit_details: dict[str, str | None] | None
    ) -> bool:
        """Determine if the head commit was authored or marked by Codex."""

        if not commit_details:
            return False

        actor_fields = [
            commit_details.get("author_login"),
            commit_details.get("author_email"),
            commit_details.get("author_name"),
            commit_details.get("committer_login"),
            commit_details.get("committer_email"),
            commit_details.get("committer_name"),
        ]

        for field in actor_fields:
            if field and isinstance(field, str):
                if any(pattern.search(field) for pattern in self._codex_actor_patterns):
                    return True

        message_values = [
            commit_details.get("message_headline"),
            commit_details.get("message"),
        ]

        for message in message_values:
            if message and isinstance(message, str):
                if self._codex_commit_message_pattern.search(message):
                    return True

        return False

    def _is_github_bot_comment(self, comment: dict) -> bool:
        """Check if comment is from a GitHub bot (not Codex/AI automation).

        Detection order matters:
        1. Check KNOWN_GITHUB_BOTS first (these are review bots we want to detect)
        2. Then check [bot] suffix for other bots
        3. Only exclude codex patterns for bots NOT in our known list
        """
        author_login = self._get_comment_author_login(comment)
        if not author_login:
            return False

        lower_login = author_login.lower()

        # Strip [bot] suffix for known bot comparison (handles both "coderabbitai" and "coderabbitai[bot]")
        base_login = lower_login.removesuffix("[bot]")

        # Check known review bots FIRST (before codex pattern exclusion)
        # These are legitimate review bots whose comments should trigger re-processing
        if base_login in self.KNOWN_GITHUB_BOTS:
            return True

        # GitHub bots have [bot] suffix - but exclude our own automation bots
        # Use case-insensitive check for robustness
        if lower_login.endswith("[bot]"):
            # Exclude our own Codex/AI automation bots (chatgpt-codex-connector[bot], etc.)
            for pattern in self._codex_actor_patterns:
                if pattern.search(lower_login):
                    return False
            return True

        return False

    def _get_last_codex_automation_comment_time(self, comments: list[dict]) -> str | None:
        """Find the timestamp of the last automation comment (any workflow marker).

        Note: Despite the method name, this checks ALL automation workflow markers
        (codex, fix-comment, fixpr) to prevent rerun gating misfires with multiple workflows.
        """
        last_time = None

        for comment in comments:
            body = comment.get("body", "")
            # Check if this is ANY automation comment (any workflow marker)
            if (
                self.CODEX_COMMIT_MARKER_PREFIX in body
                or self.FIX_COMMENT_MARKER_PREFIX in body
                or self.FIX_COMMENT_RUN_MARKER_PREFIX in body
                or self.FIXPR_MARKER_PREFIX in body
            ):
                created_at = comment.get("createdAt") or comment.get("updatedAt")
                if created_at and (last_time is None or created_at > last_time):
                    last_time = created_at

        return last_time

    def _count_codex_automation_comments(self, comments: list[dict]) -> int:
        """Count the number of Codex automation comments (with commit marker).

        This is used for safety limits - we only count comments that contain
        the CODEX_COMMIT_MARKER_PREFIX, not all comments from jleechan2015.
        """
        count = 0
        for comment in comments:
            body = comment.get("body", "")
            if self.CODEX_COMMIT_MARKER_PREFIX in body or self.FIX_COMMENT_MARKER_PREFIX in body:
                count += 1
        return count

    def _count_workflow_comments(self, comments: list[dict], workflow_type: str) -> int:
        """Count automation comments for a specific workflow type.

        NEW BEHAVIOR: Counts comments from TODAY only (daily cooldown, resets at midnight).

        Args:
            comments: List of PR comments
            workflow_type: One of 'pr_automation', 'fix_comment', 'codex_update', 'fixpr'

        Returns:
            Count of comments matching the workflow type from today

        Note: codex_update workflow operates via browser automation (not PR comments),
        so count is always 0. The limit is configured but unused, reserved for future
        compatibility if codex_update ever posts PR comments.
        """
        # codex_update doesn't post PR comments, so always returns 0
        # Limit is configured but unused (reserved for future compatibility)
        if workflow_type == "codex_update":
            return 0

        # Filter to today's comments only (daily cooldown)
        # GitHub timestamps are UTC, so compare against UTC date only
        today_utc = datetime.now(UTC).date().isoformat()
        count = 0
        for comment in comments:
            # Check if comment is from today (daily cooldown)
            # GitHub API returns ISO 8601 timestamps (UTC), extract date portion
            created_at = comment.get("createdAt") or comment.get("updatedAt")
            if not created_at:
                continue  # Skip comments without timestamps (cannot verify if from today)

            # Extract date from ISO timestamp (e.g., "2026-01-12T07:34:23Z" -> "2026-01-12")
            comment_date = created_at.split("T")[0] if "T" in created_at else created_at[:10]
            # Match if comment date matches UTC today (GitHub timestamps are always UTC)
            if comment_date != today_utc:
                continue  # Skip comments from previous days

            body = comment.get("body", "")

            if workflow_type == "pr_automation":
                # PR automation uses codex-automation-commit marker (but not fix-comment or fixpr)
                if (
                    self.CODEX_COMMIT_MARKER_PREFIX in body
                    and self.FIX_COMMENT_MARKER_PREFIX not in body
                    and self.FIX_COMMENT_RUN_MARKER_PREFIX not in body
                    and self.FIXPR_MARKER_PREFIX not in body
                ):
                    count += 1
            elif workflow_type == "fix_comment":
                # Fix-comment workflow uses dedicated markers for queued runs + completion.
                # Only count if posted by the automation user, not bots echoing the marker
                if self.FIX_COMMENT_RUN_MARKER_PREFIX in body or self.FIX_COMMENT_MARKER_PREFIX in body:
                    author = self._get_comment_author_login(comment)
                    # Only count comments from the automation user
                    # Exclude bot replies that might echo the marker in quoted text or scripts
                    if author == self.automation_username:
                        count += 1
            elif workflow_type == "fixpr":
                # FixPR workflow uses a dedicated marker in its queued comment.
                # Only count if posted by the automation user, not bots echoing the marker
                if self.FIXPR_MARKER_PREFIX in body:
                    author = self._get_comment_author_login(comment)
                    if author == self.automation_username:
                        count += 1
            # Fallback: count all automation comments
            elif (
                self.CODEX_COMMIT_MARKER_PREFIX in body
                or self.FIX_COMMENT_MARKER_PREFIX in body
                or self.FIX_COMMENT_RUN_MARKER_PREFIX in body
                or self.FIXPR_MARKER_PREFIX in body
            ):
                count += 1
        return count

    def _has_new_bot_comments_since_codex(self, comments: list[dict]) -> bool:
        """Check if there are new GitHub bot comments since the last Codex automation comment.

        This allows automation to run even when head commit is from Codex if
        there are new bot comments (like CI failures, review bot comments) that
        need attention.
        """
        last_codex_time = self._get_last_codex_automation_comment_time(comments)

        # If no Codex automation comment exists, treat any bot comment as new
        if not last_codex_time:
            for comment in comments:
                if self._is_github_bot_comment(comment):
                    created_at = comment.get("createdAt") or comment.get("updatedAt")
                    self.logger.debug(
                        "🤖 Found bot comment from %s at %s with no prior Codex automation comment",
                        self._get_comment_author_login(comment),
                        created_at,
                    )
                    return True
            return False

        for comment in comments:
            if not self._is_github_bot_comment(comment):
                continue

            created_at = comment.get("createdAt") or comment.get("updatedAt")
            if created_at and created_at > last_codex_time:
                self.logger.debug(
                    "🤖 Found new bot comment from %s at %s (after Codex comment at %s)",
                    self._get_comment_author_login(comment),
                    created_at,
                    last_codex_time,
                )
                return True

        return False

    def _get_comment_author_login(self, comment: dict) -> str:
        """Return normalized author login for a comment."""
        author = comment.get("author") or comment.get("user") or {}
        if isinstance(author, dict):
            return (author.get("login") or author.get("name") or "").strip()
        if isinstance(author, str):
            return author.strip()
        return ""

    def _has_unaddressed_comments(self, repo_full: str, pr_number: int) -> bool:
        """
        Check if PR has unaddressed comments that require a response.
        Returns True only if there are actionable comments that haven't been replied to.
        """
        try:
            # Fetch issue comments (already available from _get_pr_comment_state, but fetch fresh)
            issue_comments_cmd = [
                "gh", "api",
                f"/repos/{repo_full}/issues/{pr_number}/comments",
                "--paginate", "-F", "per_page=100"
            ]
            issue_result = AutomationUtils.execute_subprocess_with_timeout(
                issue_comments_cmd, timeout=30, check=False
            )
            issue_comments = []
            if issue_result.returncode == 0:
                try:
                    issue_comments = json.loads(issue_result.stdout or "[]")
                    if not isinstance(issue_comments, list):
                        issue_comments = []
                except json.JSONDecodeError:
                    issue_comments = []

            # Fetch review comments (review summaries)
            review_comments_cmd = [
                "gh", "api",
                f"/repos/{repo_full}/pulls/{pr_number}/reviews",
                "--paginate", "-F", "per_page=100"
            ]
            review_result = AutomationUtils.execute_subprocess_with_timeout(
                review_comments_cmd, timeout=30, check=False
            )
            review_comments = []
            if review_result.returncode == 0:
                try:
                    review_comments = json.loads(review_result.stdout or "[]")
                    if not isinstance(review_comments, list):
                        review_comments = []
                except json.JSONDecodeError:
                    review_comments = []

            # Fetch inline review comments
            inline_comments_cmd = [
                "gh", "api",
                f"/repos/{repo_full}/pulls/{pr_number}/comments",
                "--paginate", "-F", "per_page=100"
            ]
            inline_result = AutomationUtils.execute_subprocess_with_timeout(
                inline_comments_cmd, timeout=30, check=False
            )
            inline_comments = []
            if inline_result.returncode == 0:
                try:
                    inline_comments = json.loads(inline_result.stdout or "[]")
                    if not isinstance(inline_comments, list):
                        inline_comments = []
                except json.JSONDecodeError:
                    inline_comments = []

            # Check for API failures BEFORE combining comments
            # If ANY API call failed, treat as unknown and proceed conservatively
            # This prevents skipping PRs when API calls fail due to auth/rate-limit errors
            # Partial failures mean we can't reliably determine if comments exist
            api_failures = [
                ("issue comments", issue_result.returncode != 0),
                ("review comments", review_result.returncode != 0),
                ("inline comments", inline_result.returncode != 0),
            ]
            failed_endpoints = [name for name, failed in api_failures if failed]
            if failed_endpoints:
                self.logger.warning(
                    f"⚠️ API call(s) failed for PR #{pr_number} ({', '.join(failed_endpoints)}) - "
                    f"treating as unknown and proceeding conservatively"
                )
                return True  # Proceed conservatively when ANY API failure occurs

            # Combine all comments
            all_comments = issue_comments + review_comments + inline_comments

            if not all_comments:
                self.logger.debug(f"📭 PR #{pr_number} has no comments")
                return False

            # Track which inline comments have replies (for inline comments only)
            # Note: GitHub uses separate ID namespaces for issue comments, reviews, and inline comments
            # So we must only check replied_comment_ids for inline comments to avoid false positives
            replied_comment_ids = set()
            for comment in inline_comments:
                in_reply_to = comment.get("in_reply_to_id")
                if in_reply_to:
                    replied_comment_ids.add(in_reply_to)

            # Filter comments to find actionable ones
            actionable_count = 0
            automation_count = 0
            replied_count = 0

            for comment in all_comments:
                author_login = self._get_comment_author_login(comment)
                comment_body = comment.get("body", "").strip()

                # Skip empty comments (e.g., review approvals without body text)
                if not comment_body:
                    continue

                # Skip automation user's own comments
                if author_login == self.automation_username:
                    automation_count += 1
                    continue

                # Skip automation markers (queued notices, automation comments)
                if any(marker in comment_body for marker in [
                    "[AI automation",
                    "[fixpr",
                    "[fix-comment",
                    "FixPR run queued",
                    "Fix-comment run queued",
                    "AI automation -"
                ]):
                    automation_count += 1
                    continue

                # Skip inline comments that have replies (already addressed)
                # Only check replied_comment_ids for inline comments to avoid ID namespace collisions
                comment_id = comment.get("id")
                is_inline_comment = bool(
                    comment.get("pull_request_review_id")
                    or comment.get("path")
                    or comment.get("diff_hunk")
                    or comment.get("line") is not None
                )
                if is_inline_comment and comment_id in replied_comment_ids:
                    replied_count += 1
                    continue

                # Skip if this comment is itself a reply (for inline comments)
                if comment.get("in_reply_to_id"):
                    replied_count += 1
                    continue

                # Skip review comments that are just approvals/rejections without substantive feedback
                review_state = comment.get("state")
                if review_state in ["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]:
                    # Only consider actionable if there's actual body text (not just state change)
                    if not comment_body or len(comment_body) < 10:
                        continue

                # Skip informational bot messages (deployment notices, etc.)
                if self._is_github_bot_comment(comment):
                    # Check if it's informational only (deployment, status updates)
                    if any(phrase in comment_body.lower() for phrase in [
                        "deployment complete",
                        "preview is ready",
                        "checks have passed",
                        "checks have failed",
                        "rate limit exceeded"
                    ]):
                        continue

                # This is an actionable comment
                actionable_count += 1

            self.logger.debug(
                f"📊 PR #{pr_number} comment analysis: {actionable_count} actionable, "
                f"{automation_count} automation, {replied_count} replied, "
                f"{len(all_comments)} total"
            )

            return actionable_count > 0

        except Exception as e:
            self.logger.warning(
                f"⚠️ Error checking unaddressed comments for PR #{pr_number}: {e}"
            )
            # On error, assume there might be comments (safer to check than skip)
            return True

    def _extract_codex_summary_commit(self, comment_body: str) -> str | None:
        """Extract commit SHA referenced in Codex summary comment."""
        if not comment_body:
            return None

        for pattern in self.CODEX_SUMMARY_COMMIT_PATTERNS:
            match = pattern.search(comment_body)
            if match:
                return match.group(1).lower()

        return None

    def _has_pending_codex_commit(self, comments: list[dict], head_sha: str) -> bool:
        """Detect if latest commit was generated by Codex automation and is still pending."""
        if not head_sha:
            return False

        normalized_head = head_sha.lower()

        for comment in comments:
            author_login = self._get_comment_author_login(comment)
            if not author_login or self.CODEX_BOT_IDENTIFIER not in author_login.lower():
                continue

            summary_commit = self._extract_codex_summary_commit(comment.get("body", ""))
            if not summary_commit:
                continue

            if summary_commit == normalized_head or normalized_head.startswith(
                summary_commit
            ):
                return True

        return False

    def process_single_pr_by_number(
        self,
        pr_number: int,
        repository: str,
        *,
        fix_comment: bool = False,
        fixpr: bool = False,
        agent_cli: str = "claude",
        model: str = None,
    ) -> bool:
        """Process a specific PR by number and repository"""
        repo_full = self._normalize_repository_name(repository)
        self.logger.info(f"🎯 Processing target PR: {repo_full} #{pr_number}")

        # Check global automation limits (fixpr uses per-PR limits only)
        # Note: fixpr workflow bypasses global limit check - it uses per-PR fixpr_limit instead
        # This allows fixpr to process PRs independently based on per-PR comment counts
        if not fixpr and not self.safety_manager.can_start_global_run():
            self.logger.warning("🚫 Global automation limit reached - cannot process target PR")
            return False

        # Cleanup pending reviews BEFORE all eligibility checks (ensures cleanup even if PR is skipped)
        # Run cleanup for workflows that might create pending reviews (fixpr, fix_comment)
        if fixpr or fix_comment:
            self._cleanup_pending_reviews(repo_full, pr_number)

        try:
            # Check workflow-specific safety limits
            workflow_type = self._determine_workflow_type(fix_comment, fixpr)
            _, comments = self._get_pr_comment_state(repo_full, pr_number)
            # Handle API failures: if comments is None, treat as "unknown" and proceed
            # (don't skip PRs when API calls fail - assume comments might exist)
            if comments is None:
                self.logger.warning(
                    f"⚠️ Could not fetch comments for PR {repo_full} #{pr_number} - treating as unknown and proceeding"
                )
                comments = []  # Use empty list for counting, but don't skip the PR
            automation_comment_count = self._count_workflow_comments(comments, workflow_type)

            # Get workflow-specific limit
            if workflow_type == "fix_comment":
                workflow_limit = self.safety_manager.fix_comment_limit
            elif workflow_type == "fixpr":
                workflow_limit = self.safety_manager.fixpr_limit
            elif workflow_type == "pr_automation":
                workflow_limit = self.safety_manager.pr_automation_limit
            else:
                workflow_limit = self.safety_manager.pr_limit  # Fallback

            if automation_comment_count >= workflow_limit:
                self.logger.warning(
                    f"🚫 Safety limits exceeded for PR {repo_full} #{pr_number} ({workflow_type}); "
                    f"{automation_comment_count}/{workflow_limit} automation comments"
                )
                # Not an execution failure: we're intentionally skipping to avoid spamming.
                return True

            if self.no_act:
                self.logger.info(
                    "🧪 --no-act enabled: skipping processing for %s #%s (would run %s)",
                    repo_full,
                    pr_number,
                    workflow_type,
                )
                return True

            # Check safety limits for this specific PR first
            if not self.safety_manager.try_process_pr(pr_number, repo=repo_full):
                self.logger.warning(f"🚫 Internal safety limits exceeded for PR {repo_full} #{pr_number}")
                return False

            # Only record global run AFTER confirming we can process the PR
            if not self.wrapper_managed and not fixpr:
                self.safety_manager.record_global_run()
                current_runs = self.safety_manager.get_global_runs()
                self.logger.info(
                    "📊 Recorded global run %s/%s before processing target PR",
                    current_runs,
                    self.safety_manager.global_limit,
                )

            # Process PR with guaranteed cleanup
            try:
                # Get PR details using gh CLI
                result = AutomationUtils.execute_subprocess_with_timeout(
                    ["gh", "pr", "view", str(pr_number), "--repo", repo_full, "--json", "title,headRefName,baseRefName,url,author,headRefOid,mergeable"],
                    timeout=30
                )
                pr_data = json.loads(result.stdout or "{}")

                if not pr_data or "title" not in pr_data:
                    self.logger.error(f"❌ Failed to fetch PR data for #{pr_number} - empty or invalid response")
                    return False

                self.logger.info(f"📝 Found PR: {pr_data['title']}")

                if fix_comment:
                    comment_result = self._process_pr_fix_comment(
                        repo_full,
                        pr_number,
                        pr_data,
                        agent_cli=agent_cli,
                        model=model,
                    )
                elif fixpr:
                    comment_result = self._process_pr_fixpr(
                        repo_full,
                        pr_number,
                        pr_data,
                        agent_cli=agent_cli,
                        model=model,
                    )
                else:
                    # Post codex instruction comment
                    comment_result = self.post_codex_instruction_simple(repo_full, pr_number, pr_data)
                # Treat "skipped" as a neutral outcome: do not count it as failure,
                # and avoid recording an unbounded stream of skipped attempts.
                success = comment_result in {"posted", "skipped"}
                if comment_result != "skipped":
                    result = "success" if comment_result == "posted" else "failure"
                    self.safety_manager.record_pr_attempt(
                        pr_number,
                        result,
                        repo=repo_full,
                        branch=pr_data.get("headRefName"),
                    )

                if success:
                    self.logger.info(f"✅ Successfully processed target PR {repo_full} #{pr_number}")
                else:
                    self.logger.error(f"❌ Failed to process target PR {repo_full} #{pr_number}")

                return success

            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ Failed to get PR details for {repo_full} #{pr_number}: {e.stderr}")
                return False
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Failed to parse PR data for {repo_full} #{pr_number}: {e}")
                return False
            finally:
                # Always release the processing slot
                self.safety_manager.release_pr_slot(pr_number, repo=repo_full)

        except Exception as e:
            self.logger.error(f"❌ Unexpected error processing target PR {repo_full} #{pr_number}: {e}")
            self.logger.debug("Traceback: %s", traceback.format_exc())
            return False

    def run_monitoring_cycle(self, single_repo=None, max_prs=10, cutoff_hours: int = 24, fix_comment: bool = False, fixpr: bool = False, agent_cli: str = "claude", model: str = None):
        """Run a complete monitoring cycle with actionable PR counting"""
        mode_label = "fix-comment" if fix_comment else ("fixpr" if fixpr else "comment")
        self.logger.info("🚀 Starting jleechanorg PR monitoring cycle (%s mode)", mode_label)

        # FixPR workflow uses per-PR limits only, not global limit
        # Other workflows (fix-comment, pr_automation) still check global limit
        if not fixpr and not self.safety_manager.can_start_global_run():
            current_runs = self.safety_manager.get_global_runs()
            self.logger.warning(
                "🚫 Global automation limit reached %s/%s",
                current_runs,
                self.safety_manager.global_limit,
            )
            self.safety_manager.check_and_notify_limits()
            return

        global_run_recorded = self.wrapper_managed

        try:
            open_prs = self.discover_open_prs(cutoff_hours=cutoff_hours)
        except Exception as exc:
            self.logger.error("❌ Failed to discover PRs: %s", exc)
            self.logger.debug("Traceback: %s", traceback.format_exc())
            self.safety_manager.check_and_notify_limits()
            return

        # Apply single repo filter if specified
        if single_repo:
            open_prs = [pr for pr in open_prs if pr["repository"] == single_repo]
            self.logger.info(f"🎯 Filtering to repository: {single_repo}")

        if not open_prs:
            self.logger.info("📭 No open PRs found")
            return

        # Use enhanced actionable counting instead of simple max_prs limit
        target_actionable_count = max_prs  # Convert max_prs to actionable target
        actionable_processed = 0
        skipped_count = 0

        for pr in open_prs:
            if actionable_processed >= target_actionable_count:
                break

            repo_name = pr["repository"]
            repo_full_name = self._normalize_repository_name(
                pr.get("repositoryFullName") or repo_name
            )
            pr_number = pr["number"]

            # Cleanup pending reviews BEFORE any eligibility checks
            # This ensures cleanup runs even if PR is skipped for any reason
            # Run cleanup for workflows that might create pending reviews (fixpr, fix_comment)
            if fixpr or fix_comment:
                self._cleanup_pending_reviews(repo_full_name, pr_number)

            # For fixpr, check for conflicts/failing checks BEFORE is_pr_actionable
            # This ensures PRs with issues get reprocessed even if commit was already processed
            if fixpr:
                # Variables already set above, reuse them
                # Check for conflicts or failing checks first
                is_conflicting = False
                is_failing = False

                try:
                    result = AutomationUtils.execute_subprocess_with_timeout(
                        ["gh", "pr", "view", str(pr_number), "--repo", repo_full_name, "--json", "mergeable"],
                        timeout=30, check=False
                    )
                    if result.returncode == 0:
                        data = json.loads(result.stdout or "{}")
                        if data.get("mergeable") == "CONFLICTING":
                            is_conflicting = True

                    is_failing = has_failing_checks(repo_full_name, pr_number)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking fixpr eligibility for #{pr_number} ({type(e).__name__}): {e}")

                # If PR has conflicts or failing checks, mark as actionable (bypass is_pr_actionable skip)
                if is_conflicting or is_failing:
                    self.logger.info(
                        f"🔄 PR #{pr_number} has conflicts or failing checks - marking actionable for fixpr"
                    )
                    # Skip is_pr_actionable check and proceed directly to processing
                # Only check is_pr_actionable if no issues found
                elif not self.is_pr_actionable(pr):
                    skipped_count += 1
                    continue

            # For non-fixpr workflows, use standard actionable check
            elif not self.is_pr_actionable(pr):
                skipped_count += 1
                continue

            branch_name = pr.get("headRefName", "unknown")

            # Check automation comment count on GitHub (not internal attempts)
            # Determine workflow type based on mode
            workflow_type = self._determine_workflow_type(fix_comment, fixpr)
            _, comments = self._get_pr_comment_state(repo_full_name, pr_number)
            # Handle API failures: treat None as empty list
            if comments is None:
                comments = []
            automation_comment_count = self._count_workflow_comments(comments, workflow_type)

            # Get workflow-specific limit
            if workflow_type == "fix_comment":
                workflow_limit = self.safety_manager.fix_comment_limit
            elif workflow_type == "fixpr":
                workflow_limit = self.safety_manager.fixpr_limit
            elif workflow_type == "pr_automation":
                workflow_limit = self.safety_manager.pr_automation_limit
            else:
                workflow_limit = self.safety_manager.pr_limit  # Fallback

            if automation_comment_count >= workflow_limit:
                self.logger.info(
                    f"🚫 Safety limits exceeded for PR {repo_full_name} #{pr_number} ({workflow_type}); "
                    f"{automation_comment_count}/{workflow_limit} automation comments"
                )
                skipped_count += 1
                continue

            if not self.safety_manager.try_process_pr(pr_number, repo=repo_full_name, branch=branch_name):
                self.logger.info(
                    f"🚫 Internal safety limits exceeded for PR {repo_full_name} #{pr_number}; skipping"
                )
                skipped_count += 1
                continue

            self.logger.info(f"🎯 Processing PR: {repo_full_name} #{pr_number} - {pr.get('title', 'unknown')}")

            attempt_recorded = False
            try:
                if not global_run_recorded and not fixpr:
                    self.safety_manager.record_global_run()
                    global_run_recorded = True
                    current_runs = self.safety_manager.get_global_runs()
                    self.logger.info(
                        "📊 Recorded global run %s/%s before processing PRs",
                        current_runs,
                        self.safety_manager.global_limit,
                    )

                if fix_comment:
                    comment_result = self._process_pr_fix_comment(
                        repo_full_name,
                        pr_number,
                        pr,
                        agent_cli=agent_cli,
                        model=model,
                    )
                elif fixpr:
                    comment_result = self._process_pr_fixpr(
                        repo_full_name,
                        pr_number,
                        pr,
                        agent_cli=agent_cli,
                        model=model,
                    )
                else:
                    # Post codex instruction comment directly (comment-only approach)
                    comment_result = self.post_codex_instruction_simple(repo_full_name, pr_number, pr)

                # Treat "skipped" as a neutral outcome: do not count it as failure,
                # and avoid recording an unbounded stream of skipped attempts.
                success = comment_result in {"posted", "skipped"}
                if comment_result != "skipped":
                    result = "success" if comment_result == "posted" else "failure"
                    self.safety_manager.record_pr_attempt(
                        pr_number,
                        result,
                        repo=repo_full_name,
                        branch=branch_name,
                    )
                    attempt_recorded = True

                if success:
                    # Only count as processed when we actually posted; skips should not inflate stats.
                    if comment_result == "posted":
                        actionable_processed += 1
                    self.logger.info(
                        "✅ Successfully processed PR %s #%s (result=%s)",
                        repo_full_name,
                        pr_number,
                        comment_result,
                    )
                else:
                    self.logger.error(
                        "❌ Failed to process PR %s #%s (result=%s)",
                        repo_full_name,
                        pr_number,
                        comment_result,
                    )
            except Exception as e:
                self.logger.error(f"❌ Exception processing PR {repo_full_name} #{pr_number}: {e}")
                self.logger.debug("Traceback: %s", traceback.format_exc())
                # Record failure for safety manager
                self.safety_manager.record_pr_attempt(pr_number, "failure", repo=repo_full_name, branch=branch_name)
                attempt_recorded = True
            finally:
                # Always release the processing slot if record_pr_attempt didn't do it
                if not attempt_recorded:
                    self.safety_manager.release_pr_slot(pr_number, repo=repo_full_name, branch=branch_name)

        self.logger.info(f"🏁 Monitoring cycle complete: {actionable_processed} actionable PRs processed, {skipped_count} skipped")


def check_chrome_cdp_accessible(port=9222, host="127.0.0.1", timeout=5):
    """
    Validate that Chrome DevTools Protocol is accessible.

    Args:
        port: CDP port (default 9222)
        host: CDP host (default 127.0.0.1)
        timeout: Connection timeout in seconds

    Returns:
        tuple: (bool, str) - (success, message)
    """
    url_host = _format_cdp_host_for_url(host)
    url = f"http://{url_host}:{port}/json/version"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            browser_version = data.get("Browser", "Unknown")
            return True, f"✅ Chrome CDP accessible (version: {browser_version})"
    except urllib.error.URLError as e:
        return False, f"❌ Chrome CDP not accessible at {host}:{port} - {e.reason}"
    except Exception as e:
        return False, f"❌ Failed to connect to Chrome CDP: {e}"


def _parse_bool_env(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    return raw.lower() not in {"0", "false", "no", "off"}


def _validate_cdp_host(raw_host: str) -> str:
    allowed_hosts = {"127.0.0.1", "localhost", "::1"}
    host = (raw_host or "").strip()
    if host in allowed_hosts:
        return host

    print(
        f"WARNING: Ignoring unsafe CODEX_CDP_HOST value {host!r}; "
        "only localhost/127.0.0.1/::1 are allowed. Falling back to 127.0.0.1.",
        file=sys.stderr,
    )
    return "127.0.0.1"


def _format_cdp_host_for_url(host: str) -> str:
    if ":" in host and not (host.startswith("[") and host.endswith("]")):
        return f"[{host}]"
    return host


def _resolve_cdp_host_port() -> tuple[str, int]:
    raw_host = os.environ.get("CODEX_CDP_HOST", "127.0.0.1")
    host = _validate_cdp_host(raw_host)
    port_raw = os.environ.get("CODEX_CDP_PORT", "9222")
    try:
        port = int(port_raw)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port {port} out of range")
    except ValueError:
        port = 9222
    return host, port


def _detect_chrome_binary() -> str | None:
    if sys.platform == "win32":
        win_candidates = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files"))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
            / "Google/Chrome/Application/chrome.exe",
        ]
        for candidate in win_candidates:
            if candidate.exists():
                return str(candidate)

    if sys.platform == "darwin":
        mac_candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
        for candidate in mac_candidates:
            if Path(candidate).exists():
                return candidate

    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(command)
        if found:
            return found
    return None


def _start_chrome_debug(port: int, user_data_dir: str) -> tuple[bool, str]:
    start_script = os.environ.get("CODEX_CDP_START_SCRIPT")
    if start_script:
        try:
            cmd = shlex.split(start_script)
        except ValueError as exc:
            return False, f"❌ Invalid CODEX_CDP_START_SCRIPT value ({start_script}): {exc}"
        if not cmd:
            return False, "❌ CODEX_CDP_START_SCRIPT is set but empty after parsing"

        script_path = Path(cmd[0]).expanduser()
        if not script_path.is_file():
            return False, f"❌ CODEX_CDP_START_SCRIPT target does not exist or is not a file: {script_path}"
        try:
            script_path_resolved = script_path.resolve()
        except OSError as exc:
            return False, f"❌ Failed to resolve CODEX_CDP_START_SCRIPT path ({script_path}): {exc}"

        cmd[0] = str(script_path_resolved)
        cmd.append(str(port))
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True, f"🚀 Started Chrome via script {script_path_resolved} on port {port}"
        except Exception as exc:
            return False, f"❌ Failed to run CODEX_CDP_START_SCRIPT ({script_path_resolved}): {exc}"

    chrome_path = _detect_chrome_binary()
    if not chrome_path:
        return False, "❌ Could not find Chrome or Chromium binary"

    resolved_user_data_dir = Path(user_data_dir).expanduser()
    if not resolved_user_data_dir.is_absolute():
        resolved_user_data_dir = (Path.home() / resolved_user_data_dir).resolve()
    else:
        resolved_user_data_dir = resolved_user_data_dir.resolve()
    home_dir = Path.home().resolve()
    try:
        resolved_user_data_dir.relative_to(home_dir)
    except ValueError:
        return False, (
            "❌ CODEX_CDP_USER_DATA_DIR must reside under your home directory; "
            f"got {resolved_user_data_dir}"
        )
    resolved_user_data_dir.mkdir(parents=True, exist_ok=True)
    command = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={resolved_user_data_dir}",
        "--window-size=1920,1080",
        "https://chatgpt.com/",
    ]
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True, f"🚀 Started Chrome with CDP on port {port}"
    except Exception as exc:
        return False, f"❌ Failed to start Chrome with CDP: {exc}"


def ensure_chrome_cdp_accessible(timeout: int | None = None) -> tuple[bool, str]:
    host, port = _resolve_cdp_host_port()
    if timeout is None:
        timeout_raw = os.environ.get("CODEX_CDP_START_TIMEOUT", "20")
        try:
            timeout = int(timeout_raw)
        except ValueError:
            timeout = 20
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = 20
    if timeout <= 0:
        timeout = 20
    ok, message = check_chrome_cdp_accessible(port=port, host=host)
    if ok:
        return True, message

    auto_start = _parse_bool_env("CODEX_CDP_AUTO_START", default=True)
    if not auto_start:
        return False, message

    user_data_dir = os.environ.get("CODEX_CDP_USER_DATA_DIR", str(Path.home() / ".chrome-automation-profile"))
    started, start_message = _start_chrome_debug(port, user_data_dir)
    if not started:
        return False, start_message

    deadline = time.time() + timeout
    last_message = message
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        per_check_timeout = min(1.0, remaining)
        ok, last_message = check_chrome_cdp_accessible(
            port=port,
            host=host,
            timeout=per_check_timeout,
        )
        if ok:
            return True, f"{start_message}\n{last_message}"
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        time.sleep(min(1.0, remaining))

    return False, f"{start_message}\n❌ Chrome CDP still not reachable after {timeout}s ({last_message})"


def main():
    """CLI interface for jleechanorg PR monitor"""

    parser = argparse.ArgumentParser(description="jleechanorg PR Monitor")
    parser.add_argument(
        "--no-act",
        action="store_true",
        help="Do not post comments or dispatch agents (useful for evidence/testing).",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Discover PRs but do not process them")
    parser.add_argument("--fixpr", action="store_true",
                        help="Run /fixpr-only orchestrated flow for conflicts/failing checks (skips drafts)")
    parser.add_argument("--fix-comment", action="store_true",
                        help="Run fix-comment orchestration flow to resolve PR review comments")
    parser.add_argument("--fix-comment-watch", action="store_true",
                        help="Watch a PR for automation commits and post review request when detected")
    parser.add_argument("--cutoff-hours", type=int, default=24,
                        help="Look-back window in hours for PR updates (default: 24)")
    parser.add_argument("--single-repo",
                        help="Process only specific repository")
    parser.add_argument("--max-prs", type=int, default=5,
                        help="Maximum PRs to process per cycle")
    parser.add_argument("--target-pr", type=int,
                        help="Process specific PR number")
    parser.add_argument("--target-repo",
                        help="Repository for target PR (required with --target-pr)")
    parser.add_argument(
        "--fixpr-agent",
        type=_parse_fixpr_agent_chain,
        default="claude",
        help="AI CLI (or comma-separated chain) for --fixpr mode (default: claude). Example: gemini,codex",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use for agent CLI. Examples: sonnet/opus/haiku (Claude), gemini-3-pro-preview/gemini-3-auto (Gemini), composer-1 (Cursor). If not specified, CLI-specific defaults are used.",
    )
    parser.add_argument("--list-eligible", action="store_true",
                        help="Dry-run listing of PRs eligible for fixpr (conflicts/failing checks)")
    parser.add_argument("--codex-update", action="store_true",
                        help="Run Codex automation to update tasks via browser automation (use --codex-task-limit; default: 50)")
    parser.add_argument(
        "--codex-task-limit",
        type=_positive_int_arg,
        default=50,
        help="Task limit for --codex-update (default: 50, max: 200).",
    )

    # Safety limits (params; no environment variables).
    parser.add_argument("--pr-limit", type=_positive_int_arg, default=None, help="Max failed attempts per PR (default: 10).")
    parser.add_argument("--global-limit", type=_positive_int_arg, default=None, help="Max global runs per day (default: 50).")
    parser.add_argument("--approval-hours", type=_positive_int_arg, default=None, help="Manual approval validity in hours (default: 24).")
    parser.add_argument("--subprocess-timeout", type=_positive_int_arg, default=None, help="Default subprocess timeout seconds (default: 300).")
    parser.add_argument("--pr-automation-limit", type=_positive_int_arg, default=None, help="Max PR automation comments per PR (default: 10).")
    parser.add_argument("--fix-comment-limit", type=_positive_int_arg, default=None, help="Max fix-comment comments per PR (default: 10).")
    parser.add_argument("--fixpr-limit", type=_positive_int_arg, default=None, help="Max fixpr comments per PR (default: 10).")
    parser.add_argument("--automation-user", help="Override automation username for marker validation")

    args = parser.parse_args()

    try:
        args.model = _normalize_model(args.model)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    # Validate target PR arguments
    if args.target_pr and not args.target_repo:
        parser.error("--target-repo is required when using --target-pr")
    if args.target_repo and not args.target_pr:
        parser.error("--target-pr is required when using --target-repo")
    if args.fixpr and args.fix_comment:
        parser.error("--fixpr and --fix-comment are mutually exclusive")
    if args.fix_comment_watch and not (args.target_pr and args.target_repo):
        parser.error("--fix-comment-watch requires --target-pr and --target-repo")

    safety_limits: dict[str, int] = {}
    if args.pr_limit is not None:
        safety_limits["pr_limit"] = args.pr_limit
    if args.global_limit is not None:
        safety_limits["global_limit"] = args.global_limit
    if args.approval_hours is not None:
        safety_limits["approval_hours"] = args.approval_hours
    if args.subprocess_timeout is not None:
        safety_limits["subprocess_timeout"] = args.subprocess_timeout
    if args.pr_automation_limit is not None:
        safety_limits["pr_automation_limit"] = args.pr_automation_limit
    if args.fix_comment_limit is not None:
        safety_limits["fix_comment_limit"] = args.fix_comment_limit
    if args.fixpr_limit is not None:
        safety_limits["fixpr_limit"] = args.fixpr_limit

    monitor = JleechanorgPRMonitor(
        safety_limits=safety_limits or None,
        no_act=args.no_act,
        automation_username=getattr(args, "automation_user", None)
    )

    if args.fix_comment_watch:
        success = monitor.run_fix_comment_review_watcher(
            args.target_pr,
            args.target_repo,
            agent_cli=args.fixpr_agent,
        )
        sys.exit(0 if success else 1)

    if args.codex_update:
        if args.no_act:
            print("🧪 --no-act enabled: skipping codex-update run")
            sys.exit(0)

        task_limit = min(args.codex_task_limit, 200)

        print(f"🤖 Running Codex automation (first {task_limit} tasks)...")

        # Validate Chrome CDP is accessible before running (auto-starts if needed)
        cdp_ok, cdp_msg = ensure_chrome_cdp_accessible()
        print(cdp_msg)
        if not cdp_ok:
            print("\n⚠️ Skipping Codex automation (Chrome CDP unavailable).")
            print("💡 TIP: Start Chrome with CDP enabled first:")
            print("   ./automation/jleechanorg_pr_automation/openai_automation/start_chrome_debug.sh")
            print("   Or set CODEX_CDP_START_SCRIPT to a custom launcher path.")
            sys.exit(0)

        try:
            host, port = _resolve_cdp_host_port()
            # Call the codex automation module with limit
            # Use -m to run as module (works with installed package)
            # Requires Chrome with CDP enabled on port 9222
            timeout_seconds = max(300, int(task_limit * 12))  # ~12s/task, min 5 minutes
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "jleechanorg_pr_automation.openai_automation.codex_github_mentions",
                    "--use-existing-browser",
                    "--cdp-host",
                    host,
                    "--cdp-port",
                    str(port),
                    "--limit",
                    str(task_limit),
                ],
                check=False, capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        except subprocess.TimeoutExpired:
            print(f"❌ Codex automation timed out after {timeout_seconds // 60} minutes")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to run Codex automation: {e}")
            sys.exit(1)

    if args.fixpr:
        if args.target_pr and args.target_repo:
            print(f"🎯 Processing target PR (fixpr): {args.target_repo} #{args.target_pr}")
            success = monitor.process_single_pr_by_number(
                args.target_pr,
                args.target_repo,
                fixpr=True,
                agent_cli=args.fixpr_agent,
                model=args.model,
            )
            sys.exit(0 if success else 1)

        monitor.run_monitoring_cycle(
            single_repo=args.single_repo,
            max_prs=args.max_prs,
            cutoff_hours=args.cutoff_hours,
            fixpr=True,
            agent_cli=args.fixpr_agent,
            model=args.model,
        )
        return

    if args.fix_comment:
        # Handle target PR processing
        if args.target_pr and args.target_repo:
            print(f"🎯 Processing target PR (fix-comment): {args.target_repo} #{args.target_pr}")
            success = monitor.process_single_pr_by_number(
                args.target_pr,
                args.target_repo,
                fix_comment=True,
                agent_cli=args.fixpr_agent,
                model=args.model,
            )
            sys.exit(0 if success else 1)

        if args.dry_run:
            print("🔍 DRY RUN: Discovering PRs only")
            prs = monitor.discover_open_prs(cutoff_hours=args.cutoff_hours)

            if args.single_repo:
                prs = [pr for pr in prs if pr["repository"] == args.single_repo]

            print(f"📋 Found {len(prs)} open PRs:")
            for pr in prs[:args.max_prs]:
                print(f"  • {pr['repository']} PR #{pr['number']}: {pr.get('title', 'unknown')}")
            return

        monitor.run_monitoring_cycle(
            single_repo=args.single_repo,
            max_prs=args.max_prs,
            cutoff_hours=args.cutoff_hours,
            fix_comment=True,
            agent_cli=args.fixpr_agent,
            model=args.model,
        )
        return

    # Handle target PR processing
    if args.target_pr and args.target_repo:
        print(f"🎯 Processing target PR: {args.target_repo} #{args.target_pr}")
        success = monitor.process_single_pr_by_number(args.target_pr, args.target_repo)
        sys.exit(0 if success else 1)

    if args.dry_run:
        print("🔍 DRY RUN: Discovering PRs only")
        prs = monitor.discover_open_prs(cutoff_hours=args.cutoff_hours)

        if args.single_repo:
            prs = [pr for pr in prs if pr["repository"] == args.single_repo]

        print(f"📋 Found {len(prs)} open PRs:")
        for pr in prs[:args.max_prs]:
            print(f"  • {pr['repository']} PR #{pr['number']}: {pr.get('title', 'unknown')}")

        if args.list_eligible:
            print("\n🔎 Eligible for fixpr (conflicts/failing checks):")
            monitor.list_actionable_prs(
                cutoff_hours=args.cutoff_hours,
                max_prs=args.max_prs,
                single_repo=args.single_repo,
            )
    elif args.list_eligible:
        monitor.list_actionable_prs(
            cutoff_hours=args.cutoff_hours,
            max_prs=args.max_prs,
            single_repo=args.single_repo,
        )
    else:
        monitor.run_monitoring_cycle(
            cutoff_hours=args.cutoff_hours,
            model=args.model,
        )


if __name__ == "__main__":
    main()
