"""Tests for multi-CLI support in the task dispatcher."""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from orchestration.task_dispatcher import TaskDispatcher


class TestAgentCliSelection(unittest.TestCase):
    """Verify that different CLIs can be selected and executed."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_detects_codex_cli_keyword(self):
        """Ensure codex keyword detection selects the Codex CLI."""
        task = "Please run codex exec --yolo against the new hooks"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_auto_selects_only_available_cli(self):
        """Fallback to installed CLI when task has no explicit preference."""

        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:

            def which_side_effect(command):
                if command == "claude":
                    return None
                if command == "codex":
                    return "/usr/local/bin/codex"
                return None

            mock_which.side_effect = which_side_effect

            task = "Please help with integration tests"
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)

        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_create_dynamic_agent_uses_codex_command(self):
        """Ensure codex agents execute via `codex exec --yolo`."""
        agent_spec = {
            "name": "task-agent-codex-test",
            "focus": "Validate Codex CLI integration",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "codex",
        }

        with patch.object(self.dispatcher, "_cleanup_stale_prompt_files"), \
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()), \
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-codex-test", MagicMock(returncode=0, stderr="")),
            ), \
            patch("os.makedirs"), \
            patch("os.chmod"), \
            patch("builtins.open", mock_open()), \
            patch("os.path.exists", return_value=False), \
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text, \
            patch("subprocess.run") as mock_run, \
            patch("shutil.which") as mock_which:

            def which_side_effect(command):
                known_binaries = {
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        self.assertGreater(len(mock_write_text.call_args_list), 0)
        script_contents = mock_write_text.call_args_list[0][0][0]
        self.assertIn("codex exec --yolo", script_contents)
        self.assertIn(
            "< /tmp/agent_prompt_task-agent-codex-test.txt",
            script_contents,
        )
        self.assertIn("Codex exit code", script_contents)

    def test_create_dynamic_agent_falls_back_when_requested_cli_missing(self):
        """Gracefully switch to an available CLI when the preferred one is absent."""

        agent_spec = {
            "name": "task-agent-fallback-test",
            "focus": "Fallback behavior",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "claude",
        }

        with patch.object(self.dispatcher, "_cleanup_stale_prompt_files"), \
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()), \
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-fallback-test", MagicMock(returncode=0, stderr="")),
            ), \
            patch("os.makedirs"), \
            patch("os.chmod"), \
            patch("builtins.open", mock_open()), \
            patch("os.path.exists", return_value=False), \
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text, \
            patch("subprocess.run") as mock_run, \
            patch("orchestration.task_dispatcher.shutil.which") as mock_which, \
            patch.object(self.dispatcher, "_ensure_mock_claude_binary", return_value=None):

            def which_side_effect(command):
                mapping = {
                    "claude": None,
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return mapping.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        self.assertEqual(agent_spec["cli"], "codex")
        script_contents = mock_write_text.call_args_list[0][0][0]
        self.assertIn("codex exec --yolo", script_contents)


if __name__ == "__main__":
    unittest.main()
