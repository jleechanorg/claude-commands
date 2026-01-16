import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add parent directory to path to import savetmp
sys.path.append(str(Path(__file__).parent.parent))

import savetmp


class TestSaveTmpGit(unittest.TestCase):
    def setUp(self):
        self.mock_subprocess = patch("savetmp.subprocess.run").start()
        # Mock logging_util in savetmp module
        self.mock_logging = patch("savetmp.logging_util").start()

    def tearDown(self):
        patch.stopall()

    def test_run_git_command_success(self):
        """Test _run_git_command returns stdout on success."""
        self.mock_subprocess.return_value = MagicMock(stdout="result\n", returncode=0)
        result = savetmp._run_git_command(["status"])
        self.assertEqual(result, "result")

    def test_run_git_command_empty_success(self):
        """Test _run_git_command returns empty string on success with no output."""
        self.mock_subprocess.return_value = MagicMock(stdout="\n", returncode=0)
        result = savetmp._run_git_command(["diff"])
        self.assertEqual(result, "")

    def test_run_git_command_failure(self):
        """Test _run_git_command returns None on failure."""
        self.mock_subprocess.side_effect = savetmp.subprocess.CalledProcessError(
            1, "cmd"
        )
        result = savetmp._run_git_command(["status"])
        self.assertIsNone(result)

    @patch("savetmp._run_git_commands_parallel")
    @patch("savetmp._run_git_command")
    def test_resolve_repo_info_happy_path(self, mock_run_cmd, mock_run_parallel):
        """Test _resolve_repo_info with origin/main present."""
        mock_run_parallel.return_value = {
            "repo_root": "/path/to/repo",
            "branch": "feature-branch",
            "head_commit": "abc1234",
            "origin_main": "def5678",
            "upstream": "origin/feature-branch",
        }
        # First call is 3-dot diff, return some files
        mock_run_cmd.side_effect = ["file1.py\nfile2.py"]

        repo_name, branch, provenance = savetmp._resolve_repo_info()

        self.assertEqual(repo_name, "repo")
        self.assertEqual(branch, "feature-branch")
        self.assertEqual(provenance["origin_main_commit"], "def5678")
        self.assertEqual(provenance["changed_files"], ["file1.py", "file2.py"])

        # Verify NO warning called
        self.mock_logging.warning.assert_not_called()
        # Verify debug call for success
        self.mock_logging.debug.assert_called()
        debug_messages = [call[0][0] for call in self.mock_logging.debug.call_args_list]
        self.assertTrue(
            any("Three-dot diff succeeded" in msg for msg in debug_messages),
            f"Expected 'Three-dot diff succeeded' in debug messages: {debug_messages}",
        )

    @patch("savetmp._run_git_commands_parallel")
    @patch("savetmp._run_git_command")
    def test_resolve_repo_info_missing_origin_main(
        self, mock_run_cmd, mock_run_parallel
    ):
        """Test _resolve_repo_info when origin/main is missing."""
        mock_run_parallel.return_value = {
            "repo_root": "/path/to/repo",
            "branch": "feature-branch",
            "head_commit": "abc1234",
            "origin_main": None,
            "upstream": None,
        }

        repo_name, branch, provenance = savetmp._resolve_repo_info()

        # Verify warning logged
        self.mock_logging.warning.assert_called()
        self.assertIn("No base ref found", self.mock_logging.warning.call_args[0][0])
        self.assertEqual(provenance["changed_files"], [])

    @patch("savetmp._run_git_commands_parallel")
    @patch("savetmp._run_git_command")
    def test_resolve_repo_info_head_is_base(self, mock_run_cmd, mock_run_parallel):
        """Test _resolve_repo_info when HEAD == origin/main."""
        mock_run_parallel.return_value = {
            "repo_root": "/path/to/repo",
            "branch": "main",
            "head_commit": "abc1234",
            "origin_main": "abc1234",
            "upstream": None,
        }

        repo_name, branch, provenance = savetmp._resolve_repo_info()

        self.assertEqual(provenance["changed_files"], [])
        mock_run_cmd.assert_not_called()

    @patch("savetmp._run_git_commands_parallel")
    @patch("savetmp._run_git_command")
    def test_resolve_repo_info_diff_fails(self, mock_run_cmd, mock_run_parallel):
        """Test _resolve_repo_info when diff commands fail."""
        mock_run_parallel.return_value = {
            "repo_root": "/path/to/repo",
            "branch": "feature",
            "head_commit": "abc1234",
            "origin_main": "def5678",
            "upstream": None,
        }
        # Both diffs fail (return None)
        mock_run_cmd.side_effect = [None, None]

        repo_name, branch, provenance = savetmp._resolve_repo_info()

        # Verify debug call for failure
        self.mock_logging.debug.assert_called()
        debug_messages = [call[0][0] for call in self.mock_logging.debug.call_args_list]
        self.assertTrue(
            any("Three-dot diff failed" in msg for msg in debug_messages),
            f"Expected 'Three-dot diff failed' in debug messages: {debug_messages}",
        )

        # Verify warning call for both failed
        self.mock_logging.warning.assert_called()
        self.assertIn(
            "Both git diff strategies failed", self.mock_logging.warning.call_args[0][0]
        )
        self.assertEqual(provenance["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
