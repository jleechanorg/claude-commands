# cron-backup no-routine-slack — 2026-07-22

## The user's pushback, verbatim

`C0AJQ5M0A0Y / p1784734483.171289`:

> Cron Backup: changed (not committed). Total: 26 jobs.
>
> What is this? we dont need a slack alert for it i think

Phrasing: "i think" = consent to remove, not a request for clarification.
This pivot reversed the entire default in `recurring-job-notifications` —
the skill previously taught "post on success / no-op / error / slack-still-
alive", which is correct for jobs the user explicitly asked for and wrong
for jobs that just happen to be scheduled.

## The job that produced the noise

`~/.hermes/scripts/cron-backup-sync.sh` (launchd plist
`ai.hermes.schedule.cron-backup-sync.plist`, Mon-Fri 08:25 PT). Behavior
on origin/main at the time of the request:

- Export Hermes cron jobs via `hermes cron list --all` (the legacy `--json`
  flag was already removed; the parser emitted `Cron Backup: ...` strings).
- Compare against the previous exported JSON; if anything changed, write
  `docs/context/CRON_JOBS_BACKUP.json`, commit it on the live
  `~/.hermes/` repo, attempt a push.
- Slack-post via a local `do_slack()` shell helper that called
  `chat.postMessage` against `${SLACK_REVIEW_CHANNEL_ID:-C0AJQ5M0A0Y}`
  (#ai-general), with one of three templates: "committed. Total: N jobs
  (X enabled).", "changed (not committed). Total: N jobs.", or
  "no changes. Total: N jobs (X enabled).".

Every weekday the user got a Slack message about a routine posture job.
That is the bug.

## Fix shipped (PR [#790](https://github.com/jleechanorg/jleechanclaw/pull/790))

Branch: `fix/cron-backup-no-routine-slack` off `origin/main`. Two files
changed, 19 insertions(+), 21 deletions(-).

`scripts/cron-backup-sync.sh`:

```diff
-do_slack() {
-  local msg="$1"
-  [[ -f "$HOME/.profile" ]] && source "$HOME/.profile" 2>/dev/null || true
-  [[ -z "${SLACK_USER_TOKEN:-}" ]] && { log "SLACK_USER_TOKEN not set"; return 0; }
-  local cid="${SLACK_REVIEW_CHANNEL_ID:-C0AJQ5M0A0Y}"
-  local payload
-  payload=$(python3 -c "import json,sys; print(json.dumps({'channel': '$cid', 'text': sys.stdin.read().strip()}))" <<< "$msg")
-  curl -s -X POST "https://slack.com/api/chat.postMessage" \
-    -H "Authorization: Bearer $SLACK_USER_TOKEN" \
-    -H "Content-Type: application/json" -d "$payload" \
-    >> "$ROOT/logs/cron-backup/slack-$(date +%Y%m%d).log" 2>&1 || true
-}
-
-if [[ "$CHANGED" -eq 1 ]] && [[ -n "$COMMIT_SHA" ]]; then
-  do_slack "Cron Backup: committed. Total: $TOTAL jobs ($ENABLED enabled)."
-elif [[ "$CHANGED" -eq 1 ]]; then
-  do_slack "Cron Backup: changed (not committed). Total: $TOTAL jobs."
-else
-  do_slack "Cron Backup: no changes. Total: $TOTAL jobs ($ENABLED enabled)."
-fi
-
+# Routine backup state is intentionally local-only. The generated backup files,
+# git history, and this log line provide auditability without noisy Slack posts.
 log "Done. Total=$TOTAL Enabled=$ENABLED Changed=$CHANGED"
 exit 0
```

`tests/test_cron_backup_sync.py` (new, regression test):

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cron-backup-sync.sh"


def test_cron_backup_has_no_slack_transport_or_routine_status_posts():
    """Cron backup is silent on success/change; local logs remain its report."""
    text = SCRIPT.read_text()

    assert "chat.postMessage" not in text
    assert "do_slack" not in text
    assert "Cron Backup: committed" not in text
    assert "Cron Backup: changed (not committed)" not in text
    assert "Cron Backup: no changes" not in text
    assert 'log "Done. Total=$TOTAL Enabled=$ENABLED Changed=$CHANGED"' in text
```

Test run: `1 passed in 0.11s`. The shell parses cleanly under `bash -n`.
A `rg 'chat.postMessage|do_slack|Cron Backup:' scripts/cron-backup-sync.sh`
returns no matches — making the regression guard future-proof against
silent reintroduction of the transport.

## Why this fix, not "make Slack quiet"

The script already had `>> "$ROOT/logs/cron-backup/slack-$(date +%Y%m%d).log"` on the
`curl` line. The Slack token, the channel ID, the `do_slack` shell function —
none of those are load-bearing for backup correctness. They exist only to be
removed. The fix isn't a config tweak; it's a deletion.

If we had instead wrapped Slack posts in a `--quiet` flag, we'd have preserved
every future regression pathway: a developer adding a new status branch, a
launchd reload picking up an old environment variable, a token rotation
driving a fresh "no changes. Total: ? jobs (? enabled)." post (the
actual 2026-07-15 → 2026-07-21 failure mode that this script had been silently
running for a week before the `--json` regression was caught — see
`hermes-deploy-pipeline` skill §pitfall).

## Why this fix, not "remove the whole cron"

The cron is doing real work:
- Exporting cron jobs into a durable artifact (`docs/context/CRON_JOBS_BACKUP.json`).
- Generating a human-readable Markdown summary (`docs/context/CRON_JOBS_BACKUP.md`).
- Committing changes to `~/.hermes/` so the repo's git history shows *which
  launchd jobs were active when*. That is the real audit log; removing the
  Slack post does not weaken it.
- Maintaining the `BACKUP_JSON.bak` snapshot used to compute the next-run
  diff.

Removing the job would erase that audit trail. Keeping the job with the
Slack transport deleted preserves the audit + silences the noise.

## Verification trail captured during the session

```bash
$ bash -n scripts/cron-backup-sync.sh
$ python3 -m pytest tests/test_cron_backup_sync.py -q
1 passed in 0.11s
$ git push -u origin fix/cron-backup-no-routine-slack
remote: Create a pull request for 'fix/cron-backup-no-routine-slack' on GitHub
To https://github.com/jleechanorg/jleechanclaw.git
 * [new branch]            fix/cron-backup-no-routine-slack -> fix/cron-backup-no-routine-slack
$ git rev-parse origin/fix/cron-backup-no-routine-slack
e623f4e735121945ad37adfdeae1873df5b71070
$ gh api --method POST repos/jleechanorg/jleechanclaw/pulls --input - <<<"$JSON"
"html_url": "https://github.com/jleechanorg/jleechanclaw/pull/790",
"changed_files": 2, "additions": 19, "deletions": 21,
"head": "fix/cron-backup-no-routine-slack@e623f4e735121945ad37adfdeae1873df5b71070",
"base": "main"
```

## The dispatch-side prologue (useful for AO spawn workers)

Earlier in the same session I attempted `ao spawn --project jleechanclaw
--harness agy --branch fix/cron-backup-no-routine-slack --name cron-backup-
no-slack --prompt "<task brief>"`. Pre-flight heartbeat was clean:

```text
$ agy --model gemini-3.5-flash-medium --print-timeout 1m --prompt 'pong'
pong
```

…but the spawn itself failed with
`Internal server error (INTERNAL_ERROR) [request jeffreys-macbook-pro.
local/zdpKPMprYT-000861]`. `ao doctor` afterwards reported healthy
daemon/auth; no project-config regression. This is the documented
"internal-error-from-healthy-daemon" failure mode from
`skills/agento/SKILL.md` §Pitfall — the right move is the inline fallback
that this reference document describes, not retrying the spawn. The work
took 90 seconds end-to-end in the fresh worktree rather than burning a
600s tool-timeout budget on a doomed dispatch.

## Reuse plan

1. When the user pushes back on Slack noise from a scheduled job with
   "we dont need a slack alert", "stop posting this", "this is spammy",
   "kill the bot message", "make this silent" — load this skill, find
   the script, delete the `do_slack`-style transport entirely, and add a
   regression test that asserts the transport cannot return.
2. When authoring a NEW scheduled job, do NOT wire routine success / no-op
   Slack posts by default. Build the job, run it locally, ship a "no Slack
   transport" first PR, and only add a Slack path if/when the user asks.
3. The ERR-trap failure alert remains the only Slack path on this script.
   That is durable: it pages on real breakage, stays silent otherwise.
