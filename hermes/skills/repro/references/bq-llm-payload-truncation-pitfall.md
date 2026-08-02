# BQ `llm_forensics.llm_payloads` query pitfall — `request_json` is truncated to 350KB

**Verified 2026-07-21, campaign `94mvQDPZR2vQbe5d9zBx` (issue: char creation "big prompt" failure).**

## The pitfall

The `worldarchitecture-ai.llm_forensics.llm_payloads` BigQuery table has a `request_json` column that **appears uniformly capped at 350,001 bytes regardless of actual payload size**. This is NOT a `LIMIT`-style truncation in your query — the bytes are physically truncated when the payload is written. So `LENGTH(request_json)` returns 350,001 for nearly every row, even when the actual payload was 1.2MB.

## The wrong query (returns 0 hits even when the campaign is there)

```sql
-- ❌ WRONG: greps truncated request_json, never matches
SELECT ingested_at, agent, event_type, prompt_tokens, completion_tokens
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND is_test = false
  AND REGEXP_CONTAINS(CAST(request_json AS STRING), r'94mvQDPZR2vQbe5d9zBx')
ORDER BY ingested_at DESC LIMIT 30
-- Result: 0 rows even though the campaign was opened multiple times
```

`REGEXP_CONTAINS` on the truncated string never finds the campaign ID because the truncated bytes don't include it.

## The right query — filter by the TOP-LEVEL `campaign_id` column

```sql
-- ✅ RIGHT: campaign_id is a separate top-level column, not in the truncated text
SELECT ingested_at, agent, event_type, campaign_id, turn_index,
       model, prompt_tokens, completion_tokens, latency_ms,
       LENGTH(CAST(request_json AS STRING)) AS req_bytes,
       LENGTH(response_text) AS resp_bytes
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
  AND campaign_id = '94mvQDPZR2vQbe5d9zBx'
  AND is_test = false
ORDER BY ingested_at DESC LIMIT 30
```

## Diagnostic recipe when BQ shows nothing for your campaign

If the top-level column query also returns 0 rows, the user's session never reached the LLM at all. That's a **client-side or auth-side failure**, NOT a backend bug. Next diagnostics:

1. **Check Cloud Logging for the deployed service**, filtered by `jsonPayload.campaign_id` (or `httpRequest.requestUrl`):
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision" AND resource.labels.service_name="mvp-site-app-dev" AND jsonPayload.campaign_id="<CID>"' \
     --limit=30 --format='value(timestamp,severity,jsonPayload.message)' \
     --project=worldarchitecture-ai
   ```
2. **Check for any 4xx/5xx rows for the campaign URL** (broadens to `httpRequest.requestUrl`):
   ```bash
   gcloud logging read \
     'resource.type="cloud_run_revision" AND resource.labels.service_name="mvp-site-app-dev" AND httpRequest.status>=400' \
     --limit=50 --format='value(timestamp,severity,httpRequest.status,httpRequest.requestUrl)' \
     --project=worldarchitecture-ai
   ```
3. **If both empty**: the user's browser session never fired the request. Look at:
   - Client-side auth state (Firebase `currentUser` null after page idle?)
   - Streaming SSE client abort (`AbortController` cancel on tab close?)
   - Pre-prompt-state modal (`character_creation_stage='concept'` with no initial_choice yet — modal sits waiting for an LLM call that hasn't been triggered)
   - URL endpoint mismatch (`/api/campaigns/<id>/character-creation/state` 404 vs `/api/campaigns/<id>/interaction/stream` 200 — the wrong route is sometimes wired into a JS path)

## Why this matters for the "big prompt" / "stuck loading" phenotype

When a user reports "I pasted a huge prompt into the textarea and nothing happened," the temptation is to assume the backend hit a payload size limit or LLM timeout. The diagnostic order is:

1. **BQ check** (top-level `campaign_id` filter, not `request_json` regex) — confirms whether ANY LLM call was attempted
2. **Cloud Logging check** (`jsonPayload.campaign_id`, then 4xx/5xx) — confirms whether the request reached the backend
3. **Code path read** (search the JS for the form submit handler, find the endpoint, trace `sendMessage` → `fetch` → abort signals)
4. **Local Flask repro** (auth-gate-fallback Step 2 with `X-Test-User-Id` header) — proves the backend handles the big prompt end-to-end if the request does reach it

In the verified case: BQ empty, Cloud Logging empty (only my own 401s), local Flask HTTP 200 with a clean narrative — so the bug was client-side, not a payload limit. PR #8064's fix was for a different issue (user directive precedence), not this one.

## Quick schema check (run once to confirm in your project)

```sql
SELECT column_name, data_type
FROM `worldarchitecture-ai.llm_forensics.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'llm_payloads'
ORDER BY ordinal_position
```

