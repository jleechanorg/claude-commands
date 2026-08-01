---
name: py314-threadpoolexecutor-initializer-fix
description: Diagnose and fix Python 3.14 `DaemonThreadPoolExecutor` / `ThreadPoolExecutor` AttributeError on `_initializer` or `_initargs`. Triggers on the literal error string `'DaemonThreadPoolExecutor' object has no attribute '_initializer'` (or `_initargs`), or any subclass that calls `_worker(executor_ref, work_queue, self._initializer, self._initargs)` and fails under Python 3.14. Use when a ThreadPoolExecutor subclass breaks after upgrading to Python 3.14.0+.
version: 1.0
created: 2026-07-24
---

# Python 3.14 ThreadPoolExecutor `_initializer` AttributeError

## Symptom

A `ThreadPoolExecutor` subclass that overrides `_adjust_thread_count` and references `self._initializer` / `self._initargs` raises:

```
AttributeError: 'DaemonThreadPoolExecutor' object has no attribute '_initializer'
```

(or the equivalent for any other subclass). The error **does not** happen on Python 3.13 or earlier.

## Root cause

CPython 3.14 refactored `ThreadPoolExecutor` for [bpo-106320](https://github.com/python/cpython/issues/106320). The old private attributes `_initializer` and `_initargs` on the executor instance are gone. Instead:

- `__init__` accepts `initializer` / `initargs` as **public kwargs** and stores them inside a `WorkerContext` instance.
- The new `_worker(executor_ref, ctx, work_queue)` signature takes a `WorkerContext` produced by `self._create_worker_context()`.
- 3.13 and earlier: `_worker(executor_ref, work_queue, initializer, initargs)` and the names are stored on the executor instance.

## Diagnose

1. Run `python3 -c "from concurrent.futures import ThreadPoolExecutor; e = ThreadPoolExecutor(); print(hasattr(e, '_initializer'))"` under the failing interpreter. If `False`, you are on 3.14+ and need the patch.
2. Confirm the call site is `args=(..., self._initializer, self._initargs)` inside `_adjust_thread_count` (or similar override).
3. Inspect the daemon pool module — typical repo: `tools/daemon_pool.py`, class `DaemonThreadPoolExecutor` (Hermes Agent convention).

## Fix (compatibility shim)

Replace the literal `self._initializer` / `self._initargs` access with a version-branch that uses `getattr` to detect the 3.14 path:

```python
def _adjust_thread_count(self) -> None:
    # Mirrors CPython's implementation with two changes: daemon=True and
    # no _threads_queues registration. CPython 3.14 refactored the worker
    # protocol to pass a WorkerContext instead of (initializer, initargs),
    # so we branch on the available API rather than mirroring the 3.8–3.13
    # shape literally.
    if self._idle_semaphore.acquire(timeout=0):
        return

    def weakref_cb(_, q=self._work_queue):
        q.put(None)

    create_ctx = getattr(self, "_create_worker_context", None)
    if create_ctx is not None:
        # 3.14+: WorkerContext carries initializer+initargs.
        worker_args = (
            weakref.ref(self, weakref_cb),
            create_ctx(),
            self._work_queue,
        )
    else:
        # 3.13 and earlier: explicit args.
        worker_args = (
            weakref.ref(self, weakref_cb),
            self._work_queue,
            self._initializer,
            self._initargs,
        )

    num_threads = len(self._threads)
    if num_threads < self._max_workers:
        thread_name = "%s_%d" % (self._thread_name_prefix or self, num_threads)
        t = threading.Thread(
            name=thread_name,
            target=_worker,
            args=worker_args,
            daemon=True,
        )
        t.start()
        self._threads.add(t)
```

## Verify

Run the existing pool tests on **both** Python 3.13 and 3.14:

```bash
# 3.14 (the failing interpreter)
python3.14 -m pytest tests/tools/test_daemon_pool.py -v

# 3.13 (regression check via /opt/homebrew/bin/python3.13)
python3.13 -c "
from tools.daemon_pool import DaemonThreadPoolExecutor
import threading
seen = []
def _init(): seen.append('init')
pool = DaemonThreadPoolExecutor(max_workers=2, initializer=_init, initargs=())
try:
    r = pool.submit(lambda: threading.current_thread().daemon).result(timeout=5)
    assert r is True
    assert seen == ['init']
finally:
    pool.shutdown(wait=True)
print('OK on 3.13 fallback path')
"
```

Expected: 4 tests pass on 3.14, smoke test prints OK on 3.13.

## Deploy / restart

The patch is on disk but **the running gateway is still on the old bytecode**. Restart the manually-running gateway:

```bash
# 1. Find the current PID
/opt/homebrew/bin/hermes gateway status

# 2. Restart it (or kill + relaunch)
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway 2>/dev/null  # if launchd-managed
# OR for a manually-started gateway:
kill -TERM <PID> && sleep 4 && /opt/homebrew/bin/hermes gateway run &
```

**Warning:** killing the gateway drops the current Hermes session. Do this from a fresh shell or a separate detached process — not from inside a session that depends on the gateway.

## Pitfalls

- **Don't pin to 3.14.** The `getattr(self, "_create_worker_context", None)` branch keeps the code working on 3.13 today and 3.15+ for as long as the API stays. If CPython renames `_create_worker_context` in a future release, the `getattr` falls back to the 3.13 path, which will then fail under that newer interpreter — re-check the API surface on every CPython bump.
- **Don't catch the AttributeError.** That hides the diagnostic and the failure mode is currently a hard crash, which is the signal you want. Use the branch.
- **Don't update only Python.** Pinning to 3.13 buys time but the underlying CPython refactor is the new normal. Fix the shim, don't downgrade the runtime.
- **In-process pools created before the patch keep the bug.** A pod/gateway/daemon that imported the module before the patch holds a `_initializer`-less worker pool until restarted. This is the *only* reason a restart is needed after the code-level patch.

## Operational workaround — when the gateway itself is on stale bytecode

Symptom (verified 2026-07-24, multi-call session): every top-level `terminal`, `read_file`, `search_files`, `patch`, etc. call returns `Error during OpenAI-compatible API call #1: 'DaemonThreadPoolExecutor' object has no attribute '_initializer'`. The gateway is alive (the tool returns a structured error, not a connection refused) but its tool-runtime thread pool can't spawn workers. The *Deploy / restart* warning above says don't kill the gateway from inside a session — so what do you do right now?

**Pivot to `execute_code` with its built-in `terminal()` helper.** That helper runs shell calls through a different code path that does NOT depend on the broken pool:

```python
from hermes_tools import terminal
r = terminal("gh pr view 8488 --repo $GITHUB_REPOSITORY --json number,title,state")
print(r["output"])
```

- Same `terminal()` import, same return shape (`{"output": "...", "exit_code": N}`).
- `read_file` / `search_files` / `patch` / `write_file` / `web_search` / `web_extract` are exposed the same way on `hermes_tools` and remain reachable while the top-level tool wrappers are broken.
- `json_parse(text)` is the strict-tolerant JSON decoder; use it instead of `json.loads` when the API response has raw newlines inside string fields (PR bodies, review comment bodies, etc.) — `'Invalid control character'` is a common failure on those endpoints. Verified 2026-07-24 on `gh api repos/.../pulls/8488/comments`.
- Once the gateway is restarted with patched bytecode, the top-level tools come back and you can stop using the `execute_code` fallback.

**Why this works:** the gateway's top-level tool wrappers are wired through a `ThreadPoolExecutor` subclass that holds the broken `_initializer` reference. The `execute_code` interpreter runs in a separate process tree, so its own `terminal()` is unaffected. The *In-process pools* pitfall above is exactly why a fix-on-disk does not help until restart — but the `execute_code` helper is unaffected by that pool entirely, so it works immediately.

## Related references

- CPython PR: https://github.com/python/cpython/pull/132836 (refactor to WorkerContext)
- `concurrent.futures.thread` 3.14: `WorkerContext.prepare(initializer, initargs)` stores `initializer`/`initargs` on the context, not the executor.
- 3.14 `_worker` signature: `(executor_reference, ctx, work_queue)`
- 3.13 `_worker` signature: `(executor_reference, work_queue, initializer, initargs)`
