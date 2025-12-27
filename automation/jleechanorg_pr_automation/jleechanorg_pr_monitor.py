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
import subprocess
import sys
import shutil
import time
import shlex
import traceback
import urllib.request
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from .orchestrated_pr_runner import has_failing_checks, run_fixpr_batch

from .automation_safety_manager import AutomationSafetyManager
from .automation_utils import AutomationUtils
from .codex_config import (
    CODEX_COMMIT_MARKER_PREFIX as SHARED_MARKER_PREFIX,
)
from .codex_config import (
    CODEX_COMMIT_MARKER_SUFFIX as SHARED_MARKER_SUFFIX,
)
from .codex_config import (
    build_comment_intro,
)
from .utils import json_manager, setup_logging
from orchestration.task_dispatcher import CLI_PROFILES


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


class JleechanorgPRMonitor:
    """Cross-organization PR monitoring with Codex automation comments"""

    @staticmethod
    def _redact_email(email: Optional[str]) -> Optional[str]:
        """Redact email for logging while preserving domain for debugging"""
        if not email or "@" not in email:
            return email
        user, domain = email.rsplit("@", 1)
        if len(user) <= 2:
            return f"***@{domain}"
        return f"{user[:2]}***@{domain}"

    CODEX_COMMIT_MARKER_PREFIX = SHARED_MARKER_PREFIX
    CODEX_COMMIT_MARKER_SUFFIX = SHARED_MARKER_SUFFIX
    CODEX_COMMIT_MESSAGE_MARKER = "[codex-automation-commit]"
    CODEX_BOT_IDENTIFIER = "codex"
    # GitHub short SHAs display with a minimum of 7 characters, while full SHAs are 40 characters.
    CODEX_COMMIT_SHA_LENGTH_RANGE: Tuple[int, int] = (7, 40)
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
        r"\[(?:" + "|".join(_codex_actor_keywords) + r")-automation-commit\]"
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
        actor: Optional[Dict],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not isinstance(actor, dict):
            return (None, None, None)

        user_info = actor.get("user")
        login = user_info.get("login") if isinstance(user_info, dict) else None
        email = actor.get("email")
        name = actor.get("name")
        return (login, email, name)

    def __init__(self):
        self.logger = setup_logging(__name__)

        self.assistant_mentions = os.environ.get(
            "AI_ASSISTANT_MENTIONS",
            "@codex @coderabbitai @copilot @cursor",
        )

        self.wrapper_managed = os.environ.get("AUTOMATION_SAFETY_WRAPPER") == "1"

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

        self.safety_manager = AutomationSafetyManager(safety_data_dir)

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

    def _load_branch_history(self, repo_name: str, branch_name: str) -> Dict[str, str]:
        """Load processed PRs for a specific repo/branch"""
        history_file = self._get_history_file(repo_name, branch_name)
        return json_manager.read_json(str(history_file), {})

    def _save_branch_history(self, repo_name: str, branch_name: str, history: Dict[str, str]) -> None:
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

    def is_pr_actionable(self, pr_data: Dict) -> bool:
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
            if self._has_new_bot_comments_since_codex(comments):
                self.logger.info(
                    f"🤖 PR {repo_name}#{pr_number} has new bot comments since last processing - marking actionable"
                )
                return True
            return False

        # Open non-draft PRs with new commits are actionable
        return True

    def filter_eligible_prs(self, pr_list: List[Dict]) -> List[Dict]:
        """Filter list to return only actionable PRs"""
        eligible = []
        for pr in pr_list:
            if self.is_pr_actionable(pr):
                eligible.append(pr)
        return eligible

    def process_actionable_prs(self, pr_list: List[Dict], target_count: int) -> int:
        """Process up to target_count actionable PRs, returning count processed"""
        processed = 0
        for pr in pr_list:
            if processed >= target_count:
                break
            if self.is_pr_actionable(pr):
                # Simulate processing (for testing)
                processed += 1
        return processed

    def filter_and_process_prs(self, pr_list: List[Dict], target_actionable_count: int) -> int:
        """Filter PRs to actionable ones and process up to target count"""
        eligible_prs = self.filter_eligible_prs(pr_list)
        return self.process_actionable_prs(eligible_prs, target_actionable_count)

    def find_eligible_prs(self, limit: int = 10) -> List[Dict]:
        """Find eligible PRs from live GitHub data"""
        all_prs = self.discover_open_prs()
        eligible_prs = self.filter_eligible_prs(all_prs)
        return eligible_prs[:limit]

    def list_actionable_prs(self, cutoff_hours: int = 24, max_prs: int = 20, mode: str = "fixpr", single_repo: Optional[str] = None) -> List[Dict]:
        """
        Return PRs that would be processed for fixpr (merge conflicts or failing checks).
        """
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
            if pr.get("mergeable") == "CONFLICTING":
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
            print(f"  • {pr.get('repository')} PR #{pr.get('number')}: {pr.get('title')} (mergeable={pr.get('mergeable')})")
        return actionable

    def run_monitoring_cycle_with_actionable_count(self, target_actionable_count: int = 20) -> Dict:
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

    def _process_pr_comment(self, repo_name: str, pr_number: int, pr_data: Dict) -> bool:
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

    def discover_open_prs(self) -> List[Dict]:
        """Discover open PRs updated in the last 24 hours across the organization."""

        self.logger.info(f"🔍 Discovering open PRs in {self.organization} organization (last 24 hours)")

        now = datetime.utcnow()
        one_day_ago = now - timedelta(hours=24)
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
        cursor: Optional[str] = None
        recent_prs: List[Dict] = []

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
                    updated_time = datetime.fromisoformat(updated_str.replace("Z", "+00:00")).replace(tzinfo=None)
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

        recent_prs.sort(key=lambda x: x.get("updated_datetime", datetime.min), reverse=True)

        repo_counter = Counter(pr.get("repository") for pr in recent_prs if pr.get("repository"))
        for repo_name, count in repo_counter.items():
            self.logger.info("📋 %s: %s recent PRs", repo_name, count)

        self.logger.info("🎯 Total recent PRs discovered (last 24 hours): %s", len(recent_prs))

        self.logger.info("📊 Most recently updated PRs:")
        for i, pr in enumerate(recent_prs[:5], 1):
            updated_str = pr["updated_datetime"].strftime("%Y-%m-%d %H:%M")
            self.logger.info("  %s. %s #%s - %s", i, pr["repositoryFullName"], pr["number"], updated_str)

        return recent_prs


    def _find_local_repository(self, repo_name: str) -> Optional[Path]:
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

    def post_codex_instruction_simple(self, repository: str, pr_number: int, pr_data: Dict) -> str:
        """Post codex instruction comment to PR"""
        repo_full = self._normalize_repository_name(repository)
        self.logger.info(f"💬 Requesting Codex support for {repo_full} PR #{pr_number}")

        # Extract repo name and branch from PR data
        repo_name = repo_full.split("/")[-1]
        branch_name = pr_data.get("headRefName", "unknown")

        # Get current PR state including commit SHA
        head_sha, comments = self._get_pr_comment_state(repo_full, pr_number)
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

            result = AutomationUtils.execute_subprocess_with_timeout(comment_cmd, timeout=30)

            self.logger.info(f"✅ Posted Codex instruction comment on PR #{pr_number} ({repo_full})")

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

            pr_status = json.loads(result.stdout)
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
        pr_data: Dict,
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

    def _get_pr_comment_state(self, repo_full_name: str, pr_number: int) -> Tuple[Optional[str], List[Dict]]:
        """Fetch PR comment data needed for Codex comment gating"""
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
                timeout=30
            )
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
        except json.JSONDecodeError as e:
            self.logger.warning(
                f"⚠️ Failed to parse PR comment state for PR #{pr_number}: {e}"
            )

        return None, []

    def _get_head_commit_details(
        self,
        repo_full_name: str,
        pr_number: int,
        expected_sha: Optional[str] = None,
    ) -> Optional[Dict[str, Optional[str]]]:
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

    def _extract_commit_marker(self, comment_body: str) -> Optional[str]:
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

    def _has_codex_comment_for_commit(self, comments: List[Dict], head_sha: str) -> bool:
        """Determine if Codex instruction already exists for the latest commit"""
        if not head_sha:
            return False

        for comment in comments:
            body = comment.get("body", "")
            marker_sha = self._extract_commit_marker(body)
            if marker_sha and marker_sha == head_sha:
                return True

        return False

    def _is_head_commit_from_codex(
        self, commit_details: Optional[Dict[str, Optional[str]]]
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

    def _is_github_bot_comment(self, comment: Dict) -> bool:
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

    def _get_last_codex_automation_comment_time(self, comments: List[Dict]) -> Optional[str]:
        """Find the timestamp of the last Codex automation comment (with commit marker)."""
        last_time = None

        for comment in comments:
            body = comment.get("body", "")
            # Check if this is a Codex automation comment (has our marker)
            if self.CODEX_COMMIT_MARKER_PREFIX in body:
                created_at = comment.get("createdAt") or comment.get("updatedAt")
                if created_at and (last_time is None or created_at > last_time):
                    last_time = created_at

        return last_time

    def _has_new_bot_comments_since_codex(self, comments: List[Dict]) -> bool:
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

    def _get_comment_author_login(self, comment: Dict) -> str:
        """Return normalized author login for a comment."""
        author = comment.get("author") or comment.get("user") or {}
        if isinstance(author, dict):
            return (author.get("login") or author.get("name") or "").strip()
        if isinstance(author, str):
            return author.strip()
        return ""

    def _extract_codex_summary_commit(self, comment_body: str) -> Optional[str]:
        """Extract commit SHA referenced in Codex summary comment."""
        if not comment_body:
            return None

        for pattern in self.CODEX_SUMMARY_COMMIT_PATTERNS:
            match = pattern.search(comment_body)
            if match:
                return match.group(1).lower()

        return None

    def _has_pending_codex_commit(self, comments: List[Dict], head_sha: str) -> bool:
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

    def process_single_pr_by_number(self, pr_number: int, repository: str) -> bool:
        """Process a specific PR by number and repository"""
        repo_full = self._normalize_repository_name(repository)
        self.logger.info(f"🎯 Processing target PR: {repo_full} #{pr_number}")

        # Check global automation limits
        if not self.safety_manager.can_start_global_run():
            self.logger.warning("🚫 Global automation limit reached - cannot process target PR")
            return False

        try:
            # Check safety limits for this specific PR first
            if not self.safety_manager.try_process_pr(pr_number, repo=repo_full):
                self.logger.warning(f"🚫 Safety limits exceeded for PR {repo_full} #{pr_number}")
                return False

            # Only record global run AFTER confirming we can process the PR
            if not self.wrapper_managed:
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
                    ["gh", "pr", "view", str(pr_number), "--repo", repo_full, "--json", "title,headRefName,baseRefName,url,author"],
                    timeout=30
                )
                pr_data = json.loads(result.stdout)

                self.logger.info(f"📝 Found PR: {pr_data['title']}")

                # Post codex instruction comment
                comment_result = self.post_codex_instruction_simple(repo_full, pr_number, pr_data)
                success = comment_result == "posted"

                # Record PR processing attempt with result
                result = "success" if success else "failure"
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

    def run_monitoring_cycle(self, single_repo=None, max_prs=10):
        """Run a complete monitoring cycle with actionable PR counting"""
        self.logger.info("🚀 Starting jleechanorg PR monitoring cycle")

        if not self.safety_manager.can_start_global_run():
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
            open_prs = self.discover_open_prs()
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

            # Check if this PR is actionable (skip if not)
            if not self.is_pr_actionable(pr):
                skipped_count += 1
                continue

            branch_name = pr.get("headRefName", "unknown")

            if not self.safety_manager.try_process_pr(pr_number, repo=repo_full_name, branch=branch_name):
                self.logger.info(
                    f"🚫 Safety limits exceeded for PR {repo_full_name} #{pr_number}; skipping"
                )
                skipped_count += 1
                continue

            self.logger.info(f"🎯 Processing PR: {repo_full_name} #{pr_number} - {pr['title']}")

            attempt_recorded = False
            try:
                if not global_run_recorded:
                    self.safety_manager.record_global_run()
                    global_run_recorded = True
                    current_runs = self.safety_manager.get_global_runs()
                    self.logger.info(
                        "📊 Recorded global run %s/%s before processing PRs",
                        current_runs,
                        self.safety_manager.global_limit,
                    )

                # Post codex instruction comment directly (comment-only approach)
                comment_result = self.post_codex_instruction_simple(repo_full_name, pr_number, pr)

                # Treat "skipped" (already handled/guarded) the same as a success so we don't
                # artificially accumulate failure counts or noisy error logs.
                success = comment_result in {"posted", "skipped"}

                result = "success" if success else "failure"
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


