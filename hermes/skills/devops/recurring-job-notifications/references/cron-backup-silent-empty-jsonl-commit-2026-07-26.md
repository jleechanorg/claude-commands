# Silent Empty-JSONL Commit — `scripts/cron-backup-sync.sh` Bug Class

> **Bug-ref:** 2026-07-24 08:25 PT, thread `C0AJQ5M0A0Y/1784906714.446409` parent message ("Cron Backup: changed (not committed). Total: 0 jobs."). Companion to Pitfall 18 in `recurring-job-notifications/SKILL.md`.

## Symptom

A scheduled script that exports structured state to a JSONL/Markdown file, diffs against a `.bak`, and `git add && git commit`s on change posts a misleading Slack message like:

```
Cron Backup: changed (not committed). Total: 0 jobs.
```

The "not committed" phrasing implies something to fix — but the bad commit already shipped to `origin/main`. The Slack post is a red herring; the actual damage is in git history.

## Root cause: three failure modes line up

Verified on `scripts/cron-backup-sync.sh` 2026-07-24 08:25 PT run, the failure was the interaction of:

1. **Parser crash masked by `2>/dev/null`.** The python heredoc that parses `hermes cron list --all` had a `+ sched_str +` shell-evaluation error (literal text in `~/.hermes/logs/scheduled-jobs/cron-backup-sync.err.log`: `+ sched_str + : command not found`). The `2>/dev/null` mask on the python substitution hides the stderr; the script treats the parser as having "returned empty" instead of "errored".

2. **Silent fallback to empty shell.** The post-parse guard writes `CRON_JOBS='{"jobs": [], "total": 0}'` instead of aborting. This is correct behavior for a *clean empty parse*, but indistinguishable from a *crash that returned empty*. Net result: `BACKUP_JSON` and `BACKUP_MD` are written as valid-looking empty state.

3. **Empty state still commits.** The commit branch runs `git add "$BACKUP_JSON" "$BACKUP_MD" && git commit` regardless of whether `CRON_JOBS` is empty or non-empty, because `CHANGED=1` is set by `diff -q` whenever the empty shell differs from the prior `.bak`. Net result: `chore: refresh cron backup` commits `{"jobs":[], "total":0}`, which then diffs against the prior 26-job `.bak` and *deletes 367 lines* of JSONL in the committed file.

4. **`COMMIT_SHA: unbound variable` from `set -euo pipefail` + conditional init.** The script only initializes `COMMIT_SHA=""` *inside* the `if [[ $CHANGED -eq 1 ]]; then ... fi` block. When the diff branch fires but `git commit` is skipped (no changes to commit), `COMMIT_SHA` stays unset; with `set -u` the post-block Slack branches that reference `if [[ -n "$COMMIT_SHA" ]]` then trigger `unbound variable`. The script then `exit 1`s without posting any Slack message — but the empty-state commit has already landed on `origin/main`.

## Why the misleading Slack post is the worst part

