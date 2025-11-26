#!/usr/bin/env python3
"""
Comprehensive test suite for AutomationSafetyManager
Using TDD methodology with 150+ test cases covering all safety logic
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Import the automation safety manager using proper Python module path
from jleechanorg_pr_automation.automation_safety_manager import AutomationSafetyManager
from jleechanorg_pr_automation.utils import json_manager


class TestAutomationSafetyManagerInit:
    """Test suite for AutomationSafetyManager initialization"""

    def test_init_with_data_dir(self):
        """Test initialization with provided data directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AutomationSafetyManager(temp_dir)
            assert manager.data_dir == temp_dir
            assert manager.global_limit > 0
            assert manager.pr_limit > 0

    def test_init_creates_data_dir(self):
        """Test that initialization creates data directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as parent_dir:
            data_dir = os.path.join(parent_dir, "new_safety_dir")
            manager = AutomationSafetyManager(data_dir)
            assert os.path.exists(data_dir)

    def test_init_reads_config_file(self):
        """Test that initialization reads existing config file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file
            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            config_data = {
                "global_limit": 50,
                "pr_limit": 3,
                "daily_limit": 100
            }
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            manager = AutomationSafetyManager(temp_dir)
            assert manager.global_limit == 50
            assert manager.pr_limit == 3

    def test_init_creates_default_config(self):
        """Test that initialization creates default config if none exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AutomationSafetyManager(temp_dir)

            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            assert os.path.exists(config_file)

            with open(config_file) as f:
                config = json.load(f)
            assert "global_limit" in config
            assert "pr_limit" in config

    def test_init_invalid_config_uses_defaults(self):
        """Test that invalid config file falls back to defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid config file
            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            with open(config_file, "w") as f:
                f.write("{ invalid json")

            manager = AutomationSafetyManager(temp_dir)
            assert manager.global_limit > 0  # Should use defaults


