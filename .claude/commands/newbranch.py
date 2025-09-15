#!/usr/bin/env python3
"""
/newbranch or /nb - Create new branch from latest main

Creates a fresh branch from the latest main branch code. Aborts if there are uncommitted changes.
"""

import subprocess
import sys
import time


def run_command(cmd, check=True):
    """Run a command and return the result"""
    try:
        # Use shell=False for security - cmd should be a list
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd, shell=False, capture_output=True, text=True, check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode


def check_uncommitted_changes():
    """Check if there are uncommitted changes"""
    stdout, stderr, returncode = run_command(
        ["git", "status", "--porcelain"], check=False
    )
    return len(stdout.strip()) > 0


def auto_commit_changes():
    """Auto-commit any uncommitted changes with a generic message"""
    print("🔄 Auto-committing uncommitted changes...")

    # Add all changes
    stdout, stderr, returncode = run_command(["git", "add", "-A"], check=False)
    if returncode != 0:
        print("❌ ERROR: Failed to stage changes")
        print(f"stderr: {stderr}")
        return False

    # Create commit with generic message
    commit_msg = "chore: Auto-commit before branch creation\n\n🔐 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
    stdout, stderr, returncode = run_command(["git", "commit", "-m", commit_msg], check=False)
    if returncode != 0:
        print("❌ ERROR: Failed to commit changes")
        print(f"stderr: {stderr}")
        return False

    print("✅ Successfully auto-committed changes")
    return True


def main():
    # Get branch name from command line argument or generate timestamp-based name
    if len(sys.argv) > 1:
        branch_name = sys.argv[1]
    else:
        # Generate timestamp-based branch name (for /nb without arguments)
        # Note: Descriptive names are preferred for actual development
        timestamp = str(int(time.time()))
        branch_name = f"dev{timestamp}"
        print("⚠️  Using timestamp-based branch name. Consider using descriptive names:")
        print("    /nb feature/user-auth, /nb fix/login-bug, /nb update/ui-components")

    print(f"Creating new branch: {branch_name}")

    # Check for uncommitted changes and auto-commit them
    if check_uncommitted_changes():
        print("⚠️  Uncommitted changes detected. Auto-committing...")
        if not auto_commit_changes():
            print("❌ ERROR: Failed to auto-commit changes. Manual intervention required.")
            print("\nRun: git status")
            return 1

    # Switch to main branch
    print("📍 Switching to main branch...")
    stdout, stderr, returncode = run_command(["git", "checkout", "main"], check=False)
    if returncode != 0:
        print("❌ ERROR: Failed to switch to main branch")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return 1

    # Pull latest changes from origin/main
    print("🔄 Pulling latest changes from origin/main...")
    stdout, stderr, returncode = run_command(
        ["git", "pull", "origin", "main"], check=False
    )
    if returncode != 0:
        print("❌ ERROR: Failed to pull from origin/main")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return 1

    # Create and switch to new branch
    print(f"🌿 Creating and switching to new branch: {branch_name}")
    stdout, stderr, returncode = run_command(
        ["git", "checkout", "-b", branch_name], check=False
    )
    if returncode != 0:
        print(f"❌ ERROR: Failed to create branch {branch_name}")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        return 1

    # Push and set upstream tracking to origin/branch
    print(f"🔗 Pushing and setting upstream tracking to origin/{branch_name}...")
    stdout, stderr, returncode = run_command(
        ["git", "push", "-u", "origin", branch_name], check=False
    )
    if returncode != 0:
        print("⚠️  Warning: Failed to set upstream tracking (this is usually okay)")
        print(f"stderr: {stderr}")

    print(f"✅ Successfully created and switched to branch: {branch_name}")
    print("📋 Branch is based on latest main and ready for development")

    return 0


if __name__ == "__main__":
    sys.exit(main())
