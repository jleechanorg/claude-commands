# Fix-Comment Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `--fix-comment` orchestration mode that fixes PR comments via a CLI agent, then posts review-request comments with a new fix-comment marker.

**Architecture:** Extend `JleechanorgPRMonitor` with fix-comment dispatch, skip logic via a new marker, and review comment posting; add a dispatch helper in `orchestrated_pr_runner.py`; wire CLI flag and target-pr handling.

**Tech Stack:** Python (unittest/pytest), GitHub CLI (`gh`), Orchestration TaskDispatcher.


### Task 1: Add failing tests for fix-comment markers + review comment

**Files:**
- Modify: `automation/jleechanorg_pr_automation/tests/test_pr_targeting.py`
- Modify: `automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py`

**Step 1: Write the failing tests**
Add tests:
```python
    def test_fix_comment_marker_detected_for_commit(self):
        monitor = JleechanorgPRMonitor()
        test_comment = (
            f"Queued\n{monitor.FIX_COMMENT_MARKER_PREFIX}abc123"
            f"{monitor.FIX_COMMENT_MARKER_SUFFIX}"
        )
        marker = monitor._extract_fix_comment_marker(test_comment)
        self.assertEqual(marker, "abc123")
```
```python
    def test_fix_comment_review_body_includes_greptile(self):
        pr_data = {"title": "Test PR", "author": {"login": "dev"}, "headRefName": "feat"}
        comment_body = self.monitor._build_fix_comment_review_body(
            "org/repo", 123, pr_data, "abc123"
        )
        self.assertIn("@greptile", comment_body)
        self.assertIn("@codex", comment_body)
        self.assertIn(self.monitor.FIX_COMMENT_MARKER_PREFIX, comment_body)
```

**Step 2: Run tests to verify they fail**
Run:
```
./run_tests.sh automation/jleechanorg_pr_automation/tests/test_pr_targeting.py \
  automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py
```
Expected: FAIL (missing fix-comment methods/constants).

**Step 3: Minimal implementation**
Implement in `jleechanorg_pr_monitor.py`:
```python
FIX_COMMENT_MARKER_PREFIX = "<!-- fix-comment-automation-commit:"
FIX_COMMENT_MARKER_SUFFIX = "-->"

def _extract_fix_comment_marker(self, comment_body: str) -> Optional[str]:
    ...

def _build_fix_comment_review_body(...):
    ... include @greptile and marker ...
```

**Step 4: Run tests to verify they pass**
Run same command as Step 2.

**Step 5: Commit**
```
git add automation/jleechanorg_pr_automation/tests/test_pr_targeting.py \
  automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py \
  automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py
git commit -m "test: add fix-comment marker/review tests"
```


### Task 2: Implement fix-comment dispatch + review comment flow

**Files:**
- Modify: `automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py`
- Modify: `automation/jleechanorg_pr_automation/orchestrated_pr_runner.py`
- Modify: `automation/jleechanorg_pr_automation/codex_config.py`

**Step 1: Write failing test**
Add to `test_pr_filtering_matrix.py`:
```python
    def test_fix_comment_mode_dispatches_agent(self):
        pr_data = {
            "title": "Test PR",
            "author": {"login": "dev"},
            "headRefName": "feat",
            "repositoryFullName": "org/repo",
        }
        with patch.object(self.monitor, "_get_pr_comment_state", return_value=("abc123", [])), \
             patch.object(self.monitor, "_has_fix_comment_comment_for_commit", return_value=False), \
             patch.object(self.monitor, "dispatch_fix_comment_agent", return_value=True):
            result = self.monitor._process_pr_fix_comment("org/repo", 123, pr_data, agent_cli="gemini")
            self.assertEqual(result, "posted")
```

**Step 2: Run test to verify it fails**
```
./run_tests.sh automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py
```
Expected: FAIL (missing fix-comment logic).

**Step 3: Implement minimal fix-comment flow**
- Add fix-comment marker constants in `codex_config.py`.
- Add dispatch helper in `orchestrated_pr_runner.py`:
```python
def dispatch_agent_for_pr_with_task(dispatcher, pr, task_description, agent_cli="claude") -> bool:
    ...
```
- Add in `jleechanorg_pr_monitor.py`:
  - `_has_fix_comment_comment_for_commit`, `_build_fix_comment_prompt_body`, `_build_fix_comment_review_body`.
  - `dispatch_fix_comment_agent` using `TaskDispatcher` + `ensure_base_clone` + `dispatch_agent_for_pr_with_task`.
  - `_process_pr_fix_comment` that skips if marker exists, dispatches agent, posts queued + final review comments, returns `posted`/`skipped`/`failed`.
  - `_count_codex_automation_comments` should count fix-comment markers too.

**Step 4: Run tests to verify they pass**
Run tests from Step 2 + Task 1 tests.

**Step 5: Commit**
```
git add automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py \
  automation/jleechanorg_pr_automation/orchestrated_pr_runner.py \
  automation/jleechanorg_pr_automation/codex_config.py \
  automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py
git commit -m "feat: add fix-comment orchestration workflow"
```


### Task 3: CLI integration + target PR handling

**Files:**
- Modify: `automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py`

**Step 1: Write failing test (if needed)**
If coverage exists, add a unit test to assert `--fix-comment` uses `_process_pr_fix_comment` when `--target-pr` is set. Otherwise, skip test and proceed with manual verification (note in PR summary).

**Step 2: Implement CLI wiring**
- Add `--fix-comment` flag.
- Wire `--fixpr-agent` into fix-comment flow.
- Ensure `process_single_pr_by_number` can call fix-comment path when flagged.
- Ensure `run_monitoring_cycle` routes to fix-comment processing when enabled.

**Step 3: Run smoke tests**
```
./run_tests.sh automation/jleechanorg_pr_automation/tests/test_pr_targeting.py \
  automation/jleechanorg_pr_automation/tests/test_pr_filtering_matrix.py
```
Expected: PASS.

**Step 4: Commit**
```
git add automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py
git commit -m "feat: add --fix-comment CLI and routing"
```
