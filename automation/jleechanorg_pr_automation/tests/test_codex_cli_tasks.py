"""Tests for CodexCloudAPI wrapper (codex_cli_tasks.py)."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from github-owner_pr_automation.openai_automation.codex_cli_tasks import (
    CodexCloudAPI,
)

# Sample JSON matching real `codex cloud list --json` output
SAMPLE_LIST_RESPONSE = {
    "tasks": [
        {
            "id": "task_e_abc123",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123",
            "title": "GitHub Mention: bump react-router",
            "status": "ready",
            "updated_at": "2026-02-08T02:47:27Z",
            "environment_id": None,
            "environment_label": "github-owner/your-project.com",
            "summary": {"files_changed": 1, "lines_added": 5, "lines_removed": 1},
            "is_review": True,
            "attempt_total": 1,
        },
        {
            "id": "task_e_def456",
            "url": "https://chatgpt.com/codex/tasks/task_e_def456",
            "title": "GitHub Mention: Schema Validation",
            "status": "pending",
            "updated_at": "2026-02-08T02:39:26Z",
            "environment_id": None,
            "environment_label": "github-owner/your-project.com",
            "summary": {"files_changed": 0, "lines_added": 0, "lines_removed": 0},
            "is_review": True,
            "attempt_total": 1,
        },
        {
            "id": "task_e_ghi789",
            "url": "https://chatgpt.com/codex/tasks/task_e_ghi789",
            "title": "Fix login bug",
            "status": "ready",
            "updated_at": "2026-02-08T01:00:00Z",
            "environment_id": None,
            "environment_label": "github-owner/your-project.com",
            "summary": {"files_changed": 2, "lines_added": 40, "lines_removed": 10},
            "is_review": False,
            "attempt_total": 1,
        },
    ],
    "cursor": "some-cursor-token",
}
class TestFilterGithubMentions(unittest.TestCase):
    """filter_github_mentions returns only GitHub Mention-prefixed tasks."""

    def test_filters_correctly(self):
        result = CodexCloudAPI.filter_github_mentions(SAMPLE_LIST_RESPONSE["tasks"])
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t["title"].startswith("GitHub Mention:") for t in result))

    def test_empty_list(self):
        result = CodexCloudAPI.filter_github_mentions([])
        self.assertEqual(result, [])

    def test_no_matches(self):
        tasks = [{"title": "Fix something", "status": "ready"}]
        result = CodexCloudAPI.filter_github_mentions(tasks)
        self.assertEqual(result, [])

    def test_missing_title_key(self):
        tasks = [{"status": "ready"}, {"title": "GitHub Mention: x"}]
        result = CodexCloudAPI.filter_github_mentions(tasks)
        self.assertEqual(len(result), 1)


class TestFilterByStatus(unittest.TestCase):
    """filter_by_status returns tasks matching given status."""

    def test_filter_ready(self):
        result = CodexCloudAPI.filter_by_status(SAMPLE_LIST_RESPONSE["tasks"], "ready")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t["status"] == "ready" for t in result))

    def test_filter_pending(self):
        result = CodexCloudAPI.filter_by_status(SAMPLE_LIST_RESPONSE["tasks"], "pending")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "task_e_def456")

    def test_filter_no_match(self):
        result = CodexCloudAPI.filter_by_status(SAMPLE_LIST_RESPONSE["tasks"], "error")
        self.assertEqual(result, [])


class TestListTasks(unittest.TestCase):
    """list_tasks calls codex cloud list --json and parses output."""

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_basic_list(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps(SAMPLE_LIST_RESPONSE),
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI()
        result = api.list_tasks(limit=5)

        self.assertIn("tasks", result)
        self.assertEqual(len(result["tasks"]), 3)
        self.assertEqual(result["cursor"], "some-cursor-token")

        # Verify correct CLI args
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "/usr/local/bin/codex")
        self.assertIn("--json", cmd)
        self.assertIn("--limit", cmd)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_list_with_env_filter(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps(SAMPLE_LIST_RESPONSE),
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI(env_id="env_abc")
        api.list_tasks()

        cmd = mock_run.call_args[0][0]
        self.assertIn("--env", cmd)
        self.assertIn("env_abc", cmd)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_list_with_cursor(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps(SAMPLE_LIST_RESPONSE),
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI()
        api.list_tasks(cursor="prev-cursor")

        cmd = mock_run.call_args[0][0]
        self.assertIn("--cursor", cmd)
        self.assertIn("prev-cursor", cmd)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_list_uses_minimum_120_second_timeout(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps(SAMPLE_LIST_RESPONSE),
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI(timeout=30)
        api.list_tasks()

        self.assertEqual(mock_run.call_args.kwargs["timeout"], 120)


class TestListAllTasks(unittest.TestCase):
    """list_all_tasks paginates through multiple pages."""

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_pagination_stops_on_empty_cursor(self, _mock_which, mock_run):
        page1 = {"tasks": [{"id": "t1", "title": "A", "status": "ready"}], "cursor": "c1"}
        page2 = {"tasks": [{"id": "t2", "title": "B", "status": "ready"}], "cursor": None}

        mock_run.side_effect = [
            MagicMock(stdout=json.dumps(page1), stderr="", returncode=0),
            MagicMock(stdout=json.dumps(page2), stderr="", returncode=0),
        ]
        api = CodexCloudAPI()
        result = api.list_all_tasks()

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_pagination_stops_on_empty_tasks(self, _mock_which, mock_run):
        page1 = {"tasks": [{"id": "t1"}], "cursor": "c1"}
        page2 = {"tasks": [], "cursor": "c2"}

        mock_run.side_effect = [
            MagicMock(stdout=json.dumps(page1), stderr="", returncode=0),
            MagicMock(stdout=json.dumps(page2), stderr="", returncode=0),
        ]
        api = CodexCloudAPI()
        result = api.list_all_tasks()

        self.assertEqual(len(result), 1)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_max_pages_limit(self, _mock_which, mock_run):
        page = {"tasks": [{"id": "t"}], "cursor": "next"}
        mock_run.return_value = MagicMock(
            stdout=json.dumps(page), stderr="", returncode=0,
        )
        api = CodexCloudAPI()
        result = api.list_all_tasks(max_pages=3)

        self.assertEqual(len(result), 3)
        self.assertEqual(mock_run.call_count, 3)


class TestGetStatus(unittest.TestCase):
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_returns_raw_output(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(
            stdout="[READY] GitHub Mention: bump deps\ngithub-owner/your-project.com",
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI()
        result = api.get_status("task_e_abc123")

        self.assertIn("READY", result)
        cmd = mock_run.call_args[0][0]
        self.assertIn("task_e_abc123", cmd)


class TestApplyDiff(unittest.TestCase):
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_success_returns_true(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(stdout="Applied.", stderr="", returncode=0)
        api = CodexCloudAPI()
        success, error = api.apply_diff("task_e_abc123")
        self.assertTrue(success)
        self.assertEqual(error, "")

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_failure_returns_false(self, _mock_which, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "codex", stderr="conflict"
        )
        api = CodexCloudAPI()
        success, error = api.apply_diff("task_e_abc123")
        self.assertFalse(success)
        self.assertIn("conflict", error)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_with_attempt_number(self, _mock_which, mock_run):
        mock_run.return_value = MagicMock(stdout="Applied.", stderr="", returncode=0)
        api = CodexCloudAPI()
        success, _ = api.apply_diff("task_e_abc123", attempt=2)
        self.assertTrue(success)

        cmd = mock_run.call_args[0][0]
        self.assertIn("--attempt", cmd)
        self.assertIn("2", cmd)


class TestConstructor(unittest.TestCase):
    @patch("shutil.which")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path")
    def test_raises_if_binary_not_found(self, mock_detect, mock_which):
        mock_which.return_value = None
        mock_detect.return_value = Path("/mock/repo")
        with self.assertRaises(FileNotFoundError) as ctx:
            CodexCloudAPI(codex_bin="nonexistent")
        self.assertIn("nonexistent", str(ctx.exception))

    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path")
    def test_resolves_binary_path(self, mock_detect, mock_which):
        mock_detect.return_value = Path("/mock/repo")
        api = CodexCloudAPI()
        self.assertEqual(api.codex_bin, "/usr/local/bin/codex")
        self.assertEqual(mock_which.call_count, 3)  # codex, git, gh


class TestRepoContextFallback(unittest.TestCase):
    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.ensure_base_clone")
    def test_resolve_base_repo_uses_fixpr_clone_strategy(
        self,
        mock_ensure_base_clone,
        _mock_resolve_repo_path,
        _mock_which,
        _mock_run,
    ):
        mock_ensure_base_clone.return_value = Path("/tmp/pr-orch-bases/your-project.com")
        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123",
            "environment_label": "github-owner/your-project.com",
        }

        resolved = api._resolve_base_repo_path(task)

        self.assertEqual(resolved, Path("/tmp/pr-orch-bases/your-project.com"))
        mock_ensure_base_clone.assert_called_once_with("github-owner/your-project.com")

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_find_existing_pr_branch_uses_repo_flag_without_git_cwd(self, _mock_resolve_repo_path, _mock_which, mock_run):
        mock_run.return_value = MagicMock(stdout="[]", stderr="", returncode=0)
        api = CodexCloudAPI()

        result = api._find_existing_pr_branch(
            task_title="GitHub Mention: Example",
            repo_full="github-owner/your-project.com",
        )

        self.assertIsNone(result)
        cmd = mock_run.call_args[0][0]
        self.assertIn("--repo", cmd)
        self.assertIn("github-owner/your-project.com", cmd)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_find_existing_pr_by_task_id_uses_deterministic_branch_lookup(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        mock_run,
    ):
        mock_run.return_value = MagicMock(
            stdout=json.dumps([
                {
                    "number": 5671,
                    "headRefName": "codex/2eee21eb",
                    "url": "https://github.com/github-owner/your-project.com/pull/5671",
                }
            ]),
            stderr="",
            returncode=0,
        )
        api = CodexCloudAPI()

        result = api._find_existing_pr_by_task_id(
            "task_e_69a7c8d2148c832f9f8cd4e52eee21eb",
            repo_full="github-owner/your-project.com",
        )

        self.assertEqual(
            result,
            ("codex/2eee21eb", "https://github.com/github-owner/your-project.com/pull/5671"),
        )
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[:4], ["gh", "pr", "list", "--json"])
        self.assertIn("--head", cmd)
        self.assertIn("codex/2eee21eb", cmd)
        self.assertNotIn("view", cmd)

    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/tmp/local-repo"))
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.ensure_base_clone")
    def test_resolve_base_repo_does_not_fallback_when_repo_full_present(
        self,
        mock_ensure_base_clone,
        _mock_resolve_repo_path,
        _mock_which,
    ):
        mock_ensure_base_clone.side_effect = subprocess.CalledProcessError(1, "git", stderr="clone failed")
        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123",
            "environment_label": "github-owner/your-project.com",
        }

        with self.assertRaises(RuntimeError):
            api._resolve_base_repo_path(task)

    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/tmp/local-repo"))
    def test_resolve_base_repo_uses_local_path_without_env_label(
        self,
        _mock_resolve_repo_path,
        _mock_which,
    ):
        api = CodexCloudAPI()
        task = {"id": "task_e_abc123"}

        resolved = api._resolve_base_repo_path(task)

        self.assertEqual(resolved, Path("/tmp/local-repo"))

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    @patch("tempfile.mkdtemp", return_value="/tmp/codex_test_worktree")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_create_worktree_falls_back_to_remote_branch_list(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        _mock_mkdtemp,
        _mock_rmtree,
        mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="no origin/HEAD", returncode=1),  # symbolic-ref fails
            MagicMock(stdout="", stderr="", returncode=1),  # remote show origin fails
            MagicMock(stdout="", stderr="", returncode=1),  # rev-parse main fails
            MagicMock(stdout="", stderr="", returncode=1),  # rev-parse master fails
            MagicMock(stdout="origin/develop\norigin/release/main\n", stderr="", returncode=0),  # for-each-ref fallback
            MagicMock(stdout="", stderr="", returncode=0),  # prune before add
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
        ]

        api = CodexCloudAPI()
        worktree_path, base_branch = api._create_worktree("codex/test123", Path("/tmp/base-repo"))

        self.assertEqual(base_branch, "origin/develop")
        self.assertEqual(str(worktree_path), "/tmp/codex_test_worktree")
        add_call = mock_run.call_args_list[-1][0][0]
        self.assertEqual(add_call[-1], "origin/develop")

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    @patch("tempfile.mkdtemp", return_value="/tmp/codex_test_worktree_retry")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_create_worktree_prunes_and_retries_after_add_failure(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        _mock_mkdtemp,
        _mock_rmtree,
        mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # prune before add
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            subprocess.TimeoutExpired(cmd=["git", "worktree", "add"], timeout=30),  # first add fails
            MagicMock(stdout="", stderr="", returncode=0),  # prune before retry
            MagicMock(stdout="", stderr="", returncode=0),  # second add succeeds
        ]

        api = CodexCloudAPI()
        worktree_path, base_branch = api._create_worktree("codex/test123", Path("/tmp/base-repo"))

        self.assertEqual(base_branch, "main")
        self.assertEqual(str(worktree_path), "/tmp/codex_test_worktree_retry")
        commands = [call.args[0] for call in mock_run.call_args_list]
        prune_calls = [cmd for cmd in commands if cmd[:5] == ["git", "-C", "/tmp/base-repo", "worktree", "prune"]]
        add_calls = [cmd for cmd in commands if cmd[:5] == ["git", "-C", "/tmp/base-repo", "worktree", "add"]]
        self.assertEqual(len(prune_calls), 2, commands)
        self.assertEqual(len(add_calls), 2, commands)
        add_timeouts = [call.kwargs["timeout"] for call in mock_run.call_args_list if call.args[0][:5] == ["git", "-C", "/tmp/base-repo", "worktree", "add"]]
        self.assertEqual(add_timeouts, [120, 120])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_prune_stale_worktrees_removes_missing_initializing_metadata(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        mock_run,
    ):
        with tempfile.TemporaryDirectory(prefix="codex-prune-") as temp_dir:
            base_repo = Path(temp_dir)
            metadata_dir = base_repo / ".git" / "worktrees" / "stale-entry"
            metadata_dir.mkdir(parents=True)
            (metadata_dir / "locked").write_text("initializing", encoding="utf-8")
            (metadata_dir / "gitdir").write_text("/tmp/definitely-missing-worktree/.git", encoding="utf-8")

            api = CodexCloudAPI()
            api._prune_stale_worktrees(base_repo)

            self.assertFalse(metadata_dir.exists())
            mock_run.assert_called_once_with(
                ["git", "-C", str(base_repo), "worktree", "prune", "--verbose"],
                capture_output=True,
                text=True,
                timeout=api.timeout,
            )

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    @patch("tempfile.mkdtemp", return_value="/tmp/codex_test_worktree_locked")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_create_worktree_retries_locked_missing_entry_with_double_force(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        _mock_mkdtemp,
        _mock_rmtree,
        mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # prune before add
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            subprocess.CalledProcessError(
                128,
                ["git", "worktree", "add"],
                stderr=(
                    "fatal: '/tmp/codex_test_worktree_locked' is a missing but locked worktree; "
                    "use 'add -f -f' to override"
                ),
            ),
            MagicMock(stdout="", stderr="", returncode=0),  # prune before retry
            MagicMock(stdout="", stderr="", returncode=0),  # forced add succeeds
        ]

        api = CodexCloudAPI()
        worktree_path, base_branch = api._create_worktree("codex/test123", Path("/tmp/base-repo"))

        self.assertEqual(base_branch, "main")
        self.assertEqual(str(worktree_path), "/tmp/codex_test_worktree_locked")
        commands = [call.args[0] for call in mock_run.call_args_list]
        add_calls = [cmd for cmd in commands if cmd[:5] == ["git", "-C", "/tmp/base-repo", "worktree", "add"]]
        self.assertEqual(add_calls[0], [
            "git", "-C", "/tmp/base-repo", "worktree", "add", "--detach", "--no-checkout", "-f", "-f",
            "/tmp/codex_test_worktree_locked", "main",
        ])
        self.assertEqual(add_calls[1], [
            "git", "-C", "/tmp/base-repo", "worktree", "add", "--detach", "--no-checkout", "-f", "-f",
            "/tmp/codex_test_worktree_locked", "main",
        ])

    @patch("subprocess.run")
    @patch("shutil.rmtree")
    @patch("tempfile.mkdtemp", return_value="/tmp/codex_test_worktree_no_heads")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=None)
    def test_create_worktree_errors_when_no_compatible_remote_branch(
        self,
        _mock_resolve_repo_path,
        _mock_which,
        _mock_mkdtemp,
        _mock_rmtree,
        mock_run,
    ):
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="no origin/HEAD", returncode=1),  # symbolic-ref fails
            MagicMock(stdout="", stderr="", returncode=1),  # remote show origin fails
            MagicMock(stdout="", stderr="", returncode=1),  # rev-parse main fails
            MagicMock(stdout="", stderr="", returncode=1),  # rev-parse master fails
            MagicMock(stdout="origin/HEAD\n", stderr="", returncode=0),  # only HEAD is available
        ]

        api = CodexCloudAPI()

        with self.assertRaises(RuntimeError):
            api._create_worktree("codex/test123", Path("/tmp/base-repo"))


class TestApplyAndPush(unittest.TestCase):
    """apply_and_push applies diff, commits, and pushes to remote."""

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_success_flow(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test successful apply + git workflow."""
        # Mock responses for:
        # 1. git rev-parse (find main branch)
        # 2. git worktree add
        # 3. git ls-remote
        # 4. git checkout -B
        # 5. codex cloud diff
        # 6. git apply --3way
        # 7. git add .
        # 8. git commit
        # 9. git push
        # 10. git worktree remove
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (empty = branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="diff content", stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git apply
            MagicMock(stdout="", stderr="", returncode=0),  # git add
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push
        ]

        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123",
            "title": "GitHub Mention: bump deps",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123",
        }
        result = api.apply_and_push(task)

        self.assertTrue(result["success"])
        self.assertEqual(result["branch"], "codex/e_abc123")
        self.assertEqual(mock_run.call_count, 10)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_apply_failure(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test failure when codex apply fails."""
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (empty = branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="diff content", stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="conflict", returncode=1),  # git apply fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertFalse(result["success"])
        self.assertIn("conflict", result["error"])
        self.assertTrue(result["fallback_to_pr"])

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_apply_corrupt_patch_disables_pr_fallback(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Malformed diffs should fail without attempting the PR fallback path."""
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (empty = branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="diff content", stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="error: corrupt patch at line 396", returncode=1),  # git apply --3way fails
            MagicMock(stdout="", stderr="error: corrupt patch at line 396", returncode=1),  # git apply retry fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertFalse(result["success"])
        self.assertIn("corrupt patch", result["error"])
        self.assertFalse(result["fallback_to_pr"])

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_git_push_failure(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test failure when git push fails."""
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (empty = branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="diff content", stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git apply
            MagicMock(stdout="", stderr="", returncode=0),  # git add
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            subprocess.CalledProcessError(1, "git push", stderr="rejected"),  # git push fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertFalse(result["success"])
        self.assertIn("rejected", result["error"])

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_apply_and_push_uses_detached_remote_checkout_and_head_push_for_new_branch(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """New branch apply+push should avoid local branch attachment entirely."""
        mock_run.side_effect = [
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (empty = branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout --detach origin/main
            MagicMock(stdout="diff content", stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git apply
            MagicMock(stdout="", stderr="", returncode=0),  # git add
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push HEAD:branch
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertTrue(result["success"])
        commands = [call.args[0] for call in mock_run.call_args_list]
        self.assertTrue(
            any(cmd[0] == "git" and ("checkout" in cmd or "switch" in cmd) and "--detach" in cmd and "origin/main" in cmd for cmd in commands),
            commands,
        )
        self.assertTrue(
            any(cmd[0] == "git" and "push" in cmd and "HEAD:codex/e_abc123" in cmd for cmd in commands),
            commands,
        )


class TestCreatePRFromDiff(unittest.TestCase):
    """create_pr_from_diff creates PR from diff using git apply --3way."""

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_success_without_conflicts(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test successful PR creation without conflicts."""
        diff_text = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old line
+new line"""

        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git ls-remote (branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -B
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way (success)
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote before push (branch_on_remote check)
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="https://github.com/org/repo/pull/123\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment (metadata)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree remove
        ]

        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123def",
            "title": "Github Mention: bump deps",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123def",
            "summary": {"files_changed": 1, "lines_added": 5, "lines_removed": 1},
        }
        result = api.create_pr_from_diff(task)

        self.assertTrue(result["success"])
        self.assertEqual(result["branch"], "codex/bc123def")  # Last 8 chars of task_e_abc123def
        self.assertEqual(result["pr_url"], "https://github.com/org/repo/pull/123")
        self.assertFalse(result["has_conflicts"])
        self.assertFalse(result["updated_existing"])
        self.assertEqual(mock_run.call_count, 16)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_update_existing_pr(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test updating an existing PR instead of creating new one."""
        diff_text = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old line
+new line"""

        # Mock gh pr list to return an existing PR
        existing_prs_json = json.dumps([
            {
                "number": 4989,
                "title": "Condense and improve divine leverage system documentation",
                "headRefName": "claude/divine-system-cleanup-8jqKL",
                "url": "https://github.com/org/repo/pull/4989"
            }
        ])

        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by task_id)
            MagicMock(stdout=existing_prs_json, stderr="", returncode=0),  # gh pr list (found by title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git fetch
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout --detach
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way (success)
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="deadbeef\trefs/heads/claude/divine-system-cleanup-8jqKL\n", stderr="", returncode=0),  # ls-remote before push
            MagicMock(stdout="", stderr="", returncode=0),  # git push --force-with-lease
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment (update metadata)
        ]

        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123def",
            "title": "Github Mention: Condense and improve divine leverage system documentation",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123def",
            "summary": {"files_changed": 1, "lines_added": 5, "lines_removed": 1},
        }
        result = api.create_pr_from_diff(task)

        self.assertTrue(result["success"])
        self.assertEqual(result["branch"], "claude/divine-system-cleanup-8jqKL")  # Uses existing branch!
        self.assertEqual(result["pr_url"], "https://github.com/org/repo/pull/4989")  # Uses existing PR URL!
        self.assertFalse(result["has_conflicts"])
        self.assertTrue(result["updated_existing"])  # This is the key flag
        self.assertEqual(mock_run.call_count, 15)
        commands = [call.args[0] for call in mock_run.call_args_list]
        self.assertTrue(
            any(
                cmd[0] == "git"
                and ("checkout" in cmd or "switch" in cmd)
                and "--detach" in cmd
                and "origin/claude/divine-system-cleanup-8jqKL" in cmd
                for cmd in commands
            ),
            commands,
        )
        self.assertTrue(
            any(
                cmd[0] == "git"
                and "push" in cmd
                and "--force-with-lease" in cmd
                and "origin" in cmd
                and "HEAD:claude/divine-system-cleanup-8jqKL" in cmd
                for cmd in commands
            ),
            commands,
        )

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_update_existing_pr_returns_error_when_fetch_fails(
        self,
        _mock_exists,
        _mock_detect,
        _mock_which,
        _mock_prune,
        mock_run,
    ):
        """Existing PR updates should fail fast when remote branch fetch fails."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        existing_prs_json = json.dumps(
            [
                {
                    "number": 4989,
                    "title": "Github Mention: Existing PR",
                    "headRefName": "claude/divine-system-cleanup-8jqKL",
                    "url": "https://github.com/org/repo/pull/4989",
                }
            ]
        )

        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout=existing_prs_json, stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            subprocess.CalledProcessError(1, "git fetch", stderr="fatal: couldn't find remote ref"),
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree remove (cleanup)
        ]

        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123def",
            "title": "Github Mention: Existing PR",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123def",
            "summary": {"files_changed": 1, "lines_added": 5, "lines_removed": 1},
        }
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("Failed to update existing PR branch", result["error"])
        self.assertEqual(result["task_id"], "task_e_abc123def")
        commands = [call.args[0] for call in mock_run.call_args_list if call.args]
        self.assertFalse(
            any(cmd[0] == "gh" and "create" in cmd for cmd in commands),
            commands,
        )

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_success_with_conflicts(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test successful PR creation with conflict markers."""
        diff_text = "diff --git a/file.py b/file.py\n..."

        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git ls-remote (branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -B
            MagicMock(stdout="", stderr="conflict", returncode=1),  # git apply --3way (conflict)
            MagicMock(stdout="file.py\n", stderr="", returncode=0),  # git diff --name-only --diff-filter=U
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout --theirs
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote before push
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="https://github.com/org/repo/pull/456\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree remove (cleanup)
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_xyz789", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertTrue(result["success"])
        self.assertTrue(result["has_conflicts"])
        self.assertFalse(result["updated_existing"])
        self.assertEqual(result["pr_url"], "https://github.com/org/repo/pull/456")
        self.assertEqual(mock_run.call_count, 18)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_corrupt_patch_fails_without_fallback_commit(
        self,
        _mock_exists,
        _mock_detect,
        _mock_which,
        _mock_prune,
        mock_run,
    ):
        diff_text = "diff --git a/file.py b/file.py\n..."
        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (branch missing)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="", stderr="error: corrupt patch at line 396", returncode=1),  # git apply --3way fails
            MagicMock(stdout="", stderr="error: corrupt patch at line 396", returncode=1),  # git apply retry fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_xyz789", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("Stale diff - target repo has changed", result["error"])
        self.assertEqual(mock_run.call_count, 10)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_conflict_fallback_fails_cleanly_when_nothing_to_commit(
        self,
        _mock_exists,
        _mock_detect,
        _mock_which,
        _mock_prune,
        mock_run,
    ):
        diff_text = "diff --git a/file.py b/file.py\n..."
        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (branch missing)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="", stderr="conflict", returncode=1),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git diff --name-only --diff-filter=U
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git diff --cached --quiet
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_xyz789", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("no staged changes", result["error"])
        self.assertEqual(mock_run.call_count, 12)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_no_diff_available(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test failure when no diff is available."""
        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout="No diff available for this task", stderr="", returncode=0),  # codex cloud diff
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("No diff available", result["error"])
        self.assertEqual(mock_run.call_count, 6)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_gh_pr_create_failure(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test failure when gh pr create fails."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git ls-remote (branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -B
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote before push
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            subprocess.CalledProcessError(1, "gh pr create", stderr="PR already exists"),  # gh fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("PR already exists", result["error"])
        self.assertEqual(mock_run.call_count, 15)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_metadata_comment_content(self, _mock_exists, _mock_detect, _mock_which, _mock_prune, mock_run):
        """Test that PR comment includes visible PR# and branch metadata."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        pr_url = "https://github.com/org/repo/pull/123"

        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (search by title)
            MagicMock(stdout="refs/remotes/origin/main", stderr="", returncode=0),  # git symbolic-ref
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D (cleanup)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # git ls-remote (branch doesn't exist)
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -B
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote before push
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout=f"{pr_url}\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment (metadata)
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree remove
        ]

        api = CodexCloudAPI()
        task = {
            "id": "task_e_abc123",
            "title": "Test task",
            "url": "https://chatgpt.com/codex/tasks/task_e_abc123",
            "summary": {"files_changed": 1, "lines_added": 10, "lines_removed": 5}
        }
        result = api.create_pr_from_diff(task)

        self.assertTrue(result["success"])

        # Verify gh pr comment was called with correct metadata
        comment_call = [call for call in mock_run.call_args_list if "pr" in str(call) and "comment" in str(call)]
        self.assertEqual(len(comment_call), 1, "Should post exactly one metadata comment")

        # Extract the comment body from the call
        comment_args = comment_call[0][0][0]  # First positional arg (the command list)
        comment_body_idx = comment_args.index("--body") + 1
        comment_body = comment_args[comment_body_idx]

        # Verify comment contains both HTML metadata and visible text
        self.assertIn("<!-- CODEX_METADATA", comment_body)
        self.assertIn("Task: task_e_abc123", comment_body)
        self.assertIn("PR: #123", comment_body)
        self.assertIn("Branch: codex/e_abc123", comment_body)  # Last 8 chars of task_id

        # Verify visible metadata text
        self.assertIn("📋", comment_body)
        self.assertIn("PR #123", comment_body)  # Visible in main text
        self.assertIn("Branch: `codex/e_abc123`", comment_body)  # Visible in main text

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_create_pr_resets_branch_with_checkout_b(
        self,
        _mock_exists,
        _mock_detect,
        _mock_which,
        _mock_prune,
        mock_run,
    ):
        """PR creation should use checkout -B to normalize branch state."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        mock_run.side_effect = [
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="refs/remotes/origin/main\n", stderr="", returncode=0),  # symbolic-ref origin/HEAD
            MagicMock(stdout="", stderr="", returncode=0),  # branch -D (best-effort)
            MagicMock(stdout="", stderr="", returncode=0),  # worktree add
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote (branch missing)
            MagicMock(stdout="", stderr="", returncode=0),  # checkout -B
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=1),  # git diff --cached --quiet
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # ls-remote before push
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="https://github.com/org/repo/pull/456\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment
            MagicMock(stdout="", stderr="", returncode=0),  # git worktree remove
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_xyz789", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertTrue(result["success"])
        commands = [call.args[0] for call in mock_run.call_args_list]
        self.assertTrue(
            any(cmd[0] == "git" and "checkout" in cmd and "-B" in cmd and "codex/e_xyz789" in cmd and "main" in cmd for cmd in commands),
            commands,
        )

    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    def test_checkout_branch_at_target_allows_branch_checked_out_in_another_worktree(
        self,
        _mock_detect,
        _mock_which,
    ):
        """checkout -B should tolerate the branch already being checked out elsewhere."""
        with tempfile.TemporaryDirectory(prefix="codex-cli-tdd-") as temp_dir:
            temp_path = Path(temp_dir)
            base_repo = temp_path / "base"
            sibling_worktree = temp_path / "sibling"
            target_worktree = temp_path / "target"

            subprocess.run(["git", "init", str(base_repo)], check=True, capture_output=True, text=True)
            subprocess.run(["git", "-C", str(base_repo), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(base_repo), "config", "user.name", "tester"], check=True)
            (base_repo / "tracked.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(base_repo), "add", "tracked.txt"], check=True)
            subprocess.run(
                ["git", "-C", str(base_repo), "commit", "-m", "init"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(base_repo), "branch", "codex/test123"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(base_repo), "worktree", "add", str(sibling_worktree), "codex/test123"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "-C", str(base_repo), "worktree", "add", "--detach", str(target_worktree), "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )

            api = CodexCloudAPI()
            api._checkout_branch_at_target(str(target_worktree), "codex/test123", "HEAD")

            current_branch = subprocess.check_output(
                ["git", "-C", str(target_worktree), "branch", "--show-current"],
                text=True,
            ).strip()
            self.assertEqual(current_branch, "codex/test123")

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    def test_checkout_branch_at_target_uses_minimum_120_second_timeout(
        self,
        _mock_detect,
        _mock_which,
        mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        api = CodexCloudAPI(timeout=30)
        api._checkout_branch_at_target("/tmp/worktree", "codex/test123", "main")

        self.assertEqual(mock_run.call_args.kwargs["timeout"], 120)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    def test_cleanup_worktree_uses_minimum_120_second_timeout(
        self,
        _mock_detect,
        _mock_which,
        _mock_exists,
        _mock_rmtree,
        _mock_prune,
        mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        api = CodexCloudAPI(timeout=30)
        api._cleanup_worktree(Path("/tmp/worktree"), Path("/tmp/base-repo"))

        self.assertEqual(mock_run.call_args.kwargs["timeout"], 120)

    @patch("subprocess.run")
    @patch.object(CodexCloudAPI, "_prune_stale_worktrees")
    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    @patch("github-owner_pr_automation.openai_automation.codex_cli_tasks.resolve_repo_path", return_value=Path("/mock/repo"))
    def test_cleanup_temp_codex_worktree_skips_git_remove(
        self,
        _mock_detect,
        _mock_which,
        _mock_exists,
        mock_rmtree,
        mock_prune,
        mock_run,
    ):
        api = CodexCloudAPI(timeout=30)
        api._cleanup_worktree(Path("/tmp/codex_codex_abc123"), Path("/tmp/base-repo"))

        mock_run.assert_not_called()
        mock_rmtree.assert_called_once_with(Path("/tmp/codex_codex_abc123"), ignore_errors=True)
        mock_prune.assert_called_once_with(Path("/tmp/base-repo"))


if __name__ == "__main__":
    unittest.main()
