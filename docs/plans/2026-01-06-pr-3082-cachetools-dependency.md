# PR-3082 Cachetools Dependency Implementation Plan

**Goal:** Fix PR #3082 CI failures by ensuring the cachetools dependency is installed for core tests.

**Architecture:** The core tests import `mvp_site.file_cache`, which requires `cachetools`. CI currently lacks this dependency, so imports fail and cascade across tests. Add `cachetools` to `mvp_site/requirements.txt` so CI installs it before running directory-based tests.

**Tech Stack:** Python 3.11, pip, `mvp_site/requirements.txt`, `run_tests.sh`.

### Task 1: Reproduce the missing dependency failure

**Files:**
- Test: `mvp_site/tests/test_authenticated_comprehensive.py`

**Step 1: Reproduce the import failure in CI-style PYTHONPATH**

```bash
PYTHONPATH="$PWD:$PWD/mvp_site:$PWD/automation" python -c "import mvp_site"
```

Expected: FAIL with `ModuleNotFoundError: No module named 'cachetools'`.

**Step 2: Document the root cause**

Note: `mvp_site/file_cache.py` imports `cachetools.TTLCache`, but `mvp_site/requirements.txt` does not include `cachetools`.

### Task 2: Add cachetools dependency

**Files:**
- Modify: `mvp_site/requirements.txt`

**Step 1: Update requirements**

```text
cachetools
```

Add `cachetools` near other runtime dependencies.

**Step 2: Re-run the reproduction import**

```bash
PYTHONPATH="$PWD:$PWD/mvp_site:$PWD/automation" python -c "import mvp_site"
```

Expected: PASS (or at minimum, no `cachetools` import error).

### Task 3: Validate CI-relevant test command

**Files:**
- Test: `run_tests.sh`

**Step 1: Run core directory tests like CI**

```bash
./run_tests.sh --test-dirs=mvp_site --parallel --exclude-integration --exclude-mcp
```

Expected: No `ModuleNotFoundError: cachetools` failures.

**Step 2: Commit**

```bash
git add mvp_site/requirements.txt docs/plans/2026-01-06-pr-3082-cachetools-dependency.md
git commit -m "Update PR #3082: Fix cachetools dependency"
```