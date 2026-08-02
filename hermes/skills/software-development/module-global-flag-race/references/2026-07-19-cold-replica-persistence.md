# Cold-replica persistence — v1.1.0 cache fix did NOT hold across new Cloud Run replicas (2026-07-19)

Follow-up to `references/2026-07-17-pr-8418-driven-to-green.md`. That reference
captured the v1.1.0 cache-fix landing green on 2026-07-17. This one captures
the **2026-07-19 incident where the cache fix did NOT hold** — fresh Cloud Run
replicas spinning up between deployments hit the cold-cache silent-drop path
that Pitfall 10 (in SKILL.md) describes, and 186 `is_test IS NULL` rows
appeared in production in the 24h after merge.

## Headline result

PR [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418) merged at
`2026-07-19T00:54:46Z` (squash `90238d16b8`). 24 hours later, the bug returned.

## Live BQ evidence (queried 2026-07-19T21:00 UTC, clean PYTHONPATH workaround for the broken `bq` CLI)

**Per-hour is_test NULL rate, last 96h (Gemini):**

```
2026-07-19 20:00 UTC: 23/50 NULL = 54.0% populated   ← STILL BROKEN
2026-07-19 19:00 UTC: 46/168 NULL = 72.62% populated  ← STILL BROKEN
2026-07-19 18:00 UTC: 0/118 NULL = 100.0% populated   ← OK
2026-07-19 17:00 UTC: 0/66 NULL = 100.0% populated    ← OK
...
2026-07-19 13:00 UTC: 23/46 NULL = 50.0% populated   ← STILL BROKEN (cold replica)
2026-07-19 12:00 UTC: 0/23 NULL = 100.0% populated   ← OK
2026-07-17 18:00 UTC: 23/23 NULL = 0.0% populated     ← pre-fix bug
2026-07-17 09:00 UTC: 45/45 NULL = 0.0% populated     ← pre-fix bug
```

The alternating OK / NOT-OK pattern is the fingerprint of "fresh Cloud Run
replica spun up, hit the cold-cache race on first call, silently dropped
all gated columns for its lifetime, then died or was replaced."

**Last 24h aggregate:**

```
n_is_test_null = 186
n_total = 2014
pct_populated = 90.76%       ← fails watcher (target ≥95%)
co_null_5col_pct = 100.0%    ← every NULL row hits all 5 gated cols (smoking gun)
```

**7d rolling:**

```
n_is_test_null = 1237
n_total = 8636
pct_populated = 85.68%       ← cumulative window also trips the watcher
```

**Per-minute breakdown of the 2026-07-19 19:00-20:00 UTC bad window** (the
micro-burst pattern that proves one cold replica, not a fleet-wide issue):

```
2026-07-19 19:47  5 NULLs
2026-07-19 19:48  4 NULLs
2026-07-19 19:49  8 NULLs
2026-07-19 19:50  6 NULLs
2026-07-19 19:56  7 NULLs
2026-07-19 19:57  6 NULLs
2026-07-19 19:58  4 NULLs
2026-07-19 19:59  6 NULLs
2026-07-19 20:03  1 NULL
2026-07-19 20:04  2 NULLs
2026-07-19 20:05  4 NULLs
2026-07-19 20:06  8 NULLs
2026-07-19 20:07  6 NULLs
2026-07-19 20:08  2 NULLs
```

Per-replica attribution requires a `revision_id` column (currently absent
in `llm_payloads` — verified `INFORMATION_SCHEMA.COLUMNS` returned empty for
any `revision`/`replica` column). Without it, the diagnosis is
"the pattern matches cold-replica spin-up" but cannot name the specific
revision. **Fix #1 is to add `revision_id` to `_payloads_schema()` so future
incidents are diagnosable from BQ alone.**

## Root cause (read the code on `origin/main`)

`$PROJECT_ROOT/bq_logging.py:1106-1120`:

```python
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
    else frozenset()  # ← THE LEAK
)
for column_name in _GATED_COLUMNS:
    if column_name in live_columns:
        row[column_name] = gated_values[column_name]
```

When `_payloads_schema_set is None` (cold cache on a freshly-spun Cloud Run
replica) AND `_ensure_payloads_schema_cached()` returns False (transient
BQ/auth hiccup on first call), `live_columns = frozenset()` and ALL 12 gated
columns are silently dropped. The cooldown logic in
`_ensure_payloads_schema_cached` then keeps the cache cold for the next
`_payloads_schema_refresh_cooldown` seconds (60s default), during which every
insert on this replica silently drops all gated columns.

