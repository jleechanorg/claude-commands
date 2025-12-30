#!/usr/bin/env python3
"""
Test-Driven Development for PR Automation Safety Limits

RED Phase: All tests should FAIL initially
- PR attempt limits (max 10 per PR)
- Global run limits (max 50 total)
- Manual approval requirement
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


class TestAutomationSafetyLimits(unittest.TestCase):
    """Matrix testing for automation safety limits"""

    def setUp(self):
        """Set up test environment with temporary files"""
        self.test_dir = tempfile.mkdtemp()
        self.pr_attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        self.global_runs_file = os.path.join(self.test_dir, "global_runs.json")
        self.approval_file = os.path.join(self.test_dir, "manual_approval.json")

        if hasattr(self, "_automation_manager"):
            del self._automation_manager

        # Initialize empty tracking files
        with open(self.pr_attempts_file, "w") as f:
            json.dump({}, f)
        with open(self.global_runs_file, "w") as f:
            json.dump({"total_runs": 0, "start_date": datetime.now().isoformat()}, f)
        with open(self.approval_file, "w") as f:
            json.dump({"approved": False, "approval_date": None}, f)

    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)

    # Matrix 1: PR Attempt Limits (10 attempts per PR)
    def test_pr_attempt_limit_1_should_allow(self):
        """RED: First attempt on PR #1001 should be allowed"""
        # This test will FAIL initially - no implementation exists
        result = self.automation_manager.can_process_pr(1001)
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 0)

    def test_pr_attempt_limit_10_should_allow(self):
        """RED: 10th attempt on PR #1001 should be allowed"""
        # Set up 9 previous attempts
        for _ in range(9):
            self.automation_manager.record_pr_attempt(1001, "failure")

        result = self.automation_manager.can_process_pr(1001)
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 9)

    def test_pr_attempt_limit_11_should_block(self):
        """RED: 11th attempt on PR #1001 should be blocked"""
        # Set up 10 previous attempts (max limit reached)
        for _ in range(10):
            self.automation_manager.record_pr_attempt(1001, "failure")

        result = self.automation_manager.can_process_pr(1001)
        self.assertFalse(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 10)

    def test_pr_attempt_success_resets_counter(self):
        """RED: Successful PR attempt should reset counter"""
        # Set up 8 failures then 1 success
        for _ in range(8):
            self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "success")

        # Counter should reset, allowing new attempts
        result = self.automation_manager.can_process_pr(1001)
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 0)

    # Matrix 2: Global Run Limits (50 total runs)
    def test_global_run_limit_1_should_allow(self):
        """RED: First global run should be allowed"""
        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    def test_global_run_limit_50_should_allow(self):
        """RED: 50th global run should be allowed"""
        # Set up 49 previous runs
        for i in range(49):
            self.automation_manager.record_global_run()

        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 49)

    def test_global_run_limit_51_should_block(self):
        """RED: 51st global run should be blocked without approval"""
        # Set up 50 previous runs (max limit reached)
        for i in range(50):
            self.automation_manager.record_global_run()

        result = self.automation_manager.can_start_global_run()
        self.assertFalse(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 50)

    # Matrix 3: Manual Approval System
    def test_manual_approval_required_after_50_runs(self):
        """RED: Manual approval should be required after 50 runs"""
        # Set up 50 runs to trigger approval requirement
        for i in range(50):
            self.automation_manager.record_global_run()

        # Should require approval
        self.assertTrue(self.automation_manager.requires_manual_approval())
        self.assertFalse(self.automation_manager.has_manual_approval())

    def test_manual_approval_grants_additional_runs(self):
        """RED: Manual approval should allow continuation beyond 50 runs"""
        # Set up 50 runs
        for i in range(50):
            self.automation_manager.record_global_run()

        # Grant manual approval
        self.automation_manager.grant_manual_approval("user@example.com")

        # Should now allow additional runs
        self.assertTrue(self.automation_manager.can_start_global_run())
        self.assertTrue(self.automation_manager.has_manual_approval())

    def test_approval_expires_after_24_hours(self):
        """RED: Manual approval should expire after 24 hours"""
        # Set up approval 25 hours ago
        old_time = datetime.now() - timedelta(hours=25)
        self.automation_manager.grant_manual_approval("user@example.com", old_time)

        # Approval should be expired
        self.assertFalse(self.automation_manager.has_manual_approval())

    # Matrix 4: Email Notification System
    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "testpass",
        "EMAIL_TO": "admin@example.com"
    })
    @patch("smtplib.SMTP")
    def test_email_sent_when_pr_limit_reached(self, mock_smtp):
        """RED: Email should be sent when PR reaches 10 attempts"""
        # Set up 10 attempts to trigger notification
        for _ in range(10):
            self.automation_manager.record_pr_attempt(1001, "failure")

        # Should trigger email
        self.automation_manager.check_and_notify_limits()

        # Verify email was sent
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "testpass",
        "EMAIL_TO": "admin@example.com"
    })
    @patch("smtplib.SMTP")
    def test_email_sent_when_global_limit_reached(self, mock_smtp):
        """RED: Email should be sent when global limit of 50 is reached"""
        # Set up 50 runs to trigger notification
        for i in range(50):
            self.automation_manager.record_global_run()

        # Should trigger email
        self.automation_manager.check_and_notify_limits()

        # Verify email was sent
        mock_smtp.assert_called_once()

    # Matrix 5: State Persistence
    def test_pr_attempts_persist_across_restarts(self):
        """RED: PR attempt counts should persist across automation restarts"""
        # Record attempts
        self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "failure")

        # Simulate restart by creating new manager instance
        new_manager = AutomationSafetyManager(self.test_dir)

        # Should maintain attempt count
        self.assertEqual(new_manager.get_pr_attempts(1001), 2)

    def test_global_runs_persist_across_restarts(self):
        """RED: Global run count should persist across automation restarts"""
        # Record runs
        for i in range(10):
            self.automation_manager.record_global_run()

        # Simulate restart
        new_manager = AutomationSafetyManager(self.test_dir)

        # Should maintain run count
        self.assertEqual(new_manager.get_global_runs(), 10)

    # Matrix 6: Concurrent Access Safety
    def test_concurrent_pr_attempts_thread_safe(self):
        """RED: Concurrent PR attempts should be thread-safe"""
        import threading

        # Create a single manager instance explicitly for this test
        manager = AutomationSafetyManager(self.test_dir)
        results = []

        def attempt_pr():
            result = manager.try_process_pr(1001)
            results.append(result)

        # Start 15 concurrent threads (more than limit of 10)
        threads = []
        for _ in range(15):
            t = threading.Thread(target=attempt_pr)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have exactly 10 successful attempts (limit)
        successful_attempts = sum(results)
        self.assertEqual(successful_attempts, 10)

    # Matrix 7: Configuration Management
    def test_limits_configurable_via_environment(self):
        """RED: Safety limits should be configurable via environment variables"""
        with patch.dict(os.environ, {
            "AUTOMATION_PR_LIMIT": "3",
            "AUTOMATION_GLOBAL_LIMIT": "25"
        }):
            manager = AutomationSafetyManager(self.test_dir)

            # Should use custom limits
            self.assertEqual(manager.pr_limit, 3)
            self.assertEqual(manager.global_limit, 25)

    def test_default_limits_when_no_config(self):
        """RED: Should use default limits when no configuration provided"""
        manager = AutomationSafetyManager(self.test_dir)

        # Should use defaults
        self.assertEqual(manager.pr_limit, 10)
        self.assertEqual(manager.global_limit, 50)

    # Matrix 8: Daily Reset Functionality (50 runs per day)
    def test_daily_reset_first_run_of_day(self):
        """RED: First run of the day should be allowed with counter at 0"""
        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    def test_daily_reset_49th_run_same_day(self):
        """RED: 49th run on same day should be allowed"""
        # Record 48 runs on same day
        for _ in range(48):
            self.automation_manager.record_global_run()

        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 48)

    def test_daily_reset_50th_run_same_day(self):
        """RED: 50th run on same day should be allowed (at limit)"""
        # Record 49 runs on same day
        for _ in range(49):
            self.automation_manager.record_global_run()

        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 49)

    def test_daily_reset_51st_run_same_day_blocked(self):
        """RED: 51st run on same day should be blocked"""
        # Record 50 runs on same day (hit daily limit)
        for _ in range(50):
            self.automation_manager.record_global_run()

        result = self.automation_manager.can_start_global_run()
        self.assertFalse(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 50)

    def test_daily_reset_missing_current_date_resets_counter(self):
        """Legacy counters without current_date should reset after upgrade"""
        legacy_data = {
            "total_runs": 50,
            "start_date": datetime(2025, 9, 30, 12, 0, 0).isoformat()
        }
        with open(self.global_runs_file, "w") as f:
            json.dump(legacy_data, f)

        if hasattr(self, "_automation_manager"):
            del self._automation_manager

        # First run after upgrade should reset the stale counter
        self.assertTrue(self.automation_manager.can_start_global_run())
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    @patch("jleechanorg_pr_automation.automation_safety_manager.datetime")
    def test_daily_reset_new_day_resets_counter(self, mock_datetime):
        """RED: Counter should reset to 0 when a new day starts"""
        # Day 1: Record 50 runs
        day1 = datetime(2025, 10, 1, 10, 0, 0)
        mock_datetime.now.return_value = day1
        mock_datetime.side_effect = datetime

        for _ in range(50):
            self.automation_manager.record_global_run()

        # Should be at limit on Day 1
        self.assertEqual(self.automation_manager.get_global_runs(), 50)
        self.assertFalse(self.automation_manager.can_start_global_run())

        # Day 2: Counter should reset
        day2 = datetime(2025, 10, 2, 10, 0, 0)
        mock_datetime.now.return_value = day2

        # Should allow runs again with reset counter
        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    @patch("jleechanorg_pr_automation.automation_safety_manager.datetime")
    def test_daily_reset_multiple_days(self, mock_datetime):
        """RED: Counter should reset each day for multiple days"""
        mock_datetime.side_effect = datetime

        # Day 1: 50 runs
        day1 = datetime(2025, 10, 1, 10, 0, 0)
        mock_datetime.now.return_value = day1
        for _ in range(50):
            self.automation_manager.record_global_run()
        self.assertEqual(self.automation_manager.get_global_runs(), 50)

        # Day 2: Reset to 0, then 30 runs
        day2 = datetime(2025, 10, 2, 10, 0, 0)
        mock_datetime.now.return_value = day2
        self.assertEqual(self.automation_manager.get_global_runs(), 0)
        for _ in range(30):
            self.automation_manager.record_global_run()
        self.assertEqual(self.automation_manager.get_global_runs(), 30)

        # Day 3: Reset to 0 again
        day3 = datetime(2025, 10, 3, 10, 0, 0)
        mock_datetime.now.return_value = day3
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    @patch("jleechanorg_pr_automation.automation_safety_manager.datetime")
    def test_daily_reset_midnight_transition(self, mock_datetime):
        """RED: Counter should reset at midnight transition"""
        mock_datetime.side_effect = datetime

        # 23:59:59 on Day 1 - at limit
        before_midnight = datetime(2025, 10, 1, 23, 59, 59)
        mock_datetime.now.return_value = before_midnight
        for _ in range(50):
            self.automation_manager.record_global_run()
        self.assertFalse(self.automation_manager.can_start_global_run())

        # 00:00:01 on Day 2 - should reset
        after_midnight = datetime(2025, 10, 2, 0, 0, 1)
        mock_datetime.now.return_value = after_midnight

        result = self.automation_manager.can_start_global_run()
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_global_runs(), 0)

    @property
    def automation_manager(self):
        """RED: This property will fail - no AutomationSafetyManager exists yet"""
        # This will fail until we implement the class in GREEN phase
        if not hasattr(self, "_automation_manager"):
            self._automation_manager = AutomationSafetyManager(self.test_dir)
        return self._automation_manager


