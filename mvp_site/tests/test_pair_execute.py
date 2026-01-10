#!/usr/bin/env python3
"""
Unit tests for scripts/pair_execute.py

Tests the dual-agent pair programming orchestration script.
Mocks all external dependencies (subprocess, file I/O, etc.) for CI/local parity.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

# Import the module under test

import scripts.pair_execute as pair_execute



PAIR_EXECUTE_AVAILABLE = True



class TestPairExecuteHelpers(unittest.TestCase):
    """Test helper functions in pair_execute.py"""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_generate_session_id(self):
        """Test session ID generation produces unique timestamped IDs."""
        session_id_1 = pair_execute.generate_session_id()
        session_id_2 = pair_execute.generate_session_id()

        # Session IDs should start with "pair-"
        self.assertTrue(session_id_1.startswith("pair-"))
        self.assertTrue(session_id_2.startswith("pair-"))

        # Session IDs should contain timestamps and randomness (format: pair-{timestamp}-{random})
        parts_1 = session_id_1.split("-")
        parts_2 = session_id_2.split("-")
        self.assertEqual(len(parts_1), 3)  # pair, timestamp, random
        self.assertEqual(len(parts_2), 3)
        self.assertTrue(parts_1[1].isdigit())  # timestamp is numeric
        self.assertTrue(parts_1[2].isdigit())  # random is numeric
        self.assertTrue(parts_2[1].isdigit())
        self.assertTrue(parts_2[2].isdigit())

    def test_create_session_directory(self):
        """Test session directory creation."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            session_id = "pair-test-12345"
            session_dir = pair_execute.create_session_directory(session_id)

            # Should create directory with session ID
            self.assertIn(session_id, str(session_dir))
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestPairExecuteFileLocking(unittest.TestCase):
    """Test file locking mechanisms."""
    # Class removed as acquire_file_lock and release_file_lock were removed in favor of fcntl
    pass


class TestPairExecuteBeadOperations(unittest.TestCase):
    """Test Beads file operations."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_create_bead_entry_success(self):
        """Test successful bead entry creation."""
        with patch("builtins.open", mock_open()) as mock_file, patch.object(
            Path, "mkdir"
        ), patch("fcntl.flock") as mock_flock:

            result = pair_execute.create_bead_entry(
                "bd-test-123", "Test task description"
            )

            self.assertTrue(result)
            # flock should be called twice (lock and unlock)
            self.assertEqual(mock_flock.call_count, 2)

            # Verify JSON was written
            handle = mock_file()
            written_data = "".join(
                call.args[0] for call in handle.write.call_args_list
            )
            self.assertIn("bd-test-123", written_data)
            self.assertIn("Test task description", written_data)

    def test_create_bead_entry_lock_failure(self):
        """Test bead creation fails gracefully when lock cannot be acquired (IOError)."""
        with patch("builtins.open", mock_open()) as mock_file, patch(
            "fcntl.flock"
        ) as mock_flock, patch.object(Path, "mkdir"):

            mock_flock.side_effect = OSError("Lock failed")

            result = pair_execute.create_bead_entry("bd-test-123", "Task")

            self.assertFalse(result)

    def test_update_bead_status_success(self):
        """Test successful bead status update."""
        existing_beads = [
            {
                "id": "bd-test-123",
                "title": "Test Task",
                "status": "in_progress",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]

        # Use MagicMock for file to support readlines
        mock_file_obj = MagicMock()
        mock_file_obj.readlines.return_value = [json.dumps(bead) + "\n" for bead in existing_beads]
        # Also need to support context manager
        mock_file_obj.__enter__.return_value = mock_file_obj
        mock_file_obj.__exit__.return_value = None

        with patch("builtins.open", return_value=mock_file_obj):
            with patch("pathlib.Path.exists") as mock_exists, patch(
                "fcntl.flock"
            ) as mock_flock, patch("os.fsync"):

                mock_exists.return_value = True

                result = pair_execute.update_bead_status("bd-test-123", "completed")

                self.assertTrue(result)
                self.assertEqual(mock_flock.call_count, 2)

                # Verify status was updated in written data
                written_calls = [
                    call for call in mock_file_obj.write.call_args_list if call.args
                ]
                if written_calls:
                    written_data = "".join(call.args[0] for call in written_calls)
                    self.assertIn("completed", written_data)

    def test_update_bead_status_not_found(self):
        """Test bead update when bead ID doesn't exist."""
        existing_beads = [
            {"id": "bd-other-456", "status": "in_progress"}
        ]
        
        mock_file_obj = MagicMock()
        mock_file_obj.readlines.return_value = [json.dumps(bead) + "\n" for bead in existing_beads]
        mock_file_obj.__enter__.return_value = mock_file_obj
        mock_file_obj.__exit__.return_value = None

        with patch(
            "builtins.open", return_value=mock_file_obj
        ), patch("pathlib.Path.exists") as mock_exists, patch(
            "fcntl.flock"
        ) as mock_flock:

            mock_exists.return_value = True

            result = pair_execute.update_bead_status("bd-test-123", "completed")

            # Should return False when bead not found
            self.assertFalse(result)


