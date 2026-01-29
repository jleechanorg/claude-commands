#!/usr/bin/env python3
"""
Tests for atomic race condition fix in automation safety manager

This test file verifies that the atomic_update() method in SafeJSONManager
properly prevents race conditions between concurrent processes that could
bypass safety limits.

Bug Context: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
Reported by: Gemini feedback on PR #3762
Fixed: Added atomic_update() with file lock held across read-modify-write
"""

import json
import multiprocessing
import os
import tempfile
import time
from pathlib import Path

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager
from jleechanorg_pr_automation.tests.conftest import _get_inflight_count


# Module-level helper functions for multiprocessing (must be picklable)
def _increment_pr_count(pr_key: str, test_file_path: str, process_id: int):
    """Simulate a process incrementing PR inflight count"""
    manager = SafeJSONManager()

    def update_count(data):
        # Simulate some processing time to increase chance of race
        time.sleep(0.01)
        current = data.get(pr_key, 0)
        return {**data, pr_key: current + 1}

    # Use atomic_update to prevent race
    result = manager.atomic_update(test_file_path, update_count, {})
    return result


def _try_reserve_slot(pr_number: int, data_dir: str, process_id: int):
    """Simulate a process trying to reserve a PR processing slot"""
    limits = {
        "pr_automation_limit": 1,  # Only 1 concurrent processing allowed
        "pr_limit": 1,
        "approval_hours": 24,
        "subprocess_timeout": 600,
    }
    manager = AutomationSafetyManager(data_dir, limits=limits)

    # Try to reserve a slot
    success = manager.try_process_pr(pr_number, repo="test-repo")
    return (success, process_id)


def _release_slot(pr_num: int, repo_name: str, data_dir: str, limits_dict: dict, process_id: int):
    """Simulate a process releasing a PR slot"""
    mgr = AutomationSafetyManager(data_dir, limits=limits_dict)
    mgr.release_pr_slot(pr_num, repo=repo_name)
    return process_id


def test_atomic_update_prevents_race_condition(tmp_path):
    """
    Test that atomic_update() prevents race conditions between processes.

    Simulates two processes trying to increment the same PR's inflight count
    simultaneously. Without atomic updates, both processes could read count=0,
    both increment to 1, and both write 1, resulting in count=1 instead of 2.

    With atomic_update(), the file lock is held across the entire operation,
    ensuring sequential execution and correct count=2.
    """
    test_file = tmp_path / "test_inflight.json"
    json_manager = SafeJSONManager()

    # Initialize file with empty dict
    json_manager.write_json(str(test_file), {})

    # Run two processes concurrently trying to increment the same PR count
    pr_key = "worldarchitect.ai#1234"
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_increment_pr_count, (pr_key, str(test_file), i))
        results.append(result)

    pool.close()
    pool.join()

    # Verify both updates succeeded
    for result in results:
        assert result.get() is True, "Atomic update should succeed"

    # Read final state - should be 2 (both increments applied)
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data.get(pr_key) == 2, (
        f"Expected count=2 after two concurrent increments, got {final_data.get(pr_key)}. "
        "Race condition detected - atomic_update() is not working properly!"
    )


def test_try_process_pr_concurrent_reservations(tmp_path, monkeypatch):
    """
    Test that try_process_pr() properly handles concurrent reservation attempts.

    Simulates two processes trying to reserve a processing slot for the same PR
    simultaneously when pr_limit=1. Without atomic updates, both could succeed,
    bypassing the safety limit. With atomic updates, only one should succeed.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_SAFETY_DATA_DIR", str(safety_data_dir))

    # Run two processes concurrently trying to reserve the same PR
    pr_number = 5678
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_try_reserve_slot, (pr_number, str(safety_data_dir), i))
        results.append(result)

    pool.close()
    pool.join()

    # Collect results
    outcomes = [result.get() for result in results]
    successes = [outcome for outcome in outcomes if outcome[0] is True]

    # Verify that EXACTLY ONE process succeeded (safety limit enforced)
    assert len(successes) == 1, (
        f"Expected exactly 1 successful reservation (pr_limit=1), got {len(successes)}. "
        f"Outcomes: {outcomes}. Race condition detected - try_process_pr() is not atomic!"
    )


def test_atomic_update_with_nonexistent_file(tmp_path):
    """Test that atomic_update() works correctly when file doesn't exist."""
    test_file = tmp_path / "nonexistent.json"
    json_manager = SafeJSONManager()

    def add_item(data):
        data["item"] = "value"
        return data

    # Should create file and add item
    result = json_manager.atomic_update(str(test_file), add_item, {})
    assert result is True

    # Verify file was created with correct content
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {"item": "value"}


def test_atomic_update_preserves_other_keys(tmp_path):
    """Test that atomic_update() preserves data in other keys."""
    test_file = tmp_path / "test_data.json"
    json_manager = SafeJSONManager()

    # Initialize with multiple keys
    initial_data = {
        "pr1": 1,
        "pr2": 2,
        "pr3": 3,
    }
    json_manager.write_json(str(test_file), initial_data)

    # Update only one key
    def update_pr2(data):
        data["pr2"] = data.get("pr2", 0) + 10
        return data

    result = json_manager.atomic_update(str(test_file), update_pr2, {})
    assert result is True

    # Verify pr2 was updated and other keys preserved
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {
        "pr1": 1,
        "pr2": 12,  # Updated: 2 + 10
        "pr3": 3,
    }


def test_atomic_update_handles_invalid_json(tmp_path):
    """Test that atomic_update() handles corrupted JSON gracefully."""
    test_file = tmp_path / "corrupted.json"

    # Write invalid JSON
    with open(test_file, 'w') as f:
        f.write("{invalid json content")

    json_manager = SafeJSONManager()

    def add_item(data):
        # Should receive default {} since JSON is invalid
        data["new_item"] = "value"
        return data

    result = json_manager.atomic_update(str(test_file), add_item, {})
    assert result is True

    # Verify file was overwritten with valid JSON
    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {"new_item": "value"}


def test_release_pr_slot_concurrent_releases(tmp_path, monkeypatch):
    """
    Test that release_pr_slot() properly handles concurrent release attempts.

    Simulates two processes trying to release the same PR slot simultaneously.
    Without atomic updates, both could decrement the count, resulting in
    incorrect negative values or lost releases.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_SAFETY_DATA_DIR", str(safety_data_dir))

    # Setup: Reserve 2 slots for the same PR
    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 9999
    repo = "test-repo"

    # Reserve 2 slots
    assert manager.try_process_pr(pr_number, repo=repo) is True
    assert manager.try_process_pr(pr_number, repo=repo) is True

    # Run two processes concurrently trying to release slots
    pool = multiprocessing.Pool(processes=2)

    results = []
    for i in range(2):
        result = pool.apply_async(_release_slot, (pr_number, repo, str(safety_data_dir), limits, i))
        results.append(result)

    pool.close()
    pool.join()

    # Wait for all releases to complete
    for result in results:
        result.get()

    # Verify inflight count is now 0 (both slots released correctly)
    # Read the file directly to check
    inflight_file = safety_data_dir / "pr_inflight.json"
    with open(inflight_file) as f:
        inflight_data = json.load(f)

    # Use the same labeled format that _make_pr_key() generates
    pr_key = f"r=test-repo||p={pr_number}||b="
    final_count = _get_inflight_count(inflight_data, pr_key)

    assert final_count == 0, (
        f"Expected inflight count=0 after releasing 2 slots, got {final_count}. "
        "Race condition detected - release_pr_slot() is not atomic!"
    )
