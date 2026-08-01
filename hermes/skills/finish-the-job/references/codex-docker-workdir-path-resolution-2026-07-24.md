---
title: Codex P1 — module-relative file paths must resolve via os.path.dirname(__file__), never via repo-root prefix
date: 2026-07-24
verified-on: $GITHUB_REPOSITORY PR #8548 (companion-quest cadence injection refactor), Codex review comment id 3642406857
---

## Why this reference exists

When a PR adds a NEW module-relative file path (e.g. `$PROJECT_ROOT/prompts/injection/foo.md`)
loaded via `read_file_cached(path)`, the agent's instinct is to write
`os.path.join("mvp_site", constants.FOO_PATH)` because the on-disk layout
is `<repo>/$PROJECT_ROOT/...` and `read_file_cached` accepts repo-root-relative
paths in dev (`cwd=<repo>`).

In **production Docker**, `$PROJECT_ROOT/Dockerfile` sets `WORKDIR=/app/mvp_site`,
so a relative path `$PROJECT_ROOT/prompts/injection/foo.md` resolves to
`/app/$PROJECT_ROOT/$PROJECT_ROOT/prompts/injection/foo.md` — which does NOT exist
(the file is at `/app/$PROJECT_ROOT/prompts/injection/foo.md`). Every code
path that hits the new file raises `FileNotFoundError` on the first request.

Codex (CodeRabbit's chatgpt connector) caught this on PR #8548 as a P1.
The PR had merged-able green CI; the bug only fires in prod.

## The canonical pattern (verified on _load_instruction_file in $PROJECT_ROOT/agent_prompts.py:907)

For ANY module-relative file path that the build code reads via
`read_file_cached` or `open(...)`, use `os.path.dirname(__file__)`:

```python
file_path = os.path.join(
    os.path.dirname(__file__),       # module dir, e.g. /app/mvp_site
    constants.FOO_PATH,              # module-relative, e.g. "prompts/injection/foo.md"
)
content = read_file_cached(file_path)
```

This works under:
- Local dev: `cwd=<repo>`, `__file__=<repo>/$PROJECT_ROOT/agent_prompts.py` → resolves to `<repo>/$PROJECT_ROOT/prompts/injection/foo.md` ✓
- Docker: `cwd=/app/mvp_site`, `__file__=/app/$PROJECT_ROOT/agent_prompts.py` → resolves to `/app/$PROJECT_ROOT/prompts/injection/foo.md` ✓
- Tests: `cwd=/tmp/pr8548-wt-fix`, `__file__=<worktree>/$PROJECT_ROOT/agent_prompts.py` → resolves to `<worktree>/$PROJECT_ROOT/prompts/injection/foo.md` ✓

## Anti-pattern (what PR #8548 originally had)

```python
# ❌ Breaks in Docker ($PROJECT_ROOT/Dockerfile: WORKDIR=/app/mvp_site)
injection_path = os.path.join(
    "mvp_site", constants.LIVING_WORLD_COMPANION_CADENCE_PATH
)
```

In Docker, `read_file_cached` does `os.path.abspath(injection_path)` →
`/app/$PROJECT_ROOT/$PROJECT_ROOT/prompts/injection/living_world_companion_cadence.md`
which does not exist.

## Pre-merge audit checklist

Before pushing a PR that introduces a new `read_file_cached(constants.X_PATH)`
call site, run these checks in order:

1. **Grep for the anti-pattern** across `$PROJECT_ROOT/`:
   ```bash
   rg -n 'os\.path\.join\("mvp_site",' $PROJECT_ROOT/ -g '*.py'
   rg -n 'open\("$PROJECT_ROOT/' $PROJECT_ROOT/ -g '*.py'
   rg -n 'read_file_cached\("$PROJECT_ROOT/' $PROJECT_ROOT/ -g '*.py'
   ```
   Any hit is the same bug class.

2. **Compare against the canonical pattern** in `_load_instruction_file`:
   ```bash
   rg -n 'os\.path\.dirname\(__file__\)' $PROJECT_ROOT/agent_prompts.py | head -5
   ```
   The existing prompt-loading pattern uses module-relative resolution; any
   new file-loading code should match.

3. **Verify the path resolves correctly under Docker WORKDIR** by mental
   simulation: assume `cwd=/app/mvp_site` and check that the resulting
   `os.path.abspath(path)` ends with `prompts/injection/<file>.md`.

4. **Add a regression test** that pins both the fix and the file existence.
   The PR #8548 test (unittest, not pytest — the existing class is
   `unittest.TestCase`):

   ```python
   def test_injection_path_resolves_under_docker_workdir(self):
       """Regression guard for Codex review on PR #8548: in production
       Docker, WORKDIR=/app/mvp_site makes a repo-root-relative path
       resolve to /app/$PROJECT_ROOT/$PROJECT_ROOT/prompts/... — broken. The build
       path must use os.path.dirname(__file__)."""
       import importlib, inspect
       from mvp_site import constants
       from mvp_site.agent_prompts import PromptBuilder

       # Sanity: constant points to on-disk file.
       self.assertTrue(
           constants.LIVING_WORLD_COMPANION_CADENCE_PATH.endswith(
               "injection/living_world_companion_cadence.md"
           )
       )

       # Pin the fix.
       src = inspect.getsource(PromptBuilder.build_living_world_instruction)
       self.assertIn(
           "os.path.dirname(__file__)", src,
           "Path resolution must use os.path.dirname(__file__) so it works "
           "under any WORKDIR (Docker).",
       )
       self.assertNotIn(
           'os.path.join("mvp_site",', src,
           "Hardcoded '$PROJECT_ROOT/' prefix breaks under WORKDIR=/app/mvp_site "
           "(see Codex review on PR #8548).",
       )
   ```

   This passes against the fix and FAILS against the original (pre-fix)
   code, proving the regression guard is real.