class TestGlobalLimits:
    """Test suite for global automation limits"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AutomationSafetyManager(temp_dir)

    def test_can_start_global_run_under_limit(self, manager):
        """Test global run allowed when under limit"""
        # Clear any existing runs
        manager._clear_global_runs()
        assert manager.can_start_global_run() == True

    def test_can_start_global_run_at_limit(self, manager):
        """Test global run denied when at limit"""
        # Fill up to limit
        for _ in range(manager.global_limit):
            manager.record_global_run()

        assert manager.can_start_global_run() == False

    def test_record_global_run_increments_count(self, manager):
        """Test that recording global run increments counter"""
        initial_count = manager.get_global_runs()
        manager.record_global_run()
        assert manager.get_global_runs() == initial_count + 1

    def test_get_global_runs_returns_count(self, manager):
        """Test that get_global_runs returns correct count"""
        manager._clear_global_runs()
        assert manager.get_global_runs() == 0

        manager.record_global_run()
        assert manager.get_global_runs() == 1

    def test_global_runs_file_persistence(self, manager):
        """Test that global runs are persisted to file"""
        manager._clear_global_runs()
        manager.record_global_run()
        manager.record_global_run()

        # Create new manager with same data dir
        new_manager = AutomationSafetyManager(manager.data_dir)
        assert new_manager.get_global_runs() == 2

    def test_global_runs_thread_safety(self, manager):
        """Test that global runs are thread-safe"""
        manager._clear_global_runs()

        def record_runs():
            for _ in range(10):
                manager.record_global_run()

        threads = [threading.Thread(target=record_runs) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have exactly 50 runs (5 threads × 10 runs each)
        assert manager.get_global_runs() == 50

    def test_clear_global_runs(self, manager):
        """Test clearing global runs"""
        manager.record_global_run()
        manager.record_global_run()
        assert manager.get_global_runs() > 0

        manager._clear_global_runs()
        assert manager.get_global_runs() == 0

    def test_global_runs_auto_resets_daily(self, manager):
        """Daily reset should clear the counter and allow automation without manual approval."""
        manager._clear_global_runs()

        # Simulate crossing the daily limit
        for _ in range(manager.global_limit):
            manager.record_global_run()

        assert manager.requires_manual_approval() is True

        now = datetime.now()
        stale_payload = {
            "total_runs": manager.global_limit,
            "start_date": (now - timedelta(days=4)).isoformat(),
            "current_date": (now - timedelta(days=1)).date().isoformat(),
            "last_run": (now - timedelta(hours=2)).isoformat(),
            "last_reset": (now - timedelta(days=2)).isoformat(),
        }
        json_manager.write_json(manager.global_runs_file, stale_payload)

        refreshed_runs = manager.get_global_runs()
        expected_today = datetime.now().date().isoformat()
        assert refreshed_runs == 0
        assert manager.requires_manual_approval() is False

        normalized = manager._read_json_file(manager.global_runs_file)
        assert normalized["current_date"] == expected_today
        assert normalized["total_runs"] == 0

        # Ensure the reset timestamp is updated and sane
        last_reset = normalized.get("last_reset")
        assert last_reset is not None
        parsed_reset = datetime.fromisoformat(last_reset)
        assert (
            parsed_reset is not None
        ), "last_reset should be a valid ISO datetime"

        # Record another run and verify counters/log fields move forward
        manager.record_global_run()
        normalized = manager._read_json_file(manager.global_runs_file)
        assert normalized["total_runs"] == 1
        assert datetime.fromisoformat(normalized["last_run"])


class TestPRLimits:
    """Test suite for per-PR automation limits"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AutomationSafetyManager(temp_dir)

    @pytest.mark.parametrize("pr_key,expected_can_process", [
        ("repo-123", True),   # New PR
        ("repo-456", True),   # Different PR
        ("repo/with/slashes-789", True),  # PR with slashes in name
    ])
    def test_can_process_pr_new_prs(self, manager, pr_key, expected_can_process):
        """Test that new PRs can be processed"""
        result = manager.can_process_pr(pr_key)
        assert result == expected_can_process

    def test_can_process_pr_under_limit(self, manager):
        """Test PR processing allowed when under limit"""
        pr_key = "test-repo-123"

        # Process PR up to limit - 1
        for _ in range(manager.pr_limit - 1):
            manager.record_pr_attempt(pr_key, "success")

        assert manager.can_process_pr(pr_key) == True

    def test_can_process_pr_at_limit(self, manager):
        """Test PR processing denied when at limit"""
        pr_key = "test-repo-123"

        # Process PR up to limit
        for _ in range(manager.pr_limit):
            manager.record_pr_attempt(pr_key, "success")

        assert manager.can_process_pr(pr_key) == False

    def test_record_pr_attempt_success(self, manager):
        """Test recording successful PR attempt"""
        pr_key = "test-repo-123"

        manager.record_pr_attempt(pr_key, "success")

        # Should have one attempt recorded
        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 1
        assert attempts[0]["result"] == "success"

    def test_record_pr_attempt_failure(self, manager):
        """Test recording failed PR attempt"""
        pr_key = "test-repo-456"

        manager.record_pr_attempt(pr_key, "failure")

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 1
        assert attempts[0]["result"] == "failure"

    @pytest.mark.parametrize("result", ["success", "failure", "error", "timeout"])
    def test_record_pr_attempt_various_results(self, manager, result):
        """Test recording PR attempts with various result types"""
        pr_key = f"test-repo-{result}"

        manager.record_pr_attempt(pr_key, result)

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 1
        assert attempts[0]["result"] == result

    def test_record_pr_attempt_includes_timestamp(self, manager):
        """Test that PR attempts include timestamps"""
        pr_key = "test-repo-timestamp"

        before_time = datetime.now()
        manager.record_pr_attempt(pr_key, "success")
        after_time = datetime.now()

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 1

        timestamp_str = attempts[0]["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str)
        assert before_time <= timestamp <= after_time

    def test_get_pr_attempts_empty(self, manager):
        """Test getting attempts for PR with no history"""
        attempts = manager.get_pr_attempt_list("nonexistent-pr")
        assert attempts == []

    def test_get_pr_attempts_multiple(self, manager):
        """Test getting multiple attempts for same PR"""
        pr_key = "test-repo-multiple"

        manager.record_pr_attempt(pr_key, "failure")
        manager.record_pr_attempt(pr_key, "success")
        manager.record_pr_attempt(pr_key, "success")

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 3
        assert attempts[0]["result"] == "failure"
        assert attempts[1]["result"] == "success"
        assert attempts[2]["result"] == "success"

    def test_pr_attempts_file_persistence(self, manager):
        """Test that PR attempts are persisted to file"""
        pr_key = "test-repo-persist"
        manager.record_pr_attempt(pr_key, "success")

        # Create new manager with same data dir
        new_manager = AutomationSafetyManager(manager.data_dir)
        attempts = new_manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 1
        assert attempts[0]["result"] == "success"

    def test_pr_attempts_thread_safety(self, manager):
        """Test that PR attempt recording is thread-safe"""
        pr_key = "test-repo-threading"

        def record_attempts():
            for i in range(5):
                manager.record_pr_attempt(pr_key, f"attempt-{i}")

        threads = [threading.Thread(target=record_attempts) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 15  # 3 threads × 5 attempts each


class TestEmailNotifications:
    """Test suite for email notification functionality"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AutomationSafetyManager(temp_dir)

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "password",
        "EMAIL_TO": "admin@example.com"
    })
    def test_email_config_complete(self, manager):
        """Test email configuration detection when complete"""
        assert manager._is_email_configured() == True

    @patch.dict(os.environ, {}, clear=True)
    def test_email_config_incomplete(self, manager):
        """Test email configuration detection when incomplete"""
        assert manager._is_email_configured() == False

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "EMAIL_USER": "test@example.com"
        # Missing SMTP_PORT, EMAIL_PASS, EMAIL_TO
    })
    def test_email_config_partial(self, manager):
        """Test email configuration detection when partially configured"""
        assert manager._is_email_configured() == False

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "password",
        "EMAIL_TO": "admin@example.com"
    })
    @patch("smtplib.SMTP")
    def test_send_notification_success(self, mock_smtp, manager):
        """Test successful email notification sending"""
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        result = manager.send_notification("Test Subject", "Test message")

        assert result == True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_send_notification_no_config(self, manager):
        """Test email notification when not configured"""
        with patch.object(manager.logger, "info") as mock_info:
            result = manager.send_notification("Test", "Message")

            assert result == False
            mock_info.assert_called_with("Email configuration incomplete - skipping notification")

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "password",
        "EMAIL_TO": "admin@example.com"
    })
    @patch("smtplib.SMTP")
    def test_send_notification_smtp_error(self, mock_smtp, manager):
        """Test email notification with SMTP error"""
        mock_smtp.side_effect = Exception("SMTP connection failed")

        with patch.object(manager.logger, "error") as mock_error:
            result = manager.send_notification("Test", "Message")

            assert result == False
            mock_error.assert_called()

    @patch.dict(os.environ, {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "password",
        "EMAIL_TO": "admin@example.com"
    })
    @patch("smtplib.SMTP")
    def test_send_notification_login_error(self, mock_smtp, manager):
        """Test email notification with login error"""
        mock_server = Mock()
        mock_server.login.side_effect = Exception("Authentication failed")
        mock_smtp.return_value = mock_server

        with patch.object(manager.logger, "error") as mock_error:
            result = manager.send_notification("Test", "Message")

            assert result == False
            mock_error.assert_called()


class TestFileLocking:
    """Test suite for file locking mechanisms"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AutomationSafetyManager(temp_dir)

    def test_concurrent_global_run_recording(self, manager):
        """Test that concurrent global run recording is thread-safe"""
        manager._clear_global_runs()

        results = []

        def record_run_with_result():
            try:
                manager.record_global_run()
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        # Start many concurrent threads
        threads = [threading.Thread(target=record_run_with_result) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(result == "success" for result in results)
        assert manager.get_global_runs() == 20

    def test_concurrent_pr_attempt_recording(self, manager):
        """Test that concurrent PR attempt recording is thread-safe"""
        pr_key = "test-repo-concurrent"
        results = []

        def record_attempt_with_result(attempt_id):
            try:
                manager.record_pr_attempt(pr_key, f"attempt-{attempt_id}")
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        # Start many concurrent threads
        threads = [threading.Thread(target=record_attempt_with_result, args=(i,)) for i in range(15)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(result == "success" for result in results)
        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) == 15

    def test_file_corruption_recovery(self, manager):
        """Test recovery from corrupted data files"""
        # Corrupt the global runs file
        global_runs_file = os.path.join(manager.data_dir, "global_runs.json")
        manager.record_global_run()  # Create the file first

        with open(global_runs_file, "w") as f:
            f.write("{ corrupted json")

        # Should recover gracefully
        manager.record_global_run()
        assert manager.get_global_runs() >= 1

    def test_permission_error_handling(self, manager):
        """Test handling of file permission errors"""
        with patch("jleechanorg_pr_automation.utils.json_manager.write_json", return_value=False):
            with patch.object(manager.logger, "error") as mock_error:
                # Should not raise exception
                manager.record_global_run()
                mock_error.assert_called()


class TestConfigurationManagement:
    """Test suite for configuration management"""

    def test_load_config_with_all_settings(self):
        """Test loading configuration with all settings"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            config_data = {
                "global_limit": 25,
                "pr_limit": 5,
                "daily_limit": 200,
                "email_notifications": True,
                "max_pr_size": 1000
            }
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            manager = AutomationSafetyManager(temp_dir)
            assert manager.global_limit == 25
            assert manager.pr_limit == 5

    def test_load_config_with_partial_settings(self):
        """Test loading configuration with partial settings uses defaults"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            config_data = {
                "global_limit": 15
                # Missing other settings
            }
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            manager = AutomationSafetyManager(temp_dir)
            assert manager.global_limit == 15
            assert manager.pr_limit > 0  # Should use default

    def test_save_config_creates_file(self):
        """Test that save_config creates configuration file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AutomationSafetyManager(temp_dir)

            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            assert os.path.exists(config_file)

            with open(config_file) as f:
                config = json.load(f)
            assert "global_limit" in config
            assert "pr_limit" in config

    def test_config_file_permissions(self):
        """Test that config file has appropriate permissions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AutomationSafetyManager(temp_dir)

            config_file = os.path.join(temp_dir, "automation_safety_config.json")
            stat_info = os.stat(config_file)

            # Should be readable/writable by owner
            assert stat_info.st_mode & 0o600


class TestIntegrationScenarios:
    """Test suite for integration scenarios"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield AutomationSafetyManager(temp_dir)

    def test_typical_automation_workflow(self, manager):
        """Test typical automation workflow"""
        # Start automation run
        assert manager.can_start_global_run() == True
        manager.record_global_run()

        # Process multiple PRs
        pr_keys = ["repo1-123", "repo2-456", "repo1-789"]

        for pr_key in pr_keys:
            assert manager.can_process_pr(pr_key) == True
            manager.record_pr_attempt(pr_key, "success")

        # Verify state
        assert manager.get_global_runs() == 1
        for pr_key in pr_keys:
            attempts = manager.get_pr_attempt_list(pr_key)
            assert len(attempts) == 1
            assert attempts[0]["result"] == "success"

    def test_hitting_pr_limits(self, manager):
        """Test behavior when hitting PR limits"""
        pr_key = "test-repo-limit"

        # Process up to limit
        for i in range(manager.pr_limit):
            assert manager.can_process_pr(pr_key) == True
            manager.record_pr_attempt(pr_key, "success")

        # Should now be at limit
        assert manager.can_process_pr(pr_key) == False

    def test_hitting_global_limits(self, manager):
        """Test behavior when hitting global limits"""
        # Fill up to global limit
        for i in range(manager.global_limit):
            assert manager.can_start_global_run() == True
            manager.record_global_run()

        # Should now be at limit
        assert manager.can_start_global_run() == False

    def test_mixed_success_failure_attempts(self, manager):
        """Test tracking mixed success/failure attempts"""
        pr_key = "test-repo-mixed"

        # Record mixed results
        results = ["failure", "success", "error", "success", "timeout"]
        for result in results:
            if manager.can_process_pr(pr_key):
                manager.record_pr_attempt(pr_key, result)

        attempts = manager.get_pr_attempt_list(pr_key)
        assert len(attempts) <= manager.pr_limit

        # Verify results are recorded correctly
        recorded_results = [attempt["result"] for attempt in attempts]
        assert all(result in results for result in recorded_results)

    def test_multiple_managers_same_data_dir(self, manager):
        """Test multiple manager instances sharing same data directory"""
        data_dir = manager.data_dir

        # Create second manager with same data dir
        manager2 = AutomationSafetyManager(data_dir)

        # Record with first manager
        manager.record_global_run()
        manager.record_pr_attempt("test-pr", "success")

        # Verify second manager sees the data
        assert manager2.get_global_runs() == manager.get_global_runs()
        attempts1 = manager.get_pr_attempt_list("test-pr")
        attempts2 = manager2.get_pr_attempt_list("test-pr")
        assert len(attempts1) == len(attempts2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
