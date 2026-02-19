#!/usr/bin/env python3
"""
Test Suite for Agent Monitor Restart Capabilities
Red-Green TDD implementation for converge agent restart functionality
"""

import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

agent_monitor_module = importlib.import_module("agent_monitor")
ConvergeAgentRestarter = agent_monitor_module.ConvergeAgentRestarter
AgentMonitor = agent_monitor_module.AgentMonitor


class TestConvergeAgentRestarter(unittest.TestCase):
    """Test cases for ConvergeAgentRestarter class"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Mock logger
        self.mock_logger = Mock()
        self.restarter = ConvergeAgentRestarter(self.mock_logger)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_is_converge_agent_with_converge_state_marker(self):
        """Test converge agent detection with converge_state.json marker"""
        # Create workspace with converge marker
        agent_name = "task-agent-test-1"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create converge state file
        converge_state_file = f"{workspace_path}/converge_state.json"
        with open(converge_state_file, "w") as f:
            json.dump({"status": "converging"}, f)

        # Should detect as converge agent
        self.assertTrue(self.restarter.is_converge_agent(agent_name))

    def test_is_converge_agent_with_progress_log_marker(self):
        """Test converge agent detection with convergence_progress.log marker"""
        agent_name = "task-agent-test-2"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create progress log file
        progress_log_file = f"{workspace_path}/convergence_progress.log"
        with open(progress_log_file, "w") as f:
            f.write("Progress log entry")

        # Should detect as converge agent
        self.assertTrue(self.restarter.is_converge_agent(agent_name))

    def test_is_converge_agent_with_converge_marker(self):
        """Test converge agent detection with .converge_marker"""
        agent_name = "task-agent-test-3"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create converge marker file
        marker_file = f"{workspace_path}/.converge_marker"
        with open(marker_file, "w") as f:
            f.write("converge")

        # Should detect as converge agent
        self.assertTrue(self.restarter.is_converge_agent(agent_name))

    def test_is_converge_agent_without_markers(self):
        """Test non-converge agent detection (no markers present)"""
        agent_name = "task-agent-regular"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # No converge markers
        self.assertFalse(self.restarter.is_converge_agent(agent_name))

    def test_detect_stuck_agent_non_converge_agent(self):
        """Test that non-converge agents are never considered stuck"""
        agent_name = "task-agent-regular"
        status = {"workspace_info": {"last_modified": datetime.now()}}

        # Should return False for non-converge agents
        self.assertFalse(self.restarter.detect_stuck_agent(agent_name, status))

    def test_detect_stuck_agent_recent_activity(self):
        """Test that agents with recent activity are not considered stuck"""
        agent_name = "task-agent-converge"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create converge marker
        marker_file = f"{workspace_path}/.converge_marker"
        with open(marker_file, "w") as f:
            f.write("converge")

        # Recent activity (within threshold)
        recent_time = datetime.now() - timedelta(minutes=5)
        status = {"workspace_info": {"last_modified": recent_time}, "recent_output": ["Working on task..."]}

        # Mock is_converge_agent to return True
        with patch.object(self.restarter, "is_converge_agent", return_value=True):
            self.assertFalse(self.restarter.detect_stuck_agent(agent_name, status))

    def test_detect_stuck_agent_old_activity_but_progress_indicators(self):
        """Test that agents with progress indicators in output are not stuck"""
        agent_name = "task-agent-converge"

        # Old activity but progress indicators in output
        old_time = datetime.now() - timedelta(minutes=15)
        status = {
            "workspace_info": {"last_modified": old_time},
            "recent_output": ["Processing data...", "Making progress on convergence"],
        }

        # Mock is_converge_agent to return True
        with patch.object(self.restarter, "is_converge_agent", return_value=True):
            self.assertFalse(self.restarter.detect_stuck_agent(agent_name, status))

    def test_detect_stuck_agent_truly_stuck(self):
        """Test detection of genuinely stuck converge agent"""
        agent_name = "task-agent-stuck"

        # Old activity and no progress indicators
        old_time = datetime.now() - timedelta(minutes=15)
        status = {"workspace_info": {"last_modified": old_time}, "recent_output": ["Error occurred", "Waiting..."]}

        # Mock is_converge_agent to return True
        with patch.object(self.restarter, "is_converge_agent", return_value=True):
            # Initialize last_activity tracking
            self.restarter.last_activity[agent_name] = old_time

            result = self.restarter.detect_stuck_agent(agent_name, status)
            self.assertTrue(result)

    def test_get_original_command_from_file(self):
        """Test extracting original command from workspace file"""
        agent_name = "task-agent-test"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create command file
        command_file = f"{workspace_path}/original_command.txt"
        expected_command = "/converge Complete all pending tasks"
        with open(command_file, "w") as f:
            f.write(expected_command)

        result = self.restarter.get_original_command(agent_name)
        self.assertEqual(result, expected_command)

    def test_get_original_command_fallback_converge(self):
        """Test fallback command generation for converge agents"""
        agent_name = "task-agent-converge-test"

        # No command file exists
        result = self.restarter.get_original_command(agent_name)
        self.assertEqual(result, "/converge Resume previous convergence task")

    def test_get_original_command_fallback_generic(self):
        """Test fallback command generation for generic agents"""
        agent_name = "task-agent-generic"

        # No command file exists
        result = self.restarter.get_original_command(agent_name)
        self.assertEqual(result, "/orch Resume task execution")

    @patch("subprocess.run")
    def test_restart_converge_agent_success(self, mock_subprocess):
        """Test successful agent restart"""
        agent_name = "task-agent-test"

        # Mock successful subprocess calls
        mock_subprocess.return_value = Mock(returncode=0)

        # Mock get_original_command
        with patch.object(self.restarter, "get_original_command", return_value="/converge test"):
            result = self.restarter.restart_converge_agent(agent_name)

        self.assertTrue(result)
        self.assertEqual(self.restarter.restart_attempts[agent_name], 1)

    @patch("subprocess.run")
    def test_restart_converge_agent_max_attempts_exceeded(self, mock_subprocess):
        """Test restart rejection when max attempts exceeded"""
        agent_name = "task-agent-test"

        # Set restart attempts to max
        self.restarter.restart_attempts[agent_name] = self.restarter.max_restart_attempts

        result = self.restarter.restart_converge_agent(agent_name)
        self.assertFalse(result)

        # Should not attempt restart
        mock_subprocess.assert_not_called()

    @patch("subprocess.run")
    def test_restart_converge_agent_subprocess_failure(self, mock_subprocess):
        """Test restart failure due to subprocess error"""
        agent_name = "task-agent-test"

        # Mock subprocess failure
        mock_subprocess.side_effect = Exception("Subprocess failed")

        with patch.object(self.restarter, "get_original_command", return_value="/converge test"):
            result = self.restarter.restart_converge_agent(agent_name)

        self.assertFalse(result)


class TestAgentMonitorIntegration(unittest.TestCase):
    """Test cases for AgentMonitor integration with restart capabilities"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Create mock log directory
        os.makedirs("/tmp/orchestration_logs", exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @patch("agent_monitor.ConvergeAgentRestarter")
    def test_agent_monitor_initializes_restarter(self, mock_restarter_class):
        """Test that AgentMonitor properly initializes ConvergeAgentRestarter"""
        mock_restarter = Mock()
        mock_restarter_class.return_value = mock_restarter

        monitor = AgentMonitor()

        # Should create restarter instance
        mock_restarter_class.assert_called_once_with(monitor.logger)
        self.assertEqual(monitor.restarter, mock_restarter)

    @patch("subprocess.run")
    def test_ping_all_agents_triggers_restart_for_stuck_agent(self, mock_subprocess):
        """Test that ping_all_agents triggers restart for stuck converge agents"""
        # Mock tmux list-sessions to return a test agent
        mock_subprocess.return_value = Mock(returncode=0, stdout="task-agent-stuck-converge")

        monitor = AgentMonitor()

        # Mock restarter methods
        monitor.restarter.detect_stuck_agent = Mock(return_value=True)
        monitor.restarter.restart_converge_agent = Mock(return_value=True)

        # Mock other AgentMonitor methods
        monitor.ping_agent = Mock(
            return_value={
                "agent_name": "task-agent-stuck-converge",
                "tmux_active": True,
                "workspace_info": {},
                "result_info": {},
            }
        )
        monitor.log_agent_status = Mock()

        # Execute ping_all_agents
        monitor.ping_all_agents()

        # Should attempt restart
        monitor.restarter.detect_stuck_agent.assert_called_once()
        monitor.restarter.restart_converge_agent.assert_called_once_with("task-agent-stuck-converge")


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_full_restart_workflow(self, mock_subprocess):
        """Test complete workflow from detection to restart"""
        agent_name = "task-agent-converge-e2e"

        # Create converge agent workspace (matching agent_monitor.py path structure)
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create converge marker
        marker_file = f"{workspace_path}/.converge_marker"
        with open(marker_file, "w") as f:
            f.write("converge")

        # Create original command file
        command_file = f"{workspace_path}/original_command.txt"
        with open(command_file, "w") as f:
            f.write("/converge Complete integration tests")

        # Mock logger and subprocess
        mock_logger = Mock()
        mock_subprocess.return_value = Mock(returncode=0)

        # Create restarter
        restarter = ConvergeAgentRestarter(mock_logger)

        # Simulate stuck agent
        old_time = datetime.now() - timedelta(minutes=15)
        restarter.last_activity[agent_name] = old_time

        status = {"workspace_info": {"last_modified": old_time}, "recent_output": ["Stuck in loop..."]}

        # Test detection
        self.assertTrue(restarter.is_converge_agent(agent_name))
        self.assertTrue(restarter.detect_stuck_agent(agent_name, status))

        # Test restart
        result = restarter.restart_converge_agent(agent_name)
        self.assertTrue(result)

        # Verify restart was attempted
        self.assertEqual(restarter.restart_attempts[agent_name], 1)


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
