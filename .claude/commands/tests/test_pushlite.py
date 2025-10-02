import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "claude_command_scripts" / "commands" / "pushlite.sh"

assert SCRIPT_PATH.exists(), f"pushlite script not found at {SCRIPT_PATH}"
assert os.access(SCRIPT_PATH, os.X_OK), f"pushlite script is not executable: {SCRIPT_PATH}"


class PushliteIntegrationTests(unittest.TestCase):
    def run_pushlite(self, workdir: Path) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.setdefault("COPILOT_WORKFLOW", "1")
        env.setdefault("SKIP_LINT", "true")
        result = subprocess.run(
            [str(SCRIPT_PATH), "-m", "Test commit"],
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
        return result

    def init_repo(self, base_dir: Path) -> tuple[Path, Path]:
        bare_repo = base_dir / "remote.git"
        work_repo = base_dir / "work"
        work_repo.mkdir()

        subprocess.run(["git", "init", "--bare", str(bare_repo)], check=True, stdout=subprocess.PIPE)
        subprocess.run(["git", "init", str(work_repo)], check=True, stdout=subprocess.PIPE)
        subprocess.run(["git", "-C", str(work_repo), "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", str(work_repo), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(work_repo), "remote", "add", "origin", str(bare_repo)], check=True)

        (work_repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(work_repo), "add", "tracked.txt"], check=True)
        subprocess.run(
            ["git", "-C", str(work_repo), "commit", "-m", "Initial"],
            check=True,
            stdout=subprocess.PIPE,
        )
        subprocess.run(["git", "-C", str(work_repo), "branch", "-M", "main"], check=True)
        subprocess.run(
            ["git", "-C", str(work_repo), "push", "-u", "origin", "main"],
            check=True,
            stdout=subprocess.PIPE,
        )

        return bare_repo, work_repo

    def test_untracked_and_modified_files_do_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            bare_repo, work_repo = self.init_repo(base_dir)

            # Modify tracked file and add a new untracked file
            (work_repo / "tracked.txt").write_text("initial\nchange\n", encoding="utf-8")
            (work_repo / "new_file.txt").write_text("content\n", encoding="utf-8")

            result = self.run_pushlite(work_repo)

            self.assertEqual(
                result.returncode,
                0,
                msg=f"pushlite failed with output:\n{result.stdout}",
            )

            # Ensure the push reached the remote by checking the bare repo has the commit
            log_output = subprocess.run(
                ["git", "--git-dir", str(bare_repo), "log", "--oneline", "main", "-1"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout
            self.assertIn("Test commit", log_output)

    def test_empty_staging_is_skipped_without_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            bare_repo, work_repo = self.init_repo(base_dir)

            (work_repo / "note.txt").write_text("n/a\n", encoding="utf-8")

            env = os.environ.copy()
            env.setdefault("COPILOT_WORKFLOW", "1")
            env.setdefault("SKIP_LINT", "true")
            cmd = [
                str(SCRIPT_PATH),
                "--include",
                "*.py",
                "-m",
                "Should not appear",
            ]
            result = subprocess.run(
                cmd,
                cwd=work_repo,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"pushlite failed with output:\n{result.stdout}",
            )

            log_output = subprocess.run(
                ["git", "--git-dir", str(bare_repo), "log", "--oneline", "main", "-1"],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout
            self.assertNotIn("Should not appear", log_output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
