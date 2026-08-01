---
name: mac-disk-pressure-triage
description: Diagnose and safely reclaim disk space on macOS when a disk-usage alert fires (system or 3rd-party like `disk_usage_alert.sh`). Use when the user shares a disk-alert message, says "disk full", "low disk space", "running out of space", "free up disk", "reclaim space", "what's eating my disk", or when `df -h /` shows <15% free. Covers the **sealed System Volume trap** (`df /` shows ~17G used on the sealed system snapshot — the real user-data volume is `/System/Volumes/Data` at `/dev/disk3s5`), the standard investigation ladder (df → du per dir → `.claude/worktrees/agent-*` accumulation → git-worktree-registered cleanup), and the safe-cleanup decision tree (what to delete vs what to keep). Trigger on any disk-pressure phrase.
triggers:
  - disk full
  - low disk space
  - running out of disk
  - reclaim disk
  - free up space
  - what is eating my disk
  - disk usage alert
  - disk-alert
  - threshold exceeded
  - capacity 95
  - capacity 90
---

# macOS Disk Pressure Triage

## Trap #1 — `df /` lies on Apple Silicon (sealed system volume)

On modern macOS (11+), `df -h /` returns numbers for the **sealed read-only system snapshot** (`/dev/disk3s1s1` / `/dev/disk3s1`), which holds only ~17G of system files. **The real user-data volume is `/dev/disk3s5` mounted at `/System/Volumes/Data`.** A "disk full" alert that fires because `df /` looks fine is real — the sealed volume is full of pre-allocated APFS snapshots and the user's files live on the Data volume.

**Always start with:**
```bash
df -h /System/Volumes/Data
```
That number is the truth. If `df -h /` says 27% used but `/System/Volumes/Data` says 96% used, trust the Data volume. The alert script at `~/Library/Application Support/user-scope/bin/disk_usage_alert.sh` defaults to checking `/`, which can understate real pressure — read both.

## Trap #3 — APFS purgable space makes successive `df` readings drift (2026-07-14 instance)

**Symptom:** successive `df -h /System/Volumes/Data` readings taken minutes apart can show wildly different free-space values (observed 21 Gi free at 17:18 PT → 53 Gi free at 17:23 PT on the same disk with no user-driven cleanup in between). The disk-alert script fires on one snapshot, the agent reads 21G free, the user sees 53G free in real life, and the triage report overstates pressure.

**Root cause:** APFS maintains **"purgeable space"** — blocks held by older Time Machine snapshots, APFS snapshots, and `tmutil` artifacts that are allocated but reclaimable on demand. The kernel returns a conservative free-space estimate on the first read after a high-water-mark event (a big write, a snapshot rotation, an Xcode build) and re-reconciles the actual reclaimable blocks lazily as `photolibraryd`, `bird`, and `deleted` reaped in the background. Five minutes later the same `df` can show tens of gigabytes more free.

**Mitigation — read 3-4 successive `df`s before reporting the baseline:**
```bash
for i in 1 2 3 4; do
  df -h /System/Volumes/Data | tail -1 | awk -v i=$i '{print "Read " i ": " $4 " free (" $5 " used)"}'
done
```
If the four reads converge, that number is the real baseline; report it. If they drift, wait 60s and re-read — APFS reconciliation is usually settled within a minute. **Do NOT report the very first `df` reading as the post-cleanup baseline** right after the alert fired — wait for convergence or specifically tag the reading as "mid-reconciliation" so the user knows it's an upper bound.

**Also worth running to confirm purgable reality:**
```bash
diskutil apfs list 2>&1 | grep -A2 "Volume .* Data"
tmutil listlocalsnapshots / 2>/dev/null | head -10
```
A long `tmutil listlocalsnapshots` output means APFS is holding pre-purge Time Machine snapshots that account for most of the drift — those are SAFE to delete with `tmutil deletelocalsnapshots <date>` if you've reconciled Time Machine backups first, but that's a user-decision call, not an autonomous cleanup.

## Trap #5 — `state.db-wal` runaway is the silent disk hog (added 2026-07-31)

