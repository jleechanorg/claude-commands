# Stale babysit cron investigation recipe

Use when an unknown babysit cron is flooding a real user Slack thread with repeated failures (rate-limit errors, "could not fetch PR state", etc.) and you need to identify + neutralize it quickly. Verified recipe from 2026-07-31 incident (cron `124ad03896f5`, PR #8466, ~40 noise messages/day for 7+ days).

## 5-step investigation

```bash
# 1. Identify the cron job from the thread noise (each babysit post names the job_id)
#    Look for lines like: "Cronjob Response: wa-pr-8466-babysit\njob_id: 124ad03896f5"
JOB_ID="<from-thread>"   # e.g. 124ad03896f5

# 2. Confirm the watched PR is actually terminal (no babysit needed at all)
gh pr view <N> --repo $GITHUB_REPOSITORY --json state,mergedAt
#   Expectation: state=MERGED or state=CLOSED. If OPEN/active, this is NOT a stale babysit — investigate separately.

# 3. Locate the cron registration (gateway-managed crons live in cron/jobs.json; hermes crons via `cronjob action=list`)
grep -F "$JOB_ID" ~/.hermes/cron/jobs.json 2>/dev/null | head -5
# OR for hermes-managed crons:
cd ~/.hermes && python3 -c "from hermes_tools import cronjob_list; [print(j) for j in cronjob_list() if '$JOB_ID' in j.get('id','')]" 2>&1 | head

# 4. Neutralize — pick the right cancel verb:
#    - For cron/jobs.json entries:
jq "del(.jobs[] | select(.id == \"$JOB_ID\"))" ~/.hermes/cron/jobs.json > /tmp/jobs.json.tmp && mv /tmp/jobs.json.tmp ~/.hermes/cron/jobs.json
#    - For hermes crons:
cd ~/.hermes && python3 -c "from hermes_tools import cronjob_remove; cronjob_remove('$JOB_ID')"

# 5. Verify the job is gone and the launchd babysit-stale-watchdog is actually armed (so this can't recur silently)
grep -F "$JOB_ID" ~/.hermes/cron/jobs.json 2>/dev/null && echo "STILL PRESENT — cancel failed" || echo "removed"
launchctl list 2>/dev/null | grep babysit-stale-watchdog || echo "WARNING: watchdog NOT loaded — install per skill SKILL.md 'Install' section"
tail -5 ~/.hermes/cron/output/babysit-stale-watchdog.log 2>/dev/null
```

## Why each step exists

- **Step 2 first** (not step 1) — the loudest signal ("cron is spamming") is not the most informative. Confirming the watched PR is terminal proves the cron *should* be gone. If the PR is still open, the cron is not stale — different bug class.
- **Step 3** — `cron/jobs.json` is gateway-managed and gitignored; `cronjob action=list` is the hermes CLI. Different surfaces store the same job. Both must be searched.
- **Step 4** — `hermes cron remove` only works for hermes-managed crons. Gateway crons are removed by editing `cron/jobs.json` directly (gateway re-reads on next tick).
- **Step 5** — the watchdog is silent-by-design; absence of a recent heartbeat in `~/.hermes/cron/output/babysit-stale-watchdog.log` means it's not running. Without the watchdog, the next stale babysit will repeat this exact 7-day spam pattern.

## Recovery from "watchdog not loaded"

```bash
# Re-install per babysit-stale-watchdog/SKILL.md 'Install' section:
cp ~/.hermes/launchd/ai.hermes.schedule.babysit-stale-watchdog.plist.template \
   ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist
plutil -lint ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist
launchctl load -w ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist
launchctl kickstart -k gui/$(id -u)/ai.hermes.schedule.babysit-stale-watchdog
launchctl list | grep babysit-stale-watchdog   # MUST return a row
```

## Common false positives — DO NOT cancel these

- A babysit that posts "could not fetch PR state" because `gh` is **currently** rate-limited — the babysit's own `is_pr_terminal()` check correctly falls through on gh failures (see SKILL.md pitfall). Cancel only after `gh pr view` succeeds and confirms MERGED/CLOSED.
- A babysit whose `gh pr view` fails for non-rate-limit reasons (auth, network) — fix the env, don't kill the babysit.
- A one-shot `--repeat 1` cron that fired its single scheduled run and is sitting waiting for deletion — not stale, just done.

## Bug-ref

- 2026-07-31: cron `124ad03896f5` (wa-pr-8466-babysit) — ~40 rate-limit-error posts/day for 7 days into Slack thread C09GRLXF9GR/p1784235989.925899 after [PR #8466](https://github.com/$GITHUB_REPOSITORY/pull/8466) merged on 2026-07-24. Root cause: `babysit-stale-watchdog` plist was never installed on this machine, so the silent-stale-job check never ran. The skill itself was correct; the deployment was missing.