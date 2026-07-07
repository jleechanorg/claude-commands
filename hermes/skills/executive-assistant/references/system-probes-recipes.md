# System probes — verified recipes

Captures the exact probe commands, expected outputs, and common misreads for the executive-assistant system-status section. Updated 2026-07-06 sweep.

## Load average + uptime

```bash
uptime
```

Output: `16:00  up 3 days, 46 mins, 46 users, load averages: 12.98 11.71 16.76`
- 1-min / 5-min / 15-min averages
- Baseline on this machine: ~4
- Yellow: 8–15 (sustained)
- Red: >30 (spike, investigate)
- Green: <6

## Disk — the TWO probes that matter

```bash
df -h / | head -3
df -h /System/Volumes/Data | head -3
```

**Read both rows. Report the data-volume row, not the read-only system-snap row.**

| What | Mount | Typical | What it means |
|---|---|---|---|
| `/dev/disk3s1s1` (root `/`) | APFS sealed system snapshot | ~17 Gi used / ~78 Gi free / ~18% used | Read-only system volume. **Do not report this to the operator — it always looks fine.** |
| `/dev/disk3s5` (`/System/Volumes/Data`) | APFS data volume | ~789 Gi used / ~78 Gi free / ~91% used | Actual user-data usage. Report this. |

P44 in SKILL.md captures the verified misread pattern (the 2026-07-06 08:01 brief reported "Disk 9.9 Gi free of 926 Gi, 64 % used" which was the system-snap row read against the wrong column header).

## Process count

```bash
ps aux | grep -E '(hermes|agy|claude|cmux)' | grep -v grep | wc -l
```

Typical:
- 10 = quiet
- 30–80 = moderate AO/agent activity
- 100+ = heavy parallel work in flight

Trend (2026-07-06): 10 (08:01) → 87 (12:00) → 114 (16:01) — sustained climb during agento PR-cycle work.

## Hermes gateway — the plist is `ai.hermes.prod`, not `ai.hermes.gateway`

```bash
launchctl print gui/$(id -u)/ai.hermes.prod 2>&1 | head -30
```

Expected output header:
```
gui/501/ai.hermes.prod = {
    active count = 1
    path = $HOME/Library/LaunchAgents/ai.hermes.prod.plist
    type = LaunchAgent
    state = running
    program = /bin/bash
    arguments = {
        /bin/bash
        $HOME/.hermes/scripts/launchd-env-wrapper.sh
        /opt/homebrew/bin/hermes
        gateway
        run
    }
    ...
}
```

Also confirm PID is alive via `cat ~/.hermes/gateway.pid` (was `{"pid": 2167}` on 2026-07-06) and `ps -p 2167`.

**Common mistake:** `launchctl print gui/$(id -u)/ai.hermes.gateway` → returns `Bad request. Could not find service "ai.hermes.gateway"` because that label does not exist on this machine. Always use `ai.hermes.prod`.

## Critical launchd jobs — status matrix

```bash
launchctl list 2>&1 | grep -E 'hermes|ai\.hermes'
```

Output rows have format: `<pid> <status> <label>`. PID `-` means loaded but not currently running a tick. Status codes 0/1/2 are normal exit codes; 78 means the job is throttled (not an error).

Critical jobs to verify are present (regardless of running/not):
- `ai.hermes.prod` — gateway (state=running required)
- `ai.hermes.ao-notifier` — AO PR notifier
- `ai.hermes.schedule.dropped-thread-followup` — Slack thread pickup
- `ai.hermes.schedule.dropped-thread-watcher` — paired watchdog
- `ai.hermes.schedule.babysit-stale-watchdog` — catches stuck babysit crons
- `ai.hermes.schedule.auto-push-llm-wiki` — llm_wiki sync
- `ai.hermes.schedule.finish-the-job-autoarm` — auto-arm finish-the-job on stuck goals

## Disk-write health warning (transcript context loss)

`~/.hermes/logs/gateway.error.log` may show:
```
WARNING Persisted transcript lagged live cached history for session agent:main:slack:group:<channel>:<thread>
 disk=N, memory=N3 preserving live conversation context possible FTS write corruption
```

Means the FTS write path detected disk-vs-memory drift and skipped a write to avoid corruption. Symptom: a fresh session won't have prior thread context. Frequency: ≥5 in a 1h window = real problem, worth a brief note. Verified pattern in jleechanclaw 2026-07-04 codexbar investigation.

## Quick probe-all-in-one

```bash
{
  echo '=== uptime ==='; uptime
  echo '=== df /  ==='; df -h / | head -3
  echo '=== df /System/Volumes/Data ==='; df -h /System/Volumes/Data | head -3
  echo '=== process count ==='; ps aux | grep -E '(hermes|agy|claude|cmux)' | grep -v grep | wc -l
  echo '=== gateway plist ==='; launchctl print gui/$(id -u)/ai.hermes.prod 2>&1 | head -5
  echo '=== gateway.pid alive ==='; cat ~/.hermes/gateway.pid 2>/dev/null; echo
  echo '=== critical jobs ==='; launchctl list 2>&1 | grep -E 'ai\.hermes\.(ao-notifier|prod)|ai\.hermes\.schedule\.(dropped-thread|babysit-stale|finish-the-job|auto-push-llm-wiki)'
}
```