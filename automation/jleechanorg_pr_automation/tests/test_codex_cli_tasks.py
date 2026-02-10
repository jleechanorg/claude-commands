"""Tests for CodexCloudAPI wrapper (codex_cli_tasks.py)."""

import json
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from jleechanorg_pr_automation.openai_automation.codex_cli_tasks import (
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
            "environment_label": "jleechanorg/worldarchitect.ai",
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
            "environment_label": "jleechanorg/worldarchitect.ai",
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
            "environment_label": "jleechanorg/worldarchitect.ai",
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
            stdout="[READY] GitHub Mention: bump deps\njleechanorg/worldarchitect.ai",
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
    def test_raises_if_binary_not_found(self):
        with patch("shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError) as ctx:
                CodexCloudAPI(codex_bin="nonexistent")
            self.assertIn("nonexistent", str(ctx.exception))

    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_resolves_binary_path(self, mock_which):
        api = CodexCloudAPI()
        self.assertEqual(api.codex_bin, "/usr/local/bin/codex")
        self.assertEqual(mock_which.call_count, 3)  # codex, git, gh


class TestApplyAndPush(unittest.TestCase):
    """apply_and_push applies diff, commits, and pushes to remote."""

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_success_flow(self, _mock_which, mock_run):
        """Test successful apply + git workflow."""
        # Mock responses for: codex apply, git rev-parse, git add, git commit, git push
        mock_run.side_effect = [
            MagicMock(stdout="Applied.", stderr="", returncode=0),  # codex apply
            MagicMock(stdout="feat/my-branch\n", stderr="", returncode=0),  # git rev-parse
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
        self.assertEqual(result["branch"], "feat/my-branch")
        self.assertEqual(mock_run.call_count, 5)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_apply_failure(self, _mock_which, mock_run):
        """Test failure when codex apply fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "codex", stderr="conflict")

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertFalse(result["success"])
        self.assertIn("conflict", result["error"])

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_git_push_failure(self, _mock_which, mock_run):
        """Test failure when git push fails."""
        mock_run.side_effect = [
            MagicMock(stdout="Applied.", stderr="", returncode=0),  # codex apply
            MagicMock(stdout="feat/branch\n", stderr="", returncode=0),  # git rev-parse
            MagicMock(stdout="", stderr="", returncode=0),  # git add
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            subprocess.CalledProcessError(1, "git push", stderr="rejected"),  # git push fails
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.apply_and_push(task)

        self.assertFalse(result["success"])
        self.assertIn("rejected", result["error"])


class TestCreatePRFromDiff(unittest.TestCase):
    """create_pr_from_diff creates PR from diff using git apply --3way."""

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_success_without_conflicts(self, _mock_which, mock_run):
        """Test successful PR creation without conflicts."""
        diff_text = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old line
+new line"""

        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="main\n", stderr="", returncode=0),  # git rev-parse (original branch)
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -b
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way (success)
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout (return)
            MagicMock(stdout="https://github.com/org/repo/pull/123\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment
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
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_update_existing_pr(self, _mock_which, mock_run):
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
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout=existing_prs_json, stderr="", returncode=0),  # gh pr list (existing PR found by title!)
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="main\n", stderr="", returncode=0),  # git rev-parse (original branch)
            MagicMock(stdout="", stderr="", returncode=0),  # git fetch
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout (existing branch)
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way (success)
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push --force-with-lease
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout (return)
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment
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
        self.assertEqual(mock_run.call_count, 17)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_success_with_conflicts(self, _mock_which, mock_run):
        """Test successful PR creation with conflict markers."""
        diff_text = "diff --git a/file.py b/file.py\n..."

        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="main\n", stderr="", returncode=0),  # git rev-parse
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -b
            MagicMock(stdout="", stderr="conflict", returncode=1),  # git apply --3way (conflict)
            MagicMock(stdout="file.py\n", stderr="", returncode=0),  # git diff --diff-filter=U
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout --theirs
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout
            MagicMock(stdout="https://github.com/org/repo/pull/456\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment
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
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_no_diff_available(self, _mock_which, mock_run):
        """Test failure when no diff is available."""
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout="No diff available for this task", stderr="", returncode=0),  # codex cloud diff
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com"}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("No diff available", result["error"])
        self.assertEqual(mock_run.call_count, 7)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_gh_pr_create_failure(self, _mock_which, mock_run):
        """Test failure when gh pr create fails."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (title)
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="main\n", stderr="", returncode=0),  # git rev-parse
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -b
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout
            subprocess.CalledProcessError(1, "gh pr create", stderr="PR already exists"),  # gh fails
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout (return from error)
            MagicMock(stdout="", stderr="", returncode=0),  # git branch -D
        ]

        api = CodexCloudAPI()
        task = {"id": "task_e_abc123", "title": "Test", "url": "https://example.com", "summary": {}}
        result = api.create_pr_from_diff(task)

        self.assertFalse(result["success"])
        self.assertIn("PR already exists", result["error"])
        self.assertEqual(mock_run.call_count, 17)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/local/bin/codex")
    def test_metadata_comment_content(self, _mock_which, mock_run):
        """Test that PR comment includes visible PR# and branch metadata."""
        diff_text = "diff --git a/file.py b/file.py\n..."
        pr_url = "https://github.com/org/repo/pull/123"

        mock_run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # git rev-parse --verify main
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout main
            MagicMock(stdout="", stderr="", returncode=0),  # git reset --hard origin/main
            MagicMock(stdout="", stderr="", returncode=0),  # git clean -fd
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (check existing by task_id)
            MagicMock(stdout="[]", stderr="", returncode=0),  # gh pr list (check existing by title)
            MagicMock(stdout=diff_text, stderr="", returncode=0),  # codex cloud diff
            MagicMock(stdout="main\n", stderr="", returncode=0),  # git rev-parse
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout -b
            MagicMock(stdout="", stderr="", returncode=0),  # git apply --3way
            MagicMock(stdout="", stderr="", returncode=0),  # git add -A
            MagicMock(stdout="", stderr="", returncode=0),  # git commit
            MagicMock(stdout="", stderr="", returncode=0),  # git push
            MagicMock(stdout="", stderr="", returncode=0),  # git checkout
            MagicMock(stdout=f"{pr_url}\n", stderr="", returncode=0),  # gh pr create
            MagicMock(stdout="", stderr="", returncode=0),  # gh pr comment (metadata)
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


if __name__ == "__main__":
    unittest.main()
