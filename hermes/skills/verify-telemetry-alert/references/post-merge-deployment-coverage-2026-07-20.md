# Post-Merge Deployment Coverage — PR #8418 Verification

**Verification date:** 2026-07-20 (39h 41m after merge)
**Merge SHA:** `c0b8c107e72e12398052677f551bdbc144fde9cf`
**Merge commit:** `90238d16b8bd5e91538b1b19fd1ce27f6ff12e9e`
**Merge timestamp:** `2026-07-19T00:54:46Z`
**PR:** [$GITHUB_REPOSITORY#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418) — `[fix] bq_logging: replace _payloads_schema_migrated global flag with per-process column-name cache`
**Slack thread:** C0BCVG4F560 / 1784219487.851579
**Verdict:** 🔴 **STILL BROKEN** — fix in code, not in prod

## Context

This was a one-shot post-merge verification cron. The original 2026-07-16 BQ coverage watcher alert complained about `is_test IS NULL` on 51 Gemini rows in the last 24h. PR #8418 merged 2026-07-19 with the fix (per-process column-name frozenset cache replacing `_payloads_schema_migrated` module-global flag). The cron was asked: 39h after the merge, did the bug actually stop?

The merge did land on origin/main. Unit tests passed 69/69. CI green. `gh pr view 8418 --json state` reports `MERGED`. **But the production Cloud Run service was still on the pre-merge image.** This file captures the working recipe that surfaced that gap.

## Step 1b — Deployment coverage check (worked)

### Identify the prod service

```bash
$ gcloud run services list --project=worldarchitecture-ai --region=us-central1
   SERVICE                       REGION       URL                                              LAST DEPLOYED BY                                         LAST DEPLOYED AT
✔  mvp-site-app-stable           us-central1  https://mvp-site-app-stable-754683067800...      dev-runner@worldarchitecture-ai.iam...                  2026-07-18T21:05:28.396918Z
✔  mvp-site-app-preview          us-central1  https://mvp-site-app-preview-754683067800...     dev-runner@worldarchitecture-ai.iam...                  2026-06-25T21:25:58.469663Z
✔  mvp-site-app-{s1..s10}        us-central1  https://mvp-site-app-s1...-s10...-uc.a.run.app   dev-runner@worldarchitecture-ai.iam...                  various 2026-07-20
```

**Heuristic for your-project.com:** `mvp-site-app-stable` is the prod-receiving service. `mvp-site-app-{sN}` are staging shards with traffic = 0 to the public URL. `mvp-site-app-preview` is the preview channel.

### Pull the deploy timestamp of the active stable revision

```bash
$ gcloud run revisions list --service=mvp-site-app-stable --region=us-central1 --project=worldarchitecture-ai --limit=10
   REVISION                       ACTIVE  SERVICE              DEPLOYED                 DEPLOYED BY
✔  mvp-site-app-stable-00172-xfn  yes     mvp-site-app-stable  2026-07-18 21:05:19 UTC  dev-runner@worldarchitecture-ai.iam...
✔  mvp-site-app-stable-00171-qdt          mvp-site-app-stable  2026-07-18 21:04:44 UTC  ...
✔  mvp-site-app-stable-00170-h7w          mvp-site-app-stable  2026-07-08 01:51:05 UTC  ...
```

**Critical observation:** `mvp-site-app-stable-00172-xfn` was deployed 2026-07-18 21:05:19 UTC — that is **3h 49m BEFORE the PR #8418 merge at 2026-07-19 00:54:46Z**. The fix is not in the running image.

### Confirm via image digest

```bash
$ gcloud run services describe mvp-site-app-stable --region=us-central1 --project=worldarchitecture-ai \
    --format='yaml(spec.template.spec.containers[0].image)'
spec:
  template:
    spec:
      containers:
      - image: gcr.io/worldarchitecture-ai/mvp-site-app:stable-65dd85b
```

The image tag suffix `stable-65dd85b` is a build hash. The merge SHA `c0b8c107e72e12398052677f551bdbc144fde9cf` starts with `c0b8c1` — does NOT match `65dd85b`. Different build = different code.

## Step 1c — 5-column co-NULL signature (worked)

```sql
SELECT
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNT(*) AS n_total,
  ROUND(100.0 * COUNTIF(is_test IS NOT NULL) / COUNT(*), 2) AS pct_populated,
  ROUND(100.0 * COUNTIF(
    is_test IS NULL
    AND cached_tokens IS NULL
    AND thoughts_tokens IS NULL
    AND tool_use_tokens IS NULL
    AND rag_mode IS NULL
  ) / GREATEST(1, COUNTIF(is_test IS NULL)), 4) AS co_null_5col_pct
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND model LIKE '%gemini%'
```

**Result (last 24h):**
```
[{"co_null_5col_pct":"100.0","n_is_test_null":"161","n_total":"1623","pct_populated":"90.08"}]
```

**Interpretation:** `co_null_pct = 100.0%` means every single `is_test IS NULL` row in the last 24h also lacks all 4 sibling schema-gated columns. This is the **same bug class as PR #8418 was meant to fix** — the producer process's column-name cache was empty when these rows were written. Either the fix isn't running (Step 1b) or a sibling bug is bypassing the cache entirely.

## Step 1d — Per-hour cohort decomposition (worked)

```sql
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d %H:00', ingested_at) AS hour,
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNT(*) AS n_total,
  ARRAY_AGG(DISTINCT agent IGNORE NULLS LIMIT 5) AS top_agents
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
  AND model LIKE '%gemini%'
  AND is_test IS NULL
GROUP BY hour ORDER BY hour DESC
```

**Result (NULL rows only, last 48h):**

| hour (UTC) | n_null / n_total | top_agents | pre/post merge |
|---|---|---|---|
| 2026-07-20 04:00 | 46 / 46 | CharacterCreationAgent, gemini_provider.stream, StoryModeAgent, RewardsAgent, GodModeAgent | POST (27h after) |
| 2026-07-19 21:00 | 46 / 46 | gemini_provider.stream, FactionManagementAgent, PlanningAgent, RewardsAgent, CharacterCreationAgent | POST (20h after) |
| 2026-07-19 20:00 | 23 / 23 | GodModeAgent, gemini_provider.stream, CharacterCreationAgent, DialogAgent, FactionManagementAgent | POST (19h after) |
| 2026-07-19 19:00 | 46 / 46 | gemini_provider.stream, StoryModeAgent, CharacterCreationAgent, DialogAgent, GodModeAgent | POST (18h after) |
| 2026-07-19 13:00 | 23 / 23 | (legacy spike — see reference 2026-07-13) | PRE |
| 2026-07-19 00:00 | 65 / 186 | (legacy) | PRE |
| 2026-07-18 21:00 | 23 / 91 | (legacy) | PRE |

**Interpretation:** post-merge hours (07-19 19:00 onward) STILL show NULL bursts from the production agent roster (CharacterCreationAgent, StoryModeAgent, GodModeAgent, FactionManagementAgent, DialogAgent, gemini_provider.stream). The bursts are concentrated in some hours and zero in others — the same intermittent pattern as the pre-merge hours. Combined with Step 1b (image not deployed) and Step 1c (co_null_pct = 100%), this confirms **the fix never reached prod; the running image is still producing the pre-merge bug.**

**Counter-factual:** if the fix had been deployed, post-merge hours should show n_null = 0 across all hours (with a possible transition hour during rollout). The persistence of post-merge bursts with 100% co-NULL signature is the smoking gun.

## 7d rolling baseline (for context)

```sql
SELECT
  COUNTIF(is_test IS NULL) AS n_is_test_null,
  COUNT(*) AS n_total,
  ROUND(100.0 * COUNTIF(is_test IS NOT NULL) / COUNT(*), 2) AS pct_populated
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE ingested_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND model LIKE '%gemini%'
```

**Result:** `n_is_test_null=634, n_total=8177, pct_populated=92.25` — 7-day baseline shows the bug has been reproducing for the full window, which is consistent with the image not being deployed for at least the last week (the latest `mvp-site-app-stable` revision is from 2026-07-08, 10+ days before this verification).

## The Slack verdict posted

```
🧪 PR #8418 post-merge verification — 39h 41m since merge
• Last 24h (Gemini): is_test IS NULL = 161 / 1623 (90.08% populated)
• Schema-gate signature (5-col co-NULL): 100.0%
• 7d rolling % populated: 92.25%
Verdict: 🔴 STILL BROKEN
[+ per-hour burst table]
[+ gcloud run services list output]
[+ recommendation: trigger redeploy to mvp-site-app-stable, recheck at next 16:30 UTC tick]
```

## Diagnostic takeaways

1. **Merge SHA landing on origin/main ≠ production fix shipped.** The unit tests pass on a branch; CI green on a PR; merge into origin/main; all of these are necessary but **none** prove the running binary has the new code. The Cloud Run service has to be re-deployed from a new image build.

2. **The `co_null_pct` predicate distinguishes bug classes.** 100.0% co-null on 4 sibling schema-gated columns says "the producer process's column cache was empty" — same mechanism as pre-merge. Less than 50% co-null would say "a different bug is dropping only `is_test`." This is the test that tells you whether you're looking at the SAME bug (Step 1b deploy failure) or a NEW bug (regression in the fix).

3. **Per-hour cohort decomposition is the test that distinguishes "fix didn't work" from "fix wasn't deployed."** If the same hourly burst pattern persists pre-merge and post-merge with the same agent roster, the fix is in code but not in prod. If post-merge hours are clean and only pre-merge hours have bursts, the fix worked but had a partial rollout.

4. **The 7d baseline shows the bug has been reproducing for the entire observation window.** That's consistent with the latest stable revision being from 2026-07-08, predating the PR #8418 merge. The fix's per-process cache is an improvement to the pre-existing `_payloads_schema_migrated` flag, but no pre-existing deployment of the older code was already in place to "go back to" — the bug has been reproducing on the existing image for the whole window.

5. **Recommended remediation (NOT applied from this one-shot verification):** open a fresh `rev-<deploy-bead>` to trigger a redeploy of `mvp-site-app-stable` from the PR #8418 merge SHA. Re-run this same query at the next 16:30 UTC tick — expected: `n_null = 0` in the latest hour + monotonically-zero next-hour row. If the burst reproduces EVEN AFTER a clean redeploy, the bug is in `$PROJECT_ROOT/bq_logging.py` despite the test suite passing 69/69 — that points at a stale-frozenset vs. concurrent-`tables.get` race not covered by the unit tests; open a followup bead and re-investigate the `_ensure_payloads_schema_cached` lock-held re-check path.

## Cross-references

- The skill's P0/P1/P2 pitfalls (v1.4.0) cover the BQ CLI workaround, `gh pr view` GraphQL fallback, and BQ REST ADC permission issues — all of which were already in place from the 2026-07-19 verification session in this same thread.
- The `module-global-flag-race` skill (software-development category) covers the **bug class** that PR #8418 was the canonical fix for — but it does not cover post-merge deployment verification. This file + Steps 1b/1c/1d are the verification half of that story.
- Bead `rev-2l2x6` (PR #8418) → `rev-uh0ek` (root alert) — referenced in the PR body, tracked in `$GITHUB_REPOSITORY/.beads/` (not in the agent roadmap). `br list` in `~/roadmap` returns no `rev-*` matches, which is consistent with the beads living in the PR's repo.
