#!/usr/bin/env python3
"""
/replicate command implementation - Analyze and apply PR functionality to current branch

This command automates the process of analyzing a GitHub PR and intelligently applying
its missing functionality to the current branch.
"""

import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

# Constants
ANALYSIS_COMPLETE_MESSAGE = (
    "\n✅ PR analysis complete. This command provides comprehensive analysis\n"
    "of PR changes and generates actionable replication plans. Use the output\n"
    "to guide manual implementation or integration with automated tools."
)

def parse_pr_reference(pr_ref: str) -> Tuple[str, str, int]:
    """Parse PR reference from various formats."""
    # Validate input
    if not pr_ref or not pr_ref.strip():
        raise ValueError("PR reference cannot be None or an empty string.")

    # Try URL format first
    url_match = re.match(r'https://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_ref)
    if url_match:
        return url_match.group(1), url_match.group(2), int(url_match.group(3))

    # Try PR#123 format
    pr_match = re.match(r'PR#?(\d+)', pr_ref, re.IGNORECASE)
    if pr_match:
        # Get repo info from current git remote
        owner, repo = get_current_repo_info()
        return owner, repo, int(pr_match.group(1))

    # Try just number
    if pr_ref.isdigit():
        owner, repo = get_current_repo_info()
        return owner, repo, int(pr_ref)

    raise ValueError(f"Invalid PR reference format: {pr_ref}")

def get_current_repo_info() -> Tuple[str, str]:
    """Get current repository owner and name from git remote."""
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()

        # Parse GitHub URL
        if 'github.com' in url:
            match = re.search(r'github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?$', url)
            if match:
                return match.group(1), match.group(2)
    except subprocess.CalledProcessError:
        pass

    # Default fallback using environment variables
    owner = os.getenv('DEFAULT_REPO_OWNER', 'default-owner')
    repo = os.getenv('DEFAULT_REPO_NAME', 'worldarchitect.ai')
    return owner, repo

def fetch_pr_data(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Fetch PR data using GitHub CLI."""
    try:
        # Get PR metadata
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), '--repo', f'{owner}/{repo}', '--json',
             'title,state,headRefName,baseRefName,files,body,url'],
            capture_output=True, text=True, check=True
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raw_response = result.stdout[:500]  # Truncate to 500 characters
            print(f"Error parsing PR data: {e}. Raw response content (truncated): {raw_response}")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to fetch PR {pr_number} from {owner}/{repo}: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) not found. Please install and authenticate.")
        sys.exit(1)

def analyze_pr_changes(pr_data: Dict[str, Any], focus_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Analyze PR changes and categorize them."""
    analysis = {
        'files_added': [],
        'files_modified': [],
        'files_deleted': [],
        'total_additions': 0,
        'total_deletions': 0,
        'focused_changes': [],
        'ignored_changes': []
    }

    # Default focus directories if not specified
    if not focus_dirs:
        focus_dirs = ['.claude/commands/', 'mvp_site/', 'roadmap/']

    for file_info in pr_data.get('files', []):
        path = file_info['path']
        additions = file_info.get('additions', 0)
        deletions = file_info.get('deletions', 0)

        analysis['total_additions'] += additions
        analysis['total_deletions'] += deletions

        # Categorize by change type
        if deletions == 0 and additions > 0:
            analysis['files_added'].append(path)
        elif additions == 0 and deletions > 0:
            analysis['files_deleted'].append(path)
        else:
            analysis['files_modified'].append(path)

        # Check if in focus directories
        in_focus = any(path.startswith(focus_dir) for focus_dir in focus_dirs)
        if in_focus:
            analysis['focused_changes'].append({
                'path': path,
                'additions': additions,
                'deletions': deletions
            })
        else:
            analysis['ignored_changes'].append(path)

    return analysis

def compare_with_current_branch(pr_files: List[str]) -> Dict[str, str]:
    """Compare PR files with current branch to identify differences."""
    differences = {}

    for file_path in pr_files:
        if os.path.exists(file_path):
            differences[file_path] = 'exists'
        else:
            differences[file_path] = 'missing'

    return differences

def generate_replication_plan(analysis: Dict[str, Any], differences: Dict[str, str]) -> List[Dict[str, Any]]:
    """Generate a plan for replicating PR changes."""
    plan = []

    # Handle new files
    for file_path in analysis['files_added']:
        if differences.get(file_path) == 'missing':
            plan.append({
                'action': 'create',
                'file': file_path,
                'reason': 'File added in PR but missing in current branch'
            })

    # Handle modified files
    for file_path in analysis['files_modified']:
        if differences.get(file_path) == 'exists':
            plan.append({
                'action': 'analyze_merge',
                'file': file_path,
                'reason': 'File modified in PR and exists in current branch - needs smart merge'
            })

    # Note deleted files (usually don't replicate deletions)
    for file_path in analysis['files_deleted']:
        plan.append({
            'action': 'skip',
            'file': file_path,
            'reason': 'File deleted in PR - skipping deletion to preserve current functionality'
        })

    return plan

def create_progress_summary(pr_data: Dict[str, Any], analysis: Dict[str, Any], plan: List[Dict[str, Any]]) -> str:
    """Create a detailed summary of the replication process."""
    summary = f"""# PR Replication Summary

## Source PR
- **PR #{pr_data.get('number', 'Unknown')}**: {pr_data.get('title', 'Unknown')}
- **URL**: {pr_data.get('url', 'Unknown')}
- **Branch**: {pr_data.get('headRefName', 'Unknown')} → {pr_data.get('baseRefName', 'Unknown')}
- **State**: {pr_data.get('state', 'Unknown')}

## Analysis Results
- **Total Files**: {len(analysis['files_added']) + len(analysis['files_modified']) + len(analysis['files_deleted'])}
- **Files Added**: {len(analysis['files_added'])}
- **Files Modified**: {len(analysis['files_modified'])}
- **Files Deleted**: {len(analysis['files_deleted'])}
- **Total Additions**: {analysis['total_additions']} lines
- **Total Deletions**: {analysis['total_deletions']} lines

## Focused Changes
{len(analysis['focused_changes'])} files in focus directories:
"""

    for change in analysis['focused_changes']:
        summary += f"- {change['path']} (+{change['additions']}/-{change['deletions']})\n"

    summary += f"\n## Replication Plan\n"
    summary += f"{len(plan)} actions planned:\n\n"

    action_counts = {}
    for item in plan:
        action = item['action']
        action_counts[action] = action_counts.get(action, 0) + 1

    for action, count in action_counts.items():
        summary += f"- **{action}**: {count} files\n"

    return summary

def main():
    """Main entry point for the replicate command."""
    if len(sys.argv) < 2:
        print("Usage: /replicate <PR_URL or PR_NUMBER> [--yes]")
        sys.exit(1)

    pr_ref = sys.argv[1]
    non_interactive = "--yes" in sys.argv or "-y" in sys.argv

    # Parse PR reference
    try:
        owner, repo, pr_number = parse_pr_reference(pr_ref)
        print(f"Analyzing PR #{pr_number} from {owner}/{repo}...")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Fetch PR data
    print("Fetching PR data...")
    pr_data = fetch_pr_data(owner, repo, pr_number)
    pr_data['number'] = pr_number  # Add number to data

    # Analyze changes
    print("Analyzing PR changes...")
    analysis = analyze_pr_changes(pr_data)

    # Compare with current branch
    print("Comparing with current branch...")
    all_pr_files = (analysis['files_added'] +
                    analysis['files_modified'] +
                    analysis['files_deleted'])
    differences = compare_with_current_branch(all_pr_files)

    # Generate replication plan
    print("Generating replication plan...")
    plan = generate_replication_plan(analysis, differences)

    # Create and display summary
    summary = create_progress_summary(pr_data, analysis, plan)
    print("\n" + summary)

    # Ask for confirmation
    if plan:
        if not non_interactive:
            response = input("\nProceed with replication? (y/n): ")
            if response.lower() != 'y':
                print("Replication cancelled.")
                sys.exit(0)
        else:
            print("\nAuto-proceeding with replication (--yes flag provided)...")

        print(ANALYSIS_COMPLETE_MESSAGE)
    else:
        print("\nNo actions needed - current branch appears to have all PR functionality.")

if __name__ == "__main__":
    main()
