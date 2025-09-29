#!/usr/bin/env python3
"""Test to reproduce the comment posting issue."""

import subprocess
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation'))

from automation_utils import AutomationUtils

def test_gh_comment_posting():
    """Test if gh pr comment command works"""
    print("🔴 Testing GitHub CLI comment posting...")

    # Test with a simple command first to check authentication
    try:
        print("📋 Testing GitHub CLI authentication...")
        auth_result = AutomationUtils.execute_subprocess_with_timeout([
            "gh", "auth", "status"
        ], timeout=10, check=False)

        print(f"Auth status returncode: {auth_result.returncode}")
        if auth_result.returncode == 0:
            print("✅ GitHub CLI authenticated")
            print(f"Auth info: {auth_result.stderr[:200]}")
        else:
            print("❌ GitHub CLI not authenticated")
            print(f"Auth error: {auth_result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error checking auth: {e}")
        return False

    # Test comment posting on a real PR
    try:
        print("\n🧪 Testing comment posting on PR...")
        comment_cmd = [
            "gh", "pr", "comment", "1723",
            "--repo", "jleechanorg/worldarchitect.ai",
            "--body", "🧪 Test comment from automation debugging"
        ]

        print(f"Command: {' '.join(comment_cmd)}")

        result = AutomationUtils.execute_subprocess_with_timeout(
            comment_cmd, timeout=30, check=False
        )

        print(f"Comment post returncode: {result.returncode}")
        print(f"Comment post stdout: {result.stdout}")
        print(f"Comment post stderr: {result.stderr}")

        if result.returncode == 0:
            print("✅ Comment posted successfully!")
            return True
        else:
            print("❌ Comment posting failed")
            return False

    except Exception as e:
        print(f"❌ Exception during comment posting: {e}")
        return False

if __name__ == "__main__":
    print("=== COMMENT POSTING ISSUE REPRODUCTION ===")
    success = test_gh_comment_posting()

    if success:
        print("\n✅ Comment posting works - issue might be elsewhere")
    else:
        print("\n🔴 RED PHASE COMPLETE: Comment posting issue reproduced")

    sys.exit(0 if success else 1)
