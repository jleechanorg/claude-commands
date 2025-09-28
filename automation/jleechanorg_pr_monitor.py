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
from codex_config import (
    CODEX_COMMIT_MARKER_PREFIX,
    CODEX_COMMIT_MARKER_SUFFIX,
    CODEX_COMMENT_TEMPLATE,
    DEFAULT_ASSISTANT_HANDLE as CODEX_DEFAULT_ASSISTANT_HANDLE,
    build_default_comment,
    normalise_handle,
)


class JleechanorgPRMonitor:
    """Cross-organization PR monitoring with @codex automation comments"""

    CODEX_COMMENT_ENV_VAR = "CODEX_COMMENT"
    ASSISTANT_HANDLE_ENV_VAR = "ASSISTANT_HANDLE"
    DEFAULT_ASSISTANT_HANDLE = CODEX_DEFAULT_ASSISTANT_HANDLE
    DEFAULT_CODEX_COMMENT_TEMPLATE = CODEX_COMMENT_TEMPLATE

    def __init__(self):
        self.logger = self._setup_logging()

        assistant_handle = os.environ.get(
            self.ASSISTANT_HANDLE_ENV_VAR, self.DEFAULT_ASSISTANT_HANDLE
        )
        self.assistant_handle = normalise_handle(assistant_handle)
        default_comment = build_default_comment(self.assistant_handle)

        # Allow overriding the Codex instruction from the environment
        self.CODEX_COMMENT_TEXT = os.environ.get(
            self.CODEX_COMMENT_ENV_VAR,
            default_comment,
        )

        self.commit_marker_prefix = CODEX_COMMIT_MARKER_PREFIX
        self.commit_marker_suffix = CODEX_COMMIT_MARKER_SUFFIX
        # Backwards compatibility for tests/consumers accessing old attributes
        self.CODEX_COMMIT_MARKER_PREFIX = self.commit_marker_prefix
        self.CODEX_COMMIT_MARKER_SUFFIX = self.commit_marker_suffix


        # Safety manager integration
        data_dir = Path.home() / "Library" / "Application Support" / "worldarchitect-automation"
        self.safety_manager = AutomationSafetyManager(str(data_dir))

        # Organization settings
        self.organization = "jleechanorg"
        self.base_project_dir = Path.home() / "projects"

        self.logger.info(f"🏢 Initialized jleechanorg PR monitor")
        self.logger.info(f"🛡️ Safety data: {data_dir}")
        self.logger.info(f"💬 Comment-only automation mode")

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
        """Discover all open PRs across jleechanorg organization"""
        self.logger.info(f"🔍 Discovering open PRs in {self.organization} organization")

        try:
            # Get all repositories in the organization
            repos_cmd = ["gh", "repo", "list", self.organization, "--limit", "100", "--json", "name,owner"]
            repos_result = subprocess.run(repos_cmd, capture_output=True, text=True, check=True, timeout=30, shell=False)
            repositories = json.loads(repos_result.stdout)

            self.logger.info(f"📚 Found {len(repositories)} repositories")

            all_prs = []

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

                    # Add repository context to each PR
                    for pr in prs:
                        pr["repository"] = repo_name
                        pr["repositoryFullName"] = repo_full_name

                    all_prs.extend(prs)

                    if prs:
                        self.logger.info(f"📋 {repo_name}: {len(prs)} open PRs")

                except subprocess.CalledProcessError as e:
                    # Skip repositories we don't have access to
                    if "Not Found" in e.stderr or "404" in e.stderr:
                        self.logger.debug(f"⚠️ No access to {repo_full_name}")
                    else:
                        self.logger.warning(f"❌ Error getting PRs for {repo_full_name}: {e.stderr}")

            self.logger.info(f"🎯 Total open PRs discovered: {len(all_prs)}")
            return all_prs

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

        # Get current PR state including comments and test status
        head_sha, comments = self._get_pr_comment_state(repository, pr_number)

        # Check if we already have an automation comment for this commit
        if head_sha and self._has_codex_comment_for_commit(comments, head_sha):
            self.logger.info(f"♻️ Automation comment already posted for commit {head_sha[:8]} on PR #{pr_number}, skipping")
            return True

        # Check if latest comment is from AI automation
        if comments and self._is_latest_comment_from_automation(comments):
            self.logger.info(f"🤖 Latest comment is from AI automation, checking test status...")

            # Check if tests are now passing
            if self._are_tests_passing(repository, pr_number):
                self.logger.info(f"✅ Tests are passing, skipping PR {pr_number}")
                return True
            else:
                # Tests still failing, check if Codex has replied to our automation comment
                if self._has_codex_replied_to_automation(comments):
                    self.logger.info(f"🤖 Codex has already replied to automation comment, skipping PR {pr_number}")
                    return True
                else:
                    self.logger.info(f"❌ Tests still failing and no Codex reply, will post new automation comment")

        # Check if latest comment is from Codex doing work (not review)
        elif comments and self._is_latest_comment_from_codex_work(comments):
            self.logger.info(f"🤖 Latest comment is from Codex doing work, skipping PR {pr_number}")
            return True

        # Check if recent human comment is asking another AI assistant to handle the PR
        elif comments and self._has_recent_human_ai_request(comments):
            self.logger.info(f"👤 Recent human comment requesting other AI assistance, skipping PR {pr_number}")
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

            result = subprocess.run(
                comment_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
                shell=False,
            )

            self.logger.info(f"✅ Posted Codex instruction comment on PR #{pr_number}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to post comment on PR #{pr_number}: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"💥 Unexpected error posting comment: {e}")
            return False

    def _is_latest_comment_from_automation(self, comments: List[Dict]) -> bool:
        """Check if the latest comment is from AI automation"""
        if not comments:
            return False

        latest_comment = comments[-1]  # Comments should be ordered by creation time
        body = latest_comment.get('body', '')
        return '[AI automation]' in body

    def _has_codex_replied_to_automation(self, comments: List[Dict]) -> bool:
        """Check if Codex has replied after our latest automation comment"""
        if not comments:
            return False

        # Find the most recent automation comment
        latest_automation_index = -1
        for i in range(len(comments) - 1, -1, -1):
            if '[AI automation]' in comments[i].get('body', ''):
                latest_automation_index = i
                break

        if latest_automation_index == -1:
            return False  # No automation comment found

        # Check if there are any non-automation comments after the latest automation comment
        for i in range(latest_automation_index + 1, len(comments)):
            comment_body = comments[i].get('body', '')
            author = comments[i].get('author', {}).get('login', '')

            # Skip bot comments, but include any human comments (including Codex responses)
            if not author.endswith('[bot]') and '[AI automation]' not in comment_body:
                self.logger.debug(f"Found reply from {author} after automation comment")
                return True

        return False

    def _is_latest_comment_from_codex_work(self, comments: List[Dict]) -> bool:
        """Check if the latest comment is from Codex indicating work done"""
        if not comments:
            return False

        latest_comment = comments[-1]
        body = latest_comment.get('body', '').lower()
        author = latest_comment.get('author', {}).get('login', '').lower()

        # Skip if it's from automation or a bot
        if '[ai automation]' in body.lower() or author.endswith('[bot]'):
            return False

        extra_handles = os.environ.get("ADDITIONAL_AI_HANDLES", "")
        ai_usernames = {
            self.assistant_handle.lower(),
            'coderabbitai',
            'claude-dev', 'codex-assistant', 'github-copilot',
            'claude', 'anthropic-claude', 'openai-codex', 'ai-assistant',
            'chatgpt-codex-connector'
        }
        ai_usernames.update(h.strip().lstrip('@').lower() for h in extra_handles.split(',') if h.strip())

        # Must be from a known AI assistant
        if author not in ai_usernames:
            self.logger.debug(f"Comment from {author} not recognized as AI assistant")
            return False

        # Look for patterns that indicate Codex did work (not just review)
        work_indicators = [
            'i\'ve fixed',
            'i fixed',
            'i\'ve updated',
            'i updated',
            'i\'ve implemented',
            'i implemented',
            'i\'ve addressed',
            'i addressed',
            'i\'ve modified',
            'i modified',
            'i\'ve changed',
            'i changed',
            'made the following changes',
            'here are the changes',
            'i\'ve made changes',
            'changes have been made',
            'updated the code',
            'fixed the issue',
            'resolved the problem',
            'applied the fix'
        ]

        # Check if the comment contains work indicators
        for indicator in work_indicators:
            if indicator in body:
                self.logger.debug(f"Found Codex work indicator: '{indicator}' in comment from {author}")
                return True

        return False

    def _has_recent_human_ai_request(self, comments: List[Dict]) -> bool:
        """Check if recent human comment is requesting another AI assistant to handle PR"""
        if not comments:
            return False

        # Check last few comments for human AI requests
        recent_comments = comments[-3:] if len(comments) >= 3 else comments

        extra_handles = os.environ.get("ADDITIONAL_AI_HANDLES", "")
        dynamic_mentions = {f"@{self.assistant_handle}"}
        dynamic_mentions.update(
            f"@{h.lstrip('@')}" for h in extra_handles.split(',') if h.strip()
        )

        for comment in recent_comments:
            body = comment.get('body', '').lower()
            author = comment.get('author', {}).get('login', '')

            # Skip automation and bot comments
            if '[ai automation]' in body or author.endswith('[bot]'):
                continue

            # Look for humans addressing other AI assistants
            # We skip if they mention other assistants to avoid interference
            other_ai_mentions = {'@github-copilot', '@claude', '@coderabbitai', '@codex'} | dynamic_mentions
            if any(mention.lower() in body for mention in other_ai_mentions):
                self.logger.debug(f"Found recent human AI request from {author}")
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
            ], capture_output=True, text=True, check=True, timeout=30, shell=False)

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
        """Build comment body that tells Codex to fix PR comments and tests"""

        # Extract review comments and feedback
        review_feedback = []
        for comment in comments:
            body = comment.get('body', '')
            author = comment.get('author', {}).get('login', 'unknown')

            # Skip our own automation comments
            if '[AI automation]' in body:
                continue

            # Include ALL other comments (human and bot)
            if body.strip():
                review_feedback.append(f"- {author}: {body[:200]}{'...' if len(body) > 200 else ''}")

        handle = f"@{self.assistant_handle}"
        comment_body = f"""{handle} [AI automation] Please review and fix this PR

**PR Details:**
- Title: {pr_data.get('title', 'Unknown')}
- Author: {pr_data.get('author', {}).get('login', 'unknown')}
- Branch: {pr_data.get('headRefName', 'unknown')}
- Commit: {head_sha[:8] if head_sha else 'unknown'} ({head_sha or 'unknown'})

**Instructions:**
Use your judgment to fix comments from everyone or explain why it should not be fixed. Follow binary response protocol - every comment needs "DONE" or "NOT DONE" classification explicitly with an explanation. Push any commits needed to remote so the PR is updated.

**Tasks:**
1. **Fix failing tests** - Review test failures and implement fixes
2. **Address review comments** - Implement feedback from reviewers
3. **Ensure code quality** - Follow project standards and best practices

"""

        if review_feedback:
            comment_body += f"""**Review Feedback to Address:**
{chr(10).join(review_feedback)}

"""

        # Build dynamic required actions based on actual needs
        required_actions = [
            "Use `/cerebras` for substantial code changes",
            "Run tests after changes: `./run_tests.sh`",
            "Ensure all status checks pass before requesting re-review",
            "Push commits to update the PR"
        ]

        # Only add review comment action if there are actual review comments
        if review_feedback:
            required_actions.insert(2, "Address ALL review comments systematically")
            final_instruction = "/cerebras Please fix the failing tests and address all review comments in this PR."
        else:
            final_instruction = "/cerebras Please fix the failing tests and ensure this PR is ready for merge."

        comment_body += f"""**Required Actions:**
{chr(10).join(f"- {action}" for action in required_actions)}

{final_instruction}"""

        if head_sha:
            comment_body += f"\n\n{self.commit_marker_prefix}{head_sha}{self.commit_marker_suffix}"

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

        prefix_index = comment_body.find(self.commit_marker_prefix)
        if prefix_index == -1:
            return None

        start_index = prefix_index + len(self.commit_marker_prefix)
        end_index = comment_body.find(self.commit_marker_suffix, start_index)
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
            marker = f"{self.commit_marker_prefix}{head_sha}{self.commit_marker_suffix}"
            return f"{self.CODEX_COMMENT_TEXT}\n\n{marker}"

        # Fallback without marker if we could not determine the commit SHA
        return self.CODEX_COMMENT_TEXT



    def process_single_pr_by_number(self, pr_number: int, repository: str) -> bool:
        """Process a specific PR by number and repository"""
        repo_full = self._normalize_repo(repository)
        repo_name = repo_full.split("/", 1)[1] if "/" in repo_full else repo_full
        self.logger.info(f"🎯 Processing target PR: {repo_full} #{pr_number}")

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
            if not self.safety_manager.can_process_pr(pr_number, repo=repo_name):
                self.logger.warning(f"🚫 Safety limits exceeded for PR {repo_full} #{pr_number}")
                return False

            # Get PR details using gh CLI
            try:
                result = subprocess.run(
                    [
                        "gh", "pr", "view", str(pr_number),
                        "--repo", repo_full,
                        "--json", "title,headRefName,baseRefName,url,author"
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                    shell=False,
                )
                pr_data = json.loads(result.stdout)

                self.logger.info(f"📝 Found PR: {pr_data['title']}")

                # Post codex instruction comment
                success = self.post_codex_instruction_simple(repo_full, pr_number, pr_data)

                # Record PR processing attempt with result
                result = "success" if success else "failure"
                self.safety_manager.record_pr_attempt(pr_number, result, repo=repo_name)

                if success:
                    self.logger.info(f"✅ Successfully processed target PR {repo_full} #{pr_number}")
                else:
                    attempts = self.safety_manager.get_pr_attempts(pr_number, repo=repo_name)
                    self.logger.error(f"❌ Failed to process target PR {repo_full} #{pr_number} (attempt {attempts})")

                return success

            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ Failed to get PR details for {repo_full} #{pr_number}: {e.stderr}")
                return False
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Failed to parse PR data for {repo_full} #{pr_number}: {e}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Unexpected error processing target PR {repo_full} #{pr_number}: {e}")
            return False

    def run_monitoring_cycle(self, single_repo: Optional[str] = None, max_prs: int = 10) -> None:
        """Run a complete monitoring cycle"""
        self.logger.info("🚀 Starting jleechanorg PR monitoring cycle")

        # Check global automation limits
        if not self.safety_manager.can_start_global_run():
            self.logger.warning("🚫 Global automation limit reached - skipping cycle")
            return

        # Record global run
        self.safety_manager.record_global_run()
        runs = self.safety_manager.get_global_runs()
        self.logger.info(f"📊 Global run #{runs}/{self.safety_manager.global_limit}")

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
            repo_full = pr.get("repositoryFullName", f"{self.organization}/{repo_name}")
            pr_number = pr["number"]

            # Check PR-specific limits
            if not self.safety_manager.can_process_pr(pr_number, repo=repo_name):
                attempts = self.safety_manager.get_pr_attempts(pr_number, repo=repo_name)
                self.logger.info(f"⏸️ PR {repo_name}-{pr_number} blocked ({attempts}/{self.safety_manager.pr_limit} attempts)")
                continue

            self.logger.info(f"🎯 Processing PR: {repo_name}-{pr_number} - {pr['title']}")

            # Post codex instruction comment directly (comment-only approach)
            success = self.post_codex_instruction_simple(repo_full, pr_number, pr)

            # Record attempt
            result = "success" if success else "failure"
            self.safety_manager.record_pr_attempt(pr_number, result, repo=repo_name)

            if success:
                self.logger.info(f"✅ Successfully processed PR {repo_name}-{pr_number}")
                processed_count += 1
            else:
                attempts = self.safety_manager.get_pr_attempts(pr_number, repo=repo_name)
                self.logger.error(f"❌ Failed to process PR {repo_name}-{pr_number} (attempt {attempts})")

        self.logger.info(f"🏁 Monitoring cycle complete: {processed_count} PRs processed")

        # Check and notify about limits
        self.safety_manager.check_and_notify_limits()


    def _normalize_repo(self, repository: str) -> str:
        """Return repository in owner/name format."""

        if "/" in repository:
            return repository
        return f"{self.organization}/{repository}"

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
