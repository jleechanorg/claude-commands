---
name: dropped-messages/stale-mkdir-lock-bypass-2026-06-19
description: The mkdir-based lock collision pattern in dropped-thread-followup.sh — when the prior run died mid-flight (kill -9, host reboot, hung curl), the lock dir persists and silently no-ops the cron. Recipe: TMPDIR bypass to unblock the audit.
type: reference
---

# Stale `mkdir`-lock from a dead cron run blocks fresh audits (2026-06-19)

> **Cross-reference:** The audit script `~/.hermes/scripts/dropped-thread-followup.sh` line 159 uses `mkdir "$LOCK_DIR"` for mutual exclusion (where `LOCK_DIR="${TMPDIR:-/tmp}/hermes-dropped-thread.lock"`). When the prior run dies uncleanly, the directory persists. Verified 2026-06-19 on `C0AJ3SD5C79/1781868563.343059` "Redrive dropped threads".

## The trap

A *directory* lock (vs a file lock) has a specific failure mode: if the prior process was `kill -9`'d, or the host rebooted mid-run, or the script crashed inside a Python heredoc, the lock directory persists. The next invocation does `mkdir`, gets `EEXIST`, logs `SKIP: another instance running`, exits 0. The cron silently no-ops for hours/days with no alerts, no DRY_RUN output, no recovery prompt — just a flat line in `~/.hermes_prod/logs/dropped-thread-followup.log`.

**Symptom chain to recognize:**
- You run `bash ~/.hermes/scripts/dropped-thread-followup.sh`.
- Output is exactly: `[ts] SKIP: another instance running`, exit 0.
- `ps aux | grep dropped | grep -v grep` returns nothing — no live process.
- `ls -la "${TMPDIR:-/tmp}/hermes-dropped-thread.lock"` shows a directory (not a regular file).
- The actual cron job is healthy (no `last exit code 1` from launchd), it's just the lock that's stuck.

## The recipe (TMPDIR bypass — no privileged cleanup needed)

```bash
TMPDIR=/tmp/hermes_drop_audit mkdir -p /tmp/hermes_drop_audit
TMPDIR=/tmp/hermes_drop_audit DRY_RUN=1 DROP_LOOKBACK_HOURS=24 \
  DROP_CHANNELS="C0AH3RY3DK6 C09GRLXF9GR C0ALSKLU9KM C0AJ3SD5C79" \
  DROP_EXCLUDE_CHANNELS="" DROP_THREAD_REPLY_LIMIT=200 \
  bash ~/.hermes/scripts/dropped-thread-followup.sh
```

Why this works:
- `LOCK_DIR="${TMPDIR:-/tmp}/hermes-dropped-thread.lock"` evaluates to `/tmp/hermes_drop_audit/hermes-dropped-thread.lock` with the override.
- A fresh directory the script can `mkdir` cleanly without collision.
- The audit runs against the *real* state file (`~/.hermes_prod/logs/dropped-thread-state.json`) because the state-file path is hardcoded, not TMPDIR-relative.
- No mutation of the actual cron path.

## When you DO want to clean the stale lock for the launchd-driven job

If the cron itself is also stuck (not just your ad-hoc audit):

```bash
# Inspect the lock dir first — should be empty (script's cleanup is rmdir, not rm -rf)
ls -la "${TMPDIR:-/tmp}/hermes-dropped-thread.lock"
# Remove it (rmdir works because the dir IS the lock; rm -rf is overkill)
rmdir "${TMPDIR:-/tmp}/hermes-dropped-thread.lock" 2>/dev/null
# Or use the audit's TMPDIR override path if that's where the stale dir is:
rmdir "/tmp/hermes_drop_audit/hermes-dropped-thread.lock" 2>/dev/null
```

After cleanup, the next launchd tick (within `StartInterval` seconds) will `mkdir` cleanly and the cron resumes.

## Why `rm -rf` is the wrong move

The directory IS the lock — the script's cleanup path is `rmdir "$LOCK_DIR"` (line 163), which only succeeds when the directory is empty. `rm -rf` is unnecessary (the dir is empty by design) and would mask any orphan state (e.g., a debug file the script left behind). `rmdir` is the canonical cleanup.

## Diagnose why the prior run died (optional, only if it keeps happening)

```bash
# Last few log lines from the script
tail -20 ~/.hermes_prod/logs/dropped-thread-followup.log
# Last few error lines (curl timeouts, python tracebacks)
grep -E "ERROR|Traceback|timed out|exit code" ~/.hermes_prod/logs/dropped-thread-followup.log | tail -10
# launchd's view of the last run
launchctl print gui/$UID/ai.hermes.schedule.dropped-thread-followup | grep -A2 "last exit code"
```

Common causes: `chat.postMessage` curl timeout (>30s no response), a hung Python heredoc inside `resolve_channels`, or `mcp_agent_mail` reservation-file collision.

## Verified 2026-06-19

Audit invocation on `C0AJ3SD5C79/1781868563.343059`:
- First run: `[2026-06-19T04:29:52] SKIP: another instance running`, exit 0, no actionable output.
- `ps aux | grep dropped`: empty.
- `ls -la /tmp/hermes-dropped-thread.lock`: stale dir present.
- TMPDIR bypass: produced 30 actionable threads (28 unanswered + 2 standalone-noise=`test`) in 4 channels within 24h lookback, exit 0.
- Without the bypass, the cron would have continued to silently no-op indefinitely.

## Generalization

Any cron / scheduled script that uses `mkdir` as a mutex (vs `flock` on a file) is vulnerable to this exact pattern. The recovery is universal:

```bash
TMPDIR=/tmp/<unique_audit_name> mkdir -p /tmp/<unique_audit_name>
TMPDIR=/tmp/<unique_audit_name> <script> [args...]
```

If the script has hardcoded paths, you may also need to inspect the lock path with `grep -n "LOCK_DIR\|TMPDIR" <script>` to confirm the override is wired.

## How to recognize this trap in a new session

Symptom: any audit / cron-driven script returns "another instance running" or "lock already held" but `ps` shows nothing. Check:
1. `grep -nE "mkdir.*lock|flock|LOCK" <script>` to find the lock mechanism.
2. `ls -la <lock_path>` to see if it's a directory (mkdir-based) or file (flock-based).
3. If directory and empty: `rmdir` it (or use TMPDIR bypass).
4. If file: `rm` it (or check for stale PID with `lsof <file>`).