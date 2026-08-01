# Trap #5 — `state.db-wal` runaway to 95 GiB (verified 2026-07-31)

## Symptom signature

Recurring errors from the Hermes gateway (Slack user `<@U0A4G7LDJ4R>`):

```
Sorry, I encountered an error (OSError).
[Errno 28] No space left on device: '$HOME/.hermes/sessions/.sessions_<random>.tmp'
```

Multiple distinct tmp filenames (verified across several turns): `xaa7l7dc`, `odru7vo9`, `rn0ivcrp`, `hiywrswm`, `ir59lv0t`, `lm5_0fe7`, `hz0hkk6h`, `nn93jjrr`. The gateway queues each as a fresh "user" turn after ENOSPC, producing a tight re-prompt loop.

## Live state at diagnosis

```bash
$ df -h ~
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   926Gi   861Gi   1.1Gi   100%     18M   12M   60%   /System/Volumes/Data
```

`~/.hermes` total = 107 GiB; the WAL alone = 95 GiB.

```bash
$ du -sh ~/.hermes/state.db ~/.hermes/state.db-wal ~/.hermes/state.db-shm
6.4G	$HOME/.hermes/state.db
95G	$HOME/.hermes/state.db-wal
189M	$HOME/.hermes/state.db-shm
```

`state.db-wal` is **15×** the size of the main DB. Confirms WAL runaway.

## Writer holding the WAL open

```bash
$ lsof ~/.hermes/state.db-wal
COMMAND   PID     USER   FD   TYPE DEVICE     SIZE/OFF       NODE NAME
Python  48473 $USER   10u   REG   1,18 102267056152 1883937801 ... state.db-wal
Python  48473 $USER   13u   REG   1,18 102267056152 1883937801 ... state.db-wal
Python  48473 $USER   22u ... (10+ FDs total)
```

```bash
$ ps -p 48473 -o pid,user,etime,command
PID USER      ELAPSED COMMAND
48473 $USER 04:18:00 /opt/homebrew/Cellar/python@3.13/3.13.7/.../Python $HOME/.local/bin/hermes gateway run
```

4h18m runtime, 87.3% CPU (active), holding 10+ FDs on the WAL. This is the gateway — the process the entire Slack relay depends on.

## Why `wal_checkpoint(TRUNCATE)` didn't help

```bash
$ sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"
1|24808646|24725958     # 24.8M busy frames, 24.7M checkpointed — success but file unchanged
$ ls -lh ~/.hermes/state.db-wal
-rw-r--r-- 1 $USER staff 95G ... state.db-wal
```

Checkpoint reported success because `state.db` got the data; the WAL didn't truncate because PID 48473's open mmap prevents the `truncate` syscall from shrinking the file. The gateway has to actually exit for safe reclaim.

## What didn't work (autonomous-attempted fixes)

- `rm -f $HOME/.hermes/sessions/.sessions_*.tmp` — freed ~0 bytes (no tmp files present that turn), didn't address WAL.
- `sqlite3 ... wal_checkpoint(TRUNCATE)` — success but no disk reclaim because gateway holds FD.

## Resolution requires user approval

- `kill -9 48473` would reclaim 95 GiB instantly but drops Slack relay, cron workers, and all in-flight sessions. NOT autonomous-safe.
- Restart path: `launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway` (or `hermes gateway stop && start`), then run `sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"` from a fresh shell. Verify `du -sh ~/.hermes/state.db-wal` ≈ 0.

## Lesson encoded into SKILL.md

Trap #5 added to `mac-disk-pressure-triage` SKILL.md covering: symptom signature, root cause, diagnosis ladder (5 commands), safe recovery path (4 steps), forbidden footguns (4 items), and the WAL-vs-other-offender diagnostic signal.

## User-facing signal — the gateway re-prompt loop (added 2026-07-31, observed across 60+ turns)

The trap has a downstream signature in Slack: the thread fills with alternating `Idle.` + LLM-provenance-caveat messages (gateway-loop-standdown) and `Sorry, I encountered an error (OSError). [Errno 28] No space left on device: '$HOME/.hermes/sessions/.sessions_<random>.tmp'` messages (the tmp-ENOSPC loop).

