"""Test that SafetyManager reloads inflight cache from disk to prevent stale data.

This test validates that the inflight cache is reloaded from disk on each
try_process_pr() call, preventing stale cached data from blocking PR processing.

Bug: The inflight cache was only loaded once at SafetyManager initialization,
causing stale inflight counts to persist across workflow runs and block PRs
that should be processable.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from automation.jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from automation.jleechanorg_pr_automation.tests.conftest import _get_inflight_count


def test_inflight_cache_reloads_from_disk_on_each_try_process_pr(tmp_path):
    """Test that try_process_pr() reloads inflight cache from disk.

    REPRODUCES BUG: When inflight file is updated externally (by another
    process or manual cleanup), try_process_pr() should see the updated
    values, not stale cached values.

    Scenario:
    1. SafetyManager initializes with inflight count = 0
    2. External process updates inflight file (simulating cleanup)
    3. try_process_pr() should reload and see updated count
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    # Initialize with empty files
    inflight_file.write_text("{}")
    pr_attempts_file.write_text("{}")

    # Create SafetyManager
    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    pr_number = 1234
    repo = "test/repo"
    pr_key = f"r={repo}||p={pr_number}||b="

    # Reserve a slot - this should work
    assert manager.try_process_pr(pr_number, repo=repo) == True

    # Verify inflight count is 1
    with open(inflight_file) as f:
        data = json.load(f)
        assert _get_inflight_count(data, pr_key) == 1

    # Now simulate an external process cleaning up the inflight file
    # (e.g., manual cleanup or another workflow instance releasing the slot)
    with open(inflight_file, 'w') as f:
        json.dump({}, f)  # Clear all inflight entries

    # Create a NEW SafetyManager instance (simulating a new workflow run)
    manager2 = AutomationSafetyManager(str(history_dir))

    # This should work because inflight file is now empty
    # BUG: This will FAIL if the cache is not reloaded
    result = manager2.try_process_pr(pr_number, repo=repo)

    assert result == True, \
        "try_process_pr should reload inflight cache from disk and see count=0"


def test_inflight_cache_sees_external_cleanup(tmp_path):
    """Test that SAME SafetyManager instance sees external inflight cleanup.

    This is a stricter test - even without creating a new instance,
    try_process_pr() should reload from disk to see external changes.
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    # Initialize with high inflight count (simulating stuck slots)
    pr_number = 5678
    repo = "test/repo2"
    pr_key = f"r={repo}||p={pr_number}||b="

    initial_inflight = {
        pr_key: {
            "count": 10,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    }
    inflight_file.write_text(json.dumps(initial_inflight))
    pr_attempts_file.write_text("{}")

    # Create SafetyManager - it loads the high count
    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    # This should fail because count is at limit and updated_at is fresh
    assert manager.try_process_pr(pr_number, repo=repo) == False

    # Now simulate external cleanup (manual intervention)
    with open(inflight_file, 'w') as f:
        json.dump({}, f)  # Clear the stuck slot

    # Same manager instance - should reload and see the cleanup
    result = manager.try_process_pr(pr_number, repo=repo)

    assert result == True, \
        "try_process_pr should reload inflight cache and see external cleanup"


def test_inflight_decrement_persists_correctly(tmp_path):
    """Test that release_pr_slot() correctly decrements and persists.

    Ensures that when a slot is released, the inflight file is updated
    so subsequent processes see the correct count.
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    inflight_file.write_text("{}")
    pr_attempts_file.write_text("{}")

    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    pr_number = 9999
    repo = "test/repo3"
    pr_key = f"r={repo}||p={pr_number}||b="

    # Reserve a slot
    assert manager.try_process_pr(pr_number, repo=repo) == True

    # Release the slot
    manager.release_pr_slot(pr_number, repo=repo)

    # Verify the file is updated (not just in-memory cache)
    with open(inflight_file) as f:
        data = json.load(f)
        # After release, should be 0
        assert _get_inflight_count(data, pr_key) == 0

    # New manager should see count=0
    manager2 = AutomationSafetyManager(str(history_dir))
    assert manager2.try_process_pr(pr_number, repo=repo) == True


def test_multiple_workflows_dont_interfere(tmp_path):
    """Test that concurrent workflows properly share inflight state.

    Simulates two workflow instances operating on the same PR history,
    ensuring they don't step on each other's toes.
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    inflight_file.write_text("{}")
    pr_attempts_file.write_text("{}")

    # Two workflow instances
    workflow1 = AutomationSafetyManager(str(history_dir))
    workflow2 = AutomationSafetyManager(str(history_dir))

    pr_number = 1111
    repo = "test/concurrent"
    pr_key = f"r={repo}||p={pr_number}||b="

    # Workflow 1 reserves a slot
    assert workflow1.try_process_pr(pr_number, repo=repo) == True

    # Workflow 2 should reload and see the reservation
    # BUG: This will FAIL if cache is not reloaded
    result = workflow2.try_process_pr(pr_number, repo=repo)

    # Should still succeed (count would be 2, limit is 50)
    assert result == True, "Second workflow should see first workflow's reservation"

    # Verify both reservations persisted
    with open(inflight_file) as f:
        data = json.load(f)
        assert _get_inflight_count(data, pr_key) == 2, "Both workflows should have reserved slots"


def test_try_process_pr_clears_stale_inflight_entries(tmp_path):
    """Stale inflight entries should be cleared before reserving new slots."""
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    pr_number = 2468
    repo = "test/repo4"
    pr_key = f"r={repo}||p={pr_number}||b="

    stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    inflight_file.write_text(json.dumps({pr_key: {"count": 10, "updated_at": stale_time}}))
    pr_attempts_file.write_text("{}")

    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    # Should clear stale inflight and allow reservation
    assert manager.try_process_pr(pr_number, repo=repo) is True

    with open(inflight_file) as f:
        data = json.load(f)
        assert _get_inflight_count(data, pr_key) == 1


def test_try_process_pr_clears_legacy_inflight_at_limit(tmp_path):
    """Legacy inflight entries (int-only) at limit should be cleared."""
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    pr_number = 1357
    repo = "test/repo5"
    pr_key = f"r={repo}||p={pr_number}||b="

    inflight_file.write_text(json.dumps({pr_key: 10}))
    pr_attempts_file.write_text("{}")

    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    assert manager.try_process_pr(pr_number, repo=repo) is True

    with open(inflight_file) as f:
        data = json.load(f)
        assert _get_inflight_count(data, pr_key) == 1


def test_try_process_pr_blocks_when_inflight_fresh(tmp_path):
    """Fresh inflight entries at limit should still block reservations."""
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    inflight_file = history_dir / "pr_inflight.json"
    pr_attempts_file = history_dir / "pr_attempts.json"

    pr_number = 9753
    repo = "test/repo6"
    pr_key = f"r={repo}||p={pr_number}||b="

    inflight_file.write_text(
        json.dumps(
            {pr_key: {"count": 10, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    )
    pr_attempts_file.write_text("{}")

    manager = AutomationSafetyManager(str(history_dir), limits={"pr_limit": 10})

    assert manager.try_process_pr(pr_number, repo=repo) is False
