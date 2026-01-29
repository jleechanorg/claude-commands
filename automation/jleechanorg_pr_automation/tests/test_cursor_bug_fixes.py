#!/usr/bin/env python3
"""
Tests for Cursor bot bug fixes on PR #3762

Cursor bot identified two bugs in the rolling window implementation:
1. ValueError risk from using int() directly on env var
2. Inconsistent time window logic between can_process_pr() and get_pr_attempts()

These tests verify both bugs are fixed.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


def test_invalid_window_hours_env_var_graceful_fallback(tmp_path, monkeypatch):
    """
    Test that invalid AUTOMATION_ATTEMPT_WINDOW_HOURS env var doesn't crash.

    Bug: int(os.environ.get("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")) raises
    ValueError if env var is set to non-numeric value, crashing can_process_pr().

    Fix: Use coerce_positive_int() which returns default on invalid input.

    Cursor comment: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    # Set invalid env var that would cause ValueError with int()
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "not-a-number")

    # Should NOT crash - should use default 24 hours
    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 1234
    repo = "test-repo"

    # Should work without crashing
    result = manager.can_process_pr(pr_number, repo=repo)
    assert result is True, "Should allow processing with default window on invalid env var"

    # Verify get_pr_attempts also handles invalid env var gracefully
    attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
    assert attempt_count == 0, "Should return 0 attempts without crashing"


def test_negative_window_hours_uses_default(tmp_path, monkeypatch):
    """Test that negative AUTOMATION_ATTEMPT_WINDOW_HOURS uses default."""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    # Set negative value (invalid)
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "-5")

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    # Should use default (24 hours) instead of negative value
    result = manager.can_process_pr(1234, repo="test-repo")
    assert result is True


def test_zero_window_hours_uses_default(tmp_path, monkeypatch):
    """Test that zero AUTOMATION_ATTEMPT_WINDOW_HOURS uses default."""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    # Set zero (invalid)
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "0")

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    # Should use default (24 hours) instead of zero
    result = manager.can_process_pr(1234, repo="test-repo")
    assert result is True


