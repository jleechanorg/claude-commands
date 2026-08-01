---
name: verify-telemetry-alert
description: "Verify an automated alert (BQ coverage watcher, MCP Agent Mail, GH Actions billing, infra watcher) or in-house scheduled cron (Daily Bug Hunt, doc-audit, stability-report) before acking it. Cross-checks the alert's named mechanism against live state and the actual code path, then reframes the alert's framing if it misleads. Triggers: an automated cron/watchdog posts a warning/error with a named mechanism (table/flag/RPC/dataset/agent/subcommand), alert uses cumulative phrasing, alert names a Cloud Run replica / per-process flag / module-level state as suspect. Also fires for **post-merge fix verification** — Step 1b catches the failure mode where the merge landed on origin/main but the Cloud Run service was not redeployed (PR #8418 worked example in references/post-merge-deployment-coverage-2026-07-20.md). For in-house crons claiming suspiciously clean results, see references/in-house-cron-silent-failure-2026-07-15.md."
version: 1.5.0
metadata:
  hermes:
    tags: [telemetry, alerts, verification, ack, incident-response, bigquery, observability, in-house-cron, post-merge-verification]
    related_skills: [systematic-debugging, incident-proposal-current-evidence-gate, proof-before-claim, mcp-mail-ack, module-global-flag-race]
history:
  - "1.5.0 (2026-07-20): Added Step 1b (deployment-coverage verification) and Step 1c (5-column co-NULL signature diagnostic). For any post-merge fix verification on a Cloud Run service, the merge SHA landing on origin/main does NOT mean the running image has the fix. Recipe: cross-check `gcloud run revisions list --service=<stable-service>` last-deployed timestamp against the merge timestamp; if the service's last deploy predates the merge, the fix is in code but not in the running binary. Verified live 2026-07-20 against PR #8418 (`fix/bq-is-test-null-cache-replay`, merged 2026-07-19T00:54:46Z): `mvp-site-app-stable` last deployed 2026-07-18 21:05 UTC (3h 49m BEFORE the merge) on image `gcr.io/worldarchitecture-ai/mvp-site-app:stable-65dd85b`. 4 post-merge is_test NULL bursts (07-19 19:00, 20:00, 21:00, 07-20 04:00) involving the production agent roster confirmed the bug was still reproducing because the fix never reached prod. The 5-column co-NULL signature (`is_test IS NULL AND cached_tokens IS NULL AND thoughts_tokens IS NULL AND tool_use_tokens IS NULL AND rag_mode IS NULL`) distinguishes the schema-gate bug class from a generic insert-pipeline failure — the schema-gate columns are NULL together because the process's column-name cache was empty. Reference file `references/post-merge-deployment-coverage-2026-07-20.md` ships the full worked example including per-hour cohort breakdown and gcloud + bq query recipes."
  - "1.4.0 (2026-07-19): Added Pitfall P0 (Step 1 prerequisite) — the `bq` CLI on this Mac is broken because `$HOME/projects_other/hermes-agent/utils.py` shadows the gcloud SDK's `utils` module on Python's import path; fix is `env -i PATH=… PYTHONPATH=… PYTHONNOUSERSITE=1 bq query …` (paths vary per gcloud SDK install — `find /opt/homebrew/Caskroom/google-cloud-sdk -name bq_libs -type d` to locate). Added Pitfall P1 (Step 1 alternative) — when `gh pr view --json` returns `GraphQL: API rate limit already exceeded`, fall back to REST `gh api repos/<owner>/<repo>/pulls/<N>` (different bucket, usually still has budget). Pitfall P2 (Step 2 prerequisite) — when BQ REST via urllib from a sandbox returns 403 on `bigquery.jobs.create`, the sandbox's ADC lacks the IAM role; route the BQ probe through `env -i bq` on the user's authenticated gcloud session instead. Verified live 2026-07-19 against the `is_test IS NULL` alert in Slack C0BCVG4F560/1784219487.851579 — these three pitfalls cost ~10 minutes of failed probes before the workaround landed."
  - "1.3.0 (2026-07-17): Added generic anti-pattern #7 — 'Don't trust prior-session reports about remote-system behavior; re-test before claiming it's a blocker.' Verified case: 2026-07-17 cloud-build drive (Slack C09GRLXF9GR). I inherited a prior session's framing that 'git secret guard rejected the push' and reported cloud-build as broken without re-running the hand-off. The user replied 'whats the secret guard? Lets make it do a hello world program' — a 5-min hello-world proved the box actually works on clean repos and the prior blocker was project-specific (tracked secrets in main history), not box-side. Generalizes: any prior-session claim about remote/3rd-party behavior (cloud-build, CI, MCP servers, launchd jobs, cron pipelines) must be re-verified in the current session before being reported as a blocker. The hello-world validation recipe lives at `~/.hermes/skills/devops/superpowers-cloud-build/references/hello-world-validation-2026-07-17.md` — same principle for cloud-build specifically."
  - "1.2.0 (2026-07-15): Added references/in-house-cron-silent-failure-2026-07-15.md — sister-case worked example for the same 4-step protocol applied to in-house scheduled scripts (Daily Bug Hunt cron, jleechanorg/jleechanclaw#782). Captures the 'fail-closed sentinel covers the wrong failure mode' pattern: preflight-vs-output-parse counter asymmetry that produces false-negative 'clean sweep' reports. Tagged in-house-cron in hermes.tags. References section pointer added."
  - "1.1.0 (2026-07-15): Step 3a.1 added — when operator replies 'make followup' after Step 3a staleness reframing, capture the 3-grep wording-gaps checklist (file-path, threshold label, remediation) plus the test-import-via-Path.home() work-around needed to validate the patches. References/bq-coverage-wording-followup-2026-07-15.md ships the verified PR #781 worked example."
  - "1.0.0 (2026-07-15): Step 0 delivery-check + Step 3a staleness reframing added; 4 references captured (one per BQ coverage reframe, one for the staleness-reframe, references/mcp-mail-bq-coverage-2026-07-13.md retained for historical evidence)."