**Symptom:** Disk at 100%, no obvious culprit. `du -sh ~/.hermes/*` shows `state.db-wal` at **95+ GiB** while `state.db` is only ~6 GiB. Recurring `OSError [Errno 28] No space left on device: '$HOME/.hermes/sessions/.sessions_*.tmp'` errors in the gateway log — these are symptoms of disk-full, NOT the cause.

**Root cause:** SQLite WAL-mode journaling. Every gateway write (session append, cron tick, message ingest) appends to `state.db-wal`. The WAL is checkpointed back into `state.db` and truncated only when no writer holds an open transaction. The `hermes gateway` Python process holds long-lived write txns (4h+ sessions observed), so the WAL grows unbounded instead of being recycled. **Verified 2026-07-31:** PID 48473 = `hermes gateway run`, holding 10+ FDs open on `state.db-wal`, runtime 4h18m, WAL = 95 GiB.

**Why `rm .sessions_*.tmp` doesn't help:** Tmp files are only a few KB each; the gateway writes a fresh one per turn. Even if you delete them all, the next gateway turn hits ENOSPC again because the WAL is the real consumer. Don't loop on tmp cleanup — diagnose the WAL first.

**Diagnosis ladder (in this order):**

```bash
# 1. Confirm WAL runaway (expect WAL >> main DB)
du -sh ~/.hermes/state.db ~/.hermes/state.db-wal ~/.hermes/state.db-shm 2>/dev/null

# 2. Identify the writer holding the WAL open
lsof ~/.hermes/state.db-wal 2>/dev/null
# Typical: /opt/homebrew/Cellar/python@3.13/.../Python $HOME/.local/bin/hermes gateway run

# 3. Confirm it's the gateway (NOT a transient tool like sqlite3)
ps -p <pid> -o pid,user,etime,command
# Etime > 1h + command = "hermes gateway run" → this is the long-lived writer

# 4. Try a passive checkpoint (will fail while writer holds txns — that confirms the trap)
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(PASSIVE);"
# Expected: 1|<busy>|<checkpointed> with busy frames > 0 while writer is live

# 5. Force a TRUNCATE checkpoint — likely reports success but file doesn't shrink
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"
ls -lh ~/.hermes/state.db-wal
# If size unchanged → writer is holding the WAL mmap; safe truncate impossible while it lives
```

**Safe recovery path (user-approved, NOT autonomous):**

1. **Stop writing.** `cronjob pause` on heavy cron jobs (audit-firing, dropped-thread-followup) — they append to the WAL.
2. **Ask the user to restart the gateway.** `hermes gateway stop && hermes gateway start` (or `launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway`). When the gateway PID exits, all its FDs on the WAL close. A fresh sqlite3 session against `state.db` can then `PRAGMA wal_checkpoint(TRUNCATE);` and the WAL truncates to ~0 bytes.
3. **Verify reclaim.** `df -h /System/Volumes/Data` should jump by ~95 GiB. `du -sh ~/.hermes/state.db-wal` should be ~0 (or a few KB for the active WAL window).
4. **Long-term prevention.** Add a daily cron that runs `sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"` from a separate process (NOT the gateway). If the gateway's txns block it, the cron logs the busy-frame count as a health metric. WAL > 1 GiB for >24h = gateway-bug signal, post a Slack alert.

**Forbidden (autonomous-recovery footguns):**
- `kill -9` on the gateway PID — drops Slack relay, cron workers, and all in-flight sessions. User approval required.
- `rm ~/.hermes/state.db-wal` while gateway is running — corrupts the DB on next write; gateway will need a full restart anyway AND a recovery.
- `sqlite3 ... .recover` / `.backup` against a live gateway-held DB — reads see partial WAL state, backup may be inconsistent.
- Looping `rm .sessions_*.tmp` — wastes turns, doesn't free meaningful space, masks the real problem.

