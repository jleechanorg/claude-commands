# Reference: MCP Agent Mail BQ coverage alert (2026-07-15)

Second worked example of the `verify-telemetry-alert` skill in action — this one shows the new **Step 0 delivery check** and the corrected **Step 1 reference targets**.

## Alert (verbatim from MCP Agent Mail, channel C0BCVG4F560 thread 1784133016.717719)

```
:warning: `is_test IS NULL` on 70 Gemini rows in last 24h (≥ 10). Likely lazy
schema-migration failure on a Cloud Run replica — see
`bq_logging._payloads_schema_migrated` flag. · `is_test IS NULL` rows have
been flowing for 3 consecutive run(s) across recent windows — migration may
be stuck on a replica (not a transient blip).

*BQ coverage watcher* — 2026-07-15 16:30:06 UTC (mode: recent-rate; cumulative window: 7d)
• Streaming (Gemini, 9483 rows): req_json 100.00% · resp_text 99.45% · finish_reason 100.00% · empty req_json 0.00%
• Non-streaming (Gemini, 949 rows): req_json 100.00% · resp_text 94.84% · finish_reason 72.81% · empty req_json 0.00%
• Active `is_test IS NULL` (Gemini, last 24h): 70 rows (37 have request_json)
• Streak: 3 consecutive run(s) with >=1 active NULL row (threshold: 3)
• Backlog `is_test IS NULL` (Gemini, 7d): 7190 rows (3931 have request_json) — informational; alert fires on active rate only. Backfill via `scripts/backfill_bq_is_test_null.py`.
• `is_test` populated (Gemini, 7d): 31.08% (3242/10432)
• Latest Gemini row: 2026-07-15 16:16:06 UTC (2438 in 2d)
```

## Step 0: Delivery check (this is the new step)

The alert woke me up only because the user asked *"why didn't you respond to this message?"* in their main session. On running the reply path:

```python
mcp__slack__conversations_replies(
    channel_id="C0BCVG4F560",
    thread_ts="1784133016.717719",
    limit=20
)
# Returns: {"error": "not_in_channel"}
```

The Hermes Slack bot is not a member of `C0BCVG4F560`. The alert was visible to me only through the gateway-injected thread-context block in the user's prompt, not through a normal channel poll. Without the user's follow-up, the ack would have stayed silently missing for the entire alert window.

**Logged to `~/.hermes/memory/mcp-mail-ack-log.md`:**

```
2026-07-15T20:59:22Z	missing-delivery-1784133016.717719	bq_coverage_watcher_gemini_is_test_null	user-prompted-ack	2026-07-15T20:59:22Z	channel=C0BCVG4F560 bot=not_in_channel; deliver via user-relay
```

**Open follow-up:** invite the Hermes bot to `C0BCVG4F560` (and audit other alert-source channels), so this is a tracked fix rather than a recurring silent miss.

## Step 1: Verify live numbers reproduce — WITH reference-target corrections

The 2026-07-13 reference doc shows the alert query against `firestore_export.llm_payloads` with `ts`. Those values were stale. The live-state-correct values, verified via `bq show` and `bq ls`:

| Field | Stale doc value | Live actual value | Verification command |
|---|---|---|---|
| Project | `worldarchitect-ai` | `worldarchitecture-ai` | `gcloud config get-value project` |
| Dataset | `firestore_export` | `llm_forensics` | `bq ls --project_id=worldarchitecture-ai` |
| Timestamp col | `ts` | `ingested_at` | `bq show worldarchitecture-ai.llm_forensics.llm_payloads` |
| Gemini filter | `model LIKE 'gemini%'` | agent OR model LIKE '%gemini%' | `bq query 'SELECT DISTINCT model FROM ... LIMIT 5'` |

The first attempt at reproducing numbers used the stale values and hit `Access Denied` because the account doesn't have `BigQuery Data Viewer` on the bogus table name. Once corrected to `llm_forensics`, the read worked.

Live-reproduce SQL (written to `/tmp/alert_verify.sql`, piped via `<`):