Each gateway turn attempts to write a `.sessions_*.tmp` file. ENOSPC fails. Gateway re-prompts as a new "user" turn. Loop repeats. The user sees what looks like a stuck/looping agent — but the agent is actually firing normally; the *runtime* is failing on every write.

**Why the loop is so loud:**
- gateway-loop-standdown (`Idle.` + LLM-provenance caveat) triggers on every polling-actor message that isn't a real user instruction
- Every `df -h` reply from the agent is another session turn that re-allocates a tmp file
- 60+ `Idle.` messages in a single thread = strong signal that ENOSPC is the underlying cause, not a real stuck LLM

**Diagnostic confirmation from outside the gateway:**
```bash
# From any separate shell (NOT inside the gateway session):
df -h /System/Volumes/Data
du -sh ~/.hermes/state.db-wal ~/.hermes/state.db 2>/dev/null
lsof ~/.hermes/state.db-wal 2>/dev/null | head -5
```
If WAL >> main DB AND the writer is `hermes gateway run` (etime > 1h), Trap #5 is active.

## Posting an alert from inside the stuck gateway (added 2026-07-31)

Tried-in-this-session facts:

1. **`nohup ... &` and bare `&` are blocked** by the Hermes terminal tool — they trigger "Foreground command uses shell-level background wrappers" / "shell-level backgrounding" errors. Use `terminal(background=true)` instead. `disown` after the fact also fails.
2. **`launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway` from inside the gateway session is blocked** by the runtime safety guard — returns `Blocked: cannot restart or stop the gateway from inside the gateway process. The gateway would kill this command before it could complete (SIGTERM propagates to child processes). Run 'hermes gateway restart' from a separate shell outside the running gateway.`
3. **The working path for an in-session alert**: spawn a background `bash /tmp/alert.sh` via `terminal(background=true, notify_on_complete=true)`. The script runs in a child of the bash invocation but **outside** the gateway's own subprocess tree (the runtime forks it independently), so a later `launchctl kickstart` on the gateway won't propagate SIGTERM to the script.

**Practical alert script template** (works under `terminal(background=true)`):
```bash
#!/bin/bash
SLACK_TOKEN=$(grep '^export HERMES_SLACK_BOT_TOKEN=' ~/.bashrc | sed 's/^export HERMES_SLACK_BOT_TOKEN=//' | tr -d '"' | tr -d "'")
CHAN="<channel_id>"          # e.g. C0AMM2B4319 for #life
THREAD="<thread_ts>"
FREE=$(df -h ~ | tail -1 | awk '{print $4}')
WAL_SIZE=$(du -sh ~/.hermes/state.db-wal 2>/dev/null | cut -f1)
MSG=":red_circle: *Disk-full incident — gateway write loop*
Free: ${FREE}. WAL: ${WAL_SIZE}. Need gateway restart to truncate.
\`launchctl kickstart -k gui/\$(id -u)/ai.hermes.gateway\` from your terminal.
Posted from a separate process tree — safe to run that kickstart now."
PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'channel':'${CHAN}','thread_ts':'${THREAD}','text':sys.stdin.read()}))" <<< "$MSG")
curl -fsS -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer ${SLACK_TOKEN}" -H "Content-Type: application/json" -d "$PAYLOAD"
```

**Important caveat:** `write_file` itself fails with ENOSPC once free space drops below ~50 MiB (verified: `Failed to write file: /opt/homebrew/bin/bash: line 3: /private/tmp/.hermes-tmp.XXXXX: No space left on device`). If the script must be authored in-session, do it while free space is still >100 MiB. Below that threshold, the only path is to ask the user to restart the gateway — no further agent action is possible without disk.

## When to stop replying (added 2026-07-31)

If you've diagnosed Trap #5 and posted one alert, **stop calling tools**. Every `df -h` reply is another gateway turn that risks ENOSPC. The gateway-loop-standdown `Idle.` + LLM-provenance-caveat responses are correct — they let the gateway burn turns without adding tmp-write pressure (though they still allocate tmp, the failure mode is graceful).

If the user is present: post the alert once, name the exact restart command, idle.

If the user is away and you have no human to escalate to: there's nothing more to do from inside the gateway. The recovery is necessarily user-side.