def test_get_pr_attempts_consistent_with_can_process_pr(tmp_path, monkeypatch):
    """
    Test that get_pr_attempts() uses same rolling window as can_process_pr().

    Bug: can_process_pr() uses rolling window (24h default), but get_pr_attempts()
    uses daily cooldown (midnight UTC reset). This causes misleading CLI output
    like "BLOCKED (2/10 attempts)" when rolling window actually has more attempts.

    Fix: Both methods now use same rolling window logic with same env var.

    Cursor comment: https://github.com/jleechanorg/worldarchitect.ai/pull/3762
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 5678
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"  # Use :: separator for legacy format normalization

    # Create attempts: some within 24h window, some outside
    now = datetime.now(timezone.utc)

    # Attempts from 25 hours ago (outside window)
    old_attempts = [
        {
            "result": "failure",
            "timestamp": (now - timedelta(hours=25 + i)).isoformat(),
            "pr_number": pr_number,
            "repo": repo,
        }
        for i in range(3)
    ]

    # Attempts from last 12 hours (inside window)
    recent_attempts = [
        {
            "result": "failure",
            "timestamp": (now - timedelta(hours=12 - i)).isoformat(),
            "pr_number": pr_number,
            "repo": repo,
        }
        for i in range(5)
    ]

    # Write attempts to file
    attempts_file = safety_data_dir / "pr_attempts.json"
    import json
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: old_attempts + recent_attempts}, f)

    # Get count from get_pr_attempts()
    attempt_count = manager.get_pr_attempts(pr_number, repo=repo)

    # Should return 5 (only recent attempts within 24h window)
    assert attempt_count == 5, (
        f"Expected 5 attempts (within rolling window), got {attempt_count}. "
        "get_pr_attempts() should use same rolling window as can_process_pr()."
    )

    # Verify can_process_pr() also uses same window
    # With 5 attempts and limit 10, should allow processing
    can_process = manager.can_process_pr(pr_number, repo=repo)
    assert can_process is True, "Should allow processing (5 attempts < 10 limit)"

    # Add 5 more recent attempts to hit the limit
    for i in range(5):
        manager.record_pr_attempt(pr_number, "failure", repo=repo)

    # Now both methods should see 10 attempts
    attempt_count_after = manager.get_pr_attempts(pr_number, repo=repo)
    assert attempt_count_after == 10, f"Expected 10 attempts after adding 5 more, got {attempt_count_after}"

    # can_process_pr should now block (10 attempts >= 10 limit)
    can_process_after = manager.can_process_pr(pr_number, repo=repo)
    assert can_process_after is False, "Should block processing (10 attempts >= 10 limit)"


def test_consistent_window_across_custom_hours(tmp_path, monkeypatch):
    """Test that both methods respect custom AUTOMATION_ATTEMPT_WINDOW_HOURS."""
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()

    # Set custom 12-hour window
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "12")

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 9999
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"  # Use :: separator for legacy format normalization

    now = datetime.now(timezone.utc)

    # Attempts: 3 from 15h ago (outside 12h window), 2 from 6h ago (inside)
    attempts = [
        {"result": "failure", "timestamp": (now - timedelta(hours=15)).isoformat()},
        {"result": "failure", "timestamp": (now - timedelta(hours=14)).isoformat()},
        {"result": "failure", "timestamp": (now - timedelta(hours=13)).isoformat()},
        {"result": "failure", "timestamp": (now - timedelta(hours=6)).isoformat()},
        {"result": "failure", "timestamp": (now - timedelta(hours=3)).isoformat()},
    ]

    attempts_file = safety_data_dir / "pr_attempts.json"
    import json
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: attempts}, f)

    # Both methods should count only 2 attempts (within 12h window)
    attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
    assert attempt_count == 2, f"Expected 2 attempts within 12h window, got {attempt_count}"

    # can_process_pr should allow (2 < 10)
    can_process = manager.can_process_pr(pr_number, repo=repo)
    assert can_process is True, "Should allow processing (2 attempts < 10 limit)"


def test_cli_output_consistency_simulation(tmp_path, monkeypatch):
    """
    Simulate CLI --check-pr output scenario from Cursor's bug report.

    Bug example: CLI shows "BLOCKED (2/10 attempts)" when rolling window
    actually contains 8 attempts from previous day.

    This test verifies the bug is fixed by ensuring both methods return
    consistent counts for CLI display.
    """
    safety_data_dir = tmp_path / "safety"
    safety_data_dir.mkdir()
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    limits = {"pr_automation_limit": 10, "pr_limit": 10}
    manager = AutomationSafetyManager(str(safety_data_dir), limits=limits)

    pr_number = 7777
    repo = "test-repo"
    pr_key = f"{repo}::{pr_number}"  # Use :: separator for legacy format normalization

    now = datetime.now(timezone.utc)

    # Simulate scenario from Cursor's bug report:
    # - 8 attempts from yesterday (still within 24h rolling window)
    # - 2 attempts from today
    # Old buggy behavior: get_pr_attempts() returns 2 (today only)
    # New correct behavior: get_pr_attempts() returns 10 (rolling window)

    # Space the 8 "yesterday" attempts evenly within the 12-23 hour range
    yesterday_attempts = [
        {
            "result": "failure",
            "timestamp": (now - timedelta(hours=23 - i*1.5)).isoformat(),
        }
        for i in range(8)
    ]

    # 2 attempts from "today" (within last few hours)
    today_attempts = [
        {
            "result": "failure",
            "timestamp": (now - timedelta(hours=i)).isoformat(),
        }
        for i in range(2)
    ]

    attempts_file = safety_data_dir / "pr_attempts.json"
    import json
    with open(attempts_file, 'w') as f:
        json.dump({pr_key: yesterday_attempts + today_attempts}, f)

    # CLI would call these two methods to display status:
    attempt_count = manager.get_pr_attempts(pr_number, repo=repo)
    can_process = manager.can_process_pr(pr_number, repo=repo)

    # Both should see 10 attempts (8 from yesterday + 2 from today)
    assert attempt_count == 10, (
        f"CLI display count should be 10 (all attempts in rolling window), got {attempt_count}. "
        "This would cause misleading output like 'BLOCKED (2/10 attempts)' in old buggy version."
    )

    # can_process_pr should block (10 >= 10)
    assert can_process is False, (
        "Should block processing (10 attempts >= 10 limit). "
        "CLI output should accurately reflect blocking reason."
    )