---

# Verify Telemetry Alert Before Ack

## Why this skill exists

Automated alert systems (BQ coverage watchers, MCP Agent Mail cron jobs, billing anomaly detectors, quota monitors) post warning/error messages that demand acknowledgement. The naive path — read the alert, ack with the headline framing — has three recurring failure modes:

1. **Accepting misframed claims.** Cumulative-window alerts often phrase drift as if it is live ("8 consecutive days") when the underlying reality is a different window (a cold-start accumulation, a deployment boundary, a sample of n rows that all came from one replica).
2. **Skipping alert→code cross-check.** Alerts cite named mechanisms (table names, module-level flags, RPC names, schema columns). Those names can be wrong, drift from current code, or refer to a state object rather than the entity the alert implies.
3. **Silent delivery failure.** Alert lands in a channel/thread the Hermes Slack bot is not a member of (or has lost membership for). `mcp__slack__conversations_replies` returns `not_in_channel`; the ack step is silently skipped; the user only finds out minutes-to-hours later via a question like *"why didn't you respond to this?"*. This must be detected and either routed around (user-relay, alternate channel) or fixed at the membership layer.

The fix is a 4-step protocol: (0) delivery check, (1) verify live numbers reproduce, (2) cross-check named mechanism against actual code, (3) reframe if needed. Run before acking *any* automated alert with operational consequences.

## When to invoke

- MCP Agent Mail, Slack channel watchers, BQ coverage alerts, GH Actions billing alerts, GCP quota alerts, or any automated system posts an alert with a named mechanism (table name, function name, flag, RPC, dataset).
- An alert claims "X consecutive days" or "X hours sustained" — reframe risk.
- An alert names a Cloud Run replica, K8s pod, or per-process state object as the suspect.
- An alert suggests a fix that names a code path you have not read.
- An alert arrives in a channel/thread where the bot's reply path may not work (post-deploy membership reset, cross-workspace message, internal-only channel) — run Step 0 first.

## The 4-step protocol

### Step 0: Delivery check (NEW 2026-07-15 — silently failing ack is worse than no ack)

Before any verification work, confirm you can actually reply to the source thread. Bot accounts are scoped to a workspace and lose channel membership silently.

```bash
# Test that the channel is reachable for replies
mcp__slack__conversations_replies(channel_id=<chan>, thread_ts=<alert_ts>, limit=1)
# If this returns "not_in_channel" or "channel_not_found":
#   1. Try the parent channel — the alert might be in a child under a parent
#   2. Try `chat.postMessage` with the human user token (`SLACK_USER_TOKEN`) — Path B per SOUL.md `slack-cross-workspace-fallback-xoxp`. Reply will appear under the human's identity; say so in body if confusion risk.
#   3. If still blocked: log the ack with delivery=MISSING to ~/.hermes/memory/mcp-mail-ack-log.md (see `mcp-mail-ack` SOUL COMMIT) AND mention the membership gap to the user in the next reply so it becomes a tracked fix, not a silent miss.
```

Symptom of the bug this catches: the user finally notices and asks *"why didn't you respond to this message?"* — by then the operational claim has been silent for the entire alert window.

### Step 1: Verify live numbers reproduce

Before acking any alert with quantitative claims, re-run the queries or commands the alert implies. Live evidence beats alert prose.

```bash
# Example (BQ coverage alert):
bq query --use_legacy_sql=false --format=pretty '
SELECT
  COUNTIF(<alert_predicate>) AS claimed_n,
  COUNT(*) AS total
FROM `<dataset>.<table>`
WHERE <alert_window>'
```

