import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestSaveTmpValidation(unittest.TestCase):
    def _write_file(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _write_checksum(self, path: Path) -> None:
        digest = savetmp.hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_suffix(path.suffix + ".sha256").write_text(
            f"{digest}  {path.name}\n",
            encoding="utf-8",
        )

    def test_validate_bundle_requires_run_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            evidence_path = run_dir / "evidence.md"
            self._write_file(evidence_path, "# Evidence\n")
            self._write_checksum(evidence_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertIn(
                "run.json is required for validated evidence bundles.", errors
            )
            self.assertEqual(warnings, [])

    def test_validate_bundle_requires_scenarios_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            run_json_path = run_dir / "run.json"
            self._write_file(run_json_path, '{"test_result": {"passed": true}}\n')
            self._write_checksum(run_json_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertIn(
                "run.json must include a top-level scenarios array for bundle validation.",
                errors,
            )
            self.assertEqual(warnings, [])

    def test_validate_bundle_accepts_scenarios_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            run_json_path = run_dir / "run.json"
            self._write_file(
                run_json_path,
                '{"scenarios": [{"name": "ok", "campaign_id": "camp-1", "errors": []}]}\n',
            )
            self._write_checksum(run_json_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_validate_bundle_accepts_empty_scenarios_array(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            run_json_path = run_dir / "run.json"
            self._write_file(
                run_json_path,
                '{"run_id": "ts", "work_name": "generic", "scenarios": []}\n',
            )
            self._write_checksum(run_json_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_validate_bundle_requires_run_json_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            run_json_path = run_dir / "run.json"
            self._write_file(run_json_path, '["not-an-object"]\n')
            self._write_checksum(run_json_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertIn("run.json must contain a top-level JSON object.", errors)
            self.assertEqual(warnings, [])

    def test_validate_bundle_requires_scenario_traceability_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            run_json_path = run_dir / "run.json"
            self._write_file(run_json_path, '{"scenarios": [{}]}\n')
            self._write_checksum(run_json_path)

            errors, warnings = savetmp._validate_bundle(run_dir, llm_claims=False)

            self.assertIn(
                "run.json scenarios[0].name must be a non-empty string.",
                errors,
            )
            self.assertIn(
                "run.json scenarios[0].campaign_id must be a non-empty string or integer.",
                errors,
            )
            self.assertIn("run.json scenarios[0].errors must be a list.", errors)
            self.assertEqual(warnings, [])


class TestSaveTmpMain(unittest.TestCase):
    def test_main_validate_creates_generic_run_json(self):
        work_name = f"generic-evidence-{next(tempfile._get_candidate_names())}"
        base_dir = Path("/tmp") / "repo" / "branch" / work_name
        try:
            with patch.object(savetmp, "_resolve_repo_info") as mock_repo_info:
                mock_repo_info.return_value = ("repo", "branch", None)
                exit_code = savetmp.main([work_name, "--validate", "--skip-git"])

            self.assertEqual(exit_code, 0)

            run_dirs = [path for path in base_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)

            run_dir = run_dirs[0]
            run_json_path = run_dir / "run.json"
            self.assertTrue(run_json_path.exists())

            run_json = savetmp.json.loads(run_json_path.read_text(encoding="utf-8"))
            self.assertEqual(run_json["work_name"], work_name)
            self.assertEqual(run_json["scenarios"], [])
            self.assertTrue((run_dir / "run.json.sha256").exists())
        finally:
            if base_dir.exists():
                savetmp.shutil.rmtree(base_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
