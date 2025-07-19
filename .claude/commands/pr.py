#!/usr/bin/env python3
"""
/pr command implementation
End-to-end implementation from idea to working pull request
"""

import os
import subprocess
import sys
from datetime import datetime

# Import shared utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pr_utils import (
    create_or_update_pr,
    ensure_pushed_to_remote,
    generate_pr_description,
    get_files_changed,
    get_git_log_summary,
    read_scratchpad,
)


def create_feature_branch(task_name):
    """Create feature branch for implementation"""
    branch_name = f"feature/{task_name}"
    try:
        # Ensure we're on main and up to date
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        return branch_name
    except subprocess.CalledProcessError:
        print(f"❌ Failed to create branch {branch_name}")
        return None


def validate_task_scope(task_description):
    """Validate that task scope is reasonable"""
    # Simple heuristic checks
    overly_broad_keywords = [
        "rewrite",
        "entire",
        "all",
        "everything",
        "complete overhaul",
    ]

    task_lower = task_description.lower()
    for keyword in overly_broad_keywords:
        if keyword in task_lower:
            return (
                False,
                "Task appears too broad. Consider breaking down into smaller tasks.",
            )

    return True, ""


def create_scratchpad(task_name, task_description, branch):
    """Create implementation scratchpad"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""# Implementation: {task_name.replace("_", " ").title()}

**Branch**: {branch}  
**Task**: {task_description}  
**Status**: In Progress  
**Created**: {timestamp}

## Task Description

{task_description}

## Implementation Plan

[This will be filled by the implementation agent]

## Changes Made

[This will be tracked during implementation]

## Testing

[Test details will be added here]

## Notes

This is an automated implementation using /pr command.
"""

    # Replace slashes in branch name for filename
    safe_branch = branch.replace("/", "-")
    filename = f"roadmap/scratchpad_{safe_branch}.md"
    os.makedirs("roadmap", exist_ok=True)
    with open(filename, "w") as f:
        f.write(content)

    return filename


def simulate_implementation_message(task_description):
    """Generate message for what implementation would do"""
    return f"""
🤖 **Implementation Plan for: {task_description}**

The /pr command would:
1. Analyze the codebase to understand current implementation
2. Plan the changes needed
3. Implement the solution following existing patterns
4. Write/update tests to cover new functionality  
5. Run all tests until they pass
6. Create a PR with comprehensive description

**Note**: Full implementation requires agent-based execution with proper context.
This is a preview of what would be done.
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: /pr [task_description]")
        print("Example: /pr 'Add user authentication to login page'")
        return

    task_description = " ".join(sys.argv[1:])

    print(f"🚀 Starting end-to-end implementation for: {task_description}")

    # Validate task scope
    valid, message = validate_task_scope(task_description)
    if not valid:
        print(f"⚠️  {message}")
        print("Consider using /handoff for complex planning tasks.")
        return

    # Generate task name from description
    task_name = task_description.lower().replace(" ", "_")[:30]
    task_name = "".join(c for c in task_name if c.isalnum() or c == "_")

    # Create feature branch
    print("📝 Creating feature branch...")
    branch = create_feature_branch(task_name)
    if not branch:
        return

    # Create scratchpad
    print("📋 Creating implementation scratchpad...")
    scratchpad_file = create_scratchpad(task_name, task_description, branch)

    # This is where the actual implementation would happen
    # For now, we'll simulate what would be done
    print("\n" + "=" * 60)
    print(simulate_implementation_message(task_description))
    print("=" * 60)

    # In a full implementation, this would:
    # 1. Call implementation agent to analyze and code
    # 2. Run tests iteratively until passing
    # 3. Generate comprehensive PR

    # For demonstration, let's create a sample PR
    print("\n📝 Preparing pull request...")

    # Commit scratchpad
    subprocess.run(["git", "add", scratchpad_file], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Start implementation: {task_description}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        ],
        check=True,
    )

    # Push branch
    print("🔄 Pushing branch...")
    if not ensure_pushed_to_remote():
        print("❌ Failed to push branch")
        return

    # Generate PR description
    commit_messages = get_git_log_summary()
    files_changed = get_files_changed()
    scratchpad_content = read_scratchpad(branch)

    pr_title = f"Implement: {task_description}"
    pr_body = generate_pr_description(
        title=pr_title,
        branch=branch,
        test_success=False,  # Would be set by actual test run
        test_output="Tests would be run during actual implementation",
        scratchpad_content=scratchpad_content,
        commit_messages=commit_messages,
        files_changed=files_changed,
        is_handoff=False,
    )

    # Create PR
    print("🔀 Creating pull request...")
    success, pr_url = create_or_update_pr(pr_title, pr_body, draft=True)

    if success:
        print("\n" + "=" * 60)
        print("✅ PR CREATED (Draft Mode)")
        print("=" * 60)
        print(f"🔀 PR URL: {pr_url}")
        print(f"📋 Scratchpad: {scratchpad_file}")
        print(f"🌿 Branch: {branch}")
        print("\n⚠️  Note: This is a demonstration PR. Full implementation")
        print("requires agent-based execution to actually write code and tests.")
    else:
        print(f"❌ Failed to create PR: {pr_url}")


if __name__ == "__main__":
    main()