Match every headline number the alert posts. If the alert says "8,834 of 9,835 rows have is_test IS NULL", reproduce both numbers exactly. If any number diverges, say so in the ack — the alert's framing might be stale or wrong.

### Step 1b: Verify deployment coverage (NEW 2026-07-20 — for post-merge fix verification)

When the verification is a post-merge fix check ("did PR #N actually fix the bug?"), reproducing the alert numbers is **necessary but not sufficient**. The bug might still reproduce because the fix is in the code on origin/main but the running image is stale. Recipe:

```bash
# 1. Confirm the PR is merged (cheap, fast):
gh pr view <N> --repo <OWNER>/<REPO> --json state,mergedAt,headRefOid
# Expected: state=MERGED, mergedAt=<ISO timestamp>, headRefOid=<SHA>

# 2. Find the Cloud Run service that actually receives prod traffic. For
#    $GITHUB_REPOSITORY the pattern is:
#      mvp-site-app-stable      ← stable, receives all prod traffic
#      mvp-site-app-preview     ← preview channel, traffic = 0 in prod
#      mvp-site-app-{s1..s10}   ← staging shards, NOT prod
#    Verify which service has 100% latestRevision traffic:
gcloud run services list --project=<PROJECT> --region=us-central1 \
  --format='table(SERVICE,LAST DEPLOYED BY,LAST DEPLOYED AT)'

# 3. Pull the deploy timestamps of the stable service's revisions:
gcloud run revisions list --service=<stable-service> --region=us-central1 \
  --project=<PROJECT> --limit=5
# Look at the ACTIVE revision's "DEPLOYED" column.

# 4. Cross-check: is the stable service's last deploy AFTER the merge?
#    If the service's last deploy timestamp is BEFORE mergedAt, the fix
#    never reached prod. The running image still has the bug.
if [[ "$(gcloud run revisions list --service=<stable> --region=us-central1 \
  --project=<PROJECT> --limit=1 --format='value(metadata.creationTimestamp)')" \
  < "$mergedAt" ]]; then
  echo "BUG STILL REPRODUCING — fix in code, not in running binary"
fi

# 5. Optional sanity: confirm the current image tag matches the merge SHA.
gcloud run services describe <stable-service> --region=us-central1 \
  --project=<PROJECT> --format='yaml(spec.template.spec.containers[0].image)'
# If the image digest ends in `:<merge-sha-prefix>` or has a recent build
# date, the fix is live. Otherwise the image is stale.
```

**Why this is its own step.** The naive post-merge verification is "BQ numbers show the bug, but the fix code passed all unit tests, so the deploy didn't propagate." The unit tests, the CI green check, the `gh pr view MERGED` — none of these prove the running binary has the fix. They prove origin/main has the fix. A Cloud Run service is re-deployed only when someone triggers a release (manual `gcloud run deploy`, a release branch push to a workflow that watches it, or an automated promotion). The merge → deploy gap can be hours to weeks.

**Verified case 2026-07-20, PR #8418:** merge at 2026-07-19T00:54:46Z; `mvp-site-app-stable` last deployed 2026-07-18 21:05 UTC (3h 49m **before** the merge); 4 post-merge is_test NULL bursts (07-19 19:00/20:00/21:00, 07-20 04:00) involving the production agent roster confirmed the old bug still reproducing because the new code never reached the running image. The full worked example is at `references/post-merge-deployment-coverage-2026-07-20.md`.

**What to do when Step 1b fails:** do NOT mark the PR's bead resolved. Post the verdict with `🔴 STILL BROKEN — fix in code, not in prod` and a concrete remediation (trigger a redeploy to `<stable-service>` from the merge SHA, or open a fresh `rev-<deploy-bead>` and dispatch). The watcher alert will re-fire at the next tick — that's the right behavior, since the bug IS still happening.

### Step 1c: Schema-gate co-NULL signature (NEW 2026-07-20 — distinguishes schema-cache bug class)

When the alert (or the live data) shows `is_test IS NULL` rows, a generic count of NULL rows can't tell you whether the root cause is a `module-global-flag-race` (PR #8418's pattern) or a different insert-pipeline failure. The diagnostic signature that distinguishes the schema-cache bug class:

```sql
SELECT
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNTIF(
    is_test IS NULL
    AND cached_tokens IS NULL
    AND thoughts_tokens IS NULL
    AND tool_use_tokens IS NULL
    AND rag_mode IS NULL
  ) AS co_null_5col,
  ROUND(100.0 * COUNTIF(
    is_test IS NULL
    AND cached_tokens IS NULL
    AND thoughts_tokens IS NULL
    AND tool_use_tokens IS NULL
    AND rag_mode IS NULL
  ) / GREATEST(1, COUNTIF(is_test IS NULL)), 2) AS co_null_pct
FROM `<PROJECT>.<dataset>.<table>`
WHERE <alert_window>
  AND <alert_model_filter>
```

