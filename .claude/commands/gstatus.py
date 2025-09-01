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
import os
from datetime import datetime

def run_command(cmd, capture_output=True, shell=False):
    """Run shell command and return result"""
    try:
        # Convert string command to list for shell=False security
        if isinstance(cmd, str):
            cmd = cmd.split()

        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None

# call_github_mcp function removed - replaced with orchestration via gstatus.md
# GitHub data now sourced from /commentfetch command composition

def get_repo_info():
    """Extract repository owner and name from git remote"""
    remote_url = run_command("git remote get-url origin")
    if not remote_url:
        return None, None

    # Handle both HTTPS and SSH formats
    if remote_url.startswith('https://github.com/'):
        repo_part = remote_url.replace('https://github.com/', '').replace('.git', '')
    elif remote_url.startswith('git@github.com:'):
        repo_part = remote_url.replace('git@github.com:', '').replace('.git', '')
    else:
        return None, None

    if '/' in repo_part:
        owner, repo = repo_part.split('/', 1)
        return owner, repo
    return None, None

def get_current_pr():
    """Get PR number for current branch"""
    branch = run_command("git branch --show-current")
    if not branch:
        return None

    # Try to get PR from gh CLI
    pr_data = run_command(["gh", "pr", "list", "--head", branch, "--json", "number,url"])
    if pr_data:
        try:
            prs = json.loads(pr_data)
            if prs and len(prs) > 0:
                return prs[0]['number'], prs[0]['url']
        except json.JSONDecodeError:
            pass

    return None, None

def get_pr_files(pr_number, limit=15):
    """Get recent changed files in PR"""
    if not pr_number:
        return []

    files_data = run_command(["gh", "pr", "view", str(pr_number), "--json", "files"])
    if not files_data:
        return []

    try:
        pr_info = json.loads(files_data)
        files = pr_info.get('files', [])

        # Sort by most additions + deletions (most active files)
        files.sort(key=lambda f: f.get('additions', 0) + f.get('deletions', 0), reverse=True)

        return files[:limit]
    except (json.JSONDecodeError, KeyError):
        return []

def get_ci_status(pr_number):
    """Get comprehensive CI status from GitHub"""
    if not pr_number:
        return []

    status_data = run_command(["gh", "pr", "view", str(pr_number), "--json", "statusCheckRollup"])
    if not status_data:
        return []

    try:
        pr_info = json.loads(status_data)
        checks = pr_info.get('statusCheckRollup', [])

        # Ensure we handle both list and dict responses
        if isinstance(checks, dict):
            checks = [checks]
        elif not isinstance(checks, list):
            return []

        return checks
    except (json.JSONDecodeError, KeyError):
        return []

def get_merge_status(pr_number):
    """Get merge state and conflict information"""
    if not pr_number:
        return {}

    merge_data = run_command(["gh", "pr", "view", str(pr_number), "--json", "mergeable,mergeableState,state"])
    if not merge_data:
        return {}

    try:
        return json.loads(merge_data)
    except json.JSONDecodeError:
        return {}

def get_pr_comments_via_mcp(owner, repo, pr_number):
    """Get PR comments via GitHub data (sourced from /commentfetch orchestration)"""
    # Comments data now provided by gstatus.md orchestration calling /commentfetch
    # This function serves as fallback for direct CLI access when needed

    # Fallback to gh CLI
    comments_data = run_command(["gh", "pr", "view", str(pr_number), "--json", "comments"])
    if not comments_data:
        return []

    try:
        pr_info = json.loads(comments_data)
        return pr_info.get('comments', [])
    except json.JSONDecodeError:
        return []

def get_review_status(pr_number):
    """Get review and comment status with enhanced comment fetching"""
    if not pr_number:
        return [], []

    # Get repository info for MCP calls
    owner, repo = get_repo_info()

    review_data = run_command(["gh", "pr", "view", str(pr_number), "--json", "reviews"])
    if not review_data:
        reviews = []
    else:
        try:
            pr_info = json.loads(review_data)
            reviews = pr_info.get('reviews', [])
            if not isinstance(reviews, list):
                reviews = []
        except (json.JSONDecodeError, KeyError):
            reviews = []

    # Get comments via MCP with fallback
    if owner and repo:
        comments = get_pr_comments_via_mcp(owner, repo, pr_number)
    else:
        comments = []

    return reviews, comments