class TestPairExecuteAgentInstructions(unittest.TestCase):
    """Test agent instruction generation."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_generate_default_instructions(self):
        """Test default instruction generation includes required elements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)

            result = pair_execute.generate_default_instructions(
                "Implement user authentication", session_dir
            )

            # Verify structure
            self.assertIn("task", result)
            self.assertIn("coder_instructions", result)
            self.assertIn("verifier_instructions", result)
            self.assertIn("success_criteria", result)

            # Verify coder instructions include key elements
            coder_instr = result["coder_instructions"]
            self.assertIn("ITERATIVE session", coder_instr)
            self.assertIn("Beads MCP", coder_instr)
            self.assertIn("MCP Mail", coder_instr)
            self.assertIn("IMPLEMENTATION_READY", coder_instr)

            # Verify verifier instructions include key elements
            verifier_instr = result["verifier_instructions"]
            self.assertIn("ITERATIVE session", verifier_instr)
            self.assertIn("VERIFICATION_COMPLETE", verifier_instr)
            self.assertIn("VERIFICATION_FAILED", verifier_instr)
            self.assertIn("quality gatekeeper", verifier_instr)


class TestPairExecuteAgentLaunching(unittest.TestCase):
    """Test agent launching functions."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_launch_coder_agent_success(self):
        """Test successful coder agent launch."""
        with patch("subprocess.Popen") as mock_popen, patch(
            "builtins.open", mock_open()
        ), patch("time.sleep"), patch.object(Path, "mkdir"):

            # Mock process that stays running
            mock_process = MagicMock()
            mock_process.poll.return_value = None  # Still running
            mock_popen.return_value = mock_process

            success, agent_name = pair_execute.launch_coder_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test instructions",
                cli="claude",
            )

            self.assertTrue(success)
            self.assertEqual(agent_name, "claude-coder-pair-12345")
            mock_popen.assert_called_once()

            # Verify subprocess call uses list arguments (security)
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            self.assertIsInstance(cmd, list)
            self.assertIn("--agent-cli", cmd)
            self.assertIn("claude", cmd)

    def test_launch_coder_agent_failure(self):
        """Test coder agent launch failure when process exits immediately."""
        with patch("subprocess.Popen") as mock_popen, patch(
            "builtins.open", mock_open()
        ), patch("time.sleep"), patch.object(Path, "mkdir"):

            # Mock process that exits immediately
            mock_process = MagicMock()
            mock_process.poll.return_value = 1  # Exited
            mock_popen.return_value = mock_process

            success, agent_name = pair_execute.launch_coder_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test instructions",
                cli="claude",
            )

            self.assertFalse(success)

    def test_launch_verifier_agent_success(self):
        """Test successful verifier agent launch."""
        with patch("subprocess.Popen") as mock_popen, patch(
            "builtins.open", mock_open()
        ), patch("time.sleep"), patch.object(Path, "mkdir"):

            # Mock process that stays running
            mock_process = MagicMock()
            mock_process.poll.return_value = None  # Still running
            mock_popen.return_value = mock_process

            success, agent_name = pair_execute.launch_verifier_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test instructions",
                cli="codex",
            )

            self.assertTrue(success)
            self.assertEqual(agent_name, "codex-verifier-pair-12345")
            mock_popen.assert_called_once()

            # Verify subprocess call uses list arguments (security)
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            self.assertIsInstance(cmd, list)
            self.assertIn("--agent-cli", cmd)
            self.assertIn("codex", cmd)


class TestPairExecuteSubprocessSecurity(unittest.TestCase):
    """Test subprocess security (no shell=True, list args)."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_agent_launch_no_shell_injection(self):
        """Test that agent launch functions don't use shell=True."""
        with patch("subprocess.Popen") as mock_popen, patch(
            "builtins.open", mock_open()
        ), patch("time.sleep"), patch.object(Path, "mkdir"):

            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process

            # Launch both agents
            pair_execute.launch_coder_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test",
                cli="claude",
            )

            pair_execute.launch_verifier_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test",
                cli="codex",
            )

            # Verify all Popen calls use list arguments (not shell=True)
            for call_args in mock_popen.call_args_list:
                args, kwargs = call_args
                cmd = args[0]
                self.assertIsInstance(
                    cmd, list, "Subprocess calls must use list arguments"
                )
                # Verify no shell=True
                # If shell is present, it MUST be False. If absent, it defaults to False.
                if "shell" in kwargs:
                    self.assertFalse(kwargs["shell"], "shell=True must not be used")


