# Multi-user batch rollout (2026-07-20)

Notes from extending the `ai.$USER.wiki-campaign-daily-ingest` launchd
job from "$USER only" to "all real users, skip test fixtures."

## What changed

- `download_campaign.py` gained `--mode all-users` that walks `auth.list_users()`
  paginated, filters via `is_test_email()`, and runs the existing per-user
  pipeline. $USER included by default; `--exclude-$USER` skips him.
- `download_one()` now stamps `user_email` + `user_uid` into the YAML
  frontmatter so multi-user pages are auditable in the private llm-wiki repo.
- `wiki-campaign-daily-ingest.sh` switched from `--mode batch` to `--mode
  all-users`. The commit-message + header comment were updated to reflect
  multi-user scope.

## Test-email filter (mirrors wa-prod-data-query)

```python
_TEST_EMAIL_TOKENS = ("test", "anon", "dev-runner", "example.com", "jleechantest")
```

Same tokens as `wa-prod-data-query/scripts/query_real_users.py:is_test_email()`.
Substring (not exact) match, case-insensitive. If the WA team adds a new test
fixture pattern (e.g. `qa-bot`), update BOTH files in the same PR — otherwise
the daily ingest will pull test campaigns into the wiki.

## Initial run (2026-07-20)

- 135 real users discovered in 0.4s (auth.list_users paginated)
- 12 new campaigns downloaded + written to `~/llm_wiki/wiki/sources/`
  - 11 were $USER (campaigns newer than last daily run)
  - 1 was `williamdmzphang@gmail.com` ("Wyltopia", 82 scenes) — first
    non-$USER campaign ever in the private wiki
- 232 skipped (existing wiki pages with content > 500 bytes)
- 0 errors

## Bug caught during verification

The shell's "files modified during this run" detector used
`find -newermt "@<epoch>"`, which is GNU find syntax. macOS BSD find does
NOT support the `@<epoch>` prefix and silently returned 0 matches — so the
script reported `added=0` and skipped the git push, leaving 12 newly-written
wiki pages uncommitted in the working tree.

**Fix:** store both the epoch and a human-readable date string, use the latter
for `find -newermt`. Verified: re-ran with a deleted-then-re-ingested campaign
(`wyltopia-y1y9JSfs.md`), script correctly detected `added=2` and pushed to
origin/main (`e95912a0` on jleechanorg/llm-wiki).

See SKILL.md Pitfall #9 for the cross-platform `find -newermt` recipe.

## Commits (jleechanclaw)

- [`f542b4ae72`](https://github.com/jleechanorg/jleechanclaw/commit/f542b4ae72)
  feat(wiki-ingest): extend daily cron to all real users
- [`68d1f8c6e8`](https://github.com/jleechanorg/jleechanclaw/commit/68d1f8c6e8)
  fix(wiki-campaign-daily-ingest): correct mtime-based change detector

## Daily launchd job

- Plist: `~/.hermes/launchd/ai.$USER.wiki-campaign-daily-ingest.plist`
- Installed: `~/Library/LaunchAgents/ai.$USER.wiki-campaign-daily-ingest.plist`
- Schedule: daily 09:00 local time (StartCalendarInterval)
- Log: `~/Library/Logs/wiki-campaign-daily-ingest.log`
- Manifest: `/tmp/campaign_ingest_manifest.jsonl`
- Target repo: `https://github.com/jleechanorg/llm-wiki.git` (private)
