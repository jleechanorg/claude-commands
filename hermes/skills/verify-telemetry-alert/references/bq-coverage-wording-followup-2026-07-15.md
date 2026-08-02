# BQ coverage watcher — wording follow-up PR (2026-07-15)

## Context

After [the staleness reframing recipe](bq-coverage-alert-staleness-2026-07-15.md) proved the alert body was from before PR #774 merged, the operator replied *"make followup"* on the wording — they wanted a tighter version, not just an explanation. This file captures the wording-patch PR that landed.

**Operator ask (Slack out-of-band, post-#774-merge):**
> *"make followup"*

**Result:** [jleechanorg/jleechanclaw#781](https://github.com/jleechanorg/jleechanclaw/pull/781) — 11/11 tests passing (7 original + 4 new wording tests), +145/−5 across 2 files.

## The 3-grep wording-gaps checklist

When the operator says "make the wording clearer" on a fix that already shipped, audit the alert text for these three gaps. Any one of them is worth a follow-up PR; all three combined is a single PR-sized change.

### Gap 1 — File-path gap

The alert names a flag/table/function but doesn't tell the operator where the file lives. Before: *"see `bq_logging._payloads_schema_migrated` flag."* The operator has to grep the codebase to find the file. After: *"see `bq_logging._payloads_schema_migrated` flag in `$PROJECT_ROOT/bq_logging.py` (per-replica lazy migration)."*

**Detection:** `grep -E "see \`[a-zA-Z_.]+\`" <watcher>.py | grep -v 'see [a-zA-Z_/.]+\.(py|sh|sql)'`

### Gap 2 — Threshold label gap

Summary lines show a counter (`Streak: 3`, `Active NULL: 42`, `Latency p99: 850ms`) without labeling whether the threshold is hit. Operator reading the summary has to know what `3` means and whether it's good or bad. After: use `(TRIPS alert ≥ N)` when at/above threshold, `(alert threshold: N)` otherwise.

```python
# Before
summary_lines.append(f"• Streak: {streak} consecutive run(s) with >=1 active NULL row (threshold: {RECENT_STREAK_THRESHOLD})")

# After
streak_label = (
    f" (TRIPS alert \u2265 {RECENT_STREAK_THRESHOLD})"
    if streak >= RECENT_STREAK_THRESHOLD
    else f" (alert threshold: {RECENT_STREAK_THRESHOLD})"
)
summary_lines.append(f"• Streak: {streak} consecutive run(s) with >=1 active NULL row{streak_label}")
```

**Detection:** run the watcher in dry-run mode (or read `latest log entry`) and check whether the summary line shows the threshold hit status at-a-glance.

### Gap 3 — Remediation gap

The alert names the suspected mechanism but doesn't tell the operator what to do. Before: *"see `bq_logging._payloads_schema_migrated` flag."* After: *"Remediation: redeploy to force cold-start + migration on all replicas; or run `scripts/backfill_bq_is_test_null.py` to backfill the historical NULL rows."*

**Two-step remediation pattern:**
1. **Self-contained step** — what the operator can run NOW (redeploy, restart, run script).
2. **Opt-in escape hatch** — a flag/env var that bypasses the alert if the cause is known (e.g. cumulative backlog from a prior bug). The legacy cumulative-7d alert should also tell the operator how to switch to recent-rate mode: *"(Or set `BQ_WATCH_USE_RECENT_RATE=true` to switch to active-rate alerting and suppress this cumulative false-positive.)"*

## Patches applied (PR #781)

```python
# Path 1 — 24h active-window alert (USE_RECENT_RATE=true branch)
alerts.append(
    f"`is_test IS NULL` on {n_active_null} Gemini rows in last "
    f"{RECENT_WINDOW_HOURS}h (\u2265 {ACTIVE_NULL_ABS_THRESHOLD}). "
    f"Likely lazy schema-migration failure on a Cloud Run replica \u2014 "
    f"see `bq_logging._payloads_schema_migrated` flag in "      # ← file path added
    f"`$PROJECT_ROOT/bq_logging.py` (per-replica lazy migration). "    # ← context added
    f"Remediation: redeploy to force cold-start + migration on "  # ← remediation
    f"all replicas; or run `scripts/backfill_bq_is_test_null.py` "
    f"to backfill the historical NULL rows."
)

# Path 2 — streak counter line
streak_label = (
    f" (TRIPS alert \u2265 {RECENT_STREAK_THRESHOLD})"
    if streak >= RECENT_STREAK_THRESHOLD
    else f" (alert threshold: {RECENT_STREAK_THRESHOLD})"
)
summary_lines.append(
    f"\u2022 Streak: {streak} consecutive run(s) with >=1 active NULL row{streak_label}"
)

# Path 3 — legacy cumulative-7d alert (USE_RECENT_RATE=false branch)
alerts.append(
    f"`is_test IS NULL` on {n_null} Gemini rows over {WINDOW_DAYS}d "
    f"(\u2265 {IS_TEST_NULL_ABS_THRESHOLD}). "
    "Likely lazy schema-migration failure on a Cloud Run replica \u2014 "
    "see `bq_logging._payloads_schema_migrated` flag in "         # ← file path
    "`$PROJECT_ROOT/bq_logging.py` (per-replica lazy migration). "
    "Remediation: redeploy to force cold-start + migration on "   # ← remediation
    "all replicas; or run `scripts/backfill_bq_is_test_null.py` "
    "to backfill the historical NULL rows. (Or set "             # ← opt-in escape
    "BQ_WATCH_USE_RECENT_RATE=true to switch to active-rate "
    "alerting and suppress this cumulative false-positive.)"
)
```

## Test additions (4 new, 11/11 passing)

Wording tests follow the same shape: load the watcher, monkeypatch `_run_query`/`_slack_post`, run `main()`, assert the substring appears in the Slack post.

```python
def test_active_alert_includes_remediation_hint(monkeypatch, tmp_streak_state):
    watcher = _load_watcher(monkeypatch)
    bq_responses = iter([
        _streaming_rows(), _nonstream_rows(),
        _row("42", "42"),                        # active null = 42 ≥ 10
        _row("8800", "4859"), _row("10000", "1200"),
        _latest_rows(),
    ])
    posted = []
    monkeypatch.setattr(watcher, "_run_query", lambda q, t, max_rows=200: next(bq_responses))
    monkeypatch.setattr(watcher, "_bq_token", lambda: "fake-token")
    monkeypatch.setattr(watcher, "_slack_post", lambda *a, **kw: posted.append(a[1]))
    rc = watcher.main()
    assert rc == 1
    msg = posted[0]
    assert "$PROJECT_ROOT/bq_logging.py" in msg
    assert "Remediation:" in msg
    assert "redeploy" in msg.lower()
    assert "backfill_bq_is_test_null.py" in msg
```

The 4 new tests cover: active-alert remediation hint, streak label at-threshold, streak label under-threshold, legacy cumulative remediation.

## Anti-patterns avoided

- **Did NOT add new env vars, new thresholds, or change query shapes.** This is wording-only. Adding scope creep turns a 2-file +145/−5 diff into a reviewer nightmare.
- **Did NOT remove the legacy cumulative-7d branch.** Backwards compat preserved; opt-out preserved.
- **Did NOT deploy the script to `~/.hermes/scripts/`** until the PR merges. The worktree copy was temp-installed for pytest, then the deployed copy was restored from `.bak`. See `always-pr-never-local-edit` §"Worktree test-import via `Path.home()` quirk".
- **Did NOT pre-merge** the PR. The skill `proof-before-claim` + the operator's existing process both require explicit MERGE APPROVED.

## Cross-references

- Skill `verify-telemetry-alert` Step 3a.1 — Step 3a.1: Follow-up wording patch recipe (added this PR).
- Skill `verify-telemetry-alert` references/bq-coverage-alert-staleness-2026-07-15.md — the staleness reframing that prompted this follow-up.
- Skill `always-pr-never-local-edit` §"Worktree test-import via Path.home() quirk" — the test-running work-around.
- Skill `always-pr-never-local-edit` §"Local git fetch auth-block work-around for jleechanclaw" — the auth fix needed to fetch origin/main in the first place.
- PR [jleechanorg/jleechanclaw#774](https://github.com/jleechanorg/jleechanclaw/pull/774) — the parent fix that introduced recent-rate mode.
- PR [jleechanorg/jleechanclaw#781](https://github.com/jleechanorg/jleechanclaw/pull/781) — this follow-up wording PR.