def get_recent_commits(limit=3):
    """Get last N commits from remote branch"""
    branch = run_command("git branch --show-current")
    if not branch:
        return []

    # Get repository info for potential GitHub API calls
    owner, repo = get_repo_info()

    # Try GitHub API via gh CLI first
    if owner and repo:
        commits_data = run_command(["gh", "api", f"repos/{owner}/{repo}/commits", f"--field=sha={branch}", f"--field=per_page={limit}"])
        if commits_data:
            try:
                commits = json.loads(commits_data)
                return commits if isinstance(commits, list) else []
            except json.JSONDecodeError:
                pass

    # Fallback to git log
    git_commits = run_command(["git", "log", f"origin/{branch}", "--oneline", "-n", str(limit), "--pretty=format:%H|%an|%ad|%s", "--date=iso"])
    if not git_commits:
        return []

    commits = []
    for line in git_commits.split('\n'):
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) >= 4:
                commits.append({
                    'sha': parts[0][:7],
                    'author': {'name': parts[1]},
                    'commit': {
                        'author': {'date': parts[2]},
                        'message': parts[3]
                    }
                })

    return commits

def check_local_remote_diff():
    """Check differences between local and remote state"""
    branch = run_command("git branch --show-current")
    if not branch:
        return {}

    # Get ahead/behind status
    ahead_behind = run_command(["git", "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"])
    ahead, behind = 0, 0
    if ahead_behind and '	' in ahead_behind:
        try:
            behind, ahead = map(int, ahead_behind.split('\t'))
        except ValueError:
            pass

    # Get local changes
    status_output = run_command("git status --porcelain")
    staged_files = []
    modified_files = []
    untracked_files = []

    if status_output:
        for line in status_output.split('\n'):
            if len(line) >= 3:
                status = line[:2]
                filename = line[3:]

                if status[0] in 'MADRCU':  # Staged changes
                    staged_files.append(filename)
                elif status[1] in 'M':  # Modified not staged
                    modified_files.append(filename)
                elif status == '??':  # Untracked
                    untracked_files.append(filename)

    return {
        'ahead': ahead,
        'behind': behind,
        'staged_files': staged_files,
        'modified_files': modified_files,
        'untracked_files': untracked_files
    }

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, AttributeError):
        return timestamp_str

def format_file_changes(files):
    """Format file changes for display"""
    if not files:
        return "📁 **No file changes found**"

    output = ["📁 **Recent File Changes** (15 most active)"]
    output.append("")

    for i, file in enumerate(files, 1):
        filename = file.get('path', 'unknown')
        additions = file.get('additions', 0)
        deletions = file.get('deletions', 0)
        status = file.get('status', 'modified')

        # Status icons
        status_icon = {
            'added': '🆕',
            'modified': '📝',
            'removed': '🗑️',
            'renamed': '📋'
        }.get(status, '📝')

        change_summary = f"+{additions} -{deletions}" if additions or deletions else "no changes"

        output.append(f"{i:2d}. {status_icon} `{filename}` ({change_summary})")

    return "\n".join(output)

def format_ci_status(checks):
    """Format CI status for display"""
    if not checks:
        return "🔄 **No CI checks found**"

    output = ["🔄 **CI & Testing Status**"]
    output.append("")

    passing = failing = pending = 0

    for check in checks:
        if not isinstance(check, dict):
            continue

        name = check.get('context', check.get('name', 'unknown'))
        state = check.get('state', 'unknown').upper()
        description = check.get('description', '')
        url = check.get('targetUrl', check.get('url', ''))

        # State icons and counting
        if state in ['SUCCESS', 'COMPLETED']:
            icon = '✅'
            passing += 1
        elif state in ['FAILURE', 'ERROR', 'CANCELLED']:
            icon = '❌'
            failing += 1
        elif state in ['PENDING', 'IN_PROGRESS', 'QUEUED']:
            icon = '⏳'
            pending += 1
        else:
            icon = '❓'

        # Format output line
        status_line = f"{icon} **{name}**: {state}"
        if description:
            status_line += f" - {description}"
        if url:
            status_line += f" ([logs]({url}))"

        output.append(status_line)

    # Summary
    output.insert(1, f"**Summary**: {passing} passing, {failing} failing, {pending} pending")
    output.insert(2, "")

    return "\n".join(output)