**Interpretation:**
- `co_null_pct ≈ 100%` — every `is_test NULL` row also lacks all four other schema-gated columns. The producer process's column-name cache was empty (or the gate was bypassed entirely). This is the `_payloads_schema_migrated` / per-process cache bug class. Fix is in the writer code.
- `co_null_pct < 50%` — `is_test` is being independently dropped or not set on rows that DO populate other gated columns. This is a different bug (maybe a request-path code branch that bypasses the `is_test` assignment but still hits the cache). Don't conflate it with the schema-cache bug — the fix will be different.
- `co_null_pct = 0%` — `is_test` is NULL but every other gated column is populated. This is a separate field-level bug (maybe a feature flag disabling `is_test` only).

**Why this matters:** the watcher alert firing on `is_test IS NULL` (threshold N=10, streak ≥3) was the SAME alert as the original PR #8418 fix. If after the merge the `co_null_pct` drops to 0%, the fix worked but a different bug is now visible. If `co_null_pct` stays at 100%, the fix didn't take (Step 1b territory — image not deployed). If `co_null_pct` is somewhere in between, the fix partially took and a sibling bug is exposed.

**Verified case 2026-07-20, PR #8418:** post-merge, the 161 is_test NULL rows in last 24h had `co_null_pct = 100.0%` — every NULL row also lacked the 4 sibling schema-gated columns, confirming the SAME bug class was reproducing, not a new one. The `co_null_pct` is the test that proves "this is the same bug as before" vs. "this is a new regression."

### Step 1d: Per-hour cohort decomposition (NEW 2026-07-20 — for fix-vs-stale-image disambiguation)

After Steps 1b and 1c, decompose the 24h or 48h window by hour and label each hour as pre-merge / post-merge:

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d %H:00', ingested_at) AS hour,
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNT(*) AS n_total,
  ARRAY_AGG(DISTINCT agent IGNORE NULLS LIMIT 5) AS top_agents
FROM `<PROJECT>.<dataset>.<table>`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
  AND <alert_model_filter>
  AND is_test IS NULL
GROUP BY hour ORDER BY hour DESC
```

**Interpretation matrix:**

| Pre-merge hours | Post-merge hours | Diagnosis |
|---|---|---|
| n_null high | n_null = 0 | ✅ FIX HELD. The deploy reached prod AND the code works. |
| n_null high | n_null high | 🔴 STILL BROKEN. Likely Step 1b (image not redeployed). Confirm with `gcloud run revisions list`. |
| n_null = 0 | n_null high | 🔴 REGRESSION. The fix introduced a new bug. Compare agent roster to pre-merge — different agents means a new code path is failing. |
| n_null low | n_null low | ✅ FIX HELD + low traffic. Bug was minor and is now contained. |

**Verified case 2026-07-20, PR #8418:** the per-hour cohort clearly showed pre-merge hours (07-19 13:00, 19:00, 20:00, 21:00, 07-20 04:00) had 23-46 NULL rows from the production agent roster (CharacterCreationAgent, StoryModeAgent, GodModeAgent, FactionManagementAgent, etc.), while most other hours had 0 NULL rows. The bursts were concentrated in pre-merge hours with a few post-merge spikes — classic Step 1b image-not-deployed pattern (the fix hadn't reached prod yet, but the running prod was still on the pre-fix image, so it produced the same bursts as before).

**Why averaging doesn't work:** a 24h aggregate of `is_test IS NULL = 161/1623 = 9.92%` looks "almost fine" if you don't compare to the pre-merge baseline. The per-hour decomposition reveals that the pre-merge and post-merge hours have IDENTICAL burst patterns, which is the smoking gun for "fix not deployed."

**BQ reference targets for the recurring `llm_payloads` watcher (verified 2026-07-15):**

| Field | Stale alert guess | Actual value | Check |
|---|---|---|---|
| Project ID | `worldarchitect-ai` (note the `-ai` not `-ai.ai`) | `worldarchitecture-ai` | `gcloud config get-value project` |
| Dataset | `firestore_export` | `llm_forensics` | `bq ls --project_id=... <dataset>` |
| Timestamp column | `ts` | `ingested_at` | `bq show <dataset>.<table>` |
| Gemini filter | `model LIKE 'gemini%'` | `LOWER(IFNULL(agent,'')) LIKE '%gemini%' OR LOWER(IFNULL(model,'')) LIKE '%gemini%'` | `bq query 'SELECT DISTINCT model FROM ... LIMIT 5'` |

Account selection (must be a service account or human with `BigQuery Data Viewer`): `gcloud auth list` will show whether the active account is the right identity for the dataset; some watchers write to one project and read from another.

Always write the SQL to a temp file (`/tmp/alert_verify.sql`) and pipe via `<`, not shell-quoted `-e`: a stray `%` in `LIKE '%gemini%'` breaks a single-quoted heredoc on shells with format-string expansion.

### Step 2: Cross-check the named mechanism against actual code

Alerts cite named mechanisms. Treat those names as **leads**, not facts. Verify them in the actual code path.

Common pattern (verified 2026-07-13 against MCP Agent Mail BQ coverage alert):

- Alert says: *"Likely lazy schema-migration failure on a Cloud Run replica — see `bq_logging._payloads_schema_migrated` flag."*
- The name `_payloads_schema_migrated` is a **Python module-level bool** in `$PROJECT_ROOT/bq_logging.py`, NOT a table. Reading the code revealed it gates `row["is_test"] = test_flag` until a per-process PATCH migration flips the flag — meaning every Cloud Run replica carries its own copy, and any replica whose lazy migration hasn't yet run (cold start, transient 5xx, or 60s backoff retry window) inserts rows without `is_test`.

Recipe to cross-check:

```bash
# 1. Find the file the alert names (replace with the alert's named path):
rg -n "_payloads_schema_migrated" /path/to/code

