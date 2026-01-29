#!/usr/bin/env python3
"""
Tests for Cursor bot round 3 bug fixes

Cursor bot identified 1 bug after round 2 fixes:
1. Ignored return value in try_process_pr() allows false positive slot reservation

Bug Context: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
"""

import json
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import SafeJSONManager
from jleechanorg_pr_automation.tests.conftest import _get_inflight_count


def test_try_process_pr_returns_false_when_write_fails(tmp_path, caplog):
    """
    Test that try_process_pr() returns False when atomic_update() fails.

    Bug: The return value of json_manager.atomic_update() is ignored in try_process_pr().
    The reserve_slot() callback sets success = True based on internal logic, but if the
    file write fails (disk full, permissions, etc.), we still return True. This allows
    false positive slot reservation - the function claims success but nothing was persisted.

    Fix: Check atomic_update() return value and only return True if BOTH the reservation
    logic succeeded AND the file write succeeded.

    Cursor comment: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 1234
    repo = "test-repo"

    # Mock atomic_update to simulate write failure (disk full, permissions, etc.)
    with patch.object(SafeJSONManager, 'atomic_update', return_value=False):
        # Should return False when write fails, even if reservation logic says True
        result = manager.try_process_pr(pr_number, repo=repo)
        assert result is False, "try_process_pr() should return False when file write fails"


def test_try_process_pr_returns_true_only_when_both_succeed(tmp_path):
    """Test that try_process_pr() returns True only when both reservation AND write succeed"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 5678
    repo = "test-repo"

    # Normal case: both reservation logic and write should succeed
    result = manager.try_process_pr(pr_number, repo=repo)
    assert result is True, "try_process_pr() should return True when both succeed"

    # Verify slot was actually reserved in file
    inflight_file = safety_data_dir / "pr_inflight.json"
    with open(inflight_file, 'r') as f:
        data = json.load(f)

    # Use labeled format that the code actually generates
    pr_key = f"r={repo}||p={pr_number}||b="
    assert pr_key in data, "PR key should be in inflight file"
    assert _get_inflight_count(data, pr_key) == 1, "Inflight count should be 1"


def test_try_process_pr_write_failure_prevents_slot_reservation(tmp_path):
    """Test that write failure prevents false positive slot reservation"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 9999
    repo = "test-repo"

    # First successful reservation
    result1 = manager.try_process_pr(pr_number, repo=repo)
    assert result1 is True, "First reservation should succeed"

    # Mock write failure for second attempt
    with patch.object(SafeJSONManager, 'atomic_update', return_value=False):
        result2 = manager.try_process_pr(pr_number, repo=repo)
        assert result2 is False, "Second reservation should fail due to write error"

    # Verify inflight count is still 1 (not 2)
    inflight_file = safety_data_dir / "pr_inflight.json"
    with open(inflight_file, 'r') as f:
        data = json.load(f)

    # Use labeled format (r=repo||p=number||b=branch)
    pr_key = f"r={repo}||p={pr_number}||b="
    # The count should be 1 from the first successful reservation
    # The second attempt failed so it shouldn't increment
    assert _get_inflight_count(data, pr_key) == 1, "Inflight count should remain 1 after write failure"


def test_release_pr_slot_logs_error_on_write_failure(tmp_path, caplog):
    """Test that release_pr_slot() logs error when atomic_update() fails"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 7777
    repo = "test-repo"

    # Reserve a slot first
    manager.try_process_pr(pr_number, repo=repo)

    # Mock write failure for release
    caplog.clear()
    caplog.set_level(logging.ERROR)

    with patch.object(SafeJSONManager, 'atomic_update', return_value=False):
        # Should log error when write fails
        manager.release_pr_slot(pr_number, repo=repo)

    # Check that error was logged
    assert any("Failed to release slot" in record.message for record in caplog.records), \
        "release_pr_slot() should log error when file write fails"


def test_disk_full_simulation(tmp_path):
    """Simulate disk full scenario where atomic_update() fails"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 3333
    repo = "test-repo"

    # Simulate disk full by making atomic_update() return False
    with patch.object(SafeJSONManager, 'atomic_update', return_value=False):
        result = manager.try_process_pr(pr_number, repo=repo)

        # Should return False, not True (bug would return True)
        assert result is False, "Should return False when disk is full"

    # Verify no slot was reserved
    inflight_file = safety_data_dir / "pr_inflight.json"

    # File might not exist if atomic_update failed before creating it
    if inflight_file.exists():
        with open(inflight_file, 'r') as f:
            data = json.load(f)

        # Use labeled format (r=repo||p=number||b=branch)
        pr_key = f"r={repo}||p={pr_number}||b="
        assert pr_key not in data, "No slot should be reserved when write fails"


def test_permission_error_simulation(tmp_path):
    """Simulate permission error where atomic_update() fails"""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    limits = {"pr_automation_limit": 10, "pr_limit": 5}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 4444
    repo = "test-repo"

    # Simulate permission error
    with patch.object(SafeJSONManager, 'atomic_update', return_value=False):
        result = manager.try_process_pr(pr_number, repo=repo)

        # Should return False due to permission error
        assert result is False, "Should return False when permission denied"