def format_merge_status(merge_info):
    """Format merge status for display"""
    if not merge_info:
        return "🔀 **Merge status unavailable**"

    output = ["🔀 **Merge State**"]
    output.append("")

    mergeable = merge_info.get('mergeable')
    mergeable_state = merge_info.get('mergeableState', 'unknown')
    pr_state = merge_info.get('state', 'unknown')

    # Merge status icon
    if mergeable:
        merge_icon = '✅'
        merge_text = 'Ready to merge'
    elif mergeable is False:
        merge_icon = '❌'
        merge_text = 'Cannot merge'
    else:
        merge_icon = '❓'
        merge_text = 'Merge status unknown'

    output.append(f"{merge_icon} **Mergeable**: {merge_text}")
    output.append(f"📊 **State**: {pr_state.upper()}")
    output.append(f"🎯 **Merge State**: {mergeable_state.upper()}")

    # Conflict details
    if mergeable_state == 'CONFLICTING':
        output.append("")
        output.append("⚠️ **Merge conflicts detected** - use `/fixpr` to resolve")
    elif mergeable_state == 'BLOCKED':
        output.append("")
        output.append("🚫 **Merge blocked** - check required status checks and reviews")

    return "\n".join(output)

def format_recent_commits(commits):
    """Format recent commits for display"""
    if not commits:
        return "📝 **No recent commits found**"

    output = ["📝 **Recent Commits** (3 most recent)"]
    output.append("")

    for i, commit in enumerate(commits, 1):
        if not isinstance(commit, dict):
            continue

        sha = commit.get('sha', 'unknown')[:7]
        author_info = commit.get('author') or {}
        author_name = author_info.get('name') or commit.get('commit', {}).get('author', {}).get('name', 'unknown')
        date_str = commit.get('commit', {}).get('author', {}).get('date', '')
        message = commit.get('commit', {}).get('message', commit.get('message', 'No message'))

        # Format timestamp
        formatted_date = format_timestamp(date_str)

        # Truncate long commit messages
        if len(message) > 80:
            message = message[:80] + '...'

        output.append(f"{i}. **{sha}** by {author_name} ({formatted_date})")
        output.append(f"   {message}")

        if i < len(commits):
            output.append("")

    return "\n".join(output)

def format_local_remote_diff(diff_info):
    """Format local vs remote differences"""
    if not diff_info:
        return "🔄 **Local/Remote sync status unavailable**"

    output = ["🔄 **Local vs Remote Status**"]
    output.append("")

    ahead = diff_info.get('ahead', 0)
    behind = diff_info.get('behind', 0)
    staged = diff_info.get('staged_files', [])
    modified = diff_info.get('modified_files', [])
    untracked = diff_info.get('untracked_files', [])

    # Sync status
    if ahead == 0 and behind == 0:
        sync_icon = '✅'
        sync_text = 'In sync with remote'
    elif ahead > 0 and behind == 0:
        sync_icon = '⬆️'
        sync_text = f'Ahead by {ahead} commit(s)'
    elif ahead == 0 and behind > 0:
        sync_icon = '⬇️'
        sync_text = f'Behind by {behind} commit(s)'
    else:
        sync_icon = '🔄'
        sync_text = f'Diverged: {ahead} ahead, {behind} behind'

    output.append(f"{sync_icon} **Sync Status**: {sync_text}")

    # Local changes
    total_changes = len(staged) + len(modified) + len(untracked)
    if total_changes > 0:
        output.append(f"📋 **Local Changes**: {total_changes} file(s)")

        if staged:
            output.append(f"  • 🟢 **Staged**: {len(staged)} file(s)")
        if modified:
            output.append(f"  • 🟡 **Modified**: {len(modified)} file(s)")
        if untracked:
            output.append(f"  • ⚪ **Untracked**: {len(untracked)} file(s)")
    else:
        output.append("📋 **Local Changes**: Clean working directory")

    return "\n".join(output)

def format_review_status(reviews, comments):
    """Format review and comment status with enhanced comment display"""
    output = ["👥 **Review & Comments Status**"]
    output.append("")

    if not reviews and not comments:
        output.append("📝 No reviews or comments")
        return "\n".join(output)

    # Process reviews
    approved = requested_changes = pending = 0
    review_details = []

    for review in reviews:
        if not isinstance(review, dict):
            continue

        state = review.get('state', 'unknown')
        author = review.get('user', {}).get('login', 'unknown')

        if state == 'APPROVED':
            approved += 1
            review_details.append(f"✅ **@{author}**: Approved")
        elif state == 'CHANGES_REQUESTED':
            requested_changes += 1
            review_details.append(f"❌ **@{author}**: Changes requested")
        elif state == 'REVIEW_REQUESTED':
            pending += 1
            review_details.append(f"⏳ **@{author}**: Review pending")
        elif state == 'COMMENTED':
            review_details.append(f"💬 **@{author}**: Commented")

    # Summary
    if review_details:
        output.append(f"**Summary**: {approved} approved, {requested_changes} changes requested, {pending} pending")
        output.append("")
        output.extend(review_details)

    # Enhanced comments display (show last 10 instead of 5)
    if comments:
        output.append("")
        output.append("💬 **Recent Comments** (10 most recent)")
        recent_comments = sorted(comments, key=lambda c: c.get('createdAt', ''), reverse=True)[:10]

        for i, comment in enumerate(recent_comments, 1):
            if not isinstance(comment, dict):
                continue

            author = comment.get('user', {}).get('login', 'unknown')
            body = comment.get('body', '')
            created_at = comment.get('createdAt', '')

            # Enhanced truncation (150 chars instead of 100)
            display_body = body[:150]
            if len(body) > 150:
                display_body += '...'

            # Format timestamp
            formatted_time = format_timestamp(created_at)

            output.append(f"  {i:2d}. **@{author}** ({formatted_time}): {display_body}")

    return "\n".join(output)

def generate_action_items(merge_info, checks, reviews, diff_info):
    """Generate prioritized action items for mergeability"""
    action_items = []

    # Check local/remote sync first
    if diff_info:
        ahead = diff_info.get('ahead', 0)
        behind = diff_info.get('behind', 0)
        staged = diff_info.get('staged_files', [])
        modified = diff_info.get('modified_files', [])

        if behind > 0:
            action_items.append(f"⬇️ **Pull remote changes** - branch is {behind} commit(s) behind")

        if staged or modified:
            action_items.append("💾 **Commit local changes** - uncommitted work detected")

        if ahead > 0 and not staged and not modified:
            action_items.append(f"⬆️ **Push local commits** - {ahead} commit(s) ready to push")

    # Check for failing CI
    failing_checks = []
    for check in checks:
        if isinstance(check, dict) and check.get('state') in ['FAILURE', 'ERROR']:
            failing_checks.append(check.get('context', check.get('name', 'unknown')))

    if failing_checks:
        action_items.append(f"🔧 **Fix failing CI checks**: {', '.join(failing_checks)}")

    # Check for merge conflicts
    if merge_info.get('mergeableState') == 'CONFLICTING':
        action_items.append("⚔️ **Resolve merge conflicts** - run `/fixpr` for assistance")

    # Check for requested changes
    changes_requested = any(
        review.get('state') == 'CHANGES_REQUESTED'
        for review in reviews
        if isinstance(review, dict)
    )
    if changes_requested:
        action_items.append("📝 **Address review feedback** - check comments above")

    # Check for pending reviews
    pending_reviews = any(
        review.get('state') == 'REVIEW_REQUESTED'
        for review in reviews
        if isinstance(review, dict)
    )
    if pending_reviews:
        action_items.append("⏳ **Waiting for review approval** - ping reviewers if needed")

    if not action_items:
        if merge_info.get('mergeable'):
            action_items.append("🎉 **Ready to merge!** - All checks passed")
        else:
            action_items.append("🔍 **Check GitHub for specific merge requirements**")

    return action_items

def main():
    """Main status command execution"""
    print("🔍 **Fetching comprehensive PR status...**")
    print("")

    # Get repository and PR information
    owner, repo = get_repo_info()
    if not owner or not repo:
        print("❌ **Error**: Could not determine repository information")
        print("Make sure you're in a git repository with GitHub remote")
        return 1

    pr_number, pr_url = get_current_pr()
    if not pr_number:
        print(f"❌ **No PR found** for current branch")
        print("Create a PR first or switch to a branch with an existing PR")
        return 1

    print(f"📋 **PR #{pr_number}**: {pr_url}")
    print(f"📦 **Repository**: {owner}/{repo}")
    print("")

    # Gather all PR data including new features
    files = get_pr_files(pr_number)
    checks = get_ci_status(pr_number)
    merge_info = get_merge_status(pr_number)
    reviews, comments = get_review_status(pr_number)
    recent_commits = get_recent_commits()
    diff_info = check_local_remote_diff()

    # Display formatted sections
    print(format_file_changes(files))
    print("")
    print(format_ci_status(checks))
    print("")
    print(format_merge_status(merge_info))
    print("")
    print(format_recent_commits(recent_commits))
    print("")
    print(format_local_remote_diff(diff_info))
    print("")
    print(format_review_status(reviews, comments))
    print("")

    # Generate enhanced action items
    action_items = generate_action_items(merge_info, checks, reviews, diff_info)
    print("🎯 **Action Items**")
    print("")
    for item in action_items:
        print(f"  • {item}")

    print("")
    print("💡 **Next Steps**: Use `/fixpr` to automatically resolve issues")

    return 0

if __name__ == "__main__":
    sys.exit(main())
