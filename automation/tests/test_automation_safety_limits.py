#!/usr/bin/env python3
"""
Test-Driven Development for PR Automation Safety Limits

RED Phase: All tests should FAIL initially
- PR attempt limits (max 5 per PR)
- Global run limits (max 50 total)
- Manual approval requirement
"""

import sys
import os
import unittest
import tempfile
import json
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add automation directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'automation'))

# Import after path modification
from automation_safety_manager import AutomationSafetyManager


class TestAutomationSafetyLimits(unittest.TestCase):
    """Matrix testing for automation safety limits"""

    def setUp(self):
        """Set up test environment with temporary files"""
        self.test_dir = tempfile.mkdtemp()
        self.pr_attempts_file = os.path.join(self.test_dir, "pr_attempts.json")
        self.global_runs_file = os.path.join(self.test_dir, "global_runs.json")
        self.approval_file = os.path.join(self.test_dir, "manual_approval.json")

        # Initialize empty tracking files
        with open(self.pr_attempts_file, 'w') as f:
            json.dump({}, f)
        with open(self.global_runs_file, 'w') as f:
            json.dump({"total_runs": 0, "start_date": datetime.now().isoformat()}, f)
        with open(self.approval_file, 'w') as f:
            json.dump({"approved": False, "approval_date": None}, f)

    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)

    # Matrix 1: PR Attempt Limits (5 attempts per PR)
    def test_pr_attempt_limit_1_should_allow(self):
        """RED: First attempt on PR #1001 should be allowed"""
        # This test will FAIL initially - no implementation exists
        result = self.automation_manager.can_process_pr(1001)
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 0)

    def test_pr_attempt_limit_5_should_allow(self):
        """RED: 5th attempt on PR #1001 should be allowed"""
        # Set up 4 previous attempts
        self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "failure")

        result = self.automation_manager.can_process_pr(1001)
        self.assertTrue(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 4)

    def test_pr_attempt_limit_6_should_block(self):
        """RED: 6th attempt on PR #1001 should be blocked"""
        # Set up 5 previous attempts (max limit reached)
        for _ in range(5):
            self.automation_manager.record_pr_attempt(1001, "failure")

        result = self.automation_manager.can_process_pr(1001)
        self.assertFalse(result)
        self.assertEqual(self.automation_manager.get_pr_attempts(1001), 5)

    def test_pr_attempt_success_resets_counter(self):
        """RED: Successful PR attempt should reset counter"""
        # Set up 3 failures then 1 success
        self.automation_manager.record_pr_attempt(1001, "failure")
        self.automation_manager.record_pr_attempt(1001, "failure")
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
    @patch('smtplib.SMTP')
    def test_email_sent_when_pr_limit_reached(self, mock_smtp):
        """RED: Email should be sent when PR reaches 5 attempts"""
        # Set up 5 attempts to trigger notification
        for _ in range(5):
            self.automation_manager.record_pr_attempt(1001, "failure")

        # Should trigger email
        self.automation_manager.check_and_notify_limits()

        # Verify email was sent
        mock_smtp.assert_called_once()

    @patch('smtplib.SMTP')
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
        import time

        results = []

        def attempt_pr():
            result = self.automation_manager.can_process_pr(1001)
            if result:
                self.automation_manager.record_pr_attempt(1001, "failure")
            results.append(result)

        # Start 10 concurrent threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=attempt_pr)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have exactly 5 successful attempts (limit)
        successful_attempts = sum(results)
        self.assertEqual(successful_attempts, 5)

    # Matrix 7: Configuration Management
    def test_limits_configurable_via_environment(self):
        """RED: Safety limits should be configurable via environment variables"""
        with patch.dict(os.environ, {
            'AUTOMATION_PR_LIMIT': '3',
            'AUTOMATION_GLOBAL_LIMIT': '25'
        }):
            manager = AutomationSafetyManager(self.test_dir)

            # Should use custom limits
            self.assertEqual(manager.pr_limit, 3)
            self.assertEqual(manager.global_limit, 25)

    def test_default_limits_when_no_config(self):
        """RED: Should use default limits when no configuration provided"""
        manager = AutomationSafetyManager(self.test_dir)

        # Should use defaults
        self.assertEqual(manager.pr_limit, 5)
        self.assertEqual(manager.global_limit, 50)

    @property
    def automation_manager(self):
        """RED: This property will fail - no AutomationSafetyManager exists yet"""
        # This will fail until we implement the class in GREEN phase
        return AutomationSafetyManager(self.test_dir)


# Matrix 8: Integration with Existing Automation
class TestAutomationIntegration(unittest.TestCase):
    """Integration tests with existing simple_pr_batch.sh script"""

    def test_shell_script_respects_safety_limits(self):
        """RED: Shell script should check safety limits before processing"""
        # This test will fail - existing script doesn't have safety checks
        with patch('subprocess.run') as mock_run:
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
        ], capture_output=True, text=True)

    def read_launchd_plist(self):
        """Helper to read launchd plist file"""
        # This will fail - plist doesn't exist yet
        with open("/Users/jleechan/Library/LaunchAgents/com.worldarchitect.pr-automation.plist") as f:
            return f.read()


if __name__ == '__main__':
    # RED Phase: Run tests to confirm they FAIL
    print("🔴 RED Phase: Running failing tests for automation safety limits")
    print("Expected: ALL TESTS SHOULD FAIL (no implementation exists)")
    unittest.main(verbosity=2)