def _resolve_cdp_host_port() -> Tuple[str, int]:
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


def _detect_chrome_binary() -> Optional[str]:
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


def _start_chrome_debug(port: int, user_data_dir: str) -> Tuple[bool, str]:
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


def ensure_chrome_cdp_accessible(timeout: Optional[int] = None) -> Tuple[bool, str]:
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
    parser.add_argument("--dry-run", action="store_true",
                        help="Discover PRs but do not process them")
    parser.add_argument("--fixpr", action="store_true",
                        help="Run /fixpr-only orchestrated flow for conflicts/failing checks (skips drafts)")
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
    parser.add_argument("--list-eligible", action="store_true",
                        help="Dry-run listing of PRs eligible for fixpr (conflicts/failing checks)")
    parser.add_argument("--codex-update", action="store_true",
                        help="Run Codex automation to update first 200 tasks via browser automation")

    args = parser.parse_args()

    # Validate target PR arguments
    if args.target_pr and not args.target_repo:
        parser.error("--target-repo is required when using --target-pr")
    if args.target_repo and not args.target_pr:
        parser.error("--target-pr is required when using --target-repo")

    monitor = JleechanorgPRMonitor()

    if args.codex_update:
        print("🤖 Running Codex automation (first 200 tasks)...")

        # Validate Chrome CDP is accessible before running (auto-starts if needed)
        cdp_ok, cdp_msg = ensure_chrome_cdp_accessible()
        print(cdp_msg)
        if not cdp_ok:
            print("\n💡 TIP: Start Chrome with CDP enabled first:")
            print("   ./automation/jleechanorg_pr_automation/openai_automation/start_chrome_debug.sh")
            print("   Or set CODEX_CDP_START_SCRIPT to a custom launcher path.")
            sys.exit(1)

        try:
            host, port = _resolve_cdp_host_port()
            # Call the codex automation module with limit
            # Use -m to run as module (works with installed package)
            # Requires Chrome with CDP enabled on port 9222
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
                    "200",
                ],
                capture_output=True,
                text=True,
                timeout=2400  # 40 minute timeout (scaled for 200 tasks)
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        except subprocess.TimeoutExpired:
            print("❌ Codex automation timed out after 40 minutes")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to run Codex automation: {e}")
            sys.exit(1)

    if args.fixpr:
        run_fixpr_batch(args.cutoff_hours, args.max_prs, agent_cli=args.fixpr_agent)
        return

    # Handle target PR processing
    if args.target_pr and args.target_repo:
        print(f"🎯 Processing target PR: {args.target_repo} #{args.target_pr}")
        success = monitor.process_single_pr_by_number(args.target_pr, args.target_repo)
        sys.exit(0 if success else 1)

    if args.dry_run:
        print("🔍 DRY RUN: Discovering PRs only")
        prs = monitor.discover_open_prs()

        if args.single_repo:
            prs = [pr for pr in prs if pr["repository"] == args.single_repo]

        print(f"📋 Found {len(prs)} open PRs:")
        for pr in prs[:args.max_prs]:
            print(f"  • {pr['repository']} PR #{pr['number']}: {pr['title']}")

        if args.list_eligible:
            print("\n🔎 Eligible for fixpr (conflicts/failing checks):")
            monitor.list_actionable_prs(max_prs=args.max_prs, single_repo=args.single_repo)
    else:
        if args.list_eligible:
            monitor.list_actionable_prs(max_prs=args.max_prs, single_repo=args.single_repo)
        else:
            monitor.run_monitoring_cycle(single_repo=args.single_repo, max_prs=args.max_prs)


if __name__ == "__main__":
    main()
