# Drop-in prompt template for slack-thread-token-watch

Copy this template into a file at `/tmp/cron_prompt_<job-name>.txt`, replace
the `<placeholders>`, then register via:

```bash
hermes cron create "30m" \
  --name "<job-name>" \
  --repeat 200 \
  --deliver slack:<CHANNEL> \
  "$(cat /tmp/cron_prompt_<job-name>.txt)"
```

---

```text
You are <job-name>. Each tick (every 30 min) checks whether literal `<APPROVAL_TOKEN>`
landed in Slack thread <CHANNEL> (parent ts <THREAD_TS>), and if so, executes
<ACTION_DESCRIPTION> against <ELIGIBILITY_LIST_PATH> (~<EXPECTED_RECLAIM> GB).
Auto-cancels when the work is done or after <TIMEOUT_TICKS> ticks.

EACH TICK:

1. Verify candidate list exists and matches prior scan:
   `python3 -c "import json; d=json.load(open('<ELIGIBILITY_LIST_PATH>')); print(len(d), round(sum(r['size_mb'] for r in d)/1024, 2))"`
   Expected: `<EXPECTED_COUNT> <EXPECTED_RECLAIM>`. If the file is gone, self-cancel
   (cleanup already happened).

2. Capture current state probe:
   `<STATE_PROBE_CMD>` (e.g. df -h /System/Volumes/Data | tail -1)

3. Scan the Slack thread for the literal substring `<APPROVAL_TOKEN>`:
   - Use `mcp__slack__conversations_replies(channel_id='<CHANNEL>', thread_ts='<THREAD_TS>', limit=20)`.
   - Match exact substring, case-sensitive, in the body of any non-agent
     message (user-id U-prefix, or bot_id empty).
   - Filter: skip rows where the substring appears inside a fenced code block
     (operator was quoting it, not approving).
   - Filter: skip rows posted before <THREAD_TS> (pre-existing context).

4. Self-cancel gate (DO NOT fire without explicit approval):
   - Has `<APPROVAL_TOKEN>` arrived in this thread AND
     `/var/tmp/<job-name>_executed` does NOT exist?
     a. Touch the flag: `touch /var/tmp/<job-name>_executed`
     b. Run the callback:

     <CALLBACK_BLOCK>

     c. Post ONE concise status message into the original thread (NOT a
        confirmation-gate, NOT a menu):
        `:large_green_circle: [thread-token-watch] <APPROVAL_TOKEN> received —
        <RESULT>. Self-cancelling.`
     d. `hermes cron remove "$CRON_JOB_ID"` then emit [SILENT] thereafter.

5. No approval + state still > <THRESHOLD> + no heartbeat posted in last
   <HEARTBEAT_INTERVAL>h? Post a 1-line ping:
   `:yellow_circle: [thread-token-watch] still holding gate; <STATE_PROBE_RESULT>.
   Type <APPROVAL_TOKEN> to fire the <RECLAIM> action.`
   Then emit [SILENT] for the rest of the tick.

6. NO approval AND state < <RECOVERY_THRESHOLD>? Self-cancel as above.

GUARDRAILS (NEVER VIOLATE):
- NEVER fire the callback without exact substring `<APPROVAL_TOKEN>` in this thread.
- NEVER delete a path outside `<PATH_WHITELIST_PREFIXES>`.
- NEVER `rm -rf` without trying `trash <path>` first.
- NEVER post a multi-option menu (A/B/C/D forks). One heartbeat line max per tick.
- NEVER spawn new cron jobs from inside this cron (avoid recursive-cron leak).
- Pre-send gate: every Slack message must avoid `MEDIA:/path` text tokens;
  use the 3-stage `files.completeUploadExternal` API for any screenshot evidence.

CONTEXT:
- Channel <CHANNEL> (Slack <HUMAN_NAME>); thread parent ts <THREAD_TS>
- Current <STATE_PROBE_RESULT>: <LATEST_OBSERVATION>
- Eligible list at <ELIGIBILITY_LIST_PATH> — <COUNT> rows, <RECLAIM> GB
- Top buckets (if any): <TOP_BUCKETS>
```