Columns observed (2026-07-21): `ingested_at`, `agent`, `event_type`, `campaign_id`, `turn_index`, `model`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `request_json`, `response_text`, `is_test`, `session_id`, etc. **`campaign_id` is the canonical filter — never `REGEXP_CONTAINS(request_json, '<CID>')`.**

## Pitfalls observed

- **`request_json` is capped at ~350KB** — `LENGTH(CAST(request_json AS STRING))` is not a proxy for actual payload size. Do NOT use it for "is this a big request?" queries — the answer is always "appears to be exactly 350,001 bytes."
- **`response_text` may also be truncated** for long responses; if you need the full narrative, query the campaign's story docs directly via Firestore REST or `download_campaign.py`.
- **Empty `textPayload` in `gcloud logging read`** — the API may show `ERROR` severity rows with `textPayload=null`; the actual message is in `jsonPayload.message`. Always use `--format='json(timestamp,severity,textPayload,jsonPayload.message)'` or include both fields.
- **`gcloud logging read --filter ... httpRequest.requestUrl:"<pattern>"`** with bare `url` field name returns `INVALID_ARGUMENT: Field not found: 'url'`. Use `httpRequest.requestUrl` (the fully-qualified path) or `httpRequest.status>=400` (without any URL filter).
- **BQ `PYTHONPATH` pollution** (`ImportError: cannot import name 'bq_error' from 'utils'`): clear with `cd / && unset PYTHONPATH && bq query ...`. Caused by `~/projects_other/hermes-agent` polluting the import path. See `references/god-mode-directive-missing-subclasses.md` §"BQ forensic recipe."

## NEW pitfalls (2026-07-21, issue #8497)

