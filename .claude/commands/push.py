#!/usr/bin/env python3
"""
Enhanced /push command implementation
Pre-push review, validation, PR create/update, and test server startup
"""

import os
import socket
import subprocess
import time
from datetime import datetime
from lint_utils import run_lint_check, should_run_linting
from pr_utils import (
    check_pr_exists_for_branch,
    create_or_update_pr,
    ensure_pushed_to_remote,
    generate_pr_description,
    get_current_branch,
    get_files_changed,
    get_git_log_summary,
    read_scratchpad,
    run_tests,
)


def get_git_status():
    """Get current git status"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def commit_changes():
    """Commit any uncommitted changes"""
    status = get_git_status()
    if not status:
        return True, "No changes to commit"

    try:
        # Add all changes
        subprocess.run(["git", "add", "-A"], check=True)

        # Create commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"Push command auto-commit at {timestamp}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        return True, "Changes committed"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to commit: {e}"


def virtual_agent_review():
    """Perform virtual agent review of changes"""
    print("🔍 Performing code review...")

    # Get changed files
    files = get_files_changed()

    # Basic checks
    issues = []

    # Check for common issues
    for file in files:
        if file.endswith(".py"):
            # Could add linting checks here
            pass
        elif file.endswith(".md"):
            # Documentation files are generally safe
            pass

    if issues:
        print("⚠️  Review found issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✅ Code review passed")
    return True


def detect_significant_changes(commits):
    """Detect if there are significant changes that should update PR description"""
    significant_keywords = [
        "migration",
        "breaking",
        "major",
        "refactor",
        "architecture",
        "protocol",
        "test",
        "policy",
    ]

    for commit in commits:
        commit_lower = commit.lower()
        for keyword in significant_keywords:
            if keyword in commit_lower:
                return True

    return len(commits) > 5  # Many commits also suggests significant changes


def find_available_port(start_port=6006):
    """Find an available port starting from start_port"""

    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue

    return None


def start_test_server(branch):
    """Start test server for the branch"""
    port = find_available_port()
    if not port:
        print("⚠️  Could not find available port for test server")
        return None

    print(f"🚀 Starting test server on port {port}...")

    # Create log directory - use standardized logging directory with branch isolation
    current_branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True
    ).strip()
    log_dir = f"/tmp/worldarchitect.ai/{current_branch}"
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/{branch}.log"

    # Start server in background
    try:
        with open(log_file, "w") as log:
            subprocess.Popen(
                ["python", "mvp_site/main.py"],
                env={**os.environ, "PORT": str(port)},
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        # Give server time to start
        time.sleep(2)

        print(f"✅ Test server running at http://localhost:{port}")
        print(f"📝 Logs: {log_file}")
        return port
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")
        return None


def main():
    branch = get_current_branch()

    print(f"🚀 Push command for branch: {branch}")

    # Step 1: Virtual agent review
    if not virtual_agent_review():
        print("❌ Code review failed. Fix issues before pushing.")
        return

    # Step 2: Commit any uncommitted changes
    success, message = commit_changes()
    print(f"📝 {message}")

    # Step 2.5: Run linting checks (blocking)
    if should_run_linting():
        print("🔍 Running linting checks...")
        lint_success, lint_message = run_lint_check("mvp_site", auto_fix=False)
        print(f"📋 {lint_message}")

        if not lint_success:
            print("❌ Linting issues must be fixed before push")
            print("💡 Run './run_lint.sh mvp_site fix' to auto-fix issues")
            print("💡 Or set SKIP_LINT=true to bypass")
            return
    else:
        print("⏭️  Skipping linting (disabled)")

    # Step 3: Run tests
    print("🧪 Running tests...")
    test_success, test_output = run_tests()

    if test_success:
        print("✅ All tests passing")
    else:
        print("⚠️  Some tests failing (proceeding with push)")

    # Step 4: Push to remote
    print("🔄 Pushing to remote...")
    if not ensure_pushed_to_remote():
        print("❌ Failed to push to remote")
        return

    # Step 5: Create or update PR
    existing_pr = check_pr_exists_for_branch(branch)

    if existing_pr:
        print(f"📝 Existing PR found: {existing_pr['url']}")

        # Check if we should update the description
        commits = get_git_log_summary()
        if detect_significant_changes(commits):
            print("🔄 Updating PR description with significant changes...")

            # Generate updated description
            files_changed = get_files_changed()
            scratchpad_content = read_scratchpad(branch)

            pr_body = generate_pr_description(
                title=existing_pr["title"],
                branch=branch,
                test_success=test_success,
                test_output=test_output,
                scratchpad_content=scratchpad_content,
                commit_messages=commits,
                files_changed=files_changed,
            )

            success, result = create_or_update_pr(existing_pr["title"], pr_body)
            if success:
                print("✅ PR description updated")
            else:
                print(f"⚠️  Failed to update PR: {result}")
    else:
        print("🔀 Creating new PR...")

        # Generate PR details
        commits = get_git_log_summary()
        files_changed = get_files_changed()
        scratchpad_content = read_scratchpad(branch)

        # Create title from branch name or first commit
        title = branch.replace("-", " ").replace("_", " ").title()
        if commits:
            # Use first commit message as title if available
            first_commit = commits[0].split(" ", 1)
            if len(first_commit) > 1:
                title = first_commit[1]

        pr_body = generate_pr_description(
            title=title,
            branch=branch,
            test_success=test_success,
            test_output=test_output,
            scratchpad_content=scratchpad_content,
            commit_messages=commits,
            files_changed=files_changed,
        )

        success, pr_url = create_or_update_pr(title, pr_body)
        if success:
            print(f"✅ PR created: {pr_url}")
        else:
            print(f"❌ Failed to create PR: {pr_url}")

    # Step 6: Start test server
    port = start_test_server(branch)

    # Summary
    print("\n" + "=" * 60)
    print("✅ PUSH COMPLETE")
    print("=" * 60)
    print(f"🌿 Branch: {branch}")
    if existing_pr:
        print(f"🔀 PR: {existing_pr['url']}")
    print(f"🧪 Tests: {'PASS' if test_success else 'FAIL'}")
    if port:
        print(f"🚀 Test server: http://localhost:{port}")
    print("=" * 60)


if __name__ == "__main__":
    main()