5. **Run the test in the worktree**, confirm 100% pass, commit, push.

## Why the existing unit tests did NOT catch this

The existing test `test_dynamic_block_loads_from_injection_path` calls
`_build_living_world_companion_cadence_block` with `cwd=<worktree>`,
which is the dev case where the original anti-pattern still works.
No unit test in the suite simulates Docker `WORKDIR=/app/mvp_site`.
Hence the bug passed all 16 contract tests on PR #8548 but would have
broken in prod on the first living-world trigger turn.

Lesson: a unit test that exercises the dev path is not a regression
guard for the prod path. Either (a) add a `monkeypatch.chdir(/app/mvp_site)`
test that simulates Docker, or (b) static-check the source via
`inspect.getsource` for the anti-pattern (the approach taken here).

## What to do when Codex P1 (or similar) fires mid-drive

If a code-review bot flags a production bug (Docker WORKDIR, missing
env-var, race condition) on a PR you are driving to green:

1. **Stop the Green Gate push cycle.** Do not push another evidence
   refresh; fix the bug first.
2. **Create a new branch state on the PR's existing branch** (do NOT
   open a new PR — this is the same fix-on-same-branch pattern as the
   rest of the drive).
3. **Apply the fix + add the regression test in the same commit** so
   the test is provably what would have caught the bug.
4. **Run the test locally** before pushing; if it fails, the fix is
   wrong, do not push.
5. **Reply to the review comment** via the PR conversation API
   (`POST /repos/{owner}/{repo}/issues/{number}/comments` — the
   `pulls/{number}/comments/{id}/replies` endpoint returns 404, the
   `issues/{number}/comments` endpoint works).
6. **Push** the fix. The new commit triggers another Green Gate cycle
   automatically (the empty-commit pitfall does NOT apply when the
   push contains real changes).
7. **Wait for the new cycle to confirm GATE-6b + Green Gate + Bugbot
   still pass.** If any other gate fails on the new commit, fix that
   in the same session — do not push the bug fix and then post a
   "still waiting on Gate X" status.
8. **Surface the fix in the final Slack reply** with the specific
   diff URL (`github.com/<org>/<repo>/commit/<sha>`) so the user can
   verify the fix was the load-bearing change, not just a doc update.

