#!/usr/bin/env python3
"""
jleechanorg PR Monitor - Cross-Organization Automation

Discovers and processes ALL open PRs across jleechanorg organization
by posting @codex automation comments with safety limits integration.
"""

import argparse
import os
import sys
import json
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from automation_safety_manager import AutomationSafetyManager


class JleechanorgPRMonitor:
    """Cross-organization PR monitoring with @codex automation comments"""

    CODEX_COMMENT_ENV_VAR = "CODEX_COMMENT"
    ASSISTANT_HANDLE_ENV_VAR = "ASSISTANT_HANDLE"
    DEFAULT_ASSISTANT_HANDLE = "codex"
    DEFAULT_CODEX_COMMENT_TEMPLATE = (
        "@{assistant_handle} use your judgment to fix comments from everyone or explain why it "
        "should not be fixed. Follow binary response protocol every comment needs done or not "
        "done classification explicitly with an explanation. Fix any failing tests and resolve "
        "merge conflicts. Push any commits needed to remote so the PR is updated."
    )
    CODEX_COMMIT_MARKER_PREFIX = "<!-- codex-automation-commit:"
    CODEX_COMMIT_MARKER_SUFFIX = "-->"

    def __init__(self):
        self.logger = self._setup_logging()

        assistant_handle = os.environ.get(
            self.ASSISTANT_HANDLE_ENV_VAR, self.DEFAULT_ASSISTANT_HANDLE
        )
        default_comment = self.DEFAULT_CODEX_COMMENT_TEMPLATE.format(
            assistant_handle=assistant_handle
        )

        # Allow overriding the Codex instruction from the environment
        self.CODEX_COMMENT_TEXT = os.environ.get(
            self.CODEX_COMMENT_ENV_VAR,
            default_comment,
        )

        # Processing history in /tmp organized by repo/branch
        self.history_base_dir = Path("/tmp/pr_automation_history")
        self.history_base_dir.mkdir(parents=True, exist_ok=True)

        # Organization settings
        self.organization = "jleechanorg"
        self.base_project_dir = Path.home() / "projects"

        safety_data_dir = os.environ.get('AUTOMATION_SAFETY_DATA_DIR')
        if not safety_data_dir:
            default_dir = Path.home() / "Library" / "Application Support" / "worldarchitect-automation"
            default_dir.mkdir(parents=True, exist_ok=True)
            safety_data_dir = str(default_dir)

        self.safety_manager = AutomationSafetyManager(safety_data_dir)

        self.logger.info(f"🏢 Initialized jleechanorg PR monitor")
        self.logger.info(f"📁 History storage: {self.history_base_dir}")
        self.logger.info(f"💬 Comment-only automation mode")
    def _get_history_file(self, repo_name: str, branch_name: str) -> Path:
        """Get history file path for specific repo/branch"""
        repo_dir = self.history_base_dir / repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Replace slashes in branch names to avoid creating nested directories
        safe_branch_name = branch_name.replace('/', '_')
        return repo_dir / f"{safe_branch_name}.json"

    def _load_branch_history(self, repo_name: str, branch_name: str) -> Dict[str, str]:
        """Load processed PRs for a specific repo/branch"""
        history_file = self._get_history_file(repo_name, branch_name)
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"⚠️ Error loading history for {repo_name}/{branch_name}: {e}")
        return {}

    def _save_branch_history(self, repo_name: str, branch_name: str, history: Dict[str, str]) -> None:
        """Save processed PRs for a specific repo/branch"""
        history_file = self._get_history_file(repo_name, branch_name)
        try:
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except OSError as e:
            self.logger.error(f"❌ Error saving history for {repo_name}/{branch_name}: {e}")

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
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for PR monitor"""
        log_dir = Path.home() / "Library" / "Logs" / "worldarchitect-automation"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "jleechanorg_pr_monitor.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def discover_open_prs(self) -> List[Dict]:
        """Discover open PRs from last 24 hours across jleechanorg organization, ordered by most recent updates"""
        self.logger.info(f"🔍 Discovering open PRs in {self.organization} organization (last 24 hours)")

        from datetime import datetime, timedelta

        # Get current time and 24 hours ago
        now = datetime.now()
        one_day_ago = now - timedelta(hours=24)
        self.logger.info(f"📅 Filtering PRs updated since: {one_day_ago.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Get all repositories in the organization
            repos_cmd = ["gh", "repo", "list", self.organization, "--limit", "100", "--json", "name,owner"]
            repos_result = subprocess.run(repos_cmd, capture_output=True, text=True, check=True, timeout=30, shell=False)
            repositories = json.loads(repos_result.stdout)

            self.logger.info(f"📚 Found {len(repositories)} repositories")

            recent_prs = []

            for repo in repositories:
                repo_name = repo["name"]
                repo_full_name = f"{self.organization}/{repo_name}"

                try:
                    # Get open PRs for this repository
                    prs_cmd = [
                        "gh", "pr", "list",
                        "--repo", repo_full_name,
                        "--state", "open",
                        "--json", "number,title,headRefName,headRepository,baseRefName,updatedAt,url,author"
                    ]

                    prs_result = subprocess.run(prs_cmd, capture_output=True, text=True, check=True, timeout=30, shell=False)
                    prs = json.loads(prs_result.stdout)

                    # Filter PRs updated in last 3 days and add repository context
                    for pr in prs:
                        updated_str = pr.get('updatedAt', '')
                        if updated_str:
                            try:
                                # Parse ISO format: 2025-09-28T07:00:00Z
                                updated_time = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                                updated_time = updated_time.replace(tzinfo=None)  # Remove timezone for comparison

                                if updated_time >= one_day_ago:
                                    pr["repository"] = repo_name
                                    pr["repositoryFullName"] = repo_full_name
                                    pr["updated_datetime"] = updated_time
                                    recent_prs.append(pr)
                            except ValueError:
                                # Skip PRs with invalid date format
                                self.logger.debug(f"⚠️ Invalid date format for PR {pr.get('number')}: {updated_str}")
                                continue

                    recent_prs_count = len([pr for pr in prs if pr.get('updatedAt', '') and
                                          datetime.fromisoformat(pr['updatedAt'].replace('Z', '+00:00')).replace(tzinfo=None) >= one_day_ago])
                    if recent_prs_count > 0:
                        self.logger.info(f"📋 {repo_name}: {recent_prs_count} recent PRs (of {len(prs)} total)")

                except subprocess.CalledProcessError as e:
                    # Skip repositories we don't have access to
                    if "Not Found" in e.stderr or "404" in e.stderr:
                        self.logger.debug(f"⚠️ No access to {repo_full_name}")
                    else:
                        self.logger.warning(f"❌ Error getting PRs for {repo_full_name}: {e.stderr}")

            # Sort by most recently updated first
            recent_prs.sort(key=lambda x: x.get('updated_datetime', datetime.min), reverse=True)

            self.logger.info(f"🎯 Total recent PRs discovered (last 24 hours): {len(recent_prs)}")

            # Log top 5 most recent for visibility
            if recent_prs:
                self.logger.info("📊 Most recently updated PRs:")
                for i, pr in enumerate(recent_prs[:5], 1):
                    updated_str = pr['updated_datetime'].strftime('%Y-%m-%d %H:%M')
                    self.logger.info(f"  {i}. {pr['repositoryFullName']} #{pr['number']} - {updated_str}")

            return recent_prs

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to discover repositories: {e.stderr}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to parse repository data: {e}")
            return []


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

    def post_codex_instruction_simple(self, repository: str, pr_number: int, pr_data: Dict) -> bool:
        """Post codex instruction comment to PR"""
        self.logger.info(f"💬 Requesting Codex support for {repository} PR #{pr_number}")

        # Get current PR state including commit SHA
        head_sha, comments = self._get_pr_comment_state(repository, pr_number)

        if not head_sha:
            self.logger.warning(f"⚠️ Could not get commit SHA for PR #{pr_number}")
            return False

        # Extract repo name and branch from PR data
        repo_name = repository.split('/')[-1]  # Get repo name from full path
        branch_name = pr_data.get('headRefName', 'unknown')

        # Check if we should skip this PR based on commit-based tracking
        if self._should_skip_pr(repo_name, branch_name, pr_number, head_sha):
            return True

        # Build comment body that tells Codex to fix PR comments and failing tests
        comment_body = self._build_codex_comment_body_simple(repository, pr_number, pr_data, head_sha, comments)

        # Post the comment
        try:
            comment_cmd = [
                "gh", "pr", "comment", str(pr_number),
                "--repo", repository,
                "--body", comment_body
            ]

            result = subprocess.run(comment_cmd, capture_output=True, text=True, check=True, timeout=30)

            self.logger.info(f"✅ Posted Codex instruction comment on PR #{pr_number}")

            # Record that we've processed this PR with this commit
            self._record_processed_pr(repo_name, branch_name, pr_number, head_sha)

            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to post comment on PR #{pr_number}: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"💥 Unexpected error posting comment: {e}")
            return False











    def _has_automation_comment_for_commit(self, comments: List[Dict], head_sha: str) -> bool:
        """Check if we already have an automation comment for this specific commit"""
        if not comments or not head_sha:
            return False

        for comment in comments:
            body = comment.get('body', '')
            if '[AI automation]' in body and head_sha[:8] in body:
                self.logger.debug(f"Found existing automation comment for commit {head_sha[:8]}")
                return True

        return False

    def _are_tests_passing(self, repository: str, pr_number: int) -> bool:
        """Check if tests are passing on the PR"""
        try:
            # Get PR status checks
            result = subprocess.run([
                "gh", "pr", "view", str(pr_number),
                "--repo", repository,
                "--json", "statusCheckRollup"
            ], capture_output=True, text=True, check=True, timeout=30)

            pr_status = json.loads(result.stdout)
            status_checks = pr_status.get('statusCheckRollup', [])

            # If no status checks are configured, assume tests are failing
            if not status_checks:
                self.logger.debug(f"⚠️ No status checks configured for PR #{pr_number}, assuming failing")
                return False

            # Check if all status checks are successful
            for check in status_checks:
                if check.get('state') not in ['SUCCESS', 'NEUTRAL']:
                    self.logger.debug(f"❌ Status check failed: {check.get('name')} - {check.get('state')}")
                    return False

            self.logger.debug(f"✅ All {len(status_checks)} status checks passing for PR #{pr_number}")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Could not check test status for PR #{pr_number}: {e}")
            return False  # Assume tests are failing if we can't check

    def _build_codex_comment_body_simple(self, repository: str, pr_number: int, pr_data: Dict, head_sha: str, comments: List[Dict]) -> str:
        """Build comment body that tells Codex to fix PR comments, tests, and merge conflicts"""

        comment_body = f"""@codex [AI automation] Please make the following changes to this PR

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

