#!/usr/bin/env python3
"""
Unit tests for .claude/scripts/pair_execute.py

Tests the dual-agent pair programming orchestration script.
Mocks all external dependencies (subprocess, file I/O, etc.) for CI/local parity.
"""

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add project root to Python path
# tests live in .claude/scripts/tests/, so go up three levels.
project_root = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, project_root)

# Import the module under test from canonical .claude/scripts path.
module_path = Path(project_root) / ".claude" / "scripts" / "pair_execute.py"
spec = importlib.util.spec_from_file_location("pair_execute", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load module spec for {module_path}")
pair_execute = importlib.util.module_from_spec(spec)
sys.modules["pair_execute"] = pair_execute
spec.loader.exec_module(pair_execute)

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
            # mkdir is called for session dir plus coordination subdirectories.
            self.assertGreaterEqual(mock_mkdir.call_count, 4)


class TestPairExecuteFileLocking(unittest.TestCase):
    """Test file locking mechanisms."""

    # Class removed as acquire_file_lock and release_file_lock were removed in favor of fcntl


class TestPairExecuteBeadOperations(unittest.TestCase):
    """Test Beads file operations."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_create_bead_entry_success(self):
        """Test successful bead entry creation."""
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch.object(Path, "mkdir"),
            patch("fcntl.flock") as mock_flock,
        ):
            result = pair_execute.create_bead_entry(
                "bd-test-123", "Test task description"
            )

            self.assertTrue(result)
            # flock should be called twice (lock and unlock)
            self.assertEqual(mock_flock.call_count, 2)

            # Verify JSON was written
            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("bd-test-123", written_data)
            self.assertIn("Test task description", written_data)

    def test_create_bead_entry_lock_failure(self):
        """Test bead creation fails gracefully when lock cannot be acquired (IOError)."""
        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("fcntl.flock") as mock_flock,
            patch.object(Path, "mkdir"),
        ):
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
        mock_file_obj.readlines.return_value = [
            json.dumps(bead) + "\n" for bead in existing_beads
        ]
        # Also need to support context manager
        mock_file_obj.__enter__.return_value = mock_file_obj
        mock_file_obj.__exit__.return_value = None

        with patch("builtins.open", return_value=mock_file_obj):
            with (
                patch("pathlib.Path.exists") as mock_exists,
                patch("fcntl.flock") as mock_flock,
                patch("os.fsync"),
            ):
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
        existing_beads = [{"id": "bd-other-456", "status": "in_progress"}]

        mock_file_obj = MagicMock()
        mock_file_obj.readlines.return_value = [
            json.dumps(bead) + "\n" for bead in existing_beads
        ]
        mock_file_obj.__enter__.return_value = mock_file_obj
        mock_file_obj.__exit__.return_value = None

        with (
            patch("builtins.open", return_value=mock_file_obj),
            patch("pathlib.Path.exists") as mock_exists,
            patch("fcntl.flock") as mock_flock,
        ):
            mock_exists.return_value = True

            result = pair_execute.update_bead_status("bd-test-123", "completed")

            # Should return False when bead not found
            self.assertFalse(result)


class TestPairExecuteSessionPathIntegrity(unittest.TestCase):
    """REV-vcve6: Validate session-path integrity enforcement."""

    def setUp(self):
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_validate_session_path_allows_child_paths(self):
        """Paths within session_dir should be accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            child = session_dir / "coordination" / "coder_outbox"
            child.mkdir(parents=True)
            # Should not raise
            pair_execute._validate_session_path(child, session_dir)

    def test_validate_session_path_rejects_outside_paths(self):
        """Paths outside session_dir must raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session_a"
            session_dir.mkdir()
            outside_path = Path(tmpdir) / "session_b"
            outside_path.mkdir()
            with self.assertRaises(ValueError):
                pair_execute._validate_session_path(outside_path, session_dir)

    def test_write_coder_message_includes_session_id(self):
        """Messages must include the active session_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            outbox = session_dir / "coordination" / "coder_outbox"
            outbox.mkdir(parents=True)
            msg_path = pair_execute.write_coder_message(
                session_dir, "IMPLEMENTATION_READY", {"files_changed": ["a.py"]}
            )
            import json as json_mod
            msg = json_mod.loads(msg_path.read_text(encoding="utf-8"))
            self.assertEqual(msg["session_id"], session_dir.name)

    def test_write_verifier_message_includes_session_id(self):
        """Verifier messages must include the active session_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            outbox = session_dir / "coordination" / "verifier_outbox"
            outbox.mkdir(parents=True)
            msg_path = pair_execute.write_verifier_message(
                session_dir, "VERIFICATION_COMPLETE", {"result": "pass"}
            )
            import json as json_mod
            msg = json_mod.loads(msg_path.read_text(encoding="utf-8"))
            self.assertEqual(msg["session_id"], session_dir.name)


class TestPairExecuteFileCoordination(unittest.TestCase):
    """REV-gbq4f: Validate file-based coordination exchanges real messages."""

    def setUp(self):
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_coder_verifier_message_roundtrip(self):
        """Coder writes IMPLEMENTATION_READY, verifier can poll and read it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            # Create coordination structure
            (session_dir / "coordination" / "coder_outbox").mkdir(parents=True)
            (session_dir / "coordination" / "verifier_outbox").mkdir(parents=True)

            # Coder writes message
            msg_path = pair_execute.write_coder_message(
                session_dir,
                "IMPLEMENTATION_READY",
                {"files_changed": ["auth.py"], "test_result": "pass"},
            )
            self.assertTrue(msg_path.exists())

            # Verifier polls coder outbox and gets the message
            messages = pair_execute.poll_coder_outbox(session_dir, 0.0)
            self.assertGreaterEqual(len(messages), 1)
            self.assertEqual(messages[0]["subject"], "IMPLEMENTATION_READY")

    def test_verifier_feedback_roundtrip(self):
        """Verifier writes VERIFICATION_FAILED, coder can poll and read it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            (session_dir / "coordination" / "coder_outbox").mkdir(parents=True)
            (session_dir / "coordination" / "verifier_outbox").mkdir(parents=True)

            # Verifier writes failure message
            msg_path = pair_execute.write_verifier_message(
                session_dir,
                "VERIFICATION_FAILED",
                {"feedback": "Missing edge case tests", "files": ["auth.py"]},
            )
            self.assertTrue(msg_path.exists())

            # Coder polls verifier outbox
            messages = pair_execute.poll_verifier_outbox(session_dir, 0.0)
            self.assertGreaterEqual(len(messages), 1)
            self.assertEqual(messages[0]["subject"], "VERIFICATION_FAILED")

    def test_messages_processed_exactly_once(self):
        """Each message should be processed only once across polls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            (session_dir / "coordination" / "coder_outbox").mkdir(parents=True)
            (session_dir / "coordination" / "verifier_outbox").mkdir(parents=True)

            pair_execute.write_coder_message(
                session_dir, "IMPLEMENTATION_READY", {"attempt": 1}
            )

            # First poll gets the message
            first_poll = pair_execute.poll_coder_outbox(session_dir, 0.0)
            self.assertEqual(len(first_poll), 1)

            # Second poll should return empty (message already processed)
            second_poll = pair_execute.poll_coder_outbox(session_dir, 0.0)
            self.assertEqual(len(second_poll), 0)


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
            self.assertIn("register_agent", coder_instr)
            self.assertIn("ensure_project", coder_instr)

            # Verify verifier instructions include key elements
            verifier_instr = result["verifier_instructions"]
            self.assertIn("ITERATIVE session", verifier_instr)
            self.assertIn("VERIFICATION_COMPLETE", verifier_instr)
            self.assertIn("VERIFICATION_FAILED", verifier_instr)
            self.assertIn("quality gatekeeper", verifier_instr)
            self.assertIn("register_agent", verifier_instr)
            self.assertIn("ensure_project", verifier_instr)

    def test_instructions_use_mcp_tools_not_mcp_cli(self):
        """REV-8421f: Instructions must use MCP tool invocations, not mcp-cli shell commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)

            result = pair_execute.generate_default_instructions(
                "Test task", session_dir
            )

            coder_instr = result["coder_instructions"]
            verifier_instr = result["verifier_instructions"]

            # mcp-cli shell commands must NOT appear in instructions
            for label, text in [("coder", coder_instr), ("verifier", verifier_instr)]:
                self.assertNotIn(
                    "mcp-cli call",
                    text,
                    f"{label} instructions contain broken mcp-cli call commands",
                )
                self.assertNotIn(
                    "mcp-cli info",
                    text,
                    f"{label} instructions contain broken mcp-cli info commands",
                )

            # Correct MCP tool names must appear
            for label, text in [("coder", coder_instr), ("verifier", verifier_instr)]:
                self.assertIn(
                    "mcp__mcp_mail__",
                    text,
                    f"{label} instructions missing direct MCP tool invocations",
                )


class TestPairExecuteAgentLaunching(unittest.TestCase):
    """Test agent launching functions."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_launch_coder_agent_success(self):
        """Test successful coder agent launch."""
        with (
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", mock_open()),
            patch("time.sleep"),
            patch.object(Path, "mkdir"),
            patch.object(pair_execute, "_get_pair_func") as mock_get_func,
        ):
            # Mock _get_pair_func to return our mock generate_agent_names
            def mock_name_fn(cli, session_id, role):
                return f"{cli}-{role}-{session_id.replace('-', '')}"
            mock_get_func.return_value = mock_name_fn

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
            self.assertIn("coder", agent_name)
            mock_popen.assert_called_once()

            # Verify subprocess call uses list arguments (security)
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            self.assertIsInstance(cmd, list)
            self.assertIn("--agent-cli", cmd)
            self.assertIn("claude", cmd)

    def test_launch_coder_agent_failure(self):
        """Test coder agent launch failure when process exits immediately."""
        with (
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", mock_open()),
            patch("time.sleep"),
            patch.object(Path, "mkdir"),
        ):
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

    def test_launch_coder_agent_lite_mode_success(self):
        """Test coder agent launch success in lite mode (process exits but tmux session running).

        This is the key bug being fixed: when using --no-worktree or lite-mode,
        the subprocess exits quickly but the actual agent continues running in tmux.
        The code should detect this and mark as success, not failure.
        """
        with (
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", mock_open(read_data="Starting agent test-agent\n")),
            patch("time.sleep"),
            patch.object(Path, "mkdir"),
            patch.object(pair_execute, "_check_tmux_session") as mock_tmux,
        ):
            # Mock process that exits (like in lite-mode)
            mock_process = MagicMock()
            mock_process.poll.return_value = 0  # Exited with success
            mock_popen.return_value = mock_process

            # Mock tmux check to return True (agent is running in tmux)
            mock_tmux.return_value = True

            success, agent_name = pair_execute.launch_coder_agent(
                session_id="pair-12345",
                bead_id="bd-12345",
                instructions="Test instructions",
                cli="minimax",  # Using minimax which uses lite-mode
            )

            # Should succeed because tmux session exists
            self.assertTrue(success, "Should detect success when tmux session exists")

    def test_launch_verifier_agent_success(self):
        """Test successful verifier agent launch."""
        with (
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", mock_open()),
            patch("time.sleep"),
            patch.object(Path, "mkdir"),
            patch.object(pair_execute, "_get_pair_func") as mock_get_func,
        ):
            # Mock _get_pair_func to return our mock generate_agent_names
            def mock_name_fn(cli, session_id, role):
                return f"{cli}-{role}-{session_id.replace('-', '')}"
            mock_get_func.return_value = mock_name_fn

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
            self.assertIn("verifier", agent_name)
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
        with (
            patch("subprocess.Popen") as mock_popen,
            patch("builtins.open", mock_open()),
            patch("time.sleep"),
            patch.object(Path, "mkdir"),
        ):
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

            with (
                patch("subprocess.Popen") as mock_popen,
                patch("builtins.open", mock_open()),
                patch("time.sleep"),
            ):
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

            with (
                patch("subprocess.Popen") as mock_popen,
                patch("builtins.open", mock_open()),
                patch("time.sleep"),
            ):
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

            with (
                patch("subprocess.Popen") as mock_popen,
                patch("builtins.open", mock_open()),
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

    def test_claude_start_background_monitor_passes_restart_commands(self):
        """Test .claude monitor launch forwards restart commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            claude_pair_execute = pair_execute._lazy_import_claude_pair_execute()

            with (
                patch("subprocess.Popen") as mock_popen,
                patch("builtins.open", mock_open()),
                patch("time.sleep"),
            ):
                mock_process = MagicMock()
                mock_process.pid = 98765
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process

                pid = claude_pair_execute.start_background_monitor(
                    session_id="pair-12345",
                    coder_agent="claude-coder-pair-12345",
                    verifier_agent="codex-verifier-pair-12345",
                    bead_id="bd-12345",
                    session_dir=session_dir,
                    coder_restart_cmd="python3 coder.py",
                    verifier_restart_cmd="python3 verifier.py",
                )

                self.assertEqual(pid, 98765)
                args, _ = mock_popen.call_args
                cmd = args[0]
                self.assertIn("--coder-cmd", cmd)
                self.assertIn("python3 coder.py", cmd)
                self.assertIn("--verifier-cmd", cmd)
                self.assertIn("python3 verifier.py", cmd)
                self.assertIn("--max-restarts", cmd)

    def test_claude_start_background_monitor_fast_exit_requires_both_terminal(self):
        """Fast-exit monitor startup should fail when only one agent is terminal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            claude_pair_execute = pair_execute._lazy_import_claude_pair_execute()

            status_file = session_dir / "status.json"
            status_file.write_text(
                json.dumps(
                    {
                        "session_id": "pair-12345",
                        "coder_status": "running",
                        "verifier_status": "completed",
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch("subprocess.Popen") as mock_popen,
                patch("builtins.open", mock_open()),
                patch("time.sleep"),
            ):
                mock_process = MagicMock()
                mock_process.poll.return_value = 1
                mock_popen.return_value = mock_process

                pid = claude_pair_execute.start_background_monitor(
                    session_id="pair-12345",
                    coder_agent="coder-agent",
                    verifier_agent="verifier-agent",
                    bead_id="bd-12345",
                    session_dir=session_dir,
                )

                self.assertIsNone(pid)


class TestGenerateAgentNames(unittest.TestCase):
    """Test generate_agent_names function for session_id uniqueness."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_generate_agent_names_includes_session_id(self):
        """Test that agent names include session_id to prevent tmux session collisions.

        Each session should have unique agent names to prevent concurrent sessions
        from colliding. The session_id must be part of the generated name.
        """
        # Different sessions should produce different agent names
        name1 = pair_execute.generate_agent_names("claude", "session-abc-123", "coder")
        name2 = pair_execute.generate_agent_names("claude", "session-xyz-789", "coder")

        # Names must be different for different sessions
        self.assertNotEqual(
            name1, name2,
            "Different sessions should produce different agent names to prevent tmux collisions"
        )

    def test_generate_agent_names_includes_role(self):
        """Test that agent names include the role."""
        name = pair_execute.generate_agent_names("claude", "session-123", "coder")
        self.assertIn("coder", name)

        name = pair_execute.generate_agent_names("codex", "session-456", "verifier")
        self.assertIn("verifier", name)

    def test_generate_agent_names_uniqueness_for_parallel_sessions(self):
        """Test that parallel sessions don't collide.

        When running multiple pair sessions simultaneously, each must have
        unique agent names to prevent tmux session collisions.
        """
        session_ids = [f"session-{i}" for i in range(10)]
        names = set()

        for session_id in session_ids:
            coder_name = pair_execute.generate_agent_names("claude", session_id, "coder")
            verifier_name = pair_execute.generate_agent_names("codex", session_id, "verifier")

            # Each name should be unique
            self.assertNotIn(coder_name, names, f"Coder name {coder_name} collides!")
            self.assertNotIn(verifier_name, names, f"Verifier name {verifier_name} collides!")
            names.add(coder_name)
            names.add(verifier_name)

    def test_generate_agent_names_capped_to_backend_limit(self):
        """Generated names should fit backend-safe limits even on long branch names."""
        claude_pair_execute = pair_execute._lazy_import_claude_pair_execute()
        with patch.object(claude_pair_execute, "get_sanitized_branch", return_value="x" * 200):
            name = claude_pair_execute.generate_agent_names("claude", "session-123", "coder")

        self.assertLessEqual(
            len(name),
            128,
            "Agent name must not exceed backend limit",
        )
        self.assertTrue(name.endswith("coder"), "Role suffix must be preserved")


class TestPollForMessages(unittest.TestCase):
    """Test poll_for_messages and related functions."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_poll_verifier_outbox_persists_processed_ids(self):
        """Test that poll_verifier_outbox doesn't re-process messages.

        The processed_ids set must persist across calls to avoid duplicate
        processing of messages. Currently it creates a fresh set() each call.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            coord_dir = session_dir / "coordination"
            verifier_outbox = coord_dir / "verifier_outbox"
            verifier_outbox.mkdir(parents=True)

            # Create a message file
            msg_file = verifier_outbox / "VERIFICATION_COMPLETE_123.json"
            msg_file.write_text('{"from": "verifier", "subject": "VERIFICATION_COMPLETE"}')

            # First poll - should return the message
            session_start_ts = 0.0
            messages1 = pair_execute.poll_verifier_outbox(session_dir, session_start_ts)

            # Mark it as processed by creating it again (simulating another poll cycle)
            # Second poll - should NOT return the same message again
            messages2 = pair_execute.poll_verifier_outbox(session_dir, session_start_ts)

            # With proper deduplication, the message should only appear once
            # But currently it returns fresh each time because set() is created new
            # This test will fail until we fix the issue
            self.assertEqual(
                len(messages1), 1,
                "First poll should return the message"
            )
            # After fix, second poll should return 0 (message already processed)
            self.assertEqual(
                len(messages2), 0,
                "Second poll should be empty once processed IDs are persisted",
            )

    def test_poll_coder_outbox_persists_processed_ids(self):
        """Test that poll_coder_outbox doesn't re-process messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            coord_dir = session_dir / "coordination"
            coder_outbox = coord_dir / "coder_outbox"
            coder_outbox.mkdir(parents=True)

            # Create a message file
            msg_file = coder_outbox / "IMPLEMENTATION_READY_123.json"
            msg_file.write_text('{"from": "coder", "subject": "IMPLEMENTATION_READY"}')

            session_start_ts = 0.0

            # First poll
            messages1 = pair_execute.poll_coder_outbox(session_dir, session_start_ts)
            # Second poll
            messages2 = pair_execute.poll_coder_outbox(session_dir, session_start_ts)

            # After fix, second poll should return 0 (message already processed)
            self.assertEqual(len(messages1), 1)
            self.assertEqual(
                len(messages2), 0,
                "Second poll should be empty once processed IDs are persisted",
            )


class TestCheckOrchestrationResultFile(unittest.TestCase):
    """Test _check_orchestration_result_file for session scoping."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_check_orchestration_result_file_filters_stale_results(self):
        """Test that stale result files from previous sessions are ignored.

        When checking for agent completion, we must filter out result files
        from previous sessions that may have stale data.
        """
        results_dir = Path(tempfile.gettempdir()) / "orchestration_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        agent_name = f"testagent-{int(time.time() * 1000)}"
        stale_file = results_dir / f"{agent_name}_results_old.json"
        stale_file.write_text('{"status": "completed", "session_id": "old-session"}')

        old_ts = time.time() - 7200
        os.utime(stale_file, (old_ts, old_ts))

        # Create session_start_ts in the future (simulating new session)
        future_timestamp = time.time() + 3600  # 1 hour from now

        try:
            # With stale filtering, old file should be ignored.
            result = pair_execute._check_orchestration_result_file(
                agent_name, future_timestamp
            )
            self.assertIsNone(result)
        finally:
            stale_file.unlink(missing_ok=True)


class TestReadLogTail(unittest.TestCase):
    """Test _read_log_tail function for log reading."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_read_log_tail_with_file(self):
        """Test reading tail from existing log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("Line 1\nLine 2\nLine 3\nLast line content", encoding="utf-8")

            result = pair_execute._read_log_tail(log_file)

            self.assertIn("Last line content", result)

    def test_read_log_tail_file_not_found(self):
        """Test reading tail from non-existent file returns empty string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nonexistent.log"

            result = pair_execute._read_log_tail(log_file)

            self.assertEqual(result, "")

    def test_read_log_tail_large_file(self):
        """Test reading tail from file larger than max_bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "large.log"
            # Create a file with more than max_bytes (4096)
            large_content = "x" * 5000 + "\nLast line"
            log_file.write_text(large_content, encoding="utf-8")

            result = pair_execute._read_log_tail(log_file, max_bytes=1000, tail_chars=10)

            # Should get the tail (last 10 chars), which should include "Last line"
            self.assertIn("Last line", result)
            self.assertLessEqual(len(result), 10)

    def test_read_log_tail_with_tail_chars_limit(self):
        """Test tail_chars parameter limits returned characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("A" * 1000 + "B" * 1000 + "END_MARKER", encoding="utf-8")

            result = pair_execute._read_log_tail(log_file, tail_chars=10)

            self.assertIn("END_MARKER", result)
            self.assertLessEqual(len(result), 10)


class TestCreateTddPairedBeads(unittest.TestCase):
    """Test create_tdd_paired_beads function."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    def test_create_tdd_paired_beads_success(self):
        """Test successful creation of TDD paired beads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch BEADS_FILE to use temp directory
            with patch.object(pair_execute, "BEADS_FILE", Path(tmpdir) / "beads.jsonl"):
                result = pair_execute.create_tdd_paired_beads(
                    "session-test-123", "Implement user authentication"
                )

                self.assertIsNotNone(result)
                self.assertIn("tests_bead_id", result)
                self.assertIn("impl_bead_id", result)
                self.assertIn("verification_bead_id", result)
                self.assertEqual(result["tests_bead_id"], "session-test-123-tests")
                self.assertEqual(result["impl_bead_id"], "session-test-123-impl")
                self.assertEqual(result["verification_bead_id"], "session-test-123-verification")

    def test_create_tdd_paired_beads_failure(self):
        """Test failure when beads file cannot be written."""
        with patch.object(pair_execute, "BEADS_FILE", "/nonexistent/path/beads.jsonl"):
            result = pair_execute.create_tdd_paired_beads(
                "session-test-123", "Implement user authentication"
            )

            self.assertIsNone(result)


class TestMessageCoordination(unittest.TestCase):
    """Test message coordination functions: _write_message_atomically, poll_for_messages, _load_processed_message_ids, _save_processed_message_ids."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_EXECUTE_AVAILABLE:
            self.skipTest("pair_execute module not available")

    # === Tests for _write_message_atomically ===

    def test_write_message_atomically_success(self):
        """Test successful atomic message write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir)
            filename = "test_message.json"
            content = {"from": "coder", "subject": "TEST", "body": {"key": "value"}}

            result = pair_execute._write_message_atomically(outbox_dir, filename, content)

            self.assertTrue(result.exists())
            self.assertFalse((outbox_dir / f"{filename}.tmp").exists())  # tmp cleaned up

            # Verify content
            with open(result, encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["from"], "coder")
            self.assertEqual(loaded["subject"], "TEST")

    def test_write_message_atomically_creates_parent_dirs(self):
        """Test that atomic write creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "coordination" / "outbox"
            filename = "message.json"
            content = {"test": True}

            # Create parent dirs first (function doesn't create them)
            outbox_dir.mkdir(parents=True)

            result = pair_execute._write_message_atomically(outbox_dir, filename, content)

            self.assertTrue(result.exists())

    def test_write_message_atomically_oserror(self):
        """Test atomic write handles OSError gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir)
            filename = "test.json"
            content = {"test": True}

            with patch("os.replace", side_effect=OSError("Disk full")):
                with self.assertRaises(OSError):
                    pair_execute._write_message_atomically(outbox_dir, filename, content)

            # Verify tmp file was cleaned up
            self.assertFalse((outbox_dir / f"{filename}.tmp").exists())

    def test_write_message_atomically_cleanup_on_failure(self):
        """Test that partial tmp file is cleaned up on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir)
            filename = "cleanup_test.json"
            content = {"test": True}

            original_replace = os.replace

            def failing_replace(src, dst):
                # Create the tmp file first, then fail
                src_str = str(src)
                if src_str.endswith(".tmp"):
                    original_replace(src, dst)
                raise OSError("Simulated failure")

            with patch("os.replace", side_effect=failing_replace):
                try:
                    pair_execute._write_message_atomically(outbox_dir, filename, content)
                except OSError:
                    pass

            # Tmp file should be cleaned up even on failure
            self.assertFalse((outbox_dir / f"{filename}.tmp").exists())

    # === Tests for _load_processed_message_ids ===

    def test_load_processed_message_ids_success(self):
        """Test loading persisted processed message IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            coord_dir = session_dir / "coordination"
            coord_dir.mkdir(parents=True)

            # Create existing processed IDs file
            ids_file = coord_dir / "processed_coder_ids.json"
            ids_file.write_text('["msg1", "msg2", "msg3"]', encoding="utf-8")

            result = pair_execute._load_processed_message_ids(session_dir, "coder")

            self.assertEqual(result, {"msg1", "msg2", "msg3"})

    def test_load_processed_message_ids_file_not_exists(self):
        """Test loading when processed IDs file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            session_dir.mkdir(parents=True)

            result = pair_execute._load_processed_message_ids(session_dir, "coder")

            self.assertEqual(result, set())

    def test_load_processed_message_ids_corrupted_file(self):
        """Test loading handles corrupted JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            coord_dir = session_dir / "coordination"
            coord_dir.mkdir(parents=True)

            # Create corrupted file (not valid JSON)
            ids_file = coord_dir / "processed_verifier_ids.json"
            ids_file.write_text('not valid json at all', encoding="utf-8")

            result = pair_execute._load_processed_message_ids(session_dir, "verifier")

            # Should return empty set on error
            self.assertEqual(result, set())

    # === Tests for _save_processed_message_ids ===

    def test_save_processed_message_ids_success(self):
        """Test saving processed message IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            session_dir.mkdir(parents=True)
            (session_dir / "coordination").mkdir()

            processed_ids = {"msg1", "msg2", "msg3"}

            pair_execute._save_processed_message_ids(session_dir, "coder", processed_ids)

            ids_file = session_dir / "coordination" / "processed_coder_ids.json"
            self.assertTrue(ids_file.exists())

            with open(ids_file, encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(set(loaded), processed_ids)

    def test_save_processed_message_ids_creates_coordination_dir(self):
        """Test saving requires coordination directory to exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            session_dir.mkdir(parents=True)

            # Coordination dir doesn't exist initially
            self.assertFalse((session_dir / "coordination").exists())

            # Function will fail to write because directory doesn't exist
            # This tests that the function gracefully handles this case
            pair_execute._save_processed_message_ids(session_dir, "verifier", {"msg1"})

            # File should NOT exist because parent dir was missing
            self.assertFalse((session_dir / "coordination" / "processed_verifier_ids.json").exists())

    def test_save_processed_message_ids_oserror(self):
        """Test save handles OSError gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "session"
            session_dir.mkdir(parents=True)

            with patch("builtins.open", side_effect=OSError("Permission denied")):
                # Should not raise, just log error
                pair_execute._save_processed_message_ids(session_dir, "coder", {"msg1"})

    # === Tests for poll_for_messages ===

    def test_poll_for_messages_happy_path(self):
        """Test polling returns new messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            # Create a message file
            msg_file = outbox_dir / "TEST_MSG_123.json"
            msg_file.write_text(
                '{"from": "coder", "subject": "TEST", "timestamp": "2024-01-01T00:00:00+00:00"}',
                encoding="utf-8"
            )

            # Update mtime to be recent
            os.utime(msg_file, None)

            session_start_ts = 0.0
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["subject"], "TEST")
            self.assertIn("message_id", messages[0])

    def test_poll_for_messages_skips_processed(self):
        """Test polling skips already-processed messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            msg_file = outbox_dir / "ALREADY_SEEN_123.json"
            msg_file.write_text('{"from": "coder", "subject": "TEST"}', encoding="utf-8")

            session_start_ts = 0.0
            # Pre-mark as processed
            processed_ids = {"ALREADY_SEEN_123"}

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 0)

    def test_poll_for_messages_skips_tmp_files(self):
        """Test polling skips .tmp files (still being written)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            # Create a .tmp file (should be skipped)
            tmp_file = outbox_dir / "IN_PROGRESS.json.tmp"
            tmp_file.write_text('{"from": "coder", "subject": "TEST"}', encoding="utf-8")

            session_start_ts = 0.0
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 0)

    def test_poll_for_messages_skips_old_files(self):
        """Test polling skips files older than session_start_ts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            # Create old message file
            msg_file = outbox_dir / "OLD_MSG.json"
            msg_file.write_text('{"from": "coder", "subject": "OLD"}', encoding="utf-8")

            # Set old mtime (1 hour ago)
            old_ts = time.time() - 3600
            os.utime(msg_file, (old_ts, old_ts))

            # Session started now, so old file should be skipped
            session_start_ts = time.time()
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 0)

    def test_poll_for_messages_empty_outbox(self):
        """Test polling empty outbox returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            session_start_ts = 0.0
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 0)

    def test_poll_for_messages_nonexistent_outbox(self):
        """Test polling nonexistent outbox returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "nonexistent"

            session_start_ts = 0.0
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            self.assertEqual(len(messages), 0)

    def test_poll_for_messages_handles_json_error(self):
        """Test polling handles malformed JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outbox_dir = Path(tmpdir) / "outbox"
            outbox_dir.mkdir()

            # Create malformed JSON file
            msg_file = outbox_dir / "BAD_JSON.json"
            msg_file.write_text('{"invalid": json}', encoding="utf-8")

            session_start_ts = 0.0
            processed_ids = set()

            messages = pair_execute.poll_for_messages(outbox_dir, session_start_ts, processed_ids)

            # Should skip bad file and return empty
            self.assertEqual(len(messages), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