# 2. Read the insert path that uses it:
sed -n '700,750p' /path/to/bq_logging.py

# 3. Confirm what the flag is (module-level bool? env var? config?):
rg -n "^_payloads_schema_migrated\s*=" /path/to/code
```

If the named mechanism does not match code reality (different table name, different flag scope, different gating logic), the alert's diagnosis is wrong even if the numbers are right.

### Step 3a: Alert-staleness check (NEW 2026-07-15 — operator asks "is the wording clearer yet?")

Before reframing the alert's *content*, check whether the alert *body* the user is looking at is still live. Two common patterns:

**Pattern A — pre-merge alert text in user's hand, post-merge code already deployed.** Operator opens an old Slack message and asks "what does this alert even do / is the wording clearer". The current deployed alert script has already been updated; the alert they're holding is a fossil.

Recipe to prove staleness:
```bash
# 1. Identify the alert's timestamp (usually inside the body, e.g. "2026-07-06 16:30:23 UTC").
# 2. Find the deployed script.
launchctl print gui/$(id -u) 2>/dev/null | grep -i "<watcher-name>"       # macOS launchd path
# or: grep -rn "<watcher-name>" ~/.hermes/cron/ ~/.hermes/launchd/

# 3. Read the SHA of origin/main for that script.
gh api "repos/<OWNER>/<REPO>/commits?path=<script>&per_page=5" --jq '.[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'

# 4. Diff the deployed file (often a mirror under ~/.hermes/scripts/) against the post-merge version.
gh api "repos/<OWNER>/<REPO>/contents/<script>?ref=<post_merge_sha>" \
  -H "Accept: application/vnd.github.raw" > /tmp/post_merge.py
wc -l ~/.hermes/scripts/<script> /tmp/post_merge.py
diff -q ~/.hermes/scripts/<script> /tmp/post_merge.py