{self.CODEX_COMMIT_MARKER_PREFIX}{head_sha}{self.CODEX_COMMIT_MARKER_SUFFIX}
"""

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
            result = subprocess.run(
                view_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
                shell=False,
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
            comments.sort(key=lambda c: c.get('createdAt', ''))

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

    def _build_codex_comment_body(self, head_sha: Optional[str]) -> str:
        """Compose Codex instruction comment with commit marker"""
        if head_sha:
            marker = f"{self.CODEX_COMMIT_MARKER_PREFIX}{head_sha}{self.CODEX_COMMIT_MARKER_SUFFIX}"
            return f"{self.CODEX_COMMENT_TEXT}\n\n{marker}"

        # Fallback without marker if we could not determine the commit SHA
        return self.CODEX_COMMENT_TEXT



    def process_single_pr_by_number(self, pr_number: int, repository: str) -> bool:
        """Process a specific PR by number and repository"""
        self.logger.info(f"🎯 Processing target PR: {repository} #{pr_number}")

        # Check global automation limits
        if not self.safety_manager.can_start_global_run():
            self.logger.warning("🚫 Global automation limit reached - cannot process target PR")
            return False

        # Record global run
        self.safety_manager.record_global_run()
        global_run_number = self.safety_manager.get_global_runs()
        max_global_runs = self.safety_manager.global_limit
        self.logger.info(f"📊 Global run #{global_run_number}/{max_global_runs}")

        try:
            # Check safety limits for this specific PR
            pr_key = f"{repository}-{pr_number}"
            if not self.safety_manager.can_process_pr(pr_key):
                self.logger.warning(f"🚫 Safety limits exceeded for PR {repository} #{pr_number}")
                return False

            # Get PR details using gh CLI
            try:
                result = subprocess.run(
                    ["gh", "pr", "view", str(pr_number), "--repo", repository, "--json", "title,headRefName,baseRefName,url,author"],
                    capture_output=True, text=True, check=True, timeout=30
                )
                pr_data = json.loads(result.stdout)

                self.logger.info(f"📝 Found PR: {pr_data['title']}")

                # Post codex instruction comment
                success = self.post_codex_instruction_simple(repository, pr_number, pr_data)

                # Record PR processing attempt with result
                result = "success" if success else "failure"
                self.safety_manager.record_pr_attempt(pr_key, result)

                if success:
                    self.logger.info(f"✅ Successfully processed target PR {repository} #{pr_number}")
                else:
                    self.logger.error(f"❌ Failed to process target PR {repository} #{pr_number}")

                return success

            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ Failed to get PR details for {repository} #{pr_number}: {e.stderr}")
                return False
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Failed to parse PR data for {repository} #{pr_number}: {e}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Unexpected error processing target PR {repository} #{pr_number}: {e}")
            return False

    def run_monitoring_cycle(self, single_repo=None, max_prs=10):
        """Run a complete monitoring cycle"""
        self.logger.info("🚀 Starting jleechanorg PR monitoring cycle")

        # Discover all open PRs
        open_prs = self.discover_open_prs()

        # Apply single repo filter if specified
        if single_repo:
            open_prs = [pr for pr in open_prs if pr["repository"] == single_repo]
            self.logger.info(f"🎯 Filtering to repository: {single_repo}")

        if not open_prs:
            self.logger.info("📭 No open PRs found")
            return

        processed_count = 0
        max_prs_per_cycle = max_prs  # Use provided limit

        for pr in open_prs[:max_prs_per_cycle]:
            repo_name = pr["repository"]
            repo_full_name = pr["repositoryFullName"]  # Use full name for GitHub API calls
            pr_number = pr["number"]

            self.logger.info(f"🎯 Processing PR: {repo_name}-{pr_number} - {pr['title']}")

            # Post codex instruction comment directly (comment-only approach)
            success = self.post_codex_instruction_simple(repo_full_name, pr_number, pr)

            if success:
                self.logger.info(f"✅ Successfully processed PR {repo_name}-{pr_number}")
                processed_count += 1
            else:
                self.logger.error(f"❌ Failed to process PR {repo_name}-{pr_number}")

        self.logger.info(f"🏁 Monitoring cycle complete: {processed_count} PRs processed")


def main():
    """CLI interface for jleechanorg PR monitor"""

    parser = argparse.ArgumentParser(description='jleechanorg PR Monitor')
    parser.add_argument('--dry-run', action='store_true',
                        help='Discover PRs but do not process them')
    parser.add_argument('--single-repo',
                        help='Process only specific repository')
    parser.add_argument('--max-prs', type=int, default=10,
                        help='Maximum PRs to process per cycle')
    parser.add_argument('--target-pr', type=int,
                        help='Process specific PR number')
    parser.add_argument('--target-repo',
                        help='Repository for target PR (required with --target-pr)')

    args = parser.parse_args()

    # Validate target PR arguments
    if args.target_pr and not args.target_repo:
        parser.error('--target-repo is required when using --target-pr')
    if args.target_repo and not args.target_pr:
        parser.error('--target-pr is required when using --target-repo')

    monitor = JleechanorgPRMonitor()

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
    else:
        monitor.run_monitoring_cycle(single_repo=args.single_repo, max_prs=args.max_prs)


if __name__ == '__main__':
    main()
