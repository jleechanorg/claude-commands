#!/usr/bin/env python3
"""
Tests for Cursor bot round 2 bug fixes

Cursor bot identified 2 additional bugs after the initial fixes:
1. TOCTOU race condition in atomic_update() file creation
2. TypeError not caught in _parse_timestamp()

Bug Context: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
"""

import json
import multiprocessing
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager


# Module-level helper for multiprocessing (must be picklable)
def _concurrent_file_creation(file_path: str, process_id: int, data_value: int):
    """Simulate concurrent atomic_update on non-existent file"""
    manager = SafeJSONManager()

    def add_data(existing_data):
        # Simulate some processing time to increase race window
        import time
        time.sleep(0.01)

        # Add this process's data
        existing_data[f"process_{process_id}"] = data_value
        return existing_data

    result = manager.atomic_update(file_path, add_data, {})
    return (process_id, result)


def test_toctou_race_concurrent_file_creation(tmp_path):
    """
    Test that atomic_update() handles concurrent file creation without TOCTOU race.

    Bug: Two processes check os.path.exists() simultaneously, both find file missing,
    both enter 'else' branch. Process A creates file with 'w' mode and writes data.
    Process B then opens with 'w' mode which TRUNCATES immediately (before lock),
    causing Process A's data to be lost.

    Fix: Use single code path with 'a+' mode which doesn't truncate on open,
    and acquire lock BEFORE any truncation happens.

    Cursor comment: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
    """
    test_file = tmp_path / "concurrent_create.json"

    # Run 3 processes concurrently trying to create and update the same file
    pool = multiprocessing.Pool(processes=3)

    results = []
    for i in range(3):
        result = pool.apply_async(_concurrent_file_creation, (str(test_file), i, i*100))
        results.append(result)

    pool.close()
    pool.join()

    # All processes should succeed
    outcomes = [result.get() for result in results]
    for process_id, success in outcomes:
        assert success is True, f"Process {process_id} should succeed"

    # Final file should contain data from ALL processes (no data loss)
    json_manager = SafeJSONManager()
    final_data = json_manager.read_json(str(test_file), {})

    # Verify all 3 processes wrote their data
    assert "process_0" in final_data, "Process 0 data should be present"
    assert "process_1" in final_data, "Process 1 data should be present"
    assert "process_2" in final_data, "Process 2 data should be present"

    # Verify correct values
    assert final_data["process_0"] == 0
    assert final_data["process_1"] == 100
    assert final_data["process_2"] == 200

    # No data loss - TOCTOU bug would cause only last process's data to remain


def test_atomic_update_empty_file_handling(tmp_path):
    """Test that atomic_update() handles empty files correctly"""
    test_file = tmp_path / "empty.json"

    # Create empty file
    test_file.touch()

    json_manager = SafeJSONManager()

    def add_item(data):
        data["item"] = "value"
        return data

    # Should handle empty file gracefully (treat as default)
    result = json_manager.atomic_update(str(test_file), add_item, {})
    assert result is True

    final_data = json_manager.read_json(str(test_file), {})
    assert final_data == {"item": "value"}


def test_parse_timestamp_with_integer(tmp_path, monkeypatch):
    """
    Test that _parse_timestamp() handles non-string timestamps (TypeError).

    Bug: _parse_timestamp() catches ValueError and AttributeError but not TypeError.
    If timestamp field contains an integer (e.g., Unix timestamp from corrupted or
    legacy data), datetime.fromisoformat() raises TypeError which propagates up
    and crashes can_process_pr() or get_pr_attempts().

    Fix: Add TypeError to exception handler.

    Cursor comment: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 1234
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"

    # Create attempts with INTEGER timestamps (corrupted/legacy data)
    attempts_with_int_timestamps = [
        {
            "result": "failure",
            "timestamp": 1642521600,  # Integer Unix timestamp (not ISO string!)
            "pr_number": pr_number,
            "repo": repo,
        },
        {
            "result": "failure",
            "timestamp": 1642525200,  # Another integer
            "pr_number": pr_number,
            "repo": repo,
        },
    ]

    # Write corrupted data to file
    attempts_file = safety_data_dir / "pr_attempts.json"
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: attempts_with_int_timestamps}, f)

    # Should NOT crash with TypeError - should gracefully handle and filter out
    try:
        attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
        # Integer timestamps are unparseable, so they get filtered to epoch (1970)
        # which is outside any reasonable rolling window
        assert attempt_count == 0, "Integer timestamps should be treated as epoch (filtered out)"
    except TypeError:
        pytest.fail("_parse_timestamp() should catch TypeError from integer timestamps")


def test_parse_timestamp_with_none(tmp_path):
    """Test that _parse_timestamp() handles None timestamps"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 5678
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"

    # Create attempts with None timestamps
    attempts_with_none = [
        {
            "result": "failure",
            "timestamp": None,  # None timestamp
            "pr_number": pr_number,
            "repo": repo,
        },
    ]

    attempts_file = safety_data_dir / "pr_attempts.json"
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: attempts_with_none}, f)

    # Should NOT crash - early return for falsy timestamp
    attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
    assert attempt_count == 0, "None timestamps should be filtered out"


def test_parse_timestamp_with_list(tmp_path):
    """Test that _parse_timestamp() handles list timestamps (extreme case)"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 9999
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"

    # Create attempts with LIST timestamps (extreme corruption)
    attempts_with_list = [
        {
            "result": "failure",
            "timestamp": ["2026-01-18", "12:00:00"],  # List instead of string
            "pr_number": pr_number,
            "repo": repo,
        },
    ]

    attempts_file = safety_data_dir / "pr_attempts.json"
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: attempts_with_list}, f)

    # Should NOT crash with TypeError
    try:
        attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
        assert attempt_count == 0, "List timestamps should be filtered out"
    except TypeError:
        pytest.fail("_parse_timestamp() should catch TypeError from list timestamps")


def test_parse_timestamp_with_dict(tmp_path):
    """Test that _parse_timestamp() handles dict timestamps"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 7777
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"

    # Create attempts with DICT timestamps
    attempts_with_dict = [
        {
            "result": "failure",
            "timestamp": {"year": 2026, "month": 1, "day": 18},  # Dict instead of string
            "pr_number": pr_number,
            "repo": repo,
        },
    ]

    attempts_file = safety_data_dir / "pr_attempts.json"
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: attempts_with_dict}, f)

    # Should NOT crash
    try:
        attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
        assert attempt_count == 0, "Dict timestamps should be filtered out"
    except (TypeError, AttributeError):
        pytest.fail("_parse_timestamp() should catch TypeError/AttributeError from dict timestamps")