# 5. Show the operator the latest log entry — that's the text they'll actually see going forward.
tail -50 ~/.hermes/logs/<watcher>.error.log | grep -A2 "<mode-tag>"
```

**Pattern B — wording drift after a partial cherry-pick or backport.** A commit landed on `main` for the watcher but the deployed launchd copy is older. Same recipe; the `diff` will show what's not yet on the deployed machine.

Output shape for a staleness reframing:
1. Alert body timestamp (from the user's message, e.g. `2026-07-06 16:30:23 UTC`).
2. Latest commit SHA on `origin/main` for the watcher script (e.g. `99cb779`).
3. Merge date of the last wording change (e.g. `2026-07-15 20:58:26Z`).
4. Diff: deployed file vs post-merge (line counts + key wording lines).
5. Latest live log entry — the text the operator will actually see on the next cron tick.

Do NOT just say "the wording is clearer now" without showing the new text. Operator asked about wording specifically; show BOTH legacy and post-merge lines side-by-side.

### Step 3a.1: Follow-up wording patch recipe (NEW 2026-07-15 — operator says "make followup" after Step 3a)

After proving staleness and showing what PR #774 (or whichever prior PR) already fixed, the operator often replies *"make followup"* — they want a tighter version of the wording, not just an explanation. The 3-grep fix-up pattern:

**1. Identify the 3 wording gaps that survived the prior PR.** Concretely, check:
   - **File-path gap** — does the alert name the flag but not the file? Add the file path and 1-line context.
   - **Threshold gap** — does the summary line show a counter without labeling whether it's tripped? Use `(TRIPS alert ≥ N)` when at/above threshold, `(alert threshold: N)` otherwise.
   - **Remediation gap** — does the alert name the suspected mechanism but not say what to do? Add explicit remediation: `Remediation: redeploy to force cold-start + migration on all replicas; or run scripts/backfill_bq_is_test_null.py to backfill the historical NULL rows.`

**2. Make a clean branch from `origin/main` via worktree (NEVER from the user's dirty worktree — see `always-pr-never-local-edit` §"Cross-repo pre-flight").**
```bash
git -C <repo> worktree add -b fix/<watcher>-<wording-summary> /tmp/<repo>-<topic> origin/main
# NB: this assumes fresh auth — see Step 0 in the worktree auth pattern below.
```

**3. Make the patches inline.** Apply each wording change as a single targeted edit; keep the diff to <50 lines so the PR is reviewable in one pass.

**4. Add unit tests covering the new wording.** Even for a pure-wording change, add 2–4 tests asserting the new substring is present (e.g. `assert "Remediation:" in msg`). These prevent future wording regressions in CI.

**5. Pitfall — test files import via `Path.home()`.** Some test files (notably `scripts/tests/test_bq_coverage_watcher.py`) do `importlib.util.spec_from_file_location("...", Path.home() / ".hermes" / "scripts" / "<watcher>.py")` rather than importing the worktree copy. Without the work-around, your tests run against `~/.hermes/scripts/<watcher>.py` (the deployed copy), not your patched file, and all "new wording" tests fail.

Work-around recipe (run before `pytest`):
```bash
# Save the deployed copy for restore after testing
cp ~/.hermes/scripts/<watcher>.py ~/.hermes/scripts/<watcher>.py.bak-$(date +%s)
# Copy the patched worktree version into the import-target path
cp /tmp/<repo>-<topic>/scripts/<watcher>.py ~/.hermes/scripts/<watcher>.py
# Now run pytest from anywhere — tests pick up the patched file
python3 -m pytest /tmp/<repo>-<topic>/scripts/tests/test_<watcher>.py -v
# ALWAYS restore before commit, otherwise the local deploy drifts from main
mv ~/.hermes/scripts/<watcher>.py.bak-$(date +%s) ~/.hermes/scripts/<watcher>.py
```

**6. Push + open the PR.** Verify the SHA lands on `origin/<branch>` (the local `git rev-parse` is authoritative — `gh pr view --json headRefOid` lags by ~30s).

**7. In the reply, present BOTH before-and-after text.** Operator asked about wording; show the legacy lines vs the new lines side-by-side. Don't just say "I added remediation hints".

Verified case 2026-07-15, jleechanorg/jleechanclaw#781: alert body from 2026-07-06 16:30 UTC; PR #774 merged 2026-07-15 20:58 UTC; 3 wording gaps remained (file-path, threshold label, remediation hint); 4 new tests added; 11/11 passing. Follow-up PR opened at [jleechanorg/jleechanclaw#781](https://github.com/jleechanorg/jleechanclaw/pull/781).

### Step 3b: Reframe if the alert's framing misleads

Alerts often reframe raw data into a more alarming shape. Verify whether the framing matches reality.

Concrete reframe pattern (BQ coverage alert, 2026-07-13):

- Alert framing: *"`is_test IS NULL` rows have been flowing for 8 consecutive days — migration may be stuck on a replica."*
- Reality check: per-day breakdown showed `is_test` was 0% on 8/9/10 July, started appearing 11 July (53 rows), ramped 12 July (304), 13 July (644). The 8,834 NULL rows are the *cumulative cold-start window of any replica whose lazy migration hasn't flipped*, not 8 days of active drift.
- Reframe: *"The cumulative NULL count is the cold-start window across N replicas, not 8 days of drift. Migration landed on at least one replica on 2026-07-11."*

Heuristic: when an alert says "X consecutive days" or "X hours sustained", break the window into per-period buckets and ask: is this cumulative or live? A cumulative count of a per-row state column will always grow monotonically even after the underlying issue is fixed on a subset of writers.

## Output template for the ack

After verifying, ack in this shape:

1. **Verified:** which alert numbers reproduced exactly.
2. **Reframing:** if the alert's framing misleads, state the corrected picture.
3. **Root cause:** name the actual mechanism (with file:line citations), not the alert's named mechanism if it differs.
4. **Fix recipe:** concrete next steps (file paths, line numbers, test names).
5. **Open question:** what still needs human input (e.g., "open the PR now, or patch the alert threshold first?"). End with ONE concrete blocking question if needed, never a multi-option menu.

Always include `🧠 Memories used:` at the end per the always-on guardrail.

## Tooling prerequisites for Step 1 (NEW 2026-07-19 — `bq` / `gh` failures that block live probing)

Before running Step 1's live probe against BigQuery or GitHub, sanity-check the toolchain. These are silent failures on this Mac that look like "the alert is wrong" or "the API is down" but are actually local environment issues.

### P0: `bq` CLI broken on this Mac — `env -i PYTHONPATH=` workaround

Symptom: `bq query ...` fails with:

```
Traceback (most recent call last):
  File "/opt/homebrew/share/google-cloud-sdk/platform/bq/bq.py", line 42, in <module>
    import credential_loader
  File ".../credential_loader.py", line 26, in <module>
    import wrapped_credentials
  File ".../wrapped_credentials.py", line 24, in <module>
    from utils import bq_error
