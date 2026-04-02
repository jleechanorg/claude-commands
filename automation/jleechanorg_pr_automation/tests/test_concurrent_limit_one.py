#!/usr/bin/env python3
"""
RED/GREEN Test: Concurrent processing limit should be 1, not pr_limit (50)

PROBLEM:
- Current code uses self.pr_limit (50) for concurrent processing check
- This allows up to 49 concurrent agents on same PR (wrong!)
- Should only allow 1 agent per PR at a time

EXPECTED BEHAVIOR:
- First agent reserves slot → succeeds
- Second agent tries while first active → blocked
- After first releases, second can proceed
"""

import json
import os
import shutil
import tempfile
import unittest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


class TestConcurrentLimitOne(unittest.TestCase):
    """Test that concurrent processing limit is 1, not pr_limit"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.test_dir = tempfile.mkdtemp()
        self.safety_manager = AutomationSafetyManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_limit_should_be_one_not_pr_limit(self):
        """
        RED TEST: Current code uses pr_limit (50) for concurrent check.
        This test FAILS because second agent is allowed when it shouldn't be.

        EXPECTED: Only 1 agent per PR at a time (concurrent_limit=1)
        ACTUAL: Up to 50 agents per PR (uses pr_limit=50)
        """
        pr_number = 3664
        repo = "jleechanorg/worldarchitect.ai"
        branch = "test-branch"

        # First agent reserves slot
        result1 = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(result1, "First agent should reserve slot successfully")

        # Check inflight count
        pr_key = self.safety_manager._make_pr_key(pr_number, repo, branch)
        inflight_count = self.safety_manager._pr_inflight_cache.get(pr_key, 0)
        self.assertEqual(inflight_count, 1, "Inflight count should be 1")

        # Second agent tries to reserve while first is active
        result2 = self.safety_manager.try_process_pr(pr_number, repo, branch)

        # THIS IS THE FAILING ASSERTION (RED STATE)
        # Current code allows this because inflight (1) < pr_limit (50)
        # Expected: result2 should be False (blocked)
        # Actual: result2 is True (allowed - BUG!)
        self.assertFalse(
            result2,
            "Second agent should be BLOCKED when first is active (concurrent_limit=1). "
            "CURRENT BUG: Allows up to 50 concurrent agents (uses pr_limit instead of concurrent_limit)"
        )

    def test_concurrent_limit_allows_processing_after_release(self):
        """
        GREEN TEST: After first agent releases, second should be allowed.

        This validates the correct behavior path works.
        """
        pr_number = 3664
        repo = "jleechanorg/worldarchitect.ai"
        branch = "test-branch"

        # First agent reserves and releases
        result1 = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(result1, "First agent should reserve slot")

        self.safety_manager.release_pr_slot(pr_number, repo, branch)

        # Now second agent should succeed (slot is free)
        result2 = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(result2, "Second agent should succeed after first releases")

    def test_pr_limit_vs_concurrent_limit_distinction(self):
        """
        Demonstrate the difference between pr_limit and concurrent_limit:

        - pr_limit (50): Total attempts over time (prevents runaway automation)
        - concurrent_limit (1): Max agents at once (prevents race conditions)

        These are DIFFERENT concepts that got conflated in the code.
        """
        pr_number = 1234
        repo = "test/repo"
        branch = "main"

        # Simulate 10 sequential attempts (over time, not concurrent)
        for i in range(10):
            # Reserve slot
            result = self.safety_manager.try_process_pr(pr_number, repo, branch)
            self.assertTrue(result, f"Attempt {i+1} should succeed (under pr_limit=50)")

            # Release immediately (simulates agent completing)
            self.safety_manager.release_pr_slot(pr_number, repo, branch)

            # Record attempt for pr_limit tracking
            self.safety_manager.record_pr_attempt(pr_number, "success", repo, branch)

        # Check total attempts
        attempts = self.safety_manager.get_pr_attempts(pr_number, repo, branch)
        self.assertEqual(attempts, 10, "Should have 10 total attempts recorded")

        # Should still be able to process (10 < pr_limit of 50)
        can_process = self.safety_manager.can_process_pr(pr_number, repo, branch)
        self.assertTrue(can_process, "Should allow processing (10/50 attempts)")

        # But concurrent processing should still be limited to 1
        result1 = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(result1, "First concurrent agent succeeds")

        result2 = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertFalse(result2, "Second concurrent agent blocked (concurrent_limit=1)")

    def test_concurrent_limit_protects_against_race_conditions(self):
        """
        Demonstrate why concurrent_limit=1 is critical:

        Without it, two agents could:
        - Edit same files simultaneously → git conflicts
        - Apply same fixes twice → duplicate work
        - Push at same time → race condition
        """
        pr_number = 5678
        repo = "test/repo"
        branch = "feature"

        # Simulate two different workflows trying same PR
        workflow1_result = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(workflow1_result, "Workflow 1 (fixpr) reserves slot")

        # Workflow 2 (comment-validation) tries same PR
        workflow2_result = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertFalse(
            workflow2_result,
            "Workflow 2 should be blocked to prevent race conditions"
        )

        # After workflow 1 completes, workflow 2 can proceed
        self.safety_manager.release_pr_slot(pr_number, repo, branch)
        workflow2_retry = self.safety_manager.try_process_pr(pr_number, repo, branch)
        self.assertTrue(workflow2_retry, "Workflow 2 succeeds after workflow 1 completes")


if __name__ == "__main__":
    unittest.main()
