"""
Tests for per-PR attempt limit logic

Verifies that only FAILURES count against the limit, not successful attempts.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


class TestAttemptLimitLogic(unittest.TestCase):
    """Test that attempt limits only count failures, not successes"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.safety_manager = AutomationSafetyManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_successful_attempts_dont_count_against_limit(self):
        """Successful attempts should not count against pr_limit"""
        # Create 15 successful attempts (pr_limit is 10 by default)
        pr_attempts = {
            "r=test/repo||p=123||b=main": [
                {"result": "success", "timestamp": f"2026-01-0{i}T12:00:00"}
                for i in range(1, 10)
            ] + [
                {"result": "success", "timestamp": f"2026-01-{i}T12:00:00"}
                for i in range(10, 16)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should still be able to process (15 successes, 0 failures)
        can_process = self.safety_manager.can_process_pr(123, repo="test/repo", branch="main")
        self.assertTrue(can_process, "Should allow processing with 15 successful attempts")

    def test_failure_limit_blocks_processing(self):
        """10 failures should block processing"""
        # Create 10 failed attempts (exactly at limit)
        pr_attempts = {
            "r=test/repo||p=456||b=main": [
                {"result": "failure", "timestamp": f"2026-01-0{i}T12:00:00"}
                for i in range(1, 10)
            ] + [{"result": "failure", "timestamp": "2026-01-10T12:00:00"}]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should be blocked (10 failures)
        can_process = self.safety_manager.can_process_pr(456, repo="test/repo", branch="main")
        self.assertFalse(can_process, "Should block processing with 10 failed attempts")

    def test_mixed_attempts_only_count_failures(self):
        """Mixed success/failure attempts should only count failures"""
        # Create 20 total attempts: 15 successes + 5 failures
        pr_attempts = {
            "r=test/repo||p=789||b=main": [
                {"result": "success", "timestamp": f"2026-01-0{i}T12:00:00"}
                for i in range(1, 10)
            ] + [
                {"result": "success", "timestamp": f"2026-01-{i}T12:00:00"}
                for i in range(10, 16)
            ] + [
                {"result": "failure", "timestamp": f"2026-01-{i}T13:00:00"}
                for i in range(16, 21)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should still be able to process (20 total, but only 5 failures)
        can_process = self.safety_manager.can_process_pr(789, repo="test/repo", branch="main")
        self.assertTrue(can_process, "Should allow processing with 5 failures out of 20 attempts")

    def test_consecutive_failures_block_early(self):
        """10 consecutive failures should block even if total failures < limit"""
        # Create 5 successes followed by 10 consecutive failures
        pr_attempts = {
            "r=test/repo||p=999||b=main": [
                {"result": "success", "timestamp": f"2026-01-0{i}T12:00:00"}
                for i in range(1, 6)
            ] + [
                {"result": "failure", "timestamp": f"2026-01-0{i}T13:00:00"}
                for i in range(6, 10)
            ] + [
                {"result": "failure", "timestamp": f"2026-01-{i}T13:00:00"}
                for i in range(10, 16)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should be blocked (10 consecutive failures)
        can_process = self.safety_manager.can_process_pr(999, repo="test/repo", branch="main")
        self.assertFalse(can_process, "Should block processing with 10 consecutive failures")

    def test_success_resets_consecutive_failure_streak_under_total_limit(self):
        """A success should reset consecutive failures when total failures stay under the limit."""
        # Create 8 failures, then 1 success, then 1 more failure.
        # Total failures = 9 (< 10 default limit), consecutive failures = 1.
        pr_attempts = {
            "r=test/repo||p=111||b=main": [
                {"result": "failure", "timestamp": f"2026-01-0{i}T12:00:00"}
                for i in range(1, 9)
            ] + [
                {"result": "success", "timestamp": "2026-01-10T12:00:00"}
            ] + [
                {"result": "failure", "timestamp": f"2026-01-{i}T13:00:00"}
                for i in range(11, 12)
            ]
        }

        attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        with open(attempts_file, "w") as f:
            json.dump(pr_attempts, f)

        # Should still be able to process (9 total failures, 1 consecutive)
        can_process = self.safety_manager.can_process_pr(111, repo="test/repo", branch="main")
        self.assertTrue(can_process, "Should allow processing after success resets consecutive failures")


if __name__ == "__main__":
    unittest.main()