The v1.1.0 fix correctly handles the steady-state race (two writers in the
same process seeing a stale boolean). It does NOT cover the cold-replica
race because the cache is empty on first call AND a transient hiccup on
that first call propagates into the `frozenset()` fallback.

## What was wrong with my prior reasoning (lesson learned)

In the 2026-07-17 session that drove PR #8418 to green, I claimed the fix
"addresses the cold-replica race" because the cache populates from a
`tables.get` round-trip. That was wrong: the cache populates ON FIRST CALL,
and a transient hiccup on that first call freezes the cache as empty. The
cache cannot populate from itself.

The right framing: the cache is per-process and starts empty. The
`tables.get` round-trip is what populates it. If the round-trip fails on
first call, the cache STAYS empty until either (a) TTL expires (1h default)
or (b) a sibling writer's successful refresh wins. Both are worse than
treating the boot-time `_payloads_schema()` declaration as the fallback
shape.

## The fix shape (Pitfall 10 in SKILL.md, dispatched as PR `fix/bq-payloads-schema-cold-replica-fix`)

1. **`_boot_warmup_succeeded: bool = False`** — set True at the end of
   `ensure_dataset_and_tables` after the migrate attempt, regardless of
   whether the cache fetch itself succeeded (because the table HAS the
   columns we just declared/migrated, even if the cache is stale).

2. **Write-path fallback chain** (replaces the single
   `if cache_ok and _payloads_schema_set is not None: ... else frozenset()`
   ternary):
   - If cache populated → use cache (existing behavior).
   - Elif `_boot_warmup_succeeded` → fall back to
     `frozenset(_payloads_schema())` (the declared authoritative schema) +
     log structured warning with `K_REVISION`.
   - Else (truly cold, never warmed up) → log ERROR + refuse insert
     (fail-loud, not fail-soft — silently polluting BQ is worse than
     losing a row).

3. **Retry-with-backoff** on first call: retry
   `_ensure_payloads_schema_cached()` up to 3× within 500ms before falling
   through to the boot-warmup fallback. Transient BQ hiccups on cold
   replicas typically clear within 200ms.

4. **`revision_id` column** reading `os.environ.get('K_REVISION', 'local-dev')`
   (Cloud Run sets this). Add to `_payloads_schema()` as a NON-gated
   column. Make the watcher alert report the `revision_id` distribution
   of NULL rows so future cold-replica incidents are diagnosable from BQ
   alone without reading Cloud Run logs.

5. **3 new tests** in `$PROJECT_ROOT/tests/test_bq_logging_schema_migration.py`:
   - `test_cold_cache_transient_refresh_failure_includes_gated_columns`
   - `test_cold_cache_no_boot_warmup_refuses_insert`
   - `test_log_llm_payload_includes_revision_id`

## Tooling workarounds used in this investigation

### `bq` CLI broken on this Mac — `env -i PYTHONPATH=` workaround

The local `bq` CLI throws `ImportError: cannot import name 'bq_error' from 'utils'`
because `$HOME/projects_other/hermes-agent/utils.py` shadows the
gcloud SDK's `utils` module on Python's import path. The fix is to run `bq`
in a clean environment:

```bash
env -i \
  PATH=/opt/homebrew/bin:/usr/bin:/bin \
  HOME=$HOME \
  PYTHONPATH=/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/lib/third_party:\
/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/lib:\
/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/platform/bq_libs \
  PYTHONNOUSERSITE=1 \
  bq query --project_id=worldarchitecture-ai --use_legacy_sql=false --format=json \
  <<'SQL'
SELECT ... FROM `worldarchitecture-ai.llm_forensics.llm_payloads` ...
SQL
```

The `PYTHONPATH` paths may vary per gcloud SDK install — `find /opt/homebrew/Caskroom/google-cloud-sdk -name bq_libs -type d` to locate. Alternative: `unset PYTHONPATH && bq query ...` works if no other Python project in the cwd hijacks the import path (the hermes-agent tree at `$HOME/projects_other/hermes-agent/` was the shadowing culprit here, so the cwd had to be elsewhere).