**Diagnostic signal — is it the WAL or something else?** Run `du -sh ~/.hermes/* 2>/dev/null | sort -rh | head -10`. If `state.db-wal` is in the top 3 and is >> `state.db`, this trap applies. If WAL is normal but `projects/*` or `Library/Caches/*` is the offender, fall back to the standard tier ladder above.

## Trap #4 — EA-sweep disk numbers are stale by N hours; verify live before quoting (added 2026-07-21)

EA sweeps capture disk pressure at brief-time (e.g. 12:00 PT) and reference it again at 16:00 PT. **The number in the sweep is not the number the user sees now.** Real instance 2026-07-21: sweep reported `data volume 93% (809Gi used / 67Gi free)`; a later sweep within the same day appeared to escalate but the live `df -h /System/Volumes/Data` confirmed 67 Gi free (stable across 4 successive 2s reads, no APFS reconciliation drift).

When an EA sweep or alert-script number drives a triage reply:

1. Run `df -h /System/Volumes/Data` fresh (do not trust the sweep's quoted percentage).
2. Cross-check against `diskutil apfs list | grep -A2 "Volume .* Data"` for container-level ceiling + consumed.
3. **Always also report the iOS Simulator subvolumes** — `/dev/disk5s1` (typically 8.5–9 GiB iOS Bundle, often >95%) and `/dev/disk7s1` (typically 19–20 GiB iOS Simulator, often >95%). The `disk_usage_alert.sh` script does NOT watch these. Without them, a triage misses 28 GiB of commonly-fillable space on Apple Silicon dev machines.
4. If the live number is materially different from the sweep number (more free, fewer offenders), say so explicitly: "Sweep reported X; live read is Y" — and base the recommendation on Y.

Companion pitfall — do NOT delete worktrees, caches, snapshots, or user data during a verification reply. Triage replies classify and propose; cleanup is a separate user-approved action. The 89 hermes/agent processes, 6 docker runners, and 6 active `ez-mac-runner-b-N` containers observed on 2026-07-21 are the live-working set; bulk worktree deletion against them would terminate active jobs.

## Trap #2 — `du -sh ~` and `du -sh /Users/*` time out at scale

When the disk has 300+ project subdirectories or millions of files, `du` on the entire home directory can take >10 minutes and hit the 180s tool timeout. **Don't try to enumerate the whole tree at once.** Drill in by category:

```bash
# 1. Top-level categories (fast, ~5s each)
du -sh ~/Library/* 2>/dev/null | sort -rh | head -10
du -sh ~/Documents ~/Downloads ~/Desktop ~/Movies ~/Music ~/Pictures 2>/dev/null

# 2. Project/work dirs (may need -d 2 if too slow) — PREFER -d 1, NOT bare glob
du -d 1 -sh ~/projects/* 2>/dev/null | sort -rh | head -20
du -sh ~/projects/worktree_* 2>/dev/null | sort -rh | head -20

# 3. Hidden dirs at known accumulation points
du -sh ~/projects/<repo>/.claude/worktrees/ 2>/dev/null
du -sh ~/Library/Developer/CoreSimulator/* 2>/dev/null | sort -rh | head -5
du -sh ~/Library/Application\ Support/Aside/* 2>/dev/null | sort -rh | head -5
```

> **Pitfall (added 2026-07-15):** `du -sh ~/*` and `du -sh /Users/*` with a bare glob can enumerate 200+ subdirs and time out hard (180s limit). Use **`du -d 1 -sh`** (one level, ~30s total) or enumerate specific candidates individually via a list. If `du` repeatedly returns no output without timing out, suspect an APFS snapshot conflict or a corrupted dirent cache — try `ls` first to confirm the path exists.
>
> **Pitfall — `du -d 1 -sh` returns empty output on certain pools (added 2026-07-15):** `du -d 1 -sh ~/.worktrees/*` and `du -d 1 -sh ~/.gemini/antigravity-cli/brain/*` can return **no output at all** (not an error, not a timeout) when the dir has 50+ entries with mixed perm bits or when shell glob expansion interacts badly with the dotfile path. The diagnostic step that always works is a per-entry loop: `for d in <pool>/*/; do du -sh "$d" 2>/dev/null; done | sort -rh | head -15`. Use that instead of `du -d 1 -sh <pool>/*`. Same trap applies to `du -d 1 -sh ~/.claude/*` which additionally times out at 180s with the 50KB stdout cap (~1247 entries on a busy `.claude/projects/`).
>
> **Pitfall — `~/.claude/projects/` is session metadata, NOT garbage (added 2026-07-15):** When `du -d 1 -sh ~/.claude/*` reports `~/.claude/projects/` at 7G+ across ~1200+ entries, **do not propose deleting it**. Each entry is a `<cwd-hash>/<session-id>.jsonl` transcript file — the agent's past-conversation recall surface. Deleting drops `session_search` history. Tier-1 cleanup targets are `.worktrees/`, `.gemini/antigravity-cli/brain/`, `.lvl-lanes/`, `.codex/worktrees/`, `.ao/data/worktrees/`, and `.claude/file-history` (the cumulative file-edit history, regenerable).
>
> **Pitfall — subvolumes the alert script doesn't watch (added 2026-07-15):** `disk_usage_alert.sh` checks `/` by default, which on Apple Silicon routes through the sealed `/dev/disk3s1` snapshot — `df /System/Volumes/Data` is the real read for user files. **Two more subvolumes silently fill without triggering the alert:** `/dev/disk5s1` (typically 8.5G, `/Library/Caches/com.apple...`) and `/dev/disk7s1` (typically 19G, `/Library/Developer/CoreSimulator/...`). When you see these at 98% in `df -h` output, the home-data disk may still report 96% — both need cleanup. Simulator caches are safe to reap with `xcrun simctl delete unavailable` + `rm -rf ~/Library/Developer/CoreSimulator/Caches/Devices/*`. The 8.5G `/Library/Caches` is often Xcode DerivedData or installer caches — check with `du -sh /Library/Caches/* | sort -rh | head -10`.

The disk alert message body almost always contains "Threshold: 787G" or similar — that's the *raw* number from `df`, often in GB. Cross-check against `df -h /System/Volumes/Data` to confirm the alert and current free space.

## The smoking gun: worktree accumulation across many pools

Git worktrees accumulate in many pools, not just `<repo>/.claude/worktrees/`. A single user can have tens of thousands of worktree directories spread across registry-tracked and unregistered pools. **Always enumerate ALL of these before concluding "where is the disk going":**

```bash
# Registry-tracked pools (appear in `git worktree list`)
du -sh ~/projects/<repo>/.claude/worktrees/ 2>/dev/null        # delegate_task spawns
du -sh ~/.worktrees/<org>/<repo>/ 2>/dev/null                   # manual / launchd-managed lanes (e.g. wa-NNNN)
du -sh ~/.worktrees/<org>_<repo>/ 2>/dev/null                   # alt naming convention
du -sh ~/.ao/data/worktrees/<org>/<repo>-<id>/ 2>/dev/null      # Agent Orchestrator pool
du -sh ~/.codex/worktrees/ 2>/dev/null                          # Codex CLI pool (hex-hash subdirs)
du -sh ~/.lvl-lanes/ 2>/dev/null                                # leveling/green-driver lanes

# Unregistered pools (NOT in `git worktree list` — separate cleanup logic)
du -sh ~/.gemini/antigravity-cli/brain/ 2>/dev/null             # antigravity brain sessions (20G+ common)
find ~/.gemini/antigravity-cli/brain -path '*/.system_generated/worktrees/*' -type d 2>/dev/null | wc -l
```

On `your-project.com` a single triage found: `~/projects/<repo>/.claude/worktrees` 46G, `~/.worktrees/worldarchitect*` 9.7G, `~/.ao/data/worktrees/worldarchitect` 3.7G, `~/.codex/worktrees` 1.5G, `~/.lvl-lanes` 5.3G, `~/.gemini/antigravity-cli/brain` 20G. **Total often 80-120G for one active repo.** Pick a repo with the largest `~/projects/*` footprint first.

### Per-repo registry-tracked worktree triage

`delegate_task` in Hermes spawns one git worktree per subagent at `<repo>/.claude/worktrees/agent-<hash>/`. **Each worktree is a full checkout of the repo (300MB–1GB depending on repo size) plus accumulated `docs/` and `evidence/` directories.** They are registered with `git worktree list` but rarely cleaned up after the subagent finishes. On `your-project.com` this grew to **46G across 128 worktrees** in one session.

**How to detect:**
```bash
du -sh ~/projects/<repo>/.claude/worktrees/ 2>/dev/null  # main offender
ls ~/projects/<repo>/.claude/worktrees/ | wc -l           # count
```

**How to assess which are safe to remove (use the script, not the awk — see scripts/parse_worktrees.py):**
```bash
# 1. Run the reliable Python parser (see scripts/parse_worktrees.py)
python3 ~/.hermes/skills/devops/mac-disk-pressure-triage/scripts/parse_worktrees.py ~/projects/<repo>
# Outputs: total / prunable_by_git / locked / unlocked+PR-free (Tier 1 safe) / unlocked+on-PR (DO NOT DELETE)

# 2. Load open PR heads for ALL repos referenced by worktrees (REST API, paginated)
gh api 'repos/jleechanorg/<repo>/pulls?state=open&per_page=100' --jq '.[] | .head.ref' > /tmp/open_prs_<repo>.txt
gh api 'repos/jleechanorg/<repo>/pulls?state=open&per_page=100&page=2' --jq '.[] | .head.ref' >> /tmp/open_prs_<repo>.txt

# 3. Age distribution (for the antigravity / unregistered pools without git state)
find ~/.gemini/antigravity-cli/brain -maxdepth 1 -mindepth 1 -type d -mtime -7   | wc -l  # active
find ~/.gemini/antigravity-cli/brain -maxdepth 1 -mindepth 1 -type d -mtime +7   | wc -l  # stale candidates
```

**Safe cleanup recipe (3 tiers, lowest risk first):**

1. **Unlocked + not on open PR** (gold-standard Tier 1 — git registry's own state, cross-checked against live PRs):
   ```bash
   python3 ~/.hermes/skills/devops/mac-disk-pressure-triage/scripts/parse_worktrees.py ~/projects/<repo> --delete-safe --open-pr-file /tmp/open_prs_<repo>.txt
   # Or manually with git:
   git worktree list --porcelain | python3 -c '
   import sys, subprocess, os
   prunables = []
   cur = None
   for line in sys.stdin:
       line = line.rstrip()
       if line.startswith("worktree "):
           cur = line[len("worktree "):]
       elif line == "locked" or line.startswith("locked "):
           cur = None
       elif (line == "prunable" or line.startswith("prunable ")) and cur:
           prunables.append(cur); cur = None
       elif line == "":
           cur = None
   for wt in prunables:
       if os.path.isdir(wt):
           subprocess.run(["git", "worktree", "remove", "--force", wt], check=False)
   '
   ```
   Real-world: a single repo can have **hundreds** of Tier 1 candidates (one triage found 298 unlocked + PR-free worktrees in `your-project.com`, vs. 50 locked + 54 backing open PRs).
2. **Older than 30 days + not locked + not on open PR headRefName** (looser sweep — may include unregistered pools):
   ```bash
   for dir in ~/projects/<repo>/.claude/worktrees/agent-*/; do
     age_days=$(( ( $(date +%s) - $(stat -f %B "$dir") ) / 86400 ))
     [[ $age_days -lt 30 ]] && continue
     git -C ~/projects/<repo> worktree list | grep -q "$(basename "$dir")" || continue
     git -C ~/projects/<repo> worktree remove --force "$dir" 2>/dev/null || rm -rf "$dir"
   done
   ```
3. **8–30 days old + not locked + not on open PR:** same recipe with `[[ $age_days -lt 8 ]] && continue`.

**Pitfall — `prunable` worktrees:** The earlier recipe `git worktree list --porcelain | grep -B1 'prunable'` produces **false positives** — the literal text "prunable" sometimes matches nearby lines that contain the substring (e.g. branch names like `pr-7980-prunable-foo`). Use the Python parser (`scripts/parse_worktrees.py`) which checks for the EXACT `prunable` keyword, or check by running `git worktree prune --dry-run -v` (true prunables appear there with a reason).

**Pitfall — `locked` worktrees:** `git worktree remove` refuses to remove locked worktrees. Either unlock first (`git worktree unlock <path>`) OR use `rm -rf` directly. Locked worktrees may be held by a *still-running* delegate session — check `ps aux | grep -i claude` before force-removing.

**Pitfall — open PR branches:** Before bulk-deleting, ALWAYS load open PR heads via **`gh api .../pulls?state=open&per_page=100`** (paginated through 2+ pages for repos with >100 open PRs) and intersect with `git worktree list`. The `gh pr list --state open --limit 200` wrapper has been seen returning **0 results intermittently** (likely a GraphQL pagination bug at the `--limit 200` boundary), so the REST API is the safer path. Always use a file (`/tmp/open_prs_<repo>.txt`) for the intersect — pipe-based intersects break when branch names contain spaces.

**Pitfall — unregistered worktree pools:** `~/.worktrees/`, `~/.ao/data/worktrees/`, `~/.codex/worktrees/`, and `~/.lvl-lanes/` may have worktrees that are NOT in `git worktree list` of any single repo (they are registered in their own sub-pool's git dir). When cleaning these, check `git -C <pool_root>/<repo_or_lane>/ worktree list` separately for each pool's primary working dir, not the parent pool dir.

## Standard recovery tiers (priority order)

When you've found the offenders, propose cleanup in this order (most → least reclaimable, safest → most aggressive):

| Tier | Targets | Typical reclaim | Risk |
|---|---|---|---|
| 0. **Unregistered agent-pool cleanup** | `~/.gemini/antigravity-cli/brain/<uuid>/.system_generated/worktrees/*` (32K+ dirs typical), 7+ days old; `~/.codex/worktrees/<hex>/*`; `~/.lvl-lanes/<lane>` | **10-50G** | Medium — confirm no active antigravity/codex session via `ps aux \| grep -i 'gemini\|codex\|antigravity'` before bulk delete |
| 1. Stale unlocked worktrees | `git worktree list` entries that are unlocked + not on any open PR headRefName (typically **200-500 candidates** for an active repo) | 50-150G | Low — git registry confirms safety + REST-PR cross-check |
| 2. Stale worktrees 8-30d (unregistered paths) | `~/projects/*/.claude/worktrees/agent-*` 8-30d old, NOT touched by Tier 1 | 5-30G | Low — age + filesystem check |
| 3. iOS simulators | `~/Library/Developer/CoreSimulator/Caches/Devices/` | 5-10G | Low — `xcrun simctl delete unavailable` |
| 4. Browser cache (Aside/Chrome) | `~/Library/Application Support/Aside/Default`, `Profile 1` (NOT `~/Library/Caches/Aside/` — both hold state) | 1-3G | Low — fully regenerable |
| 5. Docker prune | `docker system prune -a` | 5-15G | Medium — confirm no running containers first |
| 6. Downloads duplicates | `~/Downloads/*backup*`, `*v4*`, `*v6*`, etc. | 0.5-2G | Low — user judgment call |
| 7. Photos library | `~/Pictures/Photos Library.photoslibrary` | 5-15G | High — user data, never auto-delete |
| 8. **`~/.lvl-lanes/` / `~/.worktrees/<repo>/wt-NNNN-*` closed-PR worktrees** | Every `wt-*` lane whose `gh pr list --state all --head <branch>` returns a CLOSED PR — common pattern across `your-project.com` `feat/levelup-v2-*` cluster | 1-10G per cluster | Low — sync to upstream + `git worktree remove --force`. See `references/lvl-lanes-closed-pr-pattern.md`. |
| 9. APFS subvolumes (`/dev/disk5s1`, `/dev/disk7s1`) | `/Library/Caches/*` (Xcode DerivedData, installer caches); `~/Library/Developer/CoreSimulator/Caches/Devices/*` | 5-25G | Low — `xcrun simctl delete unavailable` for simulators; inspect `/Library/Caches/*` before deletion. **Alert script does NOT watch these** — see Pitfall below. |

Always present tiers 1–4 as "do now", tier 5 as "if Docker is running", tier 6 as "you decide", and tier 7 as "never auto-touch — flag for user review."

## The disk alert script contract

The canonical macOS disk-pressure watchdog (in `~/Library/Application Support/user-scope/bin/`):
- `disk_usage_alert.sh` — checks `/` by default, posts to Slack
- `disk_usage_alert.sh --silence` — writes `$HOME/.disk-usage-alert.silenced`, suppresses future alerts
- `disk_usage_alert.sh --unsilence` — re-enables
- `disk_usage_alert.sh --status` — print current state and threshold

**When to silence during cleanup:** If you're doing a 10+ minute sweep that will temporarily keep usage high (e.g. copying out files before deleting), `--silence` first, then `--unsilence` when done. Otherwise the watchdog will spam mid-job.

**Threshold tuning:** `DISK_ALERT_THRESHOLD_GB` env var. Default derives from 90% of disk capacity. Override in the launchd plist if the default fires too aggressively.

## Companion skills

- `hermes-health-check` — gateway/Qdrant/Slack-side health (different concern; disk pressure is filesystem-side).
- `slack-thread-routing-investigation` — for posting the report to Slack if the bot gets `not_in_channel`.

## Support files

- `scripts/parse_worktrees.py` — reliable porcelain parser + Tier-1 classifier; replaces the awk/grep "prunable" pattern that produces false positives.
- `references/2026-07-14-15-apfs-lazy-purge-disk-alert.md` — first documented instance of the APFS drift trap (Trace #3).
- `references/worldarchitect-claude-worktree-leak-2026-07-14.md` — first documented instance of the `.claude/worktrees/agent-*` accumulation pattern.
- `references/lvl-lanes-closed-pr-pattern.md` — recurring `~/.lvl-lanes/wt-lvl-pr<N>/` and `~/.worktrees/<repo>/wa-NNNN-*/` closed-PR worktree reaping recipe (your-project.com fleet, 5-25G per cluster).
- `references/2026-07-31-state-db-wal-runaway-95gib.md` — Trap #5 instance: `~/.hermes/state.db-wal` ballooned to 95 GiB held open by `hermes gateway` PID 48473; verified diagnosis ladder + recovery recipe. **Also covers the user-facing `Idle.` / `:hourglass_flowing_sand:` gateway re-prompt loop signature, the runtime-level safety guard that blocks `launchctl kickstart` / `nohup` from inside the gateway session, and the working alert-script path via `terminal(background=true)`.**
- `references/2026-08-02-slack-post-under-enospc.md` — recipe for delivering a status message when the disk is full and the agent terminal is on hardline block: standalone `export HERMES_SLACK_BOT_TOKEN` + `echo '...' | curl --data-binary @-` (avoids `/tmp` redirects that fail with ENOSPC).

## Reporting findings to the user (template)

When reporting disk pressure, use this structure (matches the Slack-friendly section format):

```
🟡 **Disk pressure report — <N>% (<used>G/<total>G, <free>G free)**

🔴 Big offenders:
- <path> (<size>) — <one-line description>
- <path> (<size>) — <description>

🟡 Safe cleanup proposal (lowest → highest risk):
1. <action> → ~<N>G back
2. <action> → ~<N>G back

Pick a tier or "just show me the list" for surgical delete.
```

Always include the actual `df -h /System/Volumes/Data` output as proof. Don't just say "disk is full" — show the exact number.

## Companion skills

- `hermes-health-check` — gateway/Qdrant/Slack-side health (different concern; disk pressure is filesystem-side).
- `slack-thread-routing-investigation` — for posting the report to Slack if the bot gets `not_in_channel`.