## Pitfall: tests using `monkeypatch`/`tmp_path` in a `unittest.TestCase`

Pytest fixtures (`monkeypatch`, `tmp_path`) are NOT available in
`unittest.TestCase` subclasses. The error:

```
TypeError: TestX.test_y() missing 2 required positional arguments: 'monkeypatch' and 'tmp_path'
```

Fix: use `tempfile.TemporaryDirectory()` + explicit `os.chdir()`
with try/finally to restore the original cwd:

```python
import tempfile, os

original_cwd = os.getcwd()
with tempfile.TemporaryDirectory() as tmp:
    try:
        os.chdir(tmp)
        # ... call the function under test ...
    finally:
        os.chdir(original_cwd)
```

This was the actual error on PR #8548 first commit attempt; the fix
shipped as the second commit on the PR branch.

## Pitfall: PR review replies endpoint

`POST /repos/{owner}/{repo}/pulls/comments/{id}/replies` returns 404
in this GitHub Enterprise configuration. The working endpoint for
posting a "fixed" reply on a PR review comment is:

```
POST /repos/{owner}/{repo}/issues/{number}/comments
```

with `{"body": "..."}`. The reply appears as a normal PR conversation
comment (not threaded under the review comment), but it does carry
the user's @-mention and shows up in the PR timeline. Verified on
PR #8548 (comment id 5067566565).

## Worked example — PR #8548 (this drive)

Initial drive pushed `d58f61dcff` (evidence refresh). Green Gate PASS.
Then a Codex review was already pending from the original PR (codex
rates comments on the merged code, not the new commit). The comment
landed in the PR conversation as id 3642406857:

> **[P1] Resolve cadence prompt from the module path** — In the production
> Docker image, `$PROJECT_ROOT/Dockerfile` switches to `WORKDIR=/app/mvp_site`
> before starting gunicorn, so this relative `$PROJECT_ROOT/prompts/...` path
> resolves to `/app/$PROJECT_ROOT/$PROJECT_ROOT/prompts/...` rather than the copied
> `/app/$PROJECT_ROOT/prompts/...`. That means any living-world trigger turn
> will raise `FileNotFoundError` when `read_file_cached()` runs, breaking
> story requests every time this dynamic injection is due; build this path
> relative to `os.path.dirname(__file__)` like `_load_instruction_file()`
> does.

Fix commit `ac5d0c400b`:
- `$PROJECT_ROOT/agent_prompts.py`: replaced `os.path.join("mvp_site", constants.X_PATH)`
  with `os.path.join(os.path.dirname(__file__), constants.X_PATH)`.
- `$PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py`: added
  `test_injection_path_resolves_under_docker_workdir` regression guard.
- 17/17 contract tests pass (including the new one).

Final state: Green Gate PASS + Green Gate Precheck (Gates 1-6) PASS +
Bugbot Gate Wait PASS + CodeRabbit APPROVED. PR ready for `MERGE APPROVED`.

## Generic version of this pitfall (for the finish-the-job pitfall list)

❌ **"New module-relative file path uses repo-root prefix instead of os.path.dirname(__file__) — passes local tests, breaks in Docker WORKDIR" (added 2026-07-24, PR #8548).**

When a PR adds a new `read_file_cached(constants.X_PATH)` (or `open(X_PATH)`)
where X_PATH is module-relative, the implementation MUST use
`os.path.dirname(__file__)` to resolve. A repo-root prefix like
`os.path.join("mvp_site", X_PATH)` works in dev (cwd=repo root) but
raises `FileNotFoundError` in production Docker where
`$PROJECT_ROOT/Dockerfile` sets `WORKDIR=/app/mvp_site`. Existing unit tests
do not catch this because they run with cwd=<worktree>. The fix has
two halves: (1) switch to `os.path.dirname(__file__)`, (2) add a
regression test that asserts the source contains the fix and does NOT
contain the anti-pattern. See this reference for the full recipe.