For Python-via-urllib against the BQ REST API, `gcloud auth application-default print-access-token` + REST POST to `https://bigquery.googleapis.com/bigquery/v2/projects/<PROJECT>/queries` works from a sandbox with the right IAM — but **this Hermes sandbox has the wrong ADC** and gets 403 on `bigquery.jobs.create` for `worldarchitecture-ai`. Stick with the `env -i` `bq` wrapper.

### `gh pr view` GraphQL rate limit → REST fallback

When `gh pr view <N> --repo ... --json state,mergedAt,...` returns
`GraphQL: API rate limit already exceeded for user ID 13840161`, fall back
to the REST endpoint (different bucket from GraphQL):

```bash
gh api repos/$GITHUB_REPOSITORY/pulls/8418 \
  --jq '{number, state, merged: .merged, merge_commit_sha,
         head_sha: .head.sha, head_ref: .head.ref, additions, deletions, changed_files, title}'
```

Verify PR head vs squash commit (they differ): `gh pr view` reports the PR
head SHA (e.g., `c0b8c107...`); `git log origin/main --grep='<PR#>'`
reports the squash-commit SHA (e.g., `90238d16...`). Both are correct,
just different views.

### `gh api rate_limit` check

```bash
gh api rate_limit --jq '.resources | {core: .core, graphql: .graphql}'
```

When GraphQL bucket is exhausted but Core REST is healthy, REST endpoints
keep working. Reset timestamps are in the response (`reset` field = epoch
seconds; convert: `date -r <reset>`).

## Dispatch pattern (the AO worker was `worldarchitect-64`)

When you have a 5.3KB brief that exceeds `ao spawn --prompt <string>`'s
argv limit:

```bash
# 1. Save the brief to a stable path BEFORE spawning (worktrees can be
#    wiped by the spawn):
mkdir -p ~/.hermes/var
cat > ~/.hermes/var/<topic>-brief.md <<'BRIEF'
<full brief here>
BRIEF

# 2. Spawn with a tight <2KB initial prompt:
PROMPT=$(cat /tmp/short-prompt.txt)
ao spawn --harness claude-code \
  --issue <bead-id> \
  --branch fix/<topic> \
  --name <short-name> \
  --prompt "$PROMPT" \
  --project <registered-project-id>

# 3. Find the registered project id (NOT the GitHub owner/repo path):
ao project list

# 4. After spawn, push the full brief via tmux load-buffer +
#    paste-buffer + Enter (per dispatch-task v1.5.0):
tmux load-buffer ~/.hermes/var/<topic>-brief.md
tmux paste-buffer -t <session-id>
tmux send-keys -t <session-id> Enter

# 5. Verify the worker is running:
ao session ls | grep <session-id>   # status should be [working]
```

DO NOT pre-create the worktree with `git worktree add -b <branch>` and then
spawn — `ao spawn` will fail with `BRANCH_CHECKED_OUT_ELSEWHERE`. Let AO
create the worktree.

DO NOT pre-write the brief into the worktree path — if you `git worktree
remove` the worktree (which you might do to retry spawn), the brief gets
nuked. Use `~/.hermes/var/` instead.

## Cross-references

- `references/2026-07-16-bq-is-test-null-pr-8418.md` — original v1.0.0 design + tests
- `references/2026-07-17-pr-8418-driven-to-green.md` — v1.1.0 corrections + PR gate choreography
- Skill: `~/.hermes/skills/software-development/module-global-flag-race/SKILL.md` (v1.2.0)
- Skill: `~/.hermes/skills/devops/verify-telemetry-alert/SKILL.md` — the alert→live-probe workflow
- Skill: `~/.hermes/skills/software-development/wa-green-gate-pr-shape/SKILL.md` — PR-shape discipline
- Skill: `~/.hermes/skills/workflow/dispatch-task/SKILL.md` — AO spawn / brief / steer pattern
- PR (the v1.1.0 fix that didn't fully hold): [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418)
- Follow-up PR (this fix): `fix/bq-payloads-schema-cold-replica-fix` (in progress as of 2026-07-19, worker `worldarchitect-64`, bead `rev-zurdo`)
- Beads: `rev-2l2x6` (PR #8418) → `rev-uh0ek` (root alert) → `rev-zurdo` (cold-replica persistence)
- Slack thread: `C0BCVG4F560/1784219487.851579`