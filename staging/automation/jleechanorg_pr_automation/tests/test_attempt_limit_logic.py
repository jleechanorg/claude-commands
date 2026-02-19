"""
Tests for per-PR attempt limit logic

NEW BEHAVIOR: Counts ALL attempts (success + failure) against the limit.
This enables iterative improvements by allowing multiple successful runs.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


class TestAttemptLimitLogic(unittest.TestCase):
    """Test that attempt limits count ALL attempts (success + failure)"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.safety_manager = AutomationSafetyManager(data_dir=self.test_dir)
        # Note: Default pr_limit is now 50

    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_all_attempts_count_against_limit(self):
        """All attempts (success + failure) count against pr_limit"""
        # Create 50 successful attempts with TODAY's date (exactly at pr_limit=50 default)
        # Use valid ISO timestamps (hours 0-23, wrap using modulo)
        today = datetime.now(timezone.utc).date().isoformat()
        pr_attempts = {
            "r=test/repo||p=123||b=main": [
                {"result": "success", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(0, 50)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should be blocked (50 attempts = limit)
        can_process = self.safety_manager.can_process_pr(123, repo="test/repo", branch="main")
        self.assertFalse(can_process, "Should block processing at 50 total attempts")

    def test_failure_limit_blocks_processing(self):
        """50 failures should block processing (pr_limit=50)"""
        # Create 50 failed attempts with TODAY's date (exactly at limit)
        # Use valid ISO timestamps (hours 0-23, wrap using modulo)
        today = datetime.now(timezone.utc).date().isoformat()
        pr_attempts = {
            "r=test/repo||p=456||b=main": [
                {"result": "failure", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(0, 50)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should be blocked (50 failures = limit)
        can_process = self.safety_manager.can_process_pr(456, repo="test/repo", branch="main")
        self.assertFalse(can_process, "Should block processing with 50 failed attempts")

    def test_mixed_attempts_count_all(self):
        """Mixed success/failure attempts all count toward limit"""
        # Create 50 total attempts: 30 successes + 20 failures with TODAY's date
        # Use valid ISO timestamps (hours 0-23, use minutes to differentiate)
        today = datetime.now(timezone.utc).date().isoformat()
        pr_attempts = {
            "r=test/repo||p=789||b=main": [
                {"result": "success", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(0, 30)
            ] + [
                {"result": "failure", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(30, 50)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should be blocked (50 total attempts = limit)
        can_process = self.safety_manager.can_process_pr(789, repo="test/repo", branch="main")
        self.assertFalse(can_process, "Should block processing with 50 total attempts")

    def test_under_limit_allows_processing(self):
        """Under the limit (49 attempts) should allow processing"""
        # Create 49 attempts (1 under limit) with TODAY's date
        # Use valid ISO timestamps (hours 0-23, use minutes to differentiate)
        today = datetime.now(timezone.utc).date().isoformat()
        pr_attempts = {
            "r=test/repo||p=999||b=main": [
                {"result": "success", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(0, 29)
            ] + [
                {"result": "failure", "timestamp": f"{today}T{i % 24:02d}:{(i // 24) % 60:02d}:00Z"}
                for i in range(29, 49)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should allow processing (49 < 50 limit)
        can_process = self.safety_manager.can_process_pr(999, repo="test/repo", branch="main")
        self.assertTrue(can_process, "Should allow processing with 49 total attempts")

    def test_no_attempts_allows_processing(self):
        """No attempts should allow processing"""
        # Empty attempts
        pr_attempts = {}

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should allow processing (0 attempts)
        can_process = self.safety_manager.can_process_pr(111, repo="test/repo", branch="main")
        self.assertTrue(can_process, "Should allow processing with 0 attempts")


if __name__ == "__main__":
    unittest.main()
