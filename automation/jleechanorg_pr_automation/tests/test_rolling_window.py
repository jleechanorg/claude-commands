"""Test rolling window attempt limit behavior.

This test validates that attempt limits use a rolling window (last N hours)
instead of a daily cooldown (resets at midnight UTC).

Bug Fixed: Commit db8f8b33c changed from all-time counting to daily cooldown,
which blocked PRs for up to 24 hours even if attempts occurred early in the day.

New Behavior: Rolling window allows attempts to expire gradually as they age out
of the window, providing more predictable and responsive automation.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from automation.jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager


def test_rolling_window_excludes_old_attempts(tmp_path, monkeypatch):
    """Test that attempts older than the window are excluded from limit check.

    Scenario:
    1. PR has 10 attempts from 25 hours ago (outside 24h window)
    2. PR has 0 attempts from within last 24 hours
    3. Should allow processing (0 < 10 limit)
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Set 24 hour window
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    # Create 10 attempts from 25 hours ago (outside window)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=25)

    pr_number = 1234
    repo = "test/repo"
    pr_key = f"r={repo}||p={pr_number}||b="

    old_attempts = [
        {
            "result": "failure",
            "timestamp": (old_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(10)
    ]

    pr_attempts_file.write_text(json.dumps({pr_key: old_attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    manager = AutomationSafetyManager(str(history_dir))

    # Should allow processing - all attempts are outside the window
    assert manager.can_process_pr(pr_number, repo=repo) == True


def test_rolling_window_includes_recent_attempts(tmp_path, monkeypatch):
    """Test that attempts within the window count toward the limit.

    Scenario:
    1. PR has 10 attempts from 1 hour ago (inside 24h window)
    2. pr_limit = 10
    3. Should block processing (10 >= 10 limit)
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Set 24 hour window
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    # Create 10 attempts from 1 hour ago (inside window)
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(hours=1)

    pr_number = 5678
    repo = "test/repo2"
    pr_key = f"r={repo}||p={pr_number}||b="

    recent_attempts = [
        {
            "result": "failure",
            "timestamp": (recent_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(10)
    ]

    pr_attempts_file.write_text(json.dumps({pr_key: recent_attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    manager = AutomationSafetyManager(str(history_dir))

    # Should block processing - 10 attempts within window
    assert manager.can_process_pr(pr_number, repo=repo) == False


def test_rolling_window_mixed_old_and_recent(tmp_path, monkeypatch):
    """Test that only recent attempts count toward limit.

    Scenario:
    1. PR has 50 attempts from 25 hours ago (outside window)
    2. PR has 5 attempts from 1 hour ago (inside window)
    3. pr_limit = 10
    4. Should allow processing (5 < 10)
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Set 24 hour window
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=25)
    recent_time = now - timedelta(hours=1)

    pr_number = 9999
    repo = "test/repo3"
    pr_key = f"r={repo}||p={pr_number}||b="

    # 50 old attempts + 5 recent attempts
    old_attempts = [
        {
            "result": "failure",
            "timestamp": (old_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(50)
    ]

    recent_attempts = [
        {
            "result": "failure",
            "timestamp": (recent_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(5)
    ]

    all_attempts = old_attempts + recent_attempts

    pr_attempts_file.write_text(json.dumps({pr_key: all_attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    manager = AutomationSafetyManager(str(history_dir))

    # Should allow processing - only 5 attempts within window
    assert manager.can_process_pr(pr_number, repo=repo) == True


def test_rolling_window_configurable_size(tmp_path, monkeypatch):
    """Test that window size is configurable via env var.

    Scenario:
    1. Set window to 1 hour
    2. PR has 10 attempts from 2 hours ago
    3. Should allow processing (attempts outside 1h window)
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Set 1 hour window (not default 24)
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "1")

    # Create 10 attempts from 2 hours ago (outside 1h window)
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)

    pr_number = 3333
    repo = "test/repo4"
    pr_key = f"r={repo}||p={pr_number}||b="

    attempts = [
        {
            "result": "failure",
            "timestamp": (old_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(10)
    ]

    pr_attempts_file.write_text(json.dumps({pr_key: attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    manager = AutomationSafetyManager(str(history_dir))

    # Should allow processing - all attempts outside 1h window
    assert manager.can_process_pr(pr_number, repo=repo) == True


def test_rolling_window_boundary_condition(tmp_path, monkeypatch):
    """Test attempt at exactly the window boundary.

    Scenario:
    1. Set window to 24 hours
    2. PR has 1 attempt at exactly 24 hours ago
    3. Should allow processing (cutoff is >= not >)
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Set 24 hour window
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")

    # Create 1 attempt at exactly 24 hours ago
    now = datetime.now(timezone.utc)
    boundary_time = now - timedelta(hours=24)

    pr_number = 4444
    repo = "test/repo5"
    pr_key = f"r={repo}||p={pr_number}||b="

    attempts = [
        {
            "result": "failure",
            "timestamp": boundary_time.isoformat()
        }
    ]

    pr_attempts_file.write_text(json.dumps({pr_key: attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    manager = AutomationSafetyManager(str(history_dir))

    # Should allow processing - attempt at exactly boundary is excluded
    assert manager.can_process_pr(pr_number, repo=repo) == True


def test_rolling_window_gradual_recovery(tmp_path, monkeypatch):
    """Test that limits gradually lift as attempts age out.

    This validates the key benefit of rolling windows over daily cooldown:
    PRs can retry sooner as old attempts expire, rather than waiting until midnight.

    Scenario:
    1. PR has 10 attempts spread over 3 hours (all recent)
    2. pr_limit = 10, blocked initially
    3. Set window to 2 hours
    4. Oldest attempts age out, should allow processing
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    pr_number = 5555
    repo = "test/repo6"
    pr_key = f"r={repo}||p={pr_number}||b="

    # Create 10 attempts: 5 from 3h ago, 5 from 1h ago
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=3)
    recent_time = now - timedelta(hours=1)

    old_attempts = [
        {
            "result": "failure",
            "timestamp": (old_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(5)
    ]

    recent_attempts = [
        {
            "result": "failure",
            "timestamp": (recent_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(5)
    ]

    all_attempts = old_attempts + recent_attempts

    pr_attempts_file.write_text(json.dumps({pr_key: all_attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    # First check: 24h window, all 10 attempts count, blocked
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "24")
    manager1 = AutomationSafetyManager(str(history_dir))
    assert manager1.can_process_pr(pr_number, repo=repo) == False

    # Second check: 2h window, only 5 recent attempts count, allowed
    monkeypatch.setenv("AUTOMATION_ATTEMPT_WINDOW_HOURS", "2")
    manager2 = AutomationSafetyManager(str(history_dir))
    assert manager2.can_process_pr(pr_number, repo=repo) == True


def test_rolling_window_default_24h(tmp_path):
    """Test that default window is 24 hours when env var not set.

    Scenario:
    1. No AUTOMATION_ATTEMPT_WINDOW_HOURS env var set
    2. PR has 10 attempts from 23 hours ago (inside default 24h)
    3. Should block processing
    """
    history_dir = tmp_path / "pr_history"
    history_dir.mkdir()

    pr_attempts_file = history_dir / "pr_attempts.json"
    inflight_file = history_dir / "pr_inflight.json"

    # Create 10 attempts from 23 hours ago (inside default 24h window)
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(hours=23)

    pr_number = 6666
    repo = "test/repo7"
    pr_key = f"r={repo}||p={pr_number}||b="

    attempts = [
        {
            "result": "failure",
            "timestamp": (recent_time + timedelta(minutes=i)).isoformat()
        }
        for i in range(10)
    ]

    pr_attempts_file.write_text(json.dumps({pr_key: attempts}))
    inflight_file.write_text("{}")

    # Create config with pr_limit=10
    config_file = history_dir / "automation_safety_config.json"
    config_file.write_text(json.dumps({"pr_limit": 10}))

    # Don't set env var - should default to 24h
    manager = AutomationSafetyManager(str(history_dir))

    # Should block - 10 attempts within default 24h window
    assert manager.can_process_pr(pr_number, repo=repo) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