ImportError: cannot import name 'bq_error' from 'utils' ($HOME/projects_other/hermes-agent/utils.py)
```

Root cause: `$HOME/projects_other/hermes-agent/utils.py` shadows the gcloud SDK's `utils` module on Python's import path (the cwd or `PYTHONPATH` includes `projects_other/hermes-agent/`). The fix is to run `bq` in a clean environment with explicit `PYTHONPATH` pointing only at the gcloud SDK's library dirs:

```bash
env -i \
  PATH=/opt/homebrew/bin:/usr/bin:/bin \
  HOME=$HOME \
  PYTHONPATH=/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/lib/third_party:\
/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/lib:\
/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/platform/bq_libs \
  PYTHONNOUSERSITE=1 \
  bq query --project_id=<PROJECT> --use_legacy_sql=false --format=json \
  <<'SQL'
SELECT ... FROM `<project>.<dataset>.<table>` ...
SQL
```

Path locations may vary per gcloud SDK install — `find /opt/homebrew/Caskroom/google-cloud-sdk -name bq_libs -type d` to locate. Alternative when only one path is shadowed: `unset PYTHONPATH && cd /tmp && bq query ...` (must be a cwd outside `projects_other/hermes-agent/`). DO NOT try to "fix" the shadowing by editing `hermes-agent/utils.py` — that's a sibling repo and a separate fix.

### P1: `gh pr view --json` returns `GraphQL: API rate limit already exceeded` — fall back to REST

Symptom: `gh pr view <N> --repo ... --json state,mergedAt,...` returns empty body + stderr `GraphQL: API rate limit already exceeded for user ID 13840161.` The GraphQL bucket (`graphql.remaining: 0/5000`) is exhausted while the Core REST bucket (`core.remaining: 3000+/5000`) still has budget.

Fix — use the REST endpoint (different bucket):

```bash
gh api repos/<owner>/<repo>/pulls/<N> \
  --jq '{number, state, merged: .merged, merge_commit_sha,
         head_sha: .head.sha, head_ref: .head.ref, additions, deletions, changed_files, title}'
```

PR head SHA (`head_sha`) ≠ squash commit SHA (`merge_commit_sha`) — `gh pr view` reports the head; `git log origin/main` reports the squash. Both are correct; pick the right one for your follow-up command. Verify bucket state with `gh api rate_limit --jq '.resources | {core: .core, graphql: .graphql}'`. The `reset` field is epoch seconds — `date -r <reset>` for the wait time.

### P2: BQ REST via urllib returns 403 from a sandbox — wrong ADC

Symptom: `gcloud auth application-default print-access-token` then `POST https://bigquery.googleapis.com/bigquery/v2/projects/<PROJECT>/queries` returns HTTP 403. The sandbox's ADC lacks `bigquery.jobs.create` on `<PROJECT>`.