class TestPairExecuteMonitorLaunching(unittest.TestCase):
    """Test background monitor launching."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_start_background_monitor_success(self):
        """Test successful monitor launch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen, patch(
                "builtins.open", mock_open()
            ), patch("time.sleep"):

                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_process.poll.return_value = None  # Process still running
                mock_popen.return_value = mock_process

                pid = pair_execute.start_background_monitor(
                    session_id="pair-12345",
                    coder_agent="claude-coder-pair-12345",
                    verifier_agent="codex-verifier-pair-12345",
                    bead_id="bd-12345",
                    session_dir=session_dir,
                )

                self.assertEqual(pid, 12345)
                mock_popen.assert_called_once()

                # Verify subprocess arguments
                args, kwargs = mock_popen.call_args
                cmd = args[0]
                self.assertIsInstance(cmd, list)
                self.assertIn("--session-id", cmd)
                self.assertIn("pair-12345", cmd)
                self.assertIn("--coder-agent", cmd)
                self.assertIn("--verifier-agent", cmd)

    def test_start_background_monitor_process_exits(self):
        """Test monitor launch when process exits immediately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen, patch(
                "builtins.open", mock_open()
            ), patch("time.sleep"):

                mock_process = MagicMock()
                mock_process.poll.return_value = 1  # Process exited
                mock_popen.return_value = mock_process

                pid = pair_execute.start_background_monitor(
                    session_id="pair-12345",
                    coder_agent="claude-coder-pair-12345",
                    verifier_agent="codex-verifier-pair-12345",
                    bead_id="bd-12345",
                    session_dir=session_dir,
                )

                self.assertIsNone(pid)

    def test_start_background_monitor_failure(self):
        """Test monitor launch failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)

            with patch("subprocess.Popen") as mock_popen, patch(
                "builtins.open", mock_open()
            ):

                mock_popen.side_effect = Exception("Launch failed")

                pid = pair_execute.start_background_monitor(
                    session_id="pair-12345",
                    coder_agent="claude-coder-pair-12345",
                    verifier_agent="codex-verifier-pair-12345",
                    bead_id="bd-12345",
                    session_dir=session_dir,
                )

                self.assertIsNone(pid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
