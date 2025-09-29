#!/usr/bin/env python3
"""Test to reproduce the automation skip logic issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from jleechanorg_pr_monitor import JleechanorgPRMonitor

def test_automation_skip_behavior():
    """Test that automation incorrectly reports success when skipping PRs"""
    print("🔴 Testing automation skip logic issue...")

    os.environ['ASSISTANT_HANDLE'] = 'claude'
    os.environ['CODEX_COMMENT'] = 'Please help review and fix any issues with this PR.'

    monitor = JleechanorgPRMonitor()

    # Get one PR that would be skipped
    eligible_prs = monitor.find_eligible_prs(limit=1)
    if not eligible_prs:
        print("❌ No eligible PRs found")
        return False

    pr = eligible_prs[0]
    repo_full = pr.get('repositoryFullName', 'unknown')
    pr_number = pr.get('number', 'unknown')

    print(f"📝 Testing PR: {repo_full}#{pr_number}")

    # Run the comment posting method twice
    print("\n🔄 First run (should post comment):")
    result1 = monitor.post_codex_instruction_simple(repo_full, pr_number, pr)
    print(f"Result 1: {result1}")

    print("\n🔄 Second run (should skip but still report success):")
    result2 = monitor.post_codex_instruction_simple(repo_full, pr_number, pr)
    print(f"Result 2: {result2}")

    # The issue: both runs return True, but second run doesn't post comment
    if result1 and result2:
        print("\n🔴 ISSUE REPRODUCED: Both runs return True but second run skips posting")
        print("❌ Automation reports false success when skipping PRs")
        return True
    else:
        print("\n✅ No issue found")
        return False

if __name__ == "__main__":
    print("=== AUTOMATION SKIP LOGIC ISSUE REPRODUCTION ===")
    issue_found = test_automation_skip_behavior()

    if issue_found:
        print("\n🔴 RED PHASE COMPLETE: False success reporting issue reproduced")
    else:
        print("\n❌ Could not reproduce the issue")

    sys.exit(0)