The Slack post `Cron Backup: changed (not committed). Total: 0 jobs.` reads as an action item: "the backup failed, here's what to investigate." But the bug already shipped to `git log` via `ef5f285f87` (`+4/-367`, deleted 26 jobs' worth of structured data). The user-visible signal is a false-positive about a problem that is *already past*, not pending. The corrective action is to revert `ef5f285f87` and `git reset --hard HEAD~1` on the backup state — not to debug the parser.

## The four-step guard recipe (durable fix)

In priority order:

1. **Refuse to write empty state.** After the parse-or-fallback step, check:
   ```bash
   TOTAL=$(python3 -c "import json,sys; print(len(json.load(sys.stdin).get('jobs',[])))" < "$BACKUP_JSON")
   if [[ "$TOTAL" -eq 0 ]] && [[ -s "$BACKUP_JSON.bak" ]]; then
       PRIOR=$(python3 -c "import json,sys; print(len(json.load(sys.stdin).get('jobs',[])))" < "$BACKUP_JSON.bak")
       if [[ "$PRIOR" -gt 0 ]]; then
           log "FAIL: empty backup after non-empty prior ($PRIOR jobs) — refusing to overwrite"
           # ERR-trap alert path; do NOT post a routine "no jobs" message
           exit 1
       fi
   fi
   ```
   An empty backup after a non-empty one is NEVER a valid state. Exit 1 + ERR-trap alert (per Pitfall 5 — always `set -e` + `trap ERR`, never silent).

2. **Always init `COMMIT_SHA=""` at the top of the script**, before any branch that may skip init. With `set -u`, every variable referenced in a later branch must be guaranteed-set in the same flow or at script top. The fix is one line near the top:
   ```bash
   COMMIT_SHA=""
   TOTAL=0
   ENABLED=0
   ```

3. **Refuse to commit when the parsed job count is zero OR went from N to 0.** Either:
   - **(a) Compare parsed counts, not byte-diff of the JSONL.** Wrap the `git add && git commit` in a guard that requires `TOTAL >= 1`:
     ```bash
     if [[ "$TOTAL" -ge 1 ]] && [[ -n "$DIFF_LINES" ]]; then
         git add "$BACKUP_JSON" "$BACKUP_MD"
         git commit -m "chore: refresh cron backup" || true
         COMMIT_SHA=$(git rev-parse --short HEAD)
     fi
     ```
   - **(b) Wrap in `[[ $TOTAL -ge 1 ]] || ...`** to short-circuit before any `git` call when empty.

4. **Make the post-block branch read COMMIT_SHA from a single source-of-truth.** Use one `if/elif/else` chain with `COMMIT_SHA` resolved once at the top, not a tree of nested conditionals that can leave it unset:
   ```bash
   if [[ -n "$DIFF_LINES" ]]; then
       if [[ -n "$COMMIT_SHA" ]]; then
           do_slack "Cron Backup: committed $COMMIT_SHA. Total: $TOTAL jobs ($ENABLED enabled). ..."
       else
           do_slack "Cron Backup: detected change but skipped commit (empty or no diff). Total: $TOTAL jobs."
       fi
   elif [[ "$CHANGED" -eq 1 ]]; then
       do_slack "Cron Backup: no semantic change ..."
   else
       do_slack "Cron Backup: no changes. Total: $TOTAL jobs ($ENABLED enabled)."
   fi
   ```
   Always guarantee `COMMIT_SHA` is set (step 2) before this block.

## What `1c06096bdc` fixed (and what it didn't)

The 2026-07-24 10:37 PT commit `1c06096bdc` "fix(cron-backup-sync): descriptive Slack message with semantic diff" addressed the **message format** (multi-line descriptive + bullets for added/removed/state-change jobs). It did NOT add any of the four guards above. The parser path was rewritten to use `hermes cron list --all` table-output regex parsing (per the `--json` rejection by argparse), but the new parser still has the same `2>/dev/null` masking + empty-fallback pattern.

A followup PR is gated on the user reply in `C0AJQ5M0A0Y/1784906714.446409`:
- **(a)** Open a PR that (i) refuses to commit when JSONL parses empty or unchanged, and (ii) tags `<@U09GH5BR3QU>` `<@U0AEZC7RX1Q>` on `do_slack` failure paths.
- **(b)** Just `br create` the bug and pick it up later.

## Test shape (for when the PR lands)

```bash
# tests/test_cron_backup_sync_guards.sh — 4 contract checks

# 1. Empty parse must NOT commit
TMP=$(mktemp -d); echo '{"jobs":[],"total":0}' > "$TMP/CRON_JOBS_BACKUP.json"
echo '{"jobs":[{"id":"a","name":"x","state":"active"}],"total":1}' > "$TMP/CRON_JOBS_BACKUP.json.bak"
bash scripts/cron-backup-sync.sh 2>&1 | grep -q "refusing to overwrite" || { echo FAIL_empty; exit 1; }
test -z "$(git -C "$TMP" log --oneline)" || { echo FAIL_committed_empty; exit 1; }

# 2. Non-empty parse must commit
echo '{"jobs":[{"id":"a","name":"x","state":"active"}],"total":1}' > "$TMP/CRON_JOBS_BACKUP.json"
echo '{"jobs":[],"total":0}' > "$TMP/CRON_JOBS_BACKUP.json.bak"
bash scripts/cron-backup-sync.sh 2>&1 | grep -q "Committed:" || { echo FAIL_no_commit; exit 1; }

# 3. COMMIT_SHA must be set even on no-op branch
# (run with identical CRON_JOBS twice; second run should not crash with unbound variable)
bash scripts/cron-backup-sync.sh 2>&1 | grep -qv "unbound variable" || { echo FAIL_unbound; exit 1; }

# 4. do_slack failure must tag user (per Pitfall 18 — slack_alert contract)
# (force SLACK_USER_TOKEN=invalid, verify message body still contains <@U09GH5BR3QU>)
SLACK_USER_TOKEN=[REDACTED_SLACK_TOKEN] bash scripts/cron-backup-sync.sh 2>&1
grep -q '<@U09GH5BR3QU>' "$HOME/.hermes/logs/cron-backup/slack-$(date +%Y%m%d).log" \
  || { echo FAIL_no_mention_on_failure; exit 1; }
```

## Related pitfalls

- **Pitfall 5** — `set -e` + `trap ERR` discipline. The `cron-backup-sync.sh` script has both, but the `COMMIT_SHA: unbound variable` error happens *after* the commit branch, so the ERR trap fires too late to roll back the bad commit. The fix is prevention (steps 1-3 above), not detection.
- **Pitfall 11** — routine status posts are noise. The script's "Cron Backup: changed (not committed). Total: 0 jobs." is the worst-case interaction of Pitfall 11 (routine post) + Pitfall 18 (silent empty-state commit): it generates a daily noise post AND the post is a false-positive about an already-shipped bug.
- **Pitfall 18** — the silent parser failure + `set -euo pipefail` + `git commit` of garbage data footgun, documented in the parent skill.