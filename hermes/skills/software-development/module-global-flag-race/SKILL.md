---
name: module-global-flag-race
version: 1.3.0
description: Diagnose and fix module-global boolean/scalar flags used as schema or feature gates that race across concurrent writers — specifically the pattern where a single in-process bool gates "have we confirmed the target table has these columns / feature is initialized?" and silently drops writes on cold replicas or transient init failures. Fires when a flag like `_payloads_schema_migrated`, `_feature_initialized`, `_schema_ready` (or any module-level "we've finished first-time setup" boolean) is the gate between the writer and a column set / capability, when transient BQ / DB / feature-store failures leave the flag stuck False, and when sibling PRs (PR #8070 / #8351 family) keep trying to add retries + serialization without removing the underlying race. v1.3.0 adds Pitfall 11 (test-budget-vs-lock-hold regression — when a v1.1.0/v1.2.0 production-budget change (e.g. `_PAYLOADS_SCHEMA_RETRY_BUDGET_S = 0.5s`) breaks an existing test that holds a shared lock for longer than the new budget, the fix is to monkeypatch the budget wider in the TEST only, not loosen production; verified live 2026-07-24 against PR #8462 in $GITHUB_REPOSITORY where `test_startup_schema_migration_uses_shared_migration_lock` started failing 3/3 on the PR head but passed 3/3 on `origin/main` HEAD — same file, same assertion, different conclusion driven by the new 0.5s production budget vs the test's 5s lock hold). v1.2.0 adds Pitfall 10 (the v1.1.0 cache fix STILL drops gated columns on cold replicas between deployments — `_payloads_schema_set is None` AND `_ensure_payloads_schema_cached()` returns False on first-call → `live_columns = frozenset()` → all gated columns silently dropped for that replica's lifetime; verified live 2026-07-19 against PR #8418 with 186 NULL is_test rows in last 24h after the cache-shape fix merged) AND the diagnostic recipe to prove cold-replica persistence from BQ alone (per-hour + per-minute buckets + no revision_id column = inferred cold-start) AND the recommended structural fix shape (boot-warmup fallback flag + retry-with-backoff; treat in-process `_payloads_schema()` as the cache when `ensure_dataset_and_tables` succeeded, since that means the table HAS those columns even if the cache is stale). v1.1.0 adds Step 4.1 (cooldown re-check inside the lock — third gate, CodeRabbit-flagged), Pitfall 8 (CI stub `GOOGLE_APPLICATION_CREDENTIALS=/dev/null` failure mode requires mocking `_get_token_and_project` too, not just `_refresh_payloads_schema_set`), and Pitfall 9 (validate `tables.get` response shape before caching, or a malformed response silently drops ALL gated columns). Anti-trigger: cross-process / distributed locks (those need different machinery — leader election, fencing tokens, etc.), per-call state (no race), or scalar config flags that are immutable for process lifetime (no race). Triggers on phrases like "is_test IS NULL", "gated column dropped on cold replica", "global flag stuck False", "schema migration flag", "_payloads_schema_migrated", "boolean gate silently skips gated columns", "Cloud Run cold start drops writes", "two PRs tried to fix this", or when verify-telemetry-alert / systematic-debugging identifies the silent-drop class with a module-level boolean as the named suspect.
tags: [bug-class, race-condition, schema-migration, cloud-run, cold-start, silent-drop, root-cause-fix, durable-fix]
---

# Module-Global Flag Race (the "_payloads_schema_migrated pattern")

When a single **module-level boolean** in a Python service is used as a "first-time setup complete" gate on the hot write path, three things are simultaneously true and structurally broken:

1. **Transient failure during init leaves the flag stuck False.** On a fresh Cloud Run replica (or any cold process start), the first caller's setup attempt fails with a transient BQ / DB / Redis error. The retry-after-N-seconds logic kicks in, but every writer in the meantime sees `flag == False` and silently drops the gated fields.
2. **The flag is process-global, so cross-call race wins are inevitable.** Thread A finishes migration and sets the flag True. Thread B was mid-write, saw False, dropped gated fields. Thread C is now racing the flag flip. There is no "make gated writes wait for first successful migration" guarantee because the flag is non-atomic with the column-existence check.
3. **Sibling PRs mitigate but never fix.** Each subsequent PR adds more code: a `_migration_started` companion flag, a `_migration_next_retry_at` backoff, a lock to serialize writers. None of these remove the boolean flag structurally — they only gate WHEN the flag flips. The first cold-start writer still silently drops fields.

The right fix is not "add another flag" or "add another lock layer." The right fix is **replace the boolean with a per-process state cache keyed on the actual state** (column-name frozenset, capability list, etc.), populated by a single source-of-truth fetch (`tables.get`, `DESCRIBE`, capability probe) and guarded by a **double-check pattern under the same lock used to write the state**. Each gated field then independently guards on its presence in the cached state, not on a single global "all-or-nothing" flag.

## When to use this skill

- The bug surface is **silently dropped writes on a cold start** (co-NULL signature across multiple gated columns, full payload populated, no error logged).
- A single module-level boolean (`_feature_ready`, `_schema_migrated`, `_cache_warmed`, etc.) is the named gate.
- Two or more previous PRs attempted to fix it by adding serialization / backoff / retry-on-failure but kept the boolean flag in place.
- The bug is reproducing live (per-day BQ rows, per-minute metrics, etc.) — not historic backlog.
- A targeted BQ / metric query proves the bug is live (co-NULL signature, arrival-time micro-bursts with no populated rows between them = producing process never saw a successful setup).

## When NOT to use this skill

- **Distributed locks / cross-process coordination.** If you need a single global truth across replicas, the answer is leader election, fencing tokens, or an external coordinator (etcd, ZooKeeper, Cloud Run revision pinning). The fix shape here is intra-process only.
- **Per-call state.** If the race only spans one request and the flag is set within that request, there is no flag race — just a missing initialization order.
- **Immutable config flags.** If the flag is set from env / config and never flips during process lifetime, there is no race. (You might still have a "stuck on old value" bug, but that's a different class.)
- **Concurrency bugs unrelated to a boolean gate.** Deadlocks, data corruption, ordering violations — different classes.

## The diagnostic recipe

Before fixing, prove the bug is this class, not something else:

```bash
# 1. Confirm co-NULL signature across multiple gated columns on the same row.
#    A real race produces rows that ARE NULL on the gated set and POPULATED elsewhere.
#    (A real bug elsewhere produces uniform NULL or uniform POPULATED rows.)

bq query --use_legacy_sql=false "
SELECT
  COUNTIF(<col_a> IS NULL) AS null_a,
  COUNTIF(<col_b> IS NULL) AS null_b,
  COUNTIF(<col_a> IS NULL AND <col_b> IS NULL) AS both_null
FROM \`<project>.<dataset>.<table>\`
WHERE <time_window>
"

# 2. Confirm arrival-time micro-bursts — rows arriving close together with NO
#    populated rows between them. This is the fingerprint of "one cold replica
#    silently dropped writes for its lifetime".

bq query --use_legacy_sql=false "
SELECT
  FORMAT_TIMESTAMP('%H:%M:%S', <ts_col>) AS ts,
  COUNTIF(<gated_col> IS NULL) AS nulls,
  COUNTIF(<gated_col> IS NOT NULL) AS populated
FROM \`<project>.<dataset>.<table>\`
WHERE <time_window>
GROUP BY ts
ORDER BY ts
"

# 3. Confirm the named gate is a single boolean in the source.

grep -nE '_(migrated|initialized|ready|warmed|initialized)\s*[:=]\s*(True|False)' \
  <module_under_test>
```

If all three check out: this is the module-global flag race class. Apply the fix shape below.

## The fix shape

### Step 1: Replace the boolean with a state-cache.

```python
# BEFORE (the race):
_payloads_schema_migrated: bool = False  # global flag

# AFTER (per-process state cache keyed on actual state):
_payloads_schema_set: frozenset[str] | None = None  # actual column names
_payloads_schema_cached_at: float = 0.0
_payloads_schema_refresh_attempted_at: float = 0.0
_payloads_schema_ttl_seconds: float = 3600.0   # one BQ GET per hour per process
_payloads_schema_refresh_cooldown: float = 60.0  # 60s backoff after a failed refresh
```

### Step 2: Replace migration-completion side effect with cache population.

```python
# BEFORE: side effect that flips the boolean.
with _migration_lock:
    _migrate_table_schema(token, project, PAYLOADS_TABLE, _payloads_schema())
    _payloads_schema_migrated = True  # RACE: other threads can see False, skip gated writes

# AFTER: populate the cache from the source-of-truth fetch (tables.get / DESCRIBE / capability probe).
with _migration_lock:
    _migrate_table_schema(token, project, PAYLOADS_TABLE, _payloads_schema())
    try:
        _payloads_schema_set = _refresh_payloads_schema_set(token, project)
        _payloads_schema_cached_at = time.monotonic()
    except (RequestException, AuthError, RuntimeError) as exc:
        logging.warning(f"boot-time schema cache prime failed: {exc}")  # fail-soft
```

### Step 3: Per-field guarded writes with double-check under lock.

```python
# BEFORE: all-or-nothing flag gates a block of gated writes.
if _payloads_schema_migrated:
    row["is_test"] = test_flag
    row["user_id"] = uid
    row["cached_tokens"] = cached_tokens
    # ... 6 gated columns ...

# AFTER: per-column guard, with double-check under the same lock used to populate the cache.
if (
    _payloads_schema_set is None
    or (time.monotonic() - _payloads_schema_cached_at) >= _payloads_schema_ttl_seconds
):
    cache_ok = _ensure_payloads_schema_cached()  # double-check pattern under _migration_lock
else:
    cache_ok = True
live_columns: frozenset[str] = _payloads_schema_set if cache_ok else frozenset()
for column_name, value in gated_columns.items():
    if column_name in live_columns:
        row[column_name] = value
    # missing columns are OMITTED — BigQuery rejects unknown fields.

> **Pin declaration separately from values.** The pre-fix inline `gated = {...}` dict at the call site had to be kept in sync with `_GATED_COLUMNS` (the tuple that downstream consumers, audit logs, and migration tests iterate). Decoupling them by hoisting `_GATED_COLUMNS` to the authoritative declaration point and writing `for column_name in _GATED_COLUMNS: if column_name in live_columns: row[column_name] = gated_values[column_name]` means adding/removing a gated column is a single-line declaration change that cannot drift from the iteration. CodeRabbit review will catch any remaining inline-dict pattern — treat it as a regression.

### Step 4.1: Add the THIRD gate — cooldown re-check inside the lock.

Step 4 has the TTL double-check under the lock. It is **also** missing a cooldown re-check. A thread that races past the first cooldown gate (because the cooldown timestamp was 0.0 at evaluation time, or because another thread just released the lock and stamped the cooldown in the gap) still queues on `_migration_lock`. Without a third check inside the lock, the thread enters the `try` block and hammers BQ even though a sibling already stamped the cooldown during the wait. The fix:

```python
def _ensure_payloads_schema_cached() -> bool:
    global _payloads_schema_set, _payloads_schema_cached_at
    global _payloads_schema_refresh_attempted_at
    now = time.monotonic()
    cached_set = _payloads_schema_set
    if (
        cached_set is not None
        and (now - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds
    ):
        return True
    if (now - _payloads_schema_refresh_attempted_at) < _payloads_schema_refresh_cooldown:
        # Cooldown active — don't hammer BQ with refresh attempts.
        return False
    with _migration_lock:
        # Re-check #1: TTL — another thread may have populated while we waited.
        cached_set = _payloads_schema_set
        if (
            cached_set is not None
            and (time.monotonic() - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds
        ):
            return True
        # Re-check #2: cooldown — sibling thread may have failed-and-stamped
        # during the wait. Without this gate, the thread that acquired the
        # lock last still re-hammers BQ despite the cooldown.
        if (time.monotonic() - _payloads_schema_refresh_attempted_at) < _payloads_schema_refresh_cooldown:
            return False
        try:
            token, project = _get_token_and_project()
            new_set = _refresh_payloads_schema_set(token, project)
            _payloads_schema_set = new_set
            _payloads_schema_cached_at = time.monotonic()
            return True
        except (RequestException, AuthError, RuntimeError) as exc:
            _payloads_schema_refresh_attempted_at = time.monotonic()
            logging.warning(f"state cache refresh failed: {exc}")
            return False
```

Pin the third gate with a dedicated test (`test_schema_refresh_cooldown_holds_under_lock_acquire`) — pre-arm `_payloads_schema_refresh_attempted_at` to a recent value, two threads barrier-sync, the second thread to acquire the lock must observe the freshly-stamped cooldown and abort WITHOUT calling the mock refresh.
```

### Step 4: The double-check helper.

```python
def _ensure_payloads_schema_cached() -> bool:
    """Refresh the cached state if stale, missing, or recently failed.

    Returns True when cache is populated; False on failure (caller logs a
    warning and skips the gated columns rather than throwing). The
    double-check under ``_migration_lock`` means concurrent callers see
    the SAME populated cache, not N parallel refreshes.
    """
    global _payloads_schema_set, _payloads_schema_cached_at
    global _payloads_schema_refresh_attempted_at
    now = time.monotonic()
    cached_set = _payloads_schema_set
    if (
        cached_set is not None
        and (now - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds
    ):
        return True
    if (now - _payloads_schema_refresh_attempted_at) < _payloads_schema_refresh_cooldown:
        # Cooldown active — don't hammer BQ with refresh attempts.
        return False
    with _migration_lock:
        # Re-check under the lock: another thread may have populated while we waited.
        cached_set = _payloads_schema_set
        if (
            cached_set is not None
            and (time.monotonic() - _payloads_schema_cached_at)
            < _payloads_schema_ttl_seconds
        ):
            return True
        try:
            token, project = _get_token_and_project()
            new_set = _refresh_payloads_schema_set(token, project)
            _payloads_schema_set = new_set
            _payloads_schema_cached_at = time.monotonic()
            return True
        except (RequestException, AuthError, RuntimeError) as exc:
            _payloads_schema_refresh_attempted_at = time.monotonic()
            logging.warning(f"state cache refresh failed: {exc}")
            return False
```

### Step 5: Test the fix shape, not just the bug.

Three new tests pin the new architecture:

1. **Race test** — two threads with `threading.Barrier`, slow refresh, assert BOTH writers' rows have gated columns populated. This deterministically reproduces the pre-fix bug.
2. **Cooldown test** — after a failed refresh, a second immediate call within the cooldown window does NOT re-hit BQ.
3. **TTL test** — `time.sleep(TTL_seconds)` between two calls triggers a refresh on the second.

Existing tests that monkey-patched the old boolean flag must be rewritten to seed the new frozenset cache. Use `raising=False` on the legacy-attr setattrs so old shims don't crash, and seed the cache shape (frozenset of column names) for tests that simulate "post-startup, all gated columns present."

## Pitfalls

### Pitfall 1: Replacing the boolean with ANOTHER boolean ("_migration_started", "_migration_in_progress", etc.)

Sibling PRs almost always do this. Each new flag adds a state machine but doesn't remove the race — it just gates WHEN the original flag flips. Stop. The fix is removing the boolean entirely and replacing it with a per-process state cache.

### Pitfall 2: Reading the schema on EVERY write

The right shape is one BQ GET per process per TTL window (1h default), not per-row. If your helper does a `tables.get` per insert, you'll hit BigQuery rate limits and your `bq_logging_enabled` flag check becomes load-bearing. Keep the TTL high enough that steady state is one fetch per hour.

### Pitfall 3: Forgetting to refresh from tables.get (only refreshing from the local migration side effect)

The fix shape MUST include a `tables.get` / `DESCRIBE` / capability-probe round-trip to confirm the columns actually exist in the live table. The migration PATCH may have succeeded locally but BQ may have rejected it, or a sibling process may have modified the schema. The cache is invalidated by TTL (1h) AND by failed PATCHes. Don't skip the fetch — the whole point is to read ground truth.

### Pitfall 4: Cache miss path that throws on transient BQ hiccup

If the writer throws when the cache is unpopulated, a transient BQ outage breaks the gameplay path. The fix must be fail-soft: on refresh failure, log a warning, set `live_columns = frozenset()`, skip the gated columns, let the row insert. The downstream backfill job (the one that already exists for this exact case) fills the gaps.

### Pitfall 5: Not updating the existing test fixtures

After the rename, every test that monkey-patched `_payloads_schema_migrated = True` (or `False`) must be updated to seed `_payloads_schema_set = frozenset({...})`. This is mechanical but spans multiple test files (3+ in the bq_logging case). Use `raising=False` on the legacy-attr setattrs so a stale test attribute on legacy shims doesn't blow up the test run.

### Pitfall 6: "Just add a try/except around the flag flip" anti-fix

A common mitigation PR wraps the migration in try/except so the flag stays False on failure (with backoff). This doesn't fix the race — it just makes the race longer-lived on bad days. The race is structural (one boolean, many writers). It cannot be fixed by exception handling.

### Pitfall 7: Confusing this skill with "I need a distributed lock"

If two REPLICAS (not two in-process threads) are racing, the answer is not the fix shape above — the answer is leader election / fencing tokens. The intra-process cache fix assumes one process's writers all share the same in-memory state. For cross-process consistency, BQ / Postgres / etc. IS the source of truth; you must read it on every write (which is expensive) or accept eventual consistency.

### Pitfall 8: Skipping `_get_token_and_project` mock in tests — CI stub failure mode

CI runners (and most hermes-agent self-hosted runners) use `GOOGLE_APPLICATION_CREDENTIALS=/dev/null` as a deliberate safety stub. `_get_token_and_project()` reads this env var via `google.auth.default()` and raises `DefaultCredentialsError` BEFORE `_refresh_payloads_schema_set(token, project)` is ever called. The exception is then caught by `_ensure_payloads_schema_cached`'s `except (GoogleAuthError, ...)` block, which sets `_payloads_schema_refresh_attempted_at` to `time.monotonic()` and logs the warning — making the test look like "refresh failed, no mock called" when in reality the mock was bypassed entirely. Every test that exercises the cache-refresh path must patch BOTH `_refresh_payloads_schema_set` AND `_get_token_and_project`:

```python
monkeypatch.setattr(bq_logging, "_refresh_payloads_schema_set", mock_refresh)
monkeypatch.setattr(bq_logging, "_get_token_and_project", lambda: ("mock-token", "mock-project"))
# Now mock_refresh WILL be called, and the test is deterministic regardless
# of GOOGLE_APPLICATION_CREDENTIALS.
```

The diagnostic signature is: `_payloads_schema_refresh_attempted_at` is non-zero AFTER the test, mock call count is 0, and the warning log mentions `File /dev/null is not a valid json file` (google-auth's stub-load failure message). Local repro: set `GOOGLE_APPLICATION_CREDENTIALS=/dev/null` and run the test — if it passes locally but fails on CI, this is your bug.

### Pitfall 9: Caching an unvalidated `tables.get` response

`_refresh_payloads_schema_set` reads BQ's `tables.get` response and iterates `fields`. If the response is malformed (HTTP 200 but body is an HTML error page, an empty dict, a list, or a dict missing the `schema` key), the comprehension silently returns `frozenset()` — the same shape as "table exists but has no columns." A row inserted with `live_columns=frozenset()` will then drop ALL gated columns because none of them are in the empty set. Pin the response shape before caching:

```python
def _refresh_payloads_schema_set(token, project) -> frozenset[str]:
    resp = requests.get(url, headers=_auth_headers(token), timeout=_HTTP_TIMEOUT_S)
    if resp.status_code != 200:
        raise RuntimeError(f"tables.get {PAYLOADS_TABLE} [{resp.status_code}]: {resp.text}")
    body = resp.json()
    if not isinstance(body, dict):
        raise RuntimeError(f"tables.get {PAYLOADS_TABLE}: body is not a JSON object ({type(body).__name__})")
    schema = body.get("schema")
    if not isinstance(schema, dict):
        raise RuntimeError(f"tables.get {PAYLOADS_TABLE}: missing or non-dict 'schema'")
    fields = schema.get("fields")
    if not isinstance(fields, list):
        raise RuntimeError(f"tables.get {PAYLOADS_TABLE}: 'schema.fields' is not a list")
    return frozenset(f["name"] for f in fields if isinstance(f, dict) and f.get("name"))
```

The exception gets caught at the `_ensure_payloads_schema_cached` `except (RequestException, RuntimeError, ...)` block, stamps the cooldown, and lets the row insert without gated columns — fail-soft as designed, but now you've at least logged the malformed response and won't poison the cache for the TTL window with an `frozenset()` that looks identical to "table has zero columns."

### Pitfall 10: The v1.1.0 cache fix STILL silently drops on cold replicas between deployments

The v1.1.0 fix replaces the boolean with a per-process `frozenset[str]` cache + `tables.get` + double-check under lock. It is correct for the **steady-state** race (two writers in the same process seeing a stale boolean). It is **not** sufficient for the **cold-replica** race, because:

```python
# In log_llm_payload (the write path):
if (
    _payloads_schema_set is None
    or (time.monotonic() - _payloads_schema_cached_at) >= _payloads_schema_ttl_seconds
):
    cache_ok = _ensure_payloads_schema_cached()
else:
    cache_ok = True
live_columns: frozenset[str] = (
    _payloads_schema_set
    if cache_ok and _payloads_schema_set is not None
    else frozenset()  # ← THE LEAK: drops ALL gated cols on cold cache + transient refresh-fail
)
```

When a Cloud Run replica is cold (just spun up between deployments) AND `_ensure_payloads_schema_cached()` fails on the first call (transient BQ hiccup, IAM token not yet primed, network cold-start delay), `cache_ok=False` AND `_payloads_schema_set is None`. The writer proceeds with `live_columns = frozenset()` and omits every gated column (`is_test`, `user_id`, `cached_tokens`, `thoughts_tokens`, `tool_use_tokens`, `rag_mode`, + 6 more). The cooldown logic in `_ensure_payloads_schema_cached` then keeps the cache cold for the next `_payloads_schema_refresh_cooldown` seconds (60s default), during which every insert on this replica silently drops all gated columns.

**Verified live 2026-07-19 against PR [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418)** (which DID land the v1.1.0 fix at `90238d16b8`):
- Last 24h: 186 NULL `is_test` rows / 2014 total = **90.76% populated** (target ≥95%) — fails the watcher.
- Schema-gate signature: **100.0%** of NULL rows are 5-col co-NULL (the exact silent-drop shape).
- Per-hour pattern 2026-07-19: hour 18:00 UTC = 100% populated, hour 19:00 = 72.62%, hour 20:00 = 54.0% — fresh replicas spinning up between steady-state hours and hitting the cold-cache race.
- 7d rolling: 85.68% populated (1237 NULL rows) — the cumulative window trips every watcher run.

**The diagnostic recipe to prove cold-replica persistence from BQ alone** (no Cloud Run logs needed):

```sql
-- 1. Per-hour buckets last 96h — shows the alternating OK / NOT-OK pattern
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d %H:00', ingested_at) AS hour,
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNT(*) AS n_total,
  ROUND(100.0 * COUNTIF(is_test IS NOT NULL) / COUNT(*), 2) AS pct_populated
FROM `<project>.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 96 HOUR)
  AND model LIKE '%gemini%'
GROUP BY hour ORDER BY hour DESC;

-- 2. Per-minute buckets for the bad hours — shows the micro-bursts that
--    are the fingerprint of "one cold replica silently dropped writes for
--    its lifetime then died" (5-8 NULLs every few minutes, no populated
--    rows between).
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', ingested_at) AS minute_bucket,
  COUNT(*) AS n_null
FROM `<project>.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP('<bad-hour-start> UTC')
  AND ingested_at < TIMESTAMP('<bad-hour-end> UTC')
  AND model LIKE '%gemini%'
  AND is_test IS NULL
GROUP BY minute_bucket ORDER BY minute_bucket;

-- 3. Schema-gate signature — 5-col co-NULL on EVERY NULL row is the
--    smoking gun for "all gated cols dropped by the cache fail-soft path".
SELECT
  COUNTIF(is_test IS NULL AND cached_tokens IS NULL AND thoughts_tokens IS NULL
          AND tool_use_tokens IS NULL AND rag_mode IS NULL) AS n_co_null_5cols,
  COUNTIF(is_test IS NULL) AS n_is_test_null_total,
  ROUND(100.0 * COUNTIF(is_test IS NULL AND cached_tokens IS NULL AND thoughts_tokens IS NULL
                        AND tool_use_tokens IS NULL AND rag_mode IS NULL)
        / GREATEST(1, COUNTIF(is_test IS NULL)), 2) AS co_null_pct
FROM `<project>.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND model LIKE '%gemini%';
```

If `co_null_pct == 100.0`, the bug is the cold-cache silent-drop. Per-replica attribution requires a `revision_id` column (reading `K_REVISION` env var on Cloud Run) — **add it now** as part of the fix, not as a follow-up. Without it, you can't tell which replica is dropping.

**The structural fix shape (belt + suspenders — do both):**

1. **Boot-warmup fallback flag.** Add `_boot_warmup_succeeded: bool = False` to the module state. Set it True at the end of `ensure_dataset_and_tables` after the cache prime attempt (regardless of success/failure of the cache fetch itself, since the table exists and has the schema we just declared). In the write path, when `cache_ok=False` AND `_payloads_schema_set is None`, consult `_boot_warmup_succeeded` — if True, the table HAS the columns (we just created or migrated it during boot), so fall back to the in-process `_payloads_schema()` (the authoritative declaration) instead of `frozenset()`. If False (replica never finished boot warmup), log a structured warning with replica_id + retry attempt count, and skip the insert (better to lose a row than silently pollute BQ with NULLs — change from fail-soft to fail-loud only for the truly-no-cache case).

2. **Retry-with-backoff on first call.** Before falling through to `frozenset()`, retry `_ensure_payloads_schema_cached()` up to N=3 times within a short budget (e.g., 500ms total with 100/200/200ms delays). Transient BQ hiccups on cold replicas typically clear within 200ms. Combined with #1, this means: transient hiccup → retry succeeds → cache populated normally; transient hiccup past retry budget + boot warmup succeeded → fall back to `_payloads_schema()` declaration; transient hiccup past retry budget + boot warmup failed → log structured warning + skip insert.

3. **`revision_id` column.** Read `os.environ.get('K_REVISION', 'local-dev')` (Cloud Run sets this; local dev falls back to a sentinel). Add to `_payloads_schema()` as a NON-gated column (it's always present after the schema bump). Make the watcher alert report the `revision_id` distribution of NULL rows so future cold-replica incidents are diagnosable from BQ alone without reading Cloud Run logs.

```python
# Module state additions:
_boot_warmup_succeeded: bool = False
_boot_warmup_lock = threading.Lock()

# In ensure_dataset_and_tables, at the end:
with _boot_warmup_lock:
    _boot_warmup_succeeded = True  # table was created/migrated even if cache fetch failed

# In log_llm_payload write path, replacing the live_columns line:
if cache_ok and _payloads_schema_set is not None:
    live_columns = _payloads_schema_set
elif _boot_warmup_succeeded:
    # Cold cache, but the boot-time migrate created the table with the
    # authoritative schema. Fall back to the in-process declaration so
    # gated columns aren't silently dropped.
    live_columns = frozenset(_payloads_schema())  # use the declared schema
    logging.warning(
        f"BQ logging: schema cache cold, falling back to declared schema; "
        f"revision_id={K_REVISION}"
    )
else:
    # Cold cache AND boot warmup never completed — log loud, skip the row.
    logging.error(
        f"BQ logging: schema cache cold AND boot warmup not complete; "
        f"skipping insert to avoid silent NULL pollution. revision_id={K_REVISION}"
    )
    return None  # do NOT silently drop; refuse the insert instead

for column_name in _GATED_COLUMNS:
    if column_name in live_columns:
        row[column_name] = gated_values[column_name]
```

**Tests to pin the new architecture** (add to `$PROJECT_ROOT/tests/test_bq_logging_schema_migration.py`):

```python
def test_cold_cache_transient_refresh_failure_includes_gated_columns(monkeypatch):
    """Cold cache + transient refresh failure + boot warmup succeeded
    → fall back to declared schema; gated cols ARE in the row."""
    monkeypatch.setattr(bq_logging, "_payloads_schema_set", None)
    monkeypatch.setattr(bq_logging, "_boot_warmup_succeeded", True)
    monkeypatch.setattr(bq_logging, "_ensure_payloads_schema_cached", lambda: False)
    # ... call log_llm_payload with a mocked _insert_rows, capture the row arg ...
    assert "is_test" in captured_row
    assert "user_id" in captured_row

def test_cold_cache_no_boot_warmup_refuses_insert(monkeypatch):
    """Cold cache + boot warmup never completed → refuse the insert,
    do NOT silently drop."""
    monkeypatch.setattr(bq_logging, "_payloads_schema_set", None)
    monkeypatch.setattr(bq_logging, "_boot_warmup_succeeded", False)
    monkeypatch.setattr(bq_logging, "_ensure_payloads_schema_cached", lambda: False)
    # ... call log_llm_payload ...
    assert captured_insert_id is None  # refused, not silently dropped

def test_log_llm_payload_includes_revision_id(monkeypatch, tmp_path):
    """revision_id column reads K_REVISION env var and is included in every row."""
    monkeypatch.setenv("K_REVISION", "wa-mvp-00042-abc")
    # ... call log_llm_payload ...
    assert captured_row.get("revision_id") == "wa-mvp-00042-abc"
```

**Anti-pattern (do NOT do this):** "Just push another `_migration_started: bool` companion flag to handle cold-replica case." Each new boolean re-introduces the v1.0.0 race in a new shape. The fix is the `_boot_warmup_succeeded` flag PLUS the boot-warmup fallback to the declared schema — not another boolean. The `_boot_warmup_succeeded` flag is set ONCE during boot and never flipped, so it has no race; the `frozenset[str]` cache is keyed on actual state, not a binary "ready" signal.

### Pitfall 11: A v1.1.0/v1.2.0 production-budget change silently breaks existing tests that hold a shared resource longer than the new budget

**Verified live 2026-07-24 against PR [#8462](https://github.com/$GITHUB_REPOSITORY/pull/8462) in $GITHUB_REPOSITORY** (the Pitfall 10 follow-up). The v1.1.0 fix introduced `_PAYLOADS_SCHEMA_RETRY_BUDGET_S: float = 0.5s` — a production wall-clock budget for the cold-replica retry loop. The v1.1.0 fix also added `test_startup_schema_migration_uses_shared_migration_lock`, a regression test that holds `_migration_lock` for **5 seconds** to verify the request path *truly* blocks on the lock (the slow `_migrate_table_schema` mock waits on `release_migration.wait(timeout=5.0)`).

After merge, CI core-mvp-3 reports the new test as FAILED with `assert []` on `inserted_rows`. Root cause: the request-path writer's `_lock_before_deadline(_migration_lock, retry_deadline)` times out at 0.5s, logs "wall-clock budget exceeded", and falls back to disk-mirror (no BQ insert). The test then asserts `inserted_rows` and fails. The test was passing on the PR branch before the budget change, and it passes on `origin/main` HEAD on a clean worktree (`git checkout origin/main -- <test files>`) — same file, same assertion, same test name, but the production budget change makes it fail on the PR.

**The same-test-name-rule four-check confirms a real PR regression, not a flake:**

1. **Same test name** — `$PROJECT_ROOT/tests/test_bq_logging_schema_migration.py::test_startup_schema_migration_uses_shared_migration_lock` is unchanged on both branches.
2. **Same assertion** — `assert inserted_rows` is unchanged.
3. **Same file at the same commit** — exists on both `origin/main` and PR head (this test was added in PR #8462 itself).
4. **Explicit same-SHA reproduction on `origin/main` HEAD** — `python3 -m pytest $PROJECT_ROOT/tests/test_bq_logging_schema_migration.py::test_startup_schema_migration_uses_shared_migration_lock` on a `git checkout origin/main -- <files>` worktree → **3/3 PASS in 0.34-0.42s** (fast because the lock acquire is fast in isolation). On the PR head (clean worktree, before any fix) → **3/3 FAIL in 2.92-3.54s** (slow because the test actually waits for the 5s lock hold, then times out the 0.5s budget).

**Fix (verified on PR #8462 commit `e2253af7e1`):** monkeypatch the budget wider **in the test only**. Production code keeps the 0.5s invariant; the test widens the budget to a value that comfortably exceeds the 5s lock hold:

```python
def test_startup_schema_migration_uses_shared_migration_lock(  # noqa: PLR0915
    monkeypatch,
):
    real_lock = threading.Lock()
    monkeypatch.setattr(bq_logging, "_migration_lock", real_lock)
    # ... other monkeypatches ...
    # The shared retry budget defaults to 0.5s so a degraded replica cannot
    # hold a request-path insert for longer; this test deliberately holds the
    # migration lock for up to 5s to verify the request path *truly* blocks
    # on it, so we widen the budget to comfortably exceed that 5s wait.
    monkeypatch.setattr(bq_logging, "_PAYLOADS_SCHEMA_RETRY_BUDGET_S", 10.0)
    # ... test body unchanged ...
    assert release_migration.wait(timeout=5.0), "migration release timed out"
```

After the fix: `$PROJECT_ROOT/tests/test_bq_logging_schema_migration.py` 19/19 PASS; `$PROJECT_ROOT/tests/test_bq_logging.py` + `_integration.py` + `_schema_migration.py` 83/83 PASS. PR #8462 went from failing 1 self-hosted MVP shard (core-mvp-3) to 7-green.

**Why this is the right fix, not a budget relaxation.** The 0.5s production budget is a real correctness invariant (a degraded replica cannot hold a request-path insert for >0.5s). Relaxing it to 5s to satisfy one test would silently weaken production behavior. Widening the budget in the test preserves the invariant AND lets the test verify the lock semantics the test was written to verify. The pattern generalizes to any timeout/budget + lock-hold test combination: any test that holds a shared resource longer than a new production timeout/budget needs the budget widened in the test, not loosened in production.

**Generalization recipe (any timeout/budget + lock-hold test combination):**

1. Identify the new production budget/timeout/deadline value introduced by the PR (grep for `_TIMEOUT = \|_BUDGET = \|_LIMIT = \|_DEADLINE = ` in the diff).
2. Identify any test in the diff (or any existing test that the new budget would break) that holds a shared resource for longer than that budget.
3. Add `monkeypatch.setattr(<module>, "<CONSTANT>", <value comfortably above test's resource hold>)` to the test setup. Document the value choice in a comment ("this test deliberately holds X for N seconds to verify Y; production budget is 0.5s but the test needs at least N+1s").
4. Local verification: `python3 -m pytest <test>` 3 times in a row → all pass on the PR head.
5. Same-test-name-rule check on `origin/main`: `git checkout origin/main -- <test file> && python3 -m pytest <test>` → 3/3 pass (proving the test was always passing before the budget regression).

**Don't fall into:** "The test is flaky, just re-run" — this dismisses a real PR regression. The test is deterministic; the failure is reproducible. The PR introduced the budget that broke the test.

**Don't fall into:** "Loosen the production budget to make the test pass" — this silently weakens production. The budget is a real invariant; the test should widen the budget, not production.

**Don't fall into:** "Skip the test, mark it as known-failure" — the test is the only one that proves the lock serialization invariant the v1.1.0 fix established. Skipping it would silently lose regression coverage on the most important fix-shape property.

**Cross-skill reference:** This pattern is a sibling to the same-test-name-rule dismissal gate (the `qa-test-failure-dismissal-anti-pattern` skill) — that gate decides whether a CI failure is a real PR regression or an infra flake. Pitfall 11 is the "yes, it's a real PR regression, here's how to fix the test while keeping production tight" companion.

**PR-topology reminder:** when the v1.1.0 fix is already merged (e.g., PR #8418) and you discover the cold-replica persistence, do NOT push a follow-up commit onto the v1.1.0 branch — open a NEW branch from `origin/main` with `git worktree add -b fix/<topic> origin/main`, cherry-pick only the load-bearing change (the `_boot_warmup_succeeded` + revision_id + retry logic), and open a fresh PR. Per `pr-clean-branch-from-main-no-history-bloat` and `never-push-onto-someone-elses-pr-head`, pushing onto a non-owned PR head is the #1 PR-pollution failure mode. The follow-up PR (fix/bq-payloads-schema-cold-replica-fix, bead `rev-zurdo`) was opened on 2026-07-19 with this exact pattern.

## Reference

- `references/2026-07-16-bq-is-test-null-pr-8418.md` — worked example: the `_payloads_schema_migrated: bool` race in `$PROJECT_ROOT/bq_logging.py`, PR [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418) (commit `51242edb2`). Reproduces the live bug (5/1069 NULL rows in last 24h, co-NULL on 6 columns, two micro-bursts at 10:03 and 10:05 UTC). Previous sibling PRs #8070 (preserve additive schema migration + serialize writers) and #8351 (preserve live schema columns) attempted the same fix but kept the boolean flag in place.
- `references/2026-07-17-pr-8418-driven-to-green.md` — v1.1.0 addendum: three CodeRabbit-flagged corrections (cooldown re-check inside lock, `_GATED_COLUMNS` authoritative declaration, `_get_token_and_project` CI mock requirement), the `tables.get` response-shape validation pattern, AND the 8-section PR description gate choreography used to drive PR #8418 to green on 2026-07-17.
- `references/2026-07-19-cold-replica-persistence.md` — v1.2.0 evidence: PR #8418's v1.1.0 cache fix did NOT hold across new Cloud Run replicas between deployments. Live BQ probe on 2026-07-19 21:00 UTC shows 186 NULL is_test rows in last 24h (90.76% populated, fails ≥95% target), 100% co-NULL on 5 gated cols, per-hour pattern of alternating OK / NOT-OK as fresh replicas spin up. Follow-up PR `fix/bq-payloads-schema-cold-replica-fix` (bead `rev-zurdo`, worker `worldarchitect-64`) implements Pitfall 10's fix shape. Includes the `env -i PYTHONPATH=` workaround for the broken `bq` CLI on this Mac, and the `gh api` GraphQL rate-limit fallback to REST.

## Cross-references

- `~/.hermes/skills/software-development/systematic-debugging/SKILL.md` — the 4-phase protocol for finding root cause before fixing. Use this skill after systematic-debugging identifies the silent-drop class with a module-level boolean as the named suspect.
- `~/.hermes/skills/software-development/convergent-bug-triage/SKILL.md` — when 3+ sibling bug investigations on the same surface point to the same root class. The is_test NULL family (PR #8070 + #8351 + #8418) is exactly this pattern.
- `~/.hermes/skills/devops/verify-telemetry-alert/SKILL.md` — how to verify the BQ / metric alert that surfaces this class before assuming the alert is accurate.
- `~/.hermes/skills/worldarchitect/wa-cloud-run-deploy-failure-debug/SKILL.md` — sibling skill for Cloud Run deploy failure debugging (different class: deployment, not race).