"""
End-to-end test for safety limits false rejection bug (WA-3gx).

This test verifies try_process_pr() returns True when pr_attempts.json is empty
and safety limits are not exceeded.

Bug symptoms:
- PRs #3185, #3664, #3096 rejected with "Internal safety limits exceeded"
- automation-safety-cli shows 0/50 attempts for all three PRs
- pr_attempts.json = {}, pr_inflight.json = {}
"""

import json
import tempfile
from pathlib import Path

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import json_manager


class TestSafetyLimitsFalseRejection:
    """Test suite for WA-3gx: Safety limits false rejection bug."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for safety manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def clean_safety_manager(self, temp_data_dir):
        """Create safety manager with clean (empty) state."""
        # Initialize safety manager with temp directory
        manager = AutomationSafetyManager(data_dir=str(temp_data_dir))

        # Verify initial state is clean (empty files)
        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        pr_inflight_file = temp_data_dir / "pr_inflight.json"

        # Ensure files exist but are empty
        pr_attempts_file.write_text("{}")
        pr_inflight_file.write_text("{}")

        return manager

    def test_try_process_pr_with_empty_attempts_should_return_true(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Given: Clean safety manager state (empty pr_attempts.json)
        When: try_process_pr() is called for PR #3185
        Then: Should return True (PR has 0/50 attempts, should be allowed)
        """
        # Arrange
        test_pr_number = 3185
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "fix/spicy-mode-detection"

        # Verify clean state
        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        with open(pr_attempts_file, "r") as f:
            attempts_data = json.load(f)
        assert attempts_data == {}, "pr_attempts.json should be empty"

        # Act
        result = clean_safety_manager.try_process_pr(
            pr_number=test_pr_number,
            repo=test_repo,
            branch=test_branch,
        )

        # Save test state before assertion
        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence = {
            "test": "test_try_process_pr_with_empty_attempts_should_return_true",
            "pr_number": test_pr_number,
            "repo": test_repo,
            "branch": test_branch,
            "pr_attempts_before": attempts_data,
            "try_process_pr_result": result,
            "expected_result": True,
            "test_passed": result is True,
        }

        evidence_file = evidence_dir / "try_process_pr_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"\nEvidence saved to: {evidence_file}\n")

        assert result is True, (
            f"BUG REPRODUCED (WA-3gx): try_process_pr() returned False "
            f"when pr_attempts.json is empty. PR #{test_pr_number} should "
            f"be ALLOWED (0/50 attempts) but was rejected. "
            f"Evidence saved to {evidence_file}"
        )

    def test_can_process_pr_with_zero_attempts_should_return_true(
        self, clean_safety_manager, temp_data_dir
    ):
        """
        Verify can_process_pr() works correctly with zero attempts.

        This test isolates the can_process_pr() method to verify it's not
        the source of the bug.
        """
        test_pr_number = 3664
        test_repo = "jleechanorg/worldarchitect.ai"
        test_branch = "claude/add-action-resolution-warning"

        # Verify clean state
        pr_attempts_file = temp_data_dir / "pr_attempts.json"
        with open(pr_attempts_file, "r") as f:
            attempts_data = json.load(f)
        assert attempts_data == {}

        # Act
        result = clean_safety_manager.can_process_pr(
            pr_number=test_pr_number,
            repo=test_repo,
            branch=test_branch,
        )

        # Save evidence
        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence = {
            "test": "test_can_process_pr_with_zero_attempts_should_return_true",
            "pr_number": test_pr_number,
            "repo": test_repo,
            "branch": test_branch,
            "pr_attempts": attempts_data,
            "can_process_pr_result": result,
            "expected_result": True
        }

        evidence_file = evidence_dir / "can_process_pr_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"\ncan_process_pr() for PR #{test_pr_number}: {result}")
        print(f"Evidence saved to: {evidence_file}\n")

        # can_process_pr() should return True for 0 attempts
        assert result is True, (
            f"can_process_pr() returned False for PR #{test_pr_number} "
            f"with 0/50 attempts. This method should allow processing."
        )

    def test_atomic_update_file_write_success(self, temp_data_dir):
        """
        Test if atomic_update file writes are working correctly.

        This helps identify if file I/O or locking is the root cause.
        """
        test_file = temp_data_dir / "test_atomic_write.json"

        # Test write operation
        def update_func(data):
            return {"test_key": "test_value"}

        write_success = json_manager.atomic_update(test_file, update_func, {})

        # Verify write succeeded
        assert write_success is True, "atomic_update() should return True for successful write"

        # Verify file contents
        with open(test_file, "r") as f:
            data = json.load(f)

        evidence = {
            "test": "test_atomic_update_file_write_success",
            "write_success": write_success,
            "file_contents": data,
            "expected_contents": {"test_key": "test_value"}
        }

        evidence_dir = temp_data_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        evidence_file = evidence_dir / "atomic_update_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump(evidence, f, indent=2)

        print(f"\natomic_update() write_success: {write_success}")
        print(f"Evidence saved to: {evidence_file}\n")

        assert data == {"test_key": "test_value"}, "File should contain updated data"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