Fix — don't try to fix the ADC; route through the user's authenticated `bq` CLI session instead (Pitfall P0's `env -i` wrapper). The `bq` CLI uses the user's own gcloud credentials, not the sandbox's ADC, and it has the IAM by default. The only loss is that you can't run BQ queries from `execute_code`'s Python sandbox — call out to `terminal()` with the `env -i` wrapper instead.

Diagnostic signature that this is the issue, not a real BQ outage: 403 with `"required scope: https://www.googleapis.com/auth/bigquery"` or `"PERMISSION_DENIED: ...does not have bigquery.jobs.create permission"`, AND `gcloud auth list` shows the wrong active identity.

## Anti-patterns

- **Acking without verifying.** *"Saw the alert, looking into it."* is a non-ack. Either verify and reply with evidence, or say so explicitly: *"Not run yet — running the BQ queries now."*
- **Treating alert-named mechanisms as facts.** If the alert names `bq_logging._payloads_schema_migrated` and your codebase has no such name, say so.
- **Framing fixes around the alert's framing.** If the alert says "stuck on a replica, not a transient blip", verify — it might BE a transient blip that the cumulative window exaggerates.
- **Treating an old alert body as live.** When an operator asks *"is the wording clearer now?"* they may be holding a 9-day-old alert text while the deployed script already shipped the fix. Prove staleness via SHA diff before answering; show BOTH legacy and post-merge wording side-by-side.
- **Asking the user to choose between fix variants before applying the safe subset.** Per `no-pick-one-menus`: apply the safe subset, then list what was queued for review.
- **Trusting prior-session reports about remote-system behavior without re-testing.** (NEW 2026-07-17) The same fossilization trap as "treating an old alert body as live", but generalized: any time a previous agent session left a claim about how a remote system behaves ("cloud-build push was rejected by the secret guard", "the MCP server hangs on this endpoint", "this cron silently dies"), that claim is a fossil until re-verified. Verified case 2026-07-17 (Slack C09GRLXF9GR): I inherited a prior session's framing that "git secret guard rejected the push" and reported cloud-build as broken for `$GITHUB_REPOSITORY` without re-running the hand-off. User replied *"whats the secret guard? Lets make it do a hello world program"* — a 5-min hello-world on a clean test repo proved the box actually works and the prior blocker was project-specific (tracked secrets in main history), not box-side. **Rule:** before reporting a remote-system behavior as a blocker in the current session, re-run the relevant probe (hand-off / endpoint hit / cron invocation) on a known-good input. The hello-world validation pattern in `superpowers-cloud-build/references/hello-world-validation-2026-07-17.md` is the canonical template — same structure applies to any "prior session said X is broken" investigation: build isolated test, verify the X-is-broken claim on the test, then re-evaluate.

## Pair-with skills

- `systematic-debugging` — Phase 1 discipline (read errors, build tight loop, gather evidence) applies directly when verifying an alert with code cross-check.
- SOUL.md `proof-before-claim` and `incident-proposal-current-evidence-gate` — same discipline applied at higher stakes.
- `mcp-mail-ack` COMMIT — log every ack to `memory/mcp-mail-ack-log.md` with `(ts, summary, ack-ts)`.
- SOUL.md `slack-cross-workspace-fallback-xoxp` — Path B when the bot token lacks scope for the alert channel.

## References

- `references/mcp-mail-bq-coverage-2026-07-13.md` — worked example from the original incident, including the per-day reframe.
- `references/mcp-mail-bq-coverage-2026-07-15.md` — worked example showing: (a) Step 0 delivery-miss into channel `C0BCVG4F560`, (b) Step 1 reference-target corrections for the recurring `llm_payloads` watcher (project/dataset/column/filter), (c) the cumulative-vs-live reframe at 93.86% populated coverage.
- `references/bq-coverage-alert-staleness-2026-07-15.md` — Step 3a in action: operator asked "is the wording clearer" 9 days after PR #774 merged; recipe for proving staleness via timestamp-in-body + SHA diff + live log entry. Includes the 5-step diagnosis protocol and a `not_in_channel` pitfall.
- `references/in-house-cron-silent-failure-2026-07-15.md` — sister case where the "alert" comes from an in-house scheduled script (Daily Bug Hunt cron, `jleechanorg/jleechanclaw#782`), not a third-party telemetry alert. Same 4-step protocol applies, but the diagnostic recipe differs: read per-agent err files, verify the named subcommand exists on this install, then trace the script's preflight-vs-output-parse failure-counter asymmetry. Captures the "fail-closed sentinel covers the wrong failure mode" pattern that produces false-negative "clean sweep" reports.
- `references/post-merge-deployment-coverage-2026-07-20.md` — worked example for Steps 1b/1c/1d. PR #8418 (`fix/bq-is-test-null-cache-replay`) merged at 2026-07-19T00:54:46Z, but `mvp-site-app-stable` was last deployed 2026-07-18 21:05 UTC (3h 49m BEFORE the merge). Captures the full verification: BQ numbers, gcloud revisions list, 5-column co-NULL signature (100.0%), per-hour cohort decomposition showing 4 post-merge bursts matching pre-merge pattern, and the Slack verdict posted to C0BCVG4F560/1784219487.851579. Cross-cuts Step 1b (deploy-coverage check), Step 1c (schema-gate signature), and Step 1d (per-hour cohort).

## Verification checklist (run before posting ack)

- [ ] **Step 0:** Channel/thread reachable for reply (bot is a member; if not, logged MISSING-delivery + flagged to user)
- [ ] Alert's headline numbers reproduced exactly via live query/command
- [ ] Alert's named mechanism (table/flag/function) found in actual code and read
- [ ] BQ reference targets checked against live `bq show` / `bq ls` (project, dataset, timestamp column, model filter)
- [ ] **Step 3a:** Alert body timestamp identified; if operator is asking about wording clarity, proved staleness via SHA diff and showed BOTH legacy + post-merge text
- [ ] Per-period breakdown checked when alert uses cumulative phrasing
- [ ] Root cause stated with file:line citations
- [ ] Fix recipe is concrete (file paths, line numbers, test names)
- [ ] Open question is ONE concrete blocking question, not a multi-option menu
- [ ] `🧠 Memories used:` line included
- [ ] Ack logged to `memory/mcp-mail-ack-log.md` if MCP Agent Mail
- [ ] **If blocker came from a prior-session transcript:** re-tested the claimed behavior in the current session on a known-good input (hello-world / sandbox invocation) before reporting it as a blocker in the reply. The prior session's framing may be a fossil.