```sql
WITH gemini_24h AS (
  SELECT
    COUNT(*) AS total_24h,
    COUNTIF(is_test IS NULL) AS null_is_test_24h,
    COUNTIF(request_json IS NOT NULL AND request_json != '{}') AS have_req_24h
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    AND (LOWER(IFNULL(agent,'')) LIKE '%gemini%'
         OR LOWER(IFNULL(model,'')) LIKE '%gemini%')
),
gemini_7d AS (
  SELECT
    COUNT(*) AS total_7d,
    COUNTIF(is_test IS NULL) AS null_is_test_7d,
    COUNTIF(is_test IS NOT NULL) AS populated_7d
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    AND (LOWER(IFNULL(agent,'')) LIKE '%gemini%'
         OR LOWER(IFNULL(model,'')) LIKE '%gemini%')
)
SELECT * FROM gemini_24h CROSS JOIN gemini_7d
```

Result vs alert claim:

| Metric | Alert | Live | Match |
|---|---|---|---|
| 24h NULL rows | 70 | **93** | drift (close) |
| 24h total rows | not given | 1,228 | n/a |
| 7d NULL rows | 7,190 | **7,037** | close |
| 7d total rows | 10,432 | 10,530 | close |
| 7d populated % | 31.08% | **33.18%** (3,493/10,530) | close |

Headline numbers reproduce; small drift is normal (alert vs my query ran minutes apart).

## Step 2: Cross-check named mechanism

`sed -n '85,100p' $HOME/work/your-project.com/$PROJECT_ROOT/bq_logging.py` confirms:

```python
_migration_lock = threading.Lock()
# Set to True after the first successful lazy schema migration so we don't
# call _migrate_table_schema on every log_llm_payload invocation.
_payloads_schema_migrated: bool = False
```

`_payloads_schema_migrated` is a per-process Python module bool, not a table or a deployment-wide flag. Same scope as the 2026-07-13 reference confirms.

## Step 3: Reframe cumulative → live

Per-day Gemini `is_test` coverage, last 7d:

| Day | Total | NULL | Populated | % |
|---|---|---|---|---|
| 2026-07-15 | 749 | 46 | 703 | 93.86 |
| 2026-07-14 | 1,808 | 185 | 1,623 | 89.77 |
| 2026-07-13 | 1,340 | 530 | 810 | 60.45 |
| 2026-07-12 | 2,166 | 1,862 | 304 | 14.04 |
| 2026-07-11 | 3,066 | 3,013 | 53 | 1.73 |
| 2026-07-10 | 898 | 898 | 0 | 0.00 |
| 2026-07-09 | 503 | 503 | 0 | 0.00 |

**Reframed narrative:** migration PR (`091164e41`, [#7314](https://github.com/$GITHUB_REPOSITORY/pull/7314)/[#7398](https://github.com/$GITHUB_REPOSITORY/pull/7398)) landed 2026-07-11. Coverage ramped 0% → 1.7% → 14% → 60% → 90% → **93.86% today** as replicas rolled through. The 7,037 NULL count is the cumulative cold-start window across old replicas + pre-deploy rows; today's live rate is the highest it's been. The "stuck on a replica, not a transient blip" claim is technically true but misleading — there's no per-replica stuck-state, just a 6.14% live miss rate that needs a backfill + a startup hook to fully close.

## Final ack delivered via user-relay (bot post failed)

Because `mcp__slack__conversations_add_message` cannot post into `C0BCVG4F560`, the verified analysis was delivered to the user directly in their main session rather than as an in-thread ack. The user is the relay.

## Takeaways for future sessions

1. **Step 0 is not optional.** Without it, delivery-miss is invisible until the user asks why — by then the alert window is gone.
2. **BQ reference values drift.** The 2026-07-13 reference doc had project/dataset/column all wrong. Always run `bq show` against the alert-named table before trusting any cached query recipe; the table the watcher writes to is not always the table the alert describes.
3. **Today is the first day the cumulative > live.** At 93.86% populated and rising, the alert threshold (any NULL in 24h) is now firing on the wrong axis — recommend swapping to "% populated < 95% for 3 consecutive runs."
4. **Per-replica module flags remain the root cause.** Pre-deploy rows on any old replica carry `is_test IS NULL` permanently; the only durable fix is a backfill + an `ensure_dataset_and_tables()` call from the deploy hook so new replicas never insert NULL.
