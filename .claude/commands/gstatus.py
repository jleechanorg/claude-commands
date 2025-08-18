#!/usr/bin/env python3
"""
/gstatus command - Comprehensive PR status dashboard

Shows complete PR overview including files, CI status, merge conflicts, and GitHub state.
Integrates with /header and provides authoritative GitHub data.
"""

import json
import subprocess
import sys

def run_command(cmd, capture_output=True, shell=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return None

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
    pr_data = run_command(f'gh pr list --head "{branch}" --json number,url')
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
    
    files_data = run_command(f'gh pr view {pr_number} --json files')
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
    
    status_data = run_command(f'gh pr view {pr_number} --json statusCheckRollup')
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
    
    merge_data = run_command(f'gh pr view {pr_number} --json mergeable,mergeableState,state')
    if not merge_data:
        return {}
    
    try:
        return json.loads(merge_data)
    except json.JSONDecodeError:
        return {}

def get_review_status(pr_number):
    """Get review and comment status"""
    if not pr_number:
        return [], []
    
    review_data = run_command(f'gh pr view {pr_number} --json reviews,comments')
    if not review_data:
        return [], []
    
    try:
        pr_info = json.loads(review_data)
        reviews = pr_info.get('reviews', [])
        comments = pr_info.get('comments', [])
        
        # Ensure we handle list responses
        if not isinstance(reviews, list):
            reviews = []
        if not isinstance(comments, list):
            comments = []
            
        return reviews, comments
    except (json.JSONDecodeError, KeyError):
        return [], []

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

def format_review_status(reviews, comments):
    """Format review and comment status"""
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
    
    # Recent comments (limit to 5 most recent)
    if comments:
        output.append("")
        output.append("💬 **Recent Comments** (5 most recent)")
        recent_comments = sorted(comments, key=lambda c: c.get('createdAt', ''), reverse=True)[:5]
        
        for comment in recent_comments:
            if not isinstance(comment, dict):
                continue
                
            author = comment.get('user', {}).get('login', 'unknown')
            body = comment.get('body', '')[:100]  # Truncate long comments
            if len(comment.get('body', '')) > 100:
                body += '...'
            
            output.append(f"  • **@{author}**: {body}")
    
    return "\n".join(output)

def generate_action_items(merge_info, checks, reviews):
    """Generate prioritized action items for mergeability"""
    action_items = []
    
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
    
    # Gather all PR data
    files = get_pr_files(pr_number)
    checks = get_ci_status(pr_number)
    merge_info = get_merge_status(pr_number)
    reviews, comments = get_review_status(pr_number)
    
    # Display formatted sections
    print(format_file_changes(files))
    print("")
    print(format_ci_status(checks))
    print("")
    print(format_merge_status(merge_info))
    print("")
    print(format_review_status(reviews, comments))
    print("")
    
    # Generate action items
    action_items = generate_action_items(merge_info, checks, reviews)
    print("🎯 **Action Items**")
    print("")
    for item in action_items:
        print(f"  • {item}")
    
    print("")
    print("💡 **Next Steps**: Use `/fixpr` to automatically resolve issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())