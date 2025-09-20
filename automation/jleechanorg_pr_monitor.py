#!/usr/bin/env python3
"""
jleechanorg PR Monitor - Cross-Organization Automation

Discovers and processes ALL open PRs across jleechanorg organization
with worktree isolation and safety limits integration.
"""

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

# Add automation directory to path
sys.path.insert(0, os.path.dirname(__file__))
from automation_safety_manager import AutomationSafetyManager


class JleechanorgPRMonitor:
    """Cross-organization PR monitoring with worktree isolation"""

    def __init__(self, workspace_base: str = None):
        self.logger = self._setup_logging()

        # Workspace for isolated worktrees
        self.workspace_base = workspace_base or (Path.home() / "tmp" / "pr-automation-workspaces")
        self.workspace_base = Path(self.workspace_base)
        self.workspace_base.mkdir(parents=True, exist_ok=True)

        # Safety manager integration
        data_dir = Path.home() / "Library" / "Application Support" / "worldarchitect-automation"
        self.safety_manager = AutomationSafetyManager(str(data_dir))

        # Organization settings
        self.organization = "jleechanorg"
        self.base_project_dir = Path.home() / "projects"

        self.logger.info(f"🏢 Initialized jleechanorg PR monitor")
        self.logger.info(f"📁 Workspace: {self.workspace_base}")
        self.logger.info(f"🛡️ Safety data: {data_dir}")

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
            repos_result = subprocess.run(repos_cmd, capture_output=True, text=True, check=True)
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

                    prs_result = subprocess.run(prs_cmd, capture_output=True, text=True, check=True)
                    prs = json.loads(prs_result.stdout)

                    # Add repository context to each PR
                    for pr in prs:
                        pr["repository"] = repo_name
                        pr["repositoryFullName"] = repo_full_name
                        pr["workspaceId"] = f"{repo_name}-pr-{pr['number']}"

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

    def create_worktree_for_pr(self, pr: Dict) -> Optional[Path]:
        """Create isolated worktree for PR processing"""
        workspace_id = pr["workspaceId"]
        repo_name = pr["repository"]
        pr_number = pr["number"]
        branch_name = pr["headRefName"]

        workspace_path = self.workspace_base / workspace_id

        self.logger.info(f"🏗️ Creating worktree for {repo_name} PR #{pr_number}")
        self.logger.info(f"📂 Branch: {branch_name} → {workspace_path}")

        try:
            # Clean up existing workspace
            if workspace_path.exists():
                self.logger.info(f"🧹 Cleaning existing workspace: {workspace_path}")
                shutil.rmtree(workspace_path)

            # Find local repository
            local_repo_path = self._find_local_repository(repo_name)
            if not local_repo_path:
                self.logger.warning(f"⚠️ No local repository found for {repo_name}")
                return None

            # Change to local repository directory
            original_cwd = os.getcwd()
            os.chdir(local_repo_path)

            try:
                # Fetch latest changes
                subprocess.run(["git", "fetch", "--all"], check=True, capture_output=True)

                # Check if branch exists locally
                local_branches = subprocess.run(
                    ["git", "branch", "--list", branch_name],
                    capture_output=True, text=True
                ).stdout.strip()

                # Create worktree
                if local_branches:
                    # Branch exists locally
                    self.logger.info(f"📋 Using existing local branch: {branch_name}")
                    worktree_cmd = ["git", "worktree", "add", str(workspace_path), branch_name]
                else:
                    # Branch doesn't exist locally, create from remote
                    remote_branch = f"origin/{branch_name}"

                    # Check if remote branch exists
                    remote_branches = subprocess.run(
                        ["git", "branch", "-r", "--list", remote_branch],
                        capture_output=True, text=True
                    ).stdout.strip()

                    if remote_branches:
                        self.logger.info(f"🌐 Creating local branch from remote: {remote_branch}")
                        worktree_cmd = ["git", "worktree", "add", "-b", branch_name, str(workspace_path), remote_branch]
                    else:
                        self.logger.error(f"❌ Branch {branch_name} not found locally or remotely")
                        return None

                # Execute worktree creation
                try:
                    result = subprocess.run(worktree_cmd, capture_output=True, text=True, check=True)
                    self.logger.info(f"✅ Worktree created successfully")
                except subprocess.CalledProcessError as e:
                    # Handle branch already checked out error
                    if "already checked out" in e.stderr:
                        # Create unique branch name for this worktree
                        unique_branch = f"{branch_name}-automation-{pr_number}"
                        self.logger.info(f"🔄 Branch conflict, creating unique branch: {unique_branch}")

                        # Check if we have local or remote branch to base from
                        if local_branches:
                            # Create new branch from existing local branch
                            unique_worktree_cmd = ["git", "worktree", "add", "-b", unique_branch, str(workspace_path), branch_name]
                        else:
                            # Create new branch from remote branch
                            remote_branch = f"origin/{branch_name}"
                            unique_worktree_cmd = ["git", "worktree", "add", "-b", unique_branch, str(workspace_path), remote_branch]

                        # Try again with unique branch
                        result = subprocess.run(unique_worktree_cmd, capture_output=True, text=True, check=True)
                        self.logger.info(f"✅ Worktree created successfully with unique branch: {unique_branch}")
                    else:
                        # Re-raise if it's a different error
                        raise

                # Verify workspace
                if not workspace_path.exists():
                    self.logger.error(f"❌ Worktree creation failed: {workspace_path} doesn't exist")
                    return None

                # Set up PR metadata in workspace
                metadata = {
                    "pr_number": pr_number,
                    "repository": repo_name,
                    "repository_full_name": pr["repositoryFullName"],
                    "branch_name": branch_name,
                    "base_branch": pr["baseRefName"],
                    "pr_url": pr["url"],
                    "author": pr["author"]["login"],
                    "title": pr["title"],
                    "created_at": datetime.now().isoformat(),
                    "local_repo_path": str(local_repo_path)
                }

                metadata_file = workspace_path / ".pr-metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                self.logger.info(f"📝 PR metadata saved: {metadata_file}")
                return workspace_path

            finally:
                os.chdir(original_cwd)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to create worktree: {e.stderr}")
            return None
        except Exception as e:
            self.logger.error(f"💥 Unexpected error creating worktree: {e}")
            return None

    def _find_local_repository(self, repo_name: str) -> Optional[Path]:
        """Find local repository path for given repo name"""
        # Common patterns for local repositories
        search_paths = [
            # Standard patterns in ~/projects/
            self.base_project_dir / repo_name,
            self.base_project_dir / f"worktree_{repo_name}",
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
            if path.exists() and (path / ".git").exists():
                self.logger.debug(f"🎯 Found local repo: {path}")
                return path

        # Search for any directory containing the repo name in ~/projects/
        if self.base_project_dir.exists():
            for path in self.base_project_dir.iterdir():
                if path.is_dir() and repo_name.lower() in path.name.lower():
                    if (path / ".git").exists():
                        self.logger.debug(f"🎯 Found local repo (fuzzy): {path}")
                        return path

        # Search for project_* patterns in home directory
        home_dir = Path.home()
        for path in home_dir.iterdir():
            if path.is_dir() and path.name.startswith(f"project_{repo_name}"):
                # Check if it's a direct repo
                if (path / ".git").exists():
                    self.logger.debug(f"🎯 Found local repo (home): {path}")
                    return path
                # Check if repo is nested inside
                nested_repo = path / repo_name
                if nested_repo.exists() and (nested_repo / ".git").exists():
                    self.logger.debug(f"🎯 Found local repo (nested): {nested_repo}")
                    return nested_repo

        return None

    def process_pr_with_copilot(self, workspace_path: Path) -> bool:
        """Process PR using /copilot command in isolated workspace"""
        metadata_file = workspace_path / ".pr-metadata.json"

        if not metadata_file.exists():
            self.logger.error(f"❌ PR metadata not found: {metadata_file}")
            return False

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        pr_number = metadata["pr_number"]
        repo_name = metadata["repository"]

        self.logger.info(f"🤖 Processing {repo_name} PR #{pr_number} with /copilot")

        try:
            # Change to workspace directory
            original_cwd = os.getcwd()
            os.chdir(workspace_path)

            try:
                # Execute /copilot command
                copilot_cmd = [
                    "claude", "--dangerously-skip-permissions", "--model", "sonnet",
                    f"/copilot {pr_number} --workspace-isolation"
                ]

                result = subprocess.run(
                    copilot_cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )

                if result.returncode == 0:
                    self.logger.info(f"✅ /copilot completed successfully for PR #{pr_number}")

                    # Check if there are changes to push
                    git_status = subprocess.run(
                        ["git", "status", "--porcelain"],
                        capture_output=True, text=True
                    )

                    if git_status.stdout.strip():
                        self.logger.info(f"📝 Changes detected, pushing to remote")

                        # Add, commit and push changes
                        subprocess.run(["git", "add", "-A"], check=True)
                        subprocess.run([
                            "git", "commit", "-m",
                            f"🤖 Automated fixes for PR #{pr_number}\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
                        ], check=True)
                        subprocess.run(["git", "push", "origin", metadata["branch_name"]], check=True)

                        self.logger.info(f"🚀 Changes pushed to {metadata['branch_name']}")
                    else:
                        self.logger.info(f"📝 No changes to push for PR #{pr_number}")

                    return True
                else:
                    self.logger.error(f"❌ /copilot failed for PR #{pr_number}: {result.stderr}")
                    return False

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ /copilot timed out for PR #{pr_number}")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Command failed for PR #{pr_number}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"💥 Unexpected error processing PR #{pr_number}: {e}")
            return False

    def cleanup_workspace(self, workspace_path: Path):
        """Clean up worktree workspace"""
        if not workspace_path.exists():
            return

        metadata_file = workspace_path / ".pr-metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            local_repo_path = metadata.get("local_repo_path")
            if local_repo_path:
                try:
                    # Change to local repository
                    original_cwd = os.getcwd()
                    os.chdir(local_repo_path)

                    try:
                        # Remove worktree
                        subprocess.run(
                            ["git", "worktree", "remove", str(workspace_path), "--force"],
                            check=True, capture_output=True
                        )
                        self.logger.info(f"🧹 Worktree removed: {workspace_path}")
                    finally:
                        os.chdir(original_cwd)

                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"⚠️ Failed to remove worktree cleanly: {e}")

        # Force remove directory if it still exists
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
            self.logger.info(f"🗑️ Workspace directory removed: {workspace_path}")

    def run_monitoring_cycle(self, single_repo=None, max_prs=10):
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
            pr_number = pr["number"]
            pr_key = f"{repo_name}-{pr_number}"

            # Check PR-specific limits
            if not self.safety_manager.can_process_pr(pr_key):
                attempts = self.safety_manager.get_pr_attempts(pr_key)
                self.logger.info(f"⏸️ PR {pr_key} blocked ({attempts}/{self.safety_manager.pr_limit} attempts)")
                continue

            self.logger.info(f"🎯 Processing PR: {pr_key} - {pr['title']}")

            # Create isolated workspace
            workspace = self.create_worktree_for_pr(pr)
            if not workspace:
                self.logger.error(f"❌ Failed to create workspace for PR {pr_key}")
                continue

            try:
                # Process with /copilot
                success = self.process_pr_with_copilot(workspace)

                # Record attempt
                result = "success" if success else "failure"
                self.safety_manager.record_pr_attempt(pr_key, result)

                if success:
                    self.logger.info(f"✅ Successfully processed PR {pr_key}")
                    processed_count += 1
                else:
                    attempts = self.safety_manager.get_pr_attempts(pr_key)
                    self.logger.error(f"❌ Failed to process PR {pr_key} (attempt {attempts})")

            finally:
                # Always clean up workspace
                self.cleanup_workspace(workspace)

        self.logger.info(f"🏁 Monitoring cycle complete: {processed_count} PRs processed")

        # Check and notify about limits
        self.safety_manager.check_and_notify_limits()


def main():
    """CLI interface for jleechanorg PR monitor"""
    import argparse

    parser = argparse.ArgumentParser(description='jleechanorg PR Monitor')
    parser.add_argument('--workspace-base',
                        help='Base directory for PR workspaces')
    parser.add_argument('--dry-run', action='store_true',
                        help='Discover PRs but do not process them')
    parser.add_argument('--single-repo',
                        help='Process only specific repository')
    parser.add_argument('--max-prs', type=int, default=10,
                        help='Maximum PRs to process per cycle')

    args = parser.parse_args()

    monitor = JleechanorgPRMonitor(workspace_base=args.workspace_base)

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
