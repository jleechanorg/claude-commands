# BQ coverage watcher — alert-staleness reframing (2026-07-15)

## Context

Operator posted in Slack thread `C0BCVG4F560/1783355492.226289` then out-of-band:

> *"I merged this but what does this alert even do? It needs to be more clear in the wording on that's wrong — github.com/jleechanorg/jleechanclaw/pull/774"*

…referring to a freshly-merged jleechanclaw PR. The alert body the operator saw read:

> :warning: `is_test IS NULL` on 898 Gemini rows over 7d (≥ 100). Likely lazy schema-migration failure on a Cloud Run replica — see `bq_logging._payloads_schema_migrated` flag. · `is_test` populated = 62.35% (< 95.0%) on 2385 Gemini rows over 7d · `is_test IS NULL` rows have been flowing for 5 consecutive day(s) — migration may be stuck on a replica (not a transient blip).

## The recipe (proven pattern)

When an operator asks *"is the wording clearer now / what does this alert do"* after a fix has merged, the answer is **almost never "fix the wording"** — it's "**the alert body you saw was generated before the fix landed**". Prove this in 5 steps:

### 1. Pull the alert body's own timestamp

The watcher embeds its run-time in the message (e.g. `2026-07-06 16:30:23 UTC`). This is the kill-shot: any wording change merged later than this timestamp did NOT produce the text the user is holding.

### 2. Find the watcher + identify its launchd binding

```bash
launchctl print gui/$(id -u) 2>/dev/null | grep -i "bq-coverage\|coverage_watcher"
# → ai.hermes.schedule.bq-coverage-watcher

launchctl print gui/$(id -u)/ai.hermes.schedule.bq-coverage-watcher 2>&1 | head -40
# → arguments: /bin/bash ... bq_coverage_watcher.py
# → environment: BQ_WATCH_* env vars
```

### 3. Get the post-merge SHA + date

```bash
gh api "repos/jleechanorg/jleechanclaw/commits?path=scripts/bq_coverage_watcher.py&per_page=5" \
  --jq '.[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
# → 99cb779 fix(bq-watcher): alert on recent rate, not cumulative 7d backlog (#774)
# → 65ef7c5 [P1] fix(scripts/bq_coverage_watcher): BQ USING join type-mismatch HTTP 400 (#703)

gh pr view 774 --repo jleechanorg/jleechanclaw --json mergedAt,additions,deletions,changedFiles
# → "mergedAt": "2026-07-15T20:58:26Z"
# → 158 additions, 40 deletions, 2 files changed
```

### 4. Diff deployed copy vs post-merge

```bash
# Fetch the post-merge raw via the GitHub raw-content API.
gh api "repos/jleechanorg/jleechanclaw/contents/scripts/bq_coverage_watcher.py?ref=99cb779" \
  -H "Accept: application/vnd.github.raw" > /tmp/post_merge.py

wc -l ~/.hermes/scripts/bq_coverage_watcher.py /tmp/post_merge.py
# → 511  ~/.hermes/scripts/bq_coverage_watcher.py    ← deployed (already updated!)
# → 511  /tmp/post_merge.py                          ← origin/main @99cb779
```

If `diff -q` reports they differ AND the deployed file already matches post-merge, the operator is looking at historical log lines — not the active alert text.

### 5. Show the most-recent live log entry

```bash
tail -50 ~/.hermes/logs/bq-coverage-watcher.error.log
```

The most recent entry is the text the operator will actually see on the next cron tick. In this case it already contained the post-#774 disambiguation:

> • Backlog `is_test IS NULL` (Gemini, 7d): 7190 rows (3931 have request_json) — informational; alert fires on active rate only. Backfill via `scripts/backfill_bq_is_test_null.py`.
> • `is_test` populated (Gemini, 7d): 31.08% (3242/10432)

That single phrase — *"informational; alert fires on active rate only"* — IS the wording fix the operator asked about. It already shipped; the operator just hadn't seen a fresh alert yet because the watcher's last run happened to be clean.

## Output template (what to actually post)

Lead with the timestamp proof:

> *Status: that alert is from BEFORE PR #774 merged. That message was posted at 2026-07-06 16:30 UTC by the legacy cumulative-7d code path. You merged the fix 9 days later (2026-07-15 20:58 UTC, SHA 99cb779). The wording you saw is stale.*

Then a four-block breakdown:

1. **What the alert does** — concrete steps the watcher takes (query, threshold, post conditions).
2. **What was unclear about the OLD wording** — bullet list.
3. **What PR #774 already fixed** — quote the post-#774 lines from the latest log entry, not from a guess.
4. **What I still think is unclear and worth a follow-up patch** — narrow, optional follow-ups.

End with a single blocking question, never a multi-option menu (per `no-pick-one-menus`):

> *Want me to open a small follow-up PR tightening those three lines, or is PR #774 wording already clear enough and we leave it?*

## Pitfalls confirmed in this session

- **`mcp__slack__conversations_replies` returns `not_in_channel` when the bot isn't a member of the source channel.** Even when the alert was posted by an old watcher run that DID have membership, the bot can lose it post-deploy. Don't burn a turn posting the analysis if you can't ack the source thread — log MISSING delivery + flag to operator.
- **`launchctl print` text output mixes tabs and spaces; don't pipe through tables.** Use simple `head -40` extraction.
- **`gh api .../commits` requires the user account to have repo access;** if it's a private repo (e.g. `jleechanorg/*`) the macOS keychain `gh` token is the active one — confirm with `gh auth status` first.
- **Don't say "the wording is clearer now" without quoting it.** Operators who asked about wording want to SEE the new text. Pull it from the live log or the post-merge file, never paraphrase.

## Cross-references

- Skill `verify-telemetry-alert` Step 3a — alert-staleness protocol (added this session).
- Skill `verify-telemetry-alert` Step 0 — delivery check before logging MISSING.
- PR [jleechanorg/jleechanclaw#774](https://github.com/jleechanorg/jleechanclaw/pull/774) — the watcher fix that introduced `recent-rate` mode.
- PR [$GITHUB_REPOSITORY#8351](https://github.com/$GITHUB_REPOSITORY/pull/8351) — the root-cause `is_test IS NULL` lazy-migration fix that made the watcher fix necessary.
- AGENTS.md `verify-telemetry-alert` skill loading — this is one of the most commonly-loaded skills when the operator pings about a Slack alert.
