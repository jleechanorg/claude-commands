#!/usr/bin/env python3
"""Test to verify the comment posting fix works."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from jleechanorg_pr_monitor import JleechanorgPRMonitor

def test_comment_posting_fix():
    """Test that automation correctly reports posted vs skipped"""
    print("🟢 Testing comment posting fix...")

    os.environ['ASSISTANT_HANDLE'] = 'claude'
    os.environ['CODEX_COMMENT'] = 'Testing automation fix - this comment should be posted.'

    monitor = JleechanorgPRMonitor()

    # Get one PR for testing
    eligible_prs = monitor.find_eligible_prs(limit=1)
    if not eligible_prs:
        print("❌ No eligible PRs found")
        return False

    pr = eligible_prs[0]
    repo_full = pr.get('repositoryFullName', 'unknown')
    pr_number = pr.get('number', 'unknown')

    print(f"📝 Testing PR: {repo_full}#{pr_number}")

    # Test the new return values
    print("\n🔄 First run (should post comment and return 'posted'):")
    result1 = monitor.post_codex_instruction_simple(repo_full, pr_number, pr)
    print(f"Result 1: '{result1}'")

    print("\n🔄 Second run (should skip and return 'skipped'):")
    result2 = monitor.post_codex_instruction_simple(repo_full, pr_number, pr)
    print(f"Result 2: '{result2}'")

    # Test the _process_pr_comment method
    print("\n🔄 Testing _process_pr_comment (should return False for skipped):")
    repo_name = repo_full.split('/')[-1]
    process_result = monitor._process_pr_comment(repo_name, pr_number, pr)
    print(f"Process result: {process_result}")

    # Verify the fix
    if result1 == "posted" and result2 == "skipped" and process_result == False:
        print("\n✅ FIX VERIFIED: Automation correctly distinguishes posted vs skipped")
        return True
    else:
        print(f"\n❌ FIX FAILED: Expected 'posted', 'skipped', False - got '{result1}', '{result2}', {process_result}")
        return False

if __name__ == "__main__":
    print("=== COMMENT POSTING FIX VERIFICATION ===")
    success = test_comment_posting_fix()

    if success:
        print("\n🟢 GREEN PHASE COMPLETE: Comment posting fix working correctly")
    else:
        print("\n❌ Fix verification failed")

    sys.exit(0 if success else 1)