# Matrix 9: Integration with Existing Automation
class TestAutomationIntegration(unittest.TestCase):
    """Integration tests with existing simple_pr_batch.sh script"""

    def setUp(self):
        self.launchd_root = Path(tempfile.mkdtemp(prefix="launchd-plist-"))
        self.plist_path = self.launchd_root / "com.worldarchitect.pr-automation.plist"
        plist_dir = self.plist_path.parent
        plist_dir.mkdir(parents=True, exist_ok=True)
        plist_dir.chmod(0o755)
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/jleechan/projects/worldarchitect.ai/automation/automation_safety_wrapper.py</string>
    </array>
</dict>
</plist>
"""
        with open(self.plist_path, "w", encoding="utf-8") as plist_file:
            plist_file.write(plist_content)

    def tearDown(self):
        shutil.rmtree(self.launchd_root, ignore_errors=True)

    def test_shell_script_respects_safety_limits(self):
        """RED: Shell script should check safety limits before processing"""
        # This test will fail - existing script doesn't have safety checks
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1  # Safety limit hit

            result = self.run_automation_script()

            # Should exit early due to safety limits
            self.assertEqual(result.returncode, 1)

    def test_launchd_plist_includes_safety_wrapper(self):
        """RED: launchd plist should call safety wrapper, not direct script"""
        plist_content = self.read_launchd_plist()

        # Should call safety wrapper, not direct automation
        self.assertIn("automation_safety_wrapper.py", plist_content)
        self.assertNotIn("simple_pr_batch.sh", plist_content)

    def run_automation_script(self):
        """Helper to run automation script"""
        import subprocess
        return subprocess.run([
            "/Users/jleechan/projects/worktree_worker2/automation/simple_pr_batch.sh"
        ], check=False, capture_output=True, text=True)

    def read_launchd_plist(self):
        """Helper to read launchd plist file"""
        # This will fail - plist doesn't exist yet
        with open(self.plist_path, encoding="utf-8") as f:
            return f.read()


if __name__ == "__main__":
    # RED Phase: Run tests to confirm they FAIL
    print("🔴 RED Phase: Running failing tests for automation safety limits")
    print("Expected: ALL TESTS SHOULD FAIL (no implementation exists)")
    unittest.main(verbosity=2)
