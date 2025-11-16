#!/usr/bin/env python3
"""
/gstatus command - Comprehensive PR status dashboard with GitHub MCP integration

Enhanced version with:
- Last 10 comments via GitHub MCP
- Last 3 commits on remote branch
- Local vs remote differences analysis
- Complete synchronization status

Shows complete PR overview including files, CI status, merge conflicts, and GitHub state.
Integrates with /header and provides authoritative GitHub data.
"""

import json
import subprocess
import sys
import re
import shlex
from datetime import datetime
from urllib.parse import urlparse

def run_command(cmd, capture_output=True, shell=False):
    """Run shell command and return result - SECURE: shell=False by default"""
    try:
        # Convert string command to list for shell=False security
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        result = subprocess.run(
            cmd,
            shell=False,  # intentionally forced; shell param kept for API compatibility
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        # ValueError can be raised by shlex.split() for invalid shell syntax
        return None

# call_github_mcp function removed - replaced with orchestration via gstatus.md
# GitHub data now sourced from /commentfetch command composition

def get_repo_info():
    """Extract repository owner and name from git remote"""
    remote_url = run_command(["git", "remote", "get-url", "origin"])
    if not remote_url:
        return None, None

    # Parse GitHub URL (support https, ssh, ssh://) with input validation
    if "github.com" in remote_url and len(remote_url) < 1000:  # Prevent excessively long URLs
        try:
            # ssh form: git@github.com:owner/repo(.git)
            if remote_url.startswith("git@github.com:"):
                url_part = remote_url.split(":", 1)[1]
            else:
                # https/ssh:// forms
                parsed = urlparse(remote_url)
                if parsed.hostname == "github.com":
                    url_part = parsed.path.lstrip("/")
                else:
                    return None, None

            if url_part.endswith(".git"):
                url_part = url_part[:-4]

            # Validate path components to prevent path traversal
            parts = [p for p in url_part.split("/") if p and "/" not in p]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                # Validate owner/repo format with proper GitHub username/repo rules
                # GitHub allows: alphanumeric, dash, underscore, dot (including repos starting with dots)
                # But prevent injection by direct character validation
                github_name_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
                if (len(owner) <= 39 and len(repo) <= 100 and  # GitHub limits
                    github_name_pattern.match(owner) and
                    github_name_pattern.match(repo) and
                    owner not in ['..', '.'] and repo not in ['..', '.']):  # Prevent path traversal
                    return owner, repo
        except Exception:
            pass

    return None, None

def get_pr_number():
    """Get current PR number for the branch using gh CLI"""
    branch = run_command(["git", "branch", "--show-current"])
    if not branch:
        return None

    # Try to find PR for current branch
    pr_data = run_command(["gh", "pr", "list", "--head", branch, "--state", "open", "--limit", "1", "--json", "number"])
    if pr_data:
        try:
            prs = json.loads(pr_data)
            if isinstance(prs, list) and len(prs) > 0 and isinstance(prs[0], dict):
                pr_number = prs[0].get("number")
                if isinstance(pr_number, (int, str)) and str(pr_number).isdigit():
                    return int(pr_number)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return None

def get_pr_ci_status(pr_number):
    """Get comprehensive CI status for a PR - CRITICAL: Like fixpr.md does"""
    if not pr_number:
        return None

    # Fetch comprehensive PR data including CI status - like fixpr.md approach
    pr_data = run_command([
        "gh", "pr", "view", str(pr_number),
        "--json", "statusCheckRollup,mergeable,mergeStateStatus,state"
    ])

    if not pr_data:
        return None

    try:
        data = json.loads(pr_data)
        if not isinstance(data, dict):
            return None

        return {
            'mergeable': data.get('mergeable'),
            'mergeStateStatus': data.get('mergeStateStatus'),
            'state': data.get('state'),
            'statusCheckRollup': data.get('statusCheckRollup', [])
        }
    except (json.JSONDecodeError, ValueError, TypeError):
        return None

def analyze_ci_status(ci_status):
    """Analyze CI status and detect failing tests - CRITICAL: Following fixpr.md pattern"""
    if not ci_status or not isinstance(ci_status, dict):
        return {
            'mergeable_status': 'UNKNOWN',
            'failing_checks': [],
            'passing_checks': [],
            'pending_checks': [],
            'is_mergeable': False,
            'has_failures': True  # Conservative default
        }

    # CRITICAL: Parse statusCheckRollup like fixpr.md does
    status_checks = ci_status.get('statusCheckRollup', [])
    if not isinstance(status_checks, list):
        status_checks = []

    # Reference: CheckRun {status: QUEUED|IN_PROGRESS|COMPLETED, conclusion: SUCCESS|FAILURE|NEUTRAL|CANCELLED|TIMED_OUT|ACTION_REQUIRED|STALE|SKIPPED}
    #            StatusContext {state: PENDING|SUCCESS|FAILURE}
    failure_conclusions = {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}
    failure_states = {"FAILURE", "ERROR"}
    success_conclusions = {"SUCCESS"}
    pending_statuses = {"PENDING", "QUEUED", "IN_PROGRESS", "REQUESTED", "WAITING"}

    failing_checks, passing_checks, pending_checks = [], [], []

    # Process each check - following fixpr.md safe processing pattern
    for check in status_checks:
        if not isinstance(check, dict):
            continue

        # Get check details safely
        name = check.get('name') or check.get('context') or 'unknown'
        conclusion = (check.get('conclusion') or '').upper() or None
        state = (check.get('state') or '').upper() or None
        status = (check.get('status') or '').upper() or None
        # Only mark required when explicitly provided; else None to avoid misleading labels
        is_required = True if check.get('isRequired') is True else None
        description = check.get('description', '')

        # Classify failures
        if (conclusion in failure_conclusions) or (state in failure_states):
            failing_checks.append({
                'name': name,
                'status': conclusion or state or 'FAILURE',
                'required': is_required,
                'description': description
            })
        # Classify successes
        elif (conclusion in success_conclusions) or (state == "SUCCESS"):
            passing_checks.append({
                'name': name,
                'status': conclusion or state or 'SUCCESS',
                'required': is_required
            })
        else:
            # Pending or ambiguous
            if (status in pending_statuses) or (state == "PENDING") or (conclusion in {None, "STALE"}):
                pending_checks.append({
                    'name': name,
                    'status': conclusion or state or status or 'PENDING',
                    'required': is_required
                })
            else:
                # NEUTRAL/SKIPPED treated as non-blocking
                passing_checks.append({
                    'name': name,
                    'status': conclusion or state or status or 'NEUTRAL',
                    'required': is_required
                })

    # CRITICAL: Following fixpr.md logic for mergeable status
    mergeable = ci_status.get('mergeable')
    merge_state = ci_status.get('mergeStateStatus')

    # Determine if truly mergeable - CRITICAL: Don't trust mergeable alone
    has_failures = len(failing_checks) > 0
    has_pending = len(pending_checks) > 0
    is_unstable = merge_state == 'UNSTABLE'
    is_dirty = merge_state == 'DIRTY'
    is_conflicting = mergeable == 'CONFLICTING'
    is_blocked = merge_state in {'BLOCKED', 'HAS_HOOKS'}
    is_behind = merge_state == 'BEHIND'
    is_draft = merge_state == 'DRAFT'

    is_truly_mergeable = (
        mergeable == 'MERGEABLE' and
        merge_state == 'CLEAN' and
        not has_failures and
        not has_pending
    )

    return {
        'mergeable_status': f"{mergeable} / {merge_state}",
        'failing_checks': failing_checks,
        'passing_checks': passing_checks,
        'pending_checks': pending_checks,
        'is_mergeable': is_truly_mergeable,
        'has_failures': has_failures,
        'has_pending': has_pending,
        'is_unstable': is_unstable,
        'is_dirty': is_dirty,
        'is_conflicting': is_conflicting,
        'is_blocked': is_blocked,
        'is_behind': is_behind,
        'is_draft': is_draft
    }

def get_git_status():
    """Get comprehensive git status information"""
    status = {
        'branch': run_command(["git", "branch", "--show-current"]),
        'upstream': run_command(["git", "rev-parse", "--abbrev-ref", "@{upstream}"]),
        'ahead_behind': None,
        'staged': [],
        'modified': [],
        'untracked': [],
        'conflicts': []
    }

    # Get ahead/behind status - handle both spaces and tabs between counts
    if status['upstream']:
        ahead_behind = run_command(["git", "rev-list", "--left-right", "--count", f"{status['upstream']}...HEAD"])
        if ahead_behind:
            # Split on any whitespace (spaces, tabs) - some Git versions use different separators
            parts = ahead_behind.strip().split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                behind, ahead = parts[0], parts[1]
                status['ahead_behind'] = {'ahead': int(ahead), 'behind': int(behind)}
            else:
                # Fallback: try parsing with regex for more robust parsing
                match = re.match(r'(\d+)\s+(\d+)', ahead_behind.strip())
                if match:
                    behind, ahead = match.groups()
                    status['ahead_behind'] = {'ahead': int(ahead), 'behind': int(behind)}
                else:
                    status['ahead_behind'] = {'ahead': 0, 'behind': 0}

    # Get file status
    git_status_output = run_command(["git", "status", "--porcelain"])
    if git_status_output:
        for line in git_status_output.split('\n'):
            if not line:
                continue

            status_code = line[:2]
            filename = line[3:]

            if status_code.startswith('UU'):
                status['conflicts'].append(filename)
            elif status_code[0] in ['A', 'M', 'D', 'R', 'C']:
                status['staged'].append(filename)
            elif status_code[1] in ['M', 'D']:
                status['modified'].append(filename)
            elif status_code == '??':
                status['untracked'].append(filename)

    return status

def get_recent_commits(branch='main', limit=3):
    """Get recent commits from remote branch"""
    # Get repository info for potential GitHub API calls
    owner, repo = get_repo_info()

    # Try GitHub API via gh CLI first
    if owner and repo:
        commits_data = run_command(["gh", "api", f"repos/{owner}/{repo}/commits?sha={branch}&per_page={limit}"])
        if commits_data:
            try:
                commits = json.loads(commits_data)
                if isinstance(commits, list):
                    # Validate commit structure
                    valid_commits = []
                    for commit in commits:
                        if isinstance(commit, dict) and commit.get("sha"):
                            valid_commits.append(commit)
                    return valid_commits
                return []
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    # Fallback to git log
    git_commits = run_command([
        "git", "log", f"origin/{branch}",
        "-n", str(limit),
        "--pretty=format:%H|%an|%ad|%s",
        "--date=iso"
    ])
    if not git_commits:
        return []

    commits = []
    for line in git_commits.split('\n'):
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commits.append({
                    'sha': parts[0][:8],
                    'author': {'name': parts[1]},
                    'commit': {
                        'author': {'date': parts[2]},
                        'message': parts[3]
                    }
                })

    return commits

def format_commit(commit):
    """Format commit information for display"""
    try:
        sha = commit.get('sha', '')[:8] if commit.get('sha') else 'unknown'
        author = commit.get('author', {}).get('name') or commit.get('commit', {}).get('author', {}).get('name', 'Unknown')
        message = commit.get('commit', {}).get('message', '').split('\n')[0]

        # Handle date formatting
        date_str = commit.get('commit', {}).get('author', {}).get('date', '')
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_display = date_obj.strftime('%m/%d %H:%M')
            except ValueError:
                date_display = date_str[:10]  # Fallback to date part
        else:
            date_display = 'unknown'

        return f"  {sha} {author} {date_display} {message}"
    except Exception:
        return f"  {str(commit)}"

def get_file_changes():
    """Get file changes between local and remote"""
    branch = run_command(["git", "branch", "--show-current"])
    if not branch:
        return {'added': [], 'modified': [], 'deleted': []}

    # Get diff against origin/main or origin/master
    remote_branch = f"origin/{branch}"
    diff_output = run_command(["git", "diff", "--name-status", f"{remote_branch}...HEAD"])

    changes = {'added': [], 'modified': [], 'deleted': []}
    if diff_output:
        for line in diff_output.split('\n'):
            if not line:
                continue
            parts = line.split('\t', 1)
            if len(parts) >= 2:
                status, filename = parts[0], parts[1]
                if status == 'A':
                    changes['added'].append(filename)
                elif status == 'M':
                    changes['modified'].append(filename)
                elif status == 'D':
                    changes['deleted'].append(filename)

    return changes

def main():
    """Main execution function"""

    # Check for PR number argument
    target_pr = None
    if len(sys.argv) > 1:
        try:
            target_pr = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid PR number: {sys.argv[1]}")
            return

    print("🔍 Comprehensive Git Status Dashboard")
    print("=" * 50)

    # Basic git status
    status = get_git_status()

    print(f"📍 Current Branch: {status['branch'] or 'unknown'}")
    if status['upstream']:
        print(f"🔗 Upstream: {status['upstream']}")
        if status['ahead_behind']:
            ahead = status['ahead_behind']['ahead']
            behind = status['ahead_behind']['behind']
            if ahead > 0 or behind > 0:
                print(f"📊 Status: {ahead} ahead, {behind} behind")
            else:
                print("✅ Branch is up to date")
    else:
        print("⚠️  No upstream branch configured")

    # PR information with CI status
    pr_number = target_pr if target_pr else get_pr_number()
    if pr_number:
        owner, repo = get_repo_info()
        if owner and repo:
            print(f"🔀 PR: #{pr_number} (https://github.com/{owner}/{repo}/pull/{pr_number})")

            # CRITICAL: Get comprehensive CI status like fixpr.md
            ci_status = get_pr_ci_status(pr_number)
            if not ci_status:
                print("\n⚠️  CI STATUS: unavailable (gh not authenticated or network error)")
            ci_analysis = analyze_ci_status(ci_status or {})

            # Display CI status with proper failure detection
            print(f"\n🚨 CI STATUS: {ci_analysis['mergeable_status']}")

            if ci_analysis['has_failures']:
                print(f"❌ FAILING CHECKS ({len(ci_analysis['failing_checks'])}):")
                for check in ci_analysis['failing_checks']:
                    req_marker = " (required)" if check.get('required') is True else ""
                    desc = f" - {check['description']}" if check['description'] else ""
                    print(f"  ❌ {check['name']}: {check['status']}{req_marker}{desc}")

            if ci_analysis['passing_checks']:
                print(f"✅ PASSING CHECKS ({len(ci_analysis['passing_checks'])}):")
                for check in ci_analysis['passing_checks'][:3]:  # Show first 3
                    req_marker = " (required)" if check.get('required') is True else ""
                    print(f"  ✅ {check['name']}: {check['status']}{req_marker}")
                if len(ci_analysis['passing_checks']) > 3:
                    remaining = len(ci_analysis['passing_checks']) - 3
                    print(f"  ... and {remaining} more passing checks")

            if ci_analysis['pending_checks']:
                print(f"⏳ PENDING CHECKS ({len(ci_analysis['pending_checks'])}):")
                for check in ci_analysis['pending_checks'][:3]:  # Show first 3
                    print(f"  ⏳ {check['name']}: {check['status']}")

            # CRITICAL: Show true mergeable status
            if ci_analysis['is_mergeable']:
                print("✅ PR IS TRULY MERGEABLE")
            else:
                reasons = []
                if ci_analysis['has_failures']:
                    reasons.append("failing tests")
                if ci_analysis.get('has_pending'):
                    reasons.append("pending checks")
                if ci_analysis['is_unstable']:
                    reasons.append("unstable state")
                if ci_analysis['is_dirty']:
                    reasons.append("dirty merge state")
                if ci_analysis['is_conflicting']:
                    reasons.append("merge conflicts")
                if ci_analysis.get('is_blocked'):
                    reasons.append("blocked")
                if ci_analysis.get('is_behind'):
                    reasons.append("behind base")
                if ci_analysis.get('is_draft'):
                    reasons.append("draft")

                reason_text = ", ".join(reasons) if reasons else "unknown issues"
                print(f"❌ PR NOT MERGEABLE: {reason_text}")
    else:
        print("ℹ️  No PR found for current branch")

    # File changes
    print("\n📁 Working Directory Status:")
    if status['conflicts']:
        print(f"🚨 Merge Conflicts ({len(status['conflicts'])}):")
        for file in status['conflicts'][:5]:  # Show first 5
            print(f"  ❌ {file}")

    if status['staged']:
        print(f"📋 Staged Changes ({len(status['staged'])}):")
        for file in status['staged'][:5]:  # Show first 5
            print(f"  ✅ {file}")

    if status['modified']:
        print(f"📝 Modified Files ({len(status['modified'])}):")
        for file in status['modified'][:5]:  # Show first 5
            print(f"  🔧 {file}")

    if status['untracked']:
        print(f"❓ Untracked Files ({len(status['untracked'])}):")
        for file in status['untracked'][:3]:  # Show first 3
            print(f"  ➕ {file}")

    if not any([status['staged'], status['modified'], status['untracked'], status['conflicts']]):
        print("✨ Working directory is clean")

    # Recent commits
    print(f"\n📝 Recent Commits (origin/{status['branch'] or 'main'}):")
    commits = get_recent_commits(status['branch'] or 'main')
    if commits:
        for commit in commits[:3]:
            print(format_commit(commit))
    else:
        print("  No recent commits found")

    # File changes compared to remote
    changes = get_file_changes()
    total_changes = len(changes['added']) + len(changes['modified']) + len(changes['deleted'])

    if total_changes > 0:
        print(f"\n🔄 Local vs Remote Changes ({total_changes} total):")
        if changes['added']:
            print(f"  ➕ Added: {len(changes['added'])} files")
        if changes['modified']:
            print(f"  🔧 Modified: {len(changes['modified'])} files")
        if changes['deleted']:
            print(f"  ➖ Deleted: {len(changes['deleted'])} files")

    print("\n" + "=" * 50)
    print("📊 Status Summary Complete")

if __name__ == "__main__":
    main()
