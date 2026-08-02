# Reference: MCP Agent Mail BQ coverage alert (2026-07-13)

Concrete worked example of the `verify-telemetry-alert` skill in action.

## Alert (verbatim from MCP Agent Mail)

```
:warning: `is_test IS NULL` on 8834 Gemini rows over 7d (≥ 100). Likely lazy
schema-migration failure on a Cloud Run replica — see
`bq_logging._payloads_schema_migrated` flag.
• `is_test` populated = 10.18% (< 95.0%) on 9835 Gemini rows over 7d
• `is_test IS NULL` rows have been flowing for 8 consecutive day(s) — migration
  may be stuck on a replica (not a transient blip).

BQ coverage watcher — 2026-07-13 16:31:29 UTC (window: 7d)
• Streaming (Gemini, 8936 rows): req_json 100.00% · resp_text 99.36% ·
  finish_reason 100.00% · empty req_json 0.00%
• Non-streaming (Gemini, 899 rows): req_json 100.00% · resp_text 94.66% ·
  finish_reason 66.52% · empty req_json 0.00%
• `is_test IS NULL` (Gemini, 7d): 8834 rows (4859 have request_json)
• `is_test` populated (Gemini, 7d): 10.18% (1001/9835)
• Latest Gemini row: 2026-07-13 11:00:19 UTC (4221 in 2d)
```

Thread: `1783960740.480259` in `C0BCVG4F560` (MCP Agent Mail channel).

## Step 1: Verify live numbers reproduce

```bash
# Reproduce alert's headline numbers exactly
bq query --use_legacy_sql=false --format=pretty '
WITH gemini AS (
  SELECT *
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    AND model LIKE "gemini%"
)
SELECT
  COUNT(*) AS gemini_rows_7d,
  COUNTIF(is_test IS NULL) AS is_test_null,
  COUNTIF(is_test IS NOT NULL) AS is_test_populated,
  ROUND(100.0 * COUNTIF(is_test IS NOT NULL) / COUNT(*), 2) AS pct_populated,
  MAX(ingested_at) AS latest_ingested
FROM gemini'
```

Result:

```
| gemini_rows_7d | is_test_null | is_test_populated | pct_populated | latest_ingested       |
|                |              |                   |               |                       |
|           9835 |         8834 |              1001 |         10.18 | 2026-07-13 11:00:19   |
```

Numbers match exactly.

## Step 2: Cross-check named mechanism against actual code

Alert said: *"see `bq_logging._payloads_schema_migrated` flag"* — implying a table or column.

```bash
# Find the file the alert names
rg -l "bq_logging" --type py -g '!node_modules'
# $HOME/your-project.com_rate_25/$PROJECT_ROOT/bq_logging.py

# Locate the named flag
rg -n "_payloads_schema_migrated" $HOME/your-project.com_rate_25/$PROJECT_ROOT/bq_logging.py
# Lines 101, 496, 716, 729, 737

# Read the flag definition (it's a module-level bool, not a table)
sed -n '95,110p' $HOME/your-project.com_rate_25/$PROJECT_ROOT/bq_logging.py
# -> _payloads_schema_migrated: bool = False

# Read the insert path that gates on it
sed -n '710,745p' $HOME/your-project.com_rate_25/$PROJECT_ROOT/bq_logging.py
# -> row["is_test"] = test_flag is gated behind `if _payloads_schema_migrated:`
```

Confirmed: `_payloads_schema_migrated` is a per-process module-level bool, set to True only after `ensure_dataset_and_tables()` runs `_migrate_table_schema()` on each Cloud Run replica. The alert's name was correct as a *flag name*, but the framing implied it was a stable resource when it is actually per-process state.

## Step 3: Reframe the alert's framing

Alert said: *"8 consecutive day(s) — migration may be stuck on a replica (not a transient blip)."*

Per-day breakdown:

```bash
bq query --use_legacy_sql=false --format=pretty '
SELECT DATE(ingested_at) AS day,
       COUNTIF(is_test IS NULL) AS null_n,
       COUNTIF(is_test IS NOT NULL) AS populated_n,
       COUNT(*) AS total
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 9 DAY)
  AND model LIKE "gemini%"
GROUP BY day ORDER BY day DESC'
```

| day | null_n | populated_n | total |
|---|---|---|---|
| 2026-07-13 | 518 | 644 | 1162 |
| 2026-07-12 | 1862 | 304 | 2166 |
| 2026-07-11 | 3013 | 53 | 3066 |
| 2026-07-10 | 898 | 0 | 898 |
| 2026-07-09 | 503 | 0 | 503 |
| 2026-07-08 | 1294 | 0 | 1294 |
| 2026-07-07 | 723 | 0 | 723 |
| 2026-07-06 | 175 | 0 | 175 |

Reality: `is_test` writes started 2026-07-12 evening and ramped through 2026-07-13 — before 2026-07-12 there were zero `is_test` populated rows. The 8,834 NULL is the *cumulative cold-start window of any replica writing before its lazy migration flipped*, NOT 8 days of active drift.

Also every NULL row had `user_id IS NULL` and `extra_json.path = "gemini_provider.stream"` — single writer path, single bug.

## Final ack posted to thread

```
Ack: mcp-mail-bq-coverage-2026-07-13T16:31:29Z — action-needed: yes

Verified: 9,835 Gemini rows / 7d, 8,834 is_test IS NULL, 1,001 populated (10.18%).
Reframing: 8,834 NULL is cumulative cold-start window across replicas, not 8 days
of drift. Migration landed on at least one replica 2026-07-11.

Root cause: bq_logging._payloads_schema_migrated is per-process module flag;
rows written before per-replica migration flip land without user_id/is_test/
cached_tokens/etc. ($PROJECT_ROOT/bq_logging.py:496, 716-739).

Fix recipe: background migration thread w/ capped backoff + caller-arg-first
is_test fallback + replica-stuck metric.

Open question: open the PR now, or first patch the watcher threshold to
is_test IS NULL AND ingested_at > NOW() - INTERVAL 1 HOUR?

🧠 Memories used: [source:gateway-injected, ids:terminal-bq-queries, effect:reframed].
```

Ack logged to `$HOME/memory/mcp-mail-ack-log.md`.

## Takeaways for future sessions

1. Cumulative-window alerts need per-period breakdown — "X consecutive days" can be cumulative cold-start, not live drift.
2. Alert-named mechanisms need code cross-check — `_payloads_schema_migrated` was correctly named but the framing implied a stable resource when it was per-process state.
3. Cross-referencing all NULL-row metadata (user_id, extra_json.path) often reveals the writer is a single path with a single bug — much narrower than "stuck on a replica".
4. Per-replica module flags that gate schema migrations are a recurring anti-pattern — they require either background retry threads or caller-arg fallback to avoid silent data loss during cold-start windows.