- **`turn` vs `turn_index` column name** *(verified 2026-07-21, #8497)*. The column is `turn_index`, NOT `turn`. The wrong query:
  ```sql
  SELECT MAX(turn) FROM `worldarchitecture-ai.llm_forensics.llm_payloads` WHERE campaign_id = '<CID>'
  -- Error: 400 Unrecognized name: turn at [2:12]; reason: invalidQuery
  ```
  Always use `turn_index` directly. Burned ~30 seconds in #8497 because the schema name didn't match what I'd written in the first query.

- **Scene-number-vs-turn_index mismatch (user-reported scene ≠ BQ turn_index)** *(verified 2026-07-21, #8497)*. The user said "scene 77" but the campaign `q04GfOEl4SWnEQrFUVST` had `MAX(turn_index) = 32` — the user was misremembering. The actual buggy turn was #31. **Pitfall:** when the user references a "scene N" or "turn N", ALWAYS confirm with `SELECT MAX(turn_index) ... WHERE campaign_id='<CID>'` before assuming. The user's mental scene number often diverges from the LLM's `turn_index` counter by tens or more. **Diagnostic recipe when the user's scene N doesn't exist in BQ:**
  ```sql
  SELECT turn_index, event_type, agent, ingested_at, prompt_tokens
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE campaign_id = '<CID>'
  ORDER BY turn_index DESC
  LIMIT 10
  ```
  Cross-reference the user's reported scene timestamp (if any) against `ingested_at`; the actual buggy turn is usually the one closest in time to the user's complaint. **Or:** search `response_text` and `request_json` for the user's verbatim phrase ("nice looking slayer form", "forgot I always", etc.) — the BQ-truncated bytes may still contain it.

## NEW section (2026-07-21, issue #8501): Cross-campaign cache-hit comparison — the canonical diagnostic for LLM-streaming latency

**Symptom signature.** User reports "still streaming for scene N", "loading takes forever", "next action hangs for 30+ seconds", or any variation of perceived-latency on a single campaign. The first instinct is to blame story-history bloat (the longest prompt is the slowest). That instinct is **almost always wrong** for Gemini implicit-cache workflows.

**Why the first instinct is wrong.** Gemini implicit-context-caching reuses the prompt prefix across consecutive calls when the prefix is byte-identical. A cache hit costs ~10ms of prefill; a cache miss costs full prefill time scaled by prompt size. **Cache hit rate matters 10× more than prompt size** for user-visible latency. A 250K-token prompt with 80% cache hit completes in ~5s; a 200K-token prompt with 0% cache hit takes 30s+.

**The diagnostic step that beats all others (verified 2026-07-21, campaign `q04GfOEl4SWnEQrFUVST`).** When the user reports per-turn latency, the FIRST thing to query is **cross-campaign cache-hit comparison** — find a same-class baseline campaign (more story, more turns, no reported latency) and compare its `cached_tokens` ratio. If the slow campaign has dramatically lower cache hit % despite similar prompt size, the bug is **prompt-cache-invalidation churn**, NOT story bloat.

```sql
-- Per-campaign cache-hit aggregation, last 30 days, gemini_provider.stream only
SELECT
  campaign_id,
  COUNT(*) AS n,
  ROUND(AVG(estimated_input_tokens), 0) AS avg_in,
  ROUND(AVG(IFNULL(cached_tokens, 0)), 0) AS avg_cached,
  ROUND(SAFE_DIVIDE(AVG(IFNULL(cached_tokens, 0)), AVG(estimated_input_tokens)) * 100, 1) AS cache_hit_pct,
  ROUND(AVG(prompt_tokens), 0) AS avg_prompt,
  ROUND(AVG(story_tokens_est), 0) AS avg_story,
  ROUND(AVG(system_instruction_tokens_est), 0) AS avg_sys
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND agent = 'gemini_provider.stream'
  AND estimated_input_tokens IS NOT NULL
GROUP BY campaign_id
HAVING COUNT(*) >= 5
ORDER BY cache_hit_pct ASC  -- LOWEST cache hit = most likely culprit
LIMIT 25
```

**Per-turn cache-hit pattern (reveals cache churn).** Aggregate hides the real signal — the bug is per-turn cache invalidation. Query per-turn `cached_tokens` for the slow campaign's recent activity:

```sql
SELECT
  ingested_at,
  IFNULL(cached_tokens, 0) AS cached,
  estimated_input_tokens,
  ROUND(SAFE_DIVIDE(IFNULL(cached_tokens, 0), estimated_input_tokens) * 100, 1) AS cache_hit_pct,
  prompt_tokens,
  story_tokens_est
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = '<SLOW_CAMPAIGN_ID>'
  AND ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
  AND estimated_input_tokens IS NOT NULL
ORDER BY ingested_at DESC
LIMIT 30
```

If `cached_tokens` **alternates between 0 and a high value every turn**, the prompt prefix is shifting between consecutive calls. The LLM's request payload is byte-identical for most turns, but SOMETHING (god-mode-directive replay, story-history truncation race, per-turn dynamic system-prompt assembly) is shifting the prefix by ≥1 token, busting the implicit cache.

**The user's pivot clue is the diagnostic key.** When the user says "Campaign X had MORE story/content and didn't have this latency" or any cross-campaign comparison, treat that as ground truth and run the cross-campaign query. The slow campaign's cache_hit_pct will be far below the baseline — that's the diagnosis. Confirmed on 2026-07-21:
- `q04GfOEl4SWnEQrFUVST` (the slow campaign, user-reported): avg `cached_tokens` = 75K of 157K est_in = **48%**, with per-turn alternation between 0% and 75-147%
- `RMCPAPdfuErh8MgRuj6n` (Visenya V8, MORE story, no reported latency): avg `cached_tokens` = 114K of 139K est_in = **81.6%**, stable across all 103 calls

**Top 3 cache-buster suspects** (when `cache_hit_pct < 60%` with per-turn alternation):
1. **God-mode directive inline replay** — when the user types "GOD MODE: …", the directive text is injected inline into the system prompt. On god-mode turns, the prefix shifts; on non-god-mode turns, it doesn't. If god-mode is interleaved with normal turns, every god-mode turn busts the cache for the next normal turn.
2. **Long-form narrative module import** (e.g. a Sanguine Architecture / god-of-murder module imported from a recent PR) lives in `god_mode_directives[]` or similar state. When the LLM auto-references it, the inline reference shifts the prefix.
3. **Story-history truncation race** — `story_tokens_est` jumps 21K ↔ 31K between consecutive turns. The LLM emits a `story_history` write that includes the previous turn's narrative verbatim; on the next prefill, the new GPU-side LRU truncates it. The truncation point varies per turn → cache invalidates.

**Candidate code paths** (file:line as of 2026-07-21; check current HEAD before grepping):
- `$PROJECT_ROOT/world_logic.py:_build_story_history_bundle` — recent change to story-history truncation policy
- `$PROJECT_ROOT/agent_prompts.py:_inject_god_mode_directive_text` — direct-injection prefix that includes current user-input echo
- `$PROJECT_ROOT/agent_prompts.py:_compose_system_prompt` — any per-turn dynamic system-instruction assembly (loop over agents, conditionals on user input, etc.)

**The confirmatory BQ diff** (the recipe for the next agent):
```sql
-- Side-by-side prompt prefix diff between cache-hit and cache-miss turns on the same campaign
WITH labeled AS (
  SELECT
    ingested_at,
    IFNULL(cached_tokens, 0) AS cached,
    SUBSTR(REGEXP_REPLACE(CAST(request_json AS STRING), r'\\s+', ' '), 1, 500) AS prefix_500
  FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
  WHERE campaign_id = 'q04GfOEl4SWnEQrFUVST'
    AND ingested_at BETWEEN TIMESTAMP('2026-07-21 08:20:00') AND TIMESTAMP('2026-07-21 08:50:00')
    AND agent = 'gemini_provider.stream'
)
SELECT
  ingested_at,
  cached,
  CASE WHEN cached = 0 THEN 'CACHE_MISS' ELSE 'CACHE_HIT' END AS state,
  prefix_500
FROM labeled
ORDER BY ingested_at
```

The character that flips between consecutive turns IS the cache-buster. Compare against `RMCPAPdfuErh8MgRuj6n` doing the same over the same time window — Visenya V8's prefix should be byte-identical across consecutive turns (stable cache), q04GfO's shouldn't (churning cache).

**Related tables to also check:**
- `worldarchitecture-ai.llm_forensics.latency_metrics` has `duration_ms` (the wall-clock per LLM call), `ttfc_ms` (time-to-first-token), and `flask_handler_first_narrative_chunk` rows — the user-facing "still streaming" wait is THIS metric, NOT `llm_call.duration_ms`. Query both to separate the LLM inference time from the Flask→SSE serialization time.
- `worldarchitecture-ai.llm_forensics.backend_requests` has the HTTP request envelope; cross-reference with `latency_metrics` to identify which user action triggered the slow call.

**Latency_metrics schema (verified 2026-07-21):**
```sql
SELECT column_name FROM `worldarchitecture-ai.llm_forensics.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = 'latency_metrics' ORDER BY ordinal_position;
-- campaign_id STRING, turn_index INT64, operation STRING, agent STRING,
-- model STRING, duration_ms FLOAT64, ttfc_ms FLOAT64, prompt_tokens INT64,
-- output_tokens INT64, success BOOL, extra_json STRING
```
There is **NO** `latency_ms` column on `llm_payloads` (a common wrong-column trap) — duration lives in `latency_metrics.duration_ms`. `llm_payloads` only carries the request/response bodies + token counts.