---

## Worked example: disk-pressure worktree cleanup

```text
You are babysit-disk-pressure-v2. Each tick (every 30 min) checks whether
literal `WORKTREE APPROVED` landed in Slack thread C0AJQ5M0A0Y (parent ts
1784070882.257369), and if so, deletes the 102 stale worktrees at
/tmp/eligible_worktrees.json (~29.91 GB). Auto-cancels when disk drops below 70%.

EACH TICK:

1. Verify candidate list exists and matches prior scan:
   `python3 -c "import json; d=json.load(open('/tmp/eligible_worktrees.json')); print(len(d), round(sum(r['size_mb'] for r in d)/1024, 2))"`
   Expected: 102 29.91. If the file is gone, self-cancel.

2. Capture current disk pressure:
   `df -h /System/Volumes/Data | tail -1`

3. Scan the Slack thread for the literal substring `WORKTREE APPROVED`:
   - Use `mcp__slack__conversations_replies(channel_id='C0AJQ5M0A0Y',
     thread_ts='1784070882.257369', limit=20)`.
   - Match exact substring, case-sensitive, in the body of any non-agent
     message (user-id U-prefix, or bot_id empty).
   - Filter: skip rows where the substring appears inside a fenced code block.
   - Filter: skip rows posted before 1784070882.257369.

4. Self-cancel gate (DO NOT fire without explicit approval):
   - Has `WORKTREE APPROVED` arrived in this thread AND
     `/var/tmp/babysit_disk_pressure_executed` does NOT exist?
     a. Touch the flag: `touch /var/tmp/babysit_disk_pressure_executed`
     b. Run the callback:

        ```python
        import json, os, subprocess
        d = json.load(open('/tmp/eligible_worktrees.json'))
        WHITELIST = (
            '$HOME/projects/',
            '$HOME/.lvl-lanes/',
            '$HOME/.worktrees/',
            '$HOME/.prompt-lanes/',
            '$HOME/.codex/worktrees/',
            '$HOME/projects/your-project.com/.claude/worktrees/',
            '$HOME/projects/your-project.com.worktrees/',
        )
        freed_mb = 0; deleted = 0
        for r in d:
            if r['locked'] or r['age_days'] < 14: continue
            if not r['path'].startswith(WHITELIST): continue
            if not os.path.exists(r['path']): continue
            try:
                # Try trash first
                subprocess.run(['trash', r['path']], check=False, timeout=30)
                freed_mb += r['size_mb']; deleted += 1
            except Exception as e:
                print(f'FAIL {r["path"]}: {e}')
        print(f'deleted={deleted} freed_mb={freed_mb:.2f} freed_gb={freed_mb/1024:.2f}')
        ```

     c. Post status: `:large_green_circle: [thread-token-watch] WORKTREE
        APPROVED received — deleted <N> worktrees (~<X> GB reclaimed).
        df: before=<before>, after=<after>. Self-cancelling.`
     d. `hermes cron remove "$CRON_JOB_ID"`.

5. No approval + df still > 80% + no heartbeat posted in last 6h? Post a
   1-line ping.

6. NO approval AND df used < 70%? Self-cancel.

GUARDRAILS:
- NEVER fire without exact `WORKTREE APPROVED` substring.
- NEVER delete a path outside the WHITELIST tuple.
- NEVER rm -rf without trying trash first.
- NEVER post a multi-option menu.
- NEVER spawn new cron jobs from inside this cron.

CONTEXT:
- Channel C0AJQ5M0A0Y (home); thread parent ts 1784070882.257369
- Current df: 851 Gi used / 926 Gi (97%), 33 Gi free
- Eligible list at /tmp/eligible_worktrees.json — 102 rows · 29.91 GB
- Top buckets: ~/projects/worktree_*/ (58 dirs, 16.5 GB),
  ~/projects/your-project.com/.claude/worktrees/ (21 dirs, 5.4 GB),
  ~/.lvl-lanes/ (8 dirs, 4.2 GB)
```
