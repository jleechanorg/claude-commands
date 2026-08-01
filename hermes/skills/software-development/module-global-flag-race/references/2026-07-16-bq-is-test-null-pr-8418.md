# Worked example — `bq_logging._payloads_schema_migrated` race (PR [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418))

The first canonical case of the **module-global flag race** class. Captured
verbatim from the 2026-07-16 session that produced the durable fix.

## The bug surface

`worldarchitecture-ai.llm_forensics.llm_payloads` showed `is_test IS NULL` on
production rows. The BQ coverage watcher alerted after 4 consecutive runs with
≥1 active NULL row in 24h. Three sibling PRs (#8070, #8351, the previous
attempt at #8256) had been merged trying to fix this — each added more code
(serialize writers, preserve columns, retry-on-failure) but kept the
underlying boolean flag in place.

## Live evidence the bug was reproducing (not historic backlog)

```sql
-- Last 24h, Gemini streaming rows in worldarchitecture-ai.llm_forensics.llm_payloads
SELECT
  FORMAT_TIMESTAMP('%H:%M:%S', ingested_at) AS ts,
  COUNTIF(is_test IS NULL) AS nulls,
  COUNTIF(is_test IS NOT NULL) AS populated
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND model = 'gemini-3-flash-preview'
GROUP BY ts
ORDER BY ts
```

Result pattern (5 NULL rows in last 24h, all `gemini-3-flash-preview`):
- `10:03:37` — 1 null, 0 populated
- `10:03:47` — 1 null, 0 populated
- `10:05:27` — 1 null, 0 populated
- `10:05:48` — 1 null, 0 populated
- `10:05:49` — 1 null, 0 populated

The two micro-bursts (10:03:37+10:03:47 and 10:05:27+10:05:48+10:05:49)
with **zero populated rows between them** are the fingerprint of "one cold
replica silently dropped all writes for its lifetime." A populated row
between the bursts would mean the flag flipped mid-burst — but the absence
of populated rows proves the producing process never saw a successful
migration during that window.

## Co-NULL signature

All 5 NULL rows were co-NULL on the same 6 gated columns:

```sql
SELECT
  COUNTIF(is_test IS NULL AND user_id IS NULL
          AND cached_tokens IS NULL AND thoughts_tokens IS NULL
          AND tool_use_tokens IS NULL AND rag_mode IS NULL) AS all_gated_null,
  COUNTIF(LENGTH(request_json) > 1000) AS has_full_request,
  COUNTIF(LENGTH(response_text) > 100) AS has_response_text
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND is_test IS NULL
  AND model = 'gemini-3-flash-preview'
```

Result: `5 / 5 / 5` — all 5 NULLs were co-NULL on the 6 gated columns AND
had full `request_json` (207-348 KB) AND full `response_text`. The row was
being constructed; the gated columns were silently dropped.

## The original code (the race)

```python
# $PROJECT_ROOT/bq_logging.py — pre-fix
_payloads_schema_migrated: bool = False  # module-level boolean
_migration_started: bool = False
_migration_next_retry_at: float = 0.0
_migration_lock = threading.Lock()

def log_llm_payload(...):
    if not _payloads_schema_migrated:
        with _migration_lock:
            if (
                not _payloads_schema_migrated
                and not _migration_started
                and time.monotonic() >= _migration_next_retry_at
            ):
                _migration_started = True
                try:
                    mig_token, mig_project = _get_token_and_project()
                    _migrate_table_schema(mig_token, mig_project, PAYLOADS_TABLE, _payloads_schema())
                    _payloads_schema_migrated = True  # RACE: other threads see False, drop gated writes
                except Exception as mig_exc:
                    _migration_started = False
                    _migration_next_retry_at = time.monotonic() + 60.0
                    logging.warning(f"BQ logging: lazy schema migration failed: {mig_exc}")
    if _payloads_schema_migrated:  # all-or-nothing block
        row["user_id"] = uid
        row["is_test"] = test_flag
        row["cached_tokens"] = cached_tokens
        row["thoughts_tokens"] = thoughts_tokens
        row["tool_use_tokens"] = tool_use_tokens
        row["rag_mode"] = rag_mode
        # ... 6 gated columns dropped if flag is False ...
```

## Why sibling PRs didn't fix it

PR #8070 ([9dc9e0816](https://github.com/$GITHUB_REPOSITORY/commit/9dc9e08168))
"preserve additive schema migration + serialize writers" — added the
`_migration_lock` and `_migration_started` flag, but kept
`_payloads_schema_migrated: bool` as the all-or-nothing gate. Reduced the
rate of silently-dropped rows but didn't remove the race.

PR #8351 ([fa64189728](https://github.com/$GITHUB_REPOSITORY/commit/fa64189728))
"preserve live schema columns" — fixed a related bug (migration wiping
columns added by another revision), didn't address the cold-replica race.

The pattern: each sibling PR added ANOTHER flag/lock/retry, none removed
the underlying boolean.

## The fix (PR #8418, commit 51242edb2)

```python
# $PROJECT_ROOT/bq_logging.py — post-fix
_payloads_schema_set: frozenset[str] | None = None  # actual column names
_payloads_schema_cached_at: float = 0.0
_payloads_schema_refresh_attempted_at: float = 0.0
_payloads_schema_ttl_seconds: float = 3600.0   # one BQ GET per process per hour
_payloads_schema_refresh_cooldown: float = 60.0  # 60s backoff after a failed refresh
_migration_lock = threading.Lock()  # same lock, still serializes

def _refresh_payloads_schema_set(token, project) -> frozenset[str]:
    """Read the live ``llm_payloads`` schema and return the column-name set."""
    url = f"{_api_root()}/projects/{project}/datasets/{_dataset()}/tables/{PAYLOADS_TABLE}"
    resp = requests.get(url, headers=_auth_headers(token), timeout=_HTTP_TIMEOUT_S)
    if resp.status_code != 200:
        raise RuntimeError(f"tables.get {PAYLOADS_TABLE} [{resp.status_code}]: {resp.text}")
    fields = (resp.json().get("schema") or {}).get("fields") or []
    return frozenset(f["name"] for f in fields if isinstance(f, dict) and f.get("name"))

def _ensure_payloads_schema_cached() -> bool:
    """Double-check pattern: refresh cache if stale/missing/failed."""
    global _payloads_schema_set, _payloads_schema_cached_at, _payloads_schema_refresh_attempted_at
    now = time.monotonic()
    cached_set = _payloads_schema_set
    if cached_set is not None and (now - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds:
        return True
    if (now - _payloads_schema_refresh_attempted_at) < _payloads_schema_refresh_cooldown:
        return False  # cooldown active — don't hammer BQ
    with _migration_lock:
        # Re-check under the lock
        cached_set = _payloads_schema_set
        if cached_set is not None and (time.monotonic() - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds:
            return True
        try:
            token, project = _get_token_and_project()
            new_set = _refresh_payloads_schema_set(token, project)
            _payloads_schema_set = new_set
            _payloads_schema_cached_at = time.monotonic()
            return True
        except (RequestException, GoogleAuthError, RuntimeError) as exc:
            _payloads_schema_refresh_attempted_at = time.monotonic()
            logging.warning(f"BQ logging: payloads schema refresh failed: {exc}")
            return False

def log_llm_payload(...):
    # ... (build base row) ...
    if (_payloads_schema_set is None
        or (time.monotonic() - _payloads_schema_cached_at) >= _payloads_schema_ttl_seconds):
        cache_ok = _ensure_payloads_schema_cached()
    else:
        cache_ok = True
    live_columns: frozenset[str] = _payloads_schema_set if cache_ok else frozenset()
    gated = {
        "user_id": uid,
        "is_test": test_flag,
        "cached_tokens": cached_tokens,
        "thoughts_tokens": thoughts_tokens,
        "tool_use_tokens": tool_use_tokens,
        "rag_mode": rag_mode,
    }
    for column_name, value in gated.items():
        # Per-column guard: each gated column is independent of the others.
        if column_name in live_columns:
            row[column_name] = value
        # missing columns are OMITTED — BigQuery rejects unknown fields.
```

## Tests that pin the new shape

1. `test_schema_cache_set_populates_after_tables_get` — successful refresh
   populates the per-process column-name cache.
2. `test_log_llm_payload_includes_is_test_after_successful_schema_refresh` —
   after a successful refresh, the FIRST insert includes `is_test` /
   `user_id` / gated columns.
3. `test_schema_refresh_failure_omits_gated_columns_with_warning` — failed
   refresh logs a warning AND inserts without gated columns (fail-soft);
   cache is empty but `log_llm_payload` doesn't throw.
4. `test_schema_refresh_cooldown_suppresses_immediate_retry` — after a
   failed refresh, a second immediate call within the 60s cooldown does NOT
   re-hit BQ.
5. `test_schema_cache_stale_re_triggers_refresh` — `TTL=0` cache is stale
   on every insert; each insert triggers a refresh (deterministic).
6. `test_schema_cache_two_threads_race_both_populate_is_test` — TWO threads
   with `threading.Barrier`, slow refresh, assert BOTH writers' rows have
   gated columns populated. This deterministically reproduces the pre-fix
   bug and asserts the fix's race-freedom.

## Test fixture migration

Three existing test files used the legacy boolean flag:

- `$PROJECT_ROOT/tests/test_bq_logging.py` — `_capture_payload_row` helper
  monkey-patched `_payloads_schema_migrated = True`. New helper seeds
  `_payloads_schema_set = frozenset({...})` instead.
- `$PROJECT_ROOT/tests/test_bq_logging_schema_migration.py` —
  `test_startup_schema_migration_uses_shared_migration_lock` and
  `test_lazy_migration_concurrent_writers_block_during_in_flight_migration`
  patched the legacy flag. Rewrote to seed the new cache AND assert
  `_payloads_schema_set == frozenset({...})` after the in-flight lock
  releases.
- `$PROJECT_ROOT/tests/test_bq_logging_rag_mode.py`,
  `$PROJECT_ROOT/tests/test_bq_logging_tier2_tokens.py` — helpers updated.
- `$PROJECT_ROOT/tests/test_bq_truly_raw_gemini.py`,
  `$PROJECT_ROOT/tests/test_gemini_detailed_response_logging.py` — added new
  cache seed with `raising=False` on the legacy-attr setattrs so old shims
  don't crash.

## Post-merge metrics to watch

After PR #8418 merges, the BQ coverage watcher should show:

- `is_test IS NULL` on Gemini rows → **0 rows** within 24h of rollout.
- Per-day `is_test` populated % (Gemini) → **>99.5%** sustained.
- 7-day rolling `is_test` populated % (Gemini) → recovers from ~40% to
  >99% as the historic 7/9-7/12 outage rolls out of the window.

## Cross-references

- Skill: `~/.hermes/skills/software-development/module-global-flag-race/SKILL.md`
- Sibling PRs: #8070 ([9dc9e0816](https://github.com/$GITHUB_REPOSITORY/commit/9dc9e08168)),
  #8351 ([fa64189728](https://github.com/$GITHUB_REPOSITORY/commit/fa64189728))
- Fix PR: [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418)
  ([51242edb2](https://github.com/$GITHUB_REPOSITORY/commit/51242edb252cb7e1e3f54f1b7c9ea80c1579abd0))
- Bead: `rev-l27zc` (closed 2026-07-16)
- Slack thread: `C0BCVG4F560/1784219487.851579` (originating BQ coverage
  watcher alert)