# 2026-07-14-15 — Di[REDACTED_OPENAI_KEY] alert cycle: 891G → 904G → stable at 833G / 95% (APFS lazy-purge trap)

## Two consecutive di[REDACTED_OPENAI_KEY] alerts, two different false floors

**2026-07-14 23:14 UTC** — alert fired at 891G used / 926G (96%). Triage session ran, found 42 worktrees >=14d totaling ~12 GB, posted the cleanup proposal as `WORKTREE APPROVED` gate in the same thread (`C0AJQ5M0A0Y / 1784070882.257369`, prior post at ts `1784071360.715809`). User never replied in-thread.

**2026-07-15 00:14 UTC** — alert re-fired at 904G used / 926G (97%, 21G free). Triage opened on the same thread. Initial `df -h /System/Volumes/Data` reading showed 866G used (98%, 21G free). Five minutes later, after running `du` per directory and `git worktree prune`, the same `df` showed 833G used (95%, 53G free) — a **32 GB swing with no user-visible cleanup in between**.

## What caused the 32 GB swing

APFS maintains **purgable space** — blocks held by older Time Machine snapshots, APFS snapshots, and `tmutil` artifacts that are allocated but reclaimable on demand. The first `df` reading after a high-water-mark event (a large write, an Xcode build cycle, or `disk_usage_alert.sh` itself running) returns a conservative free-space estimate that undercounts purgable blocks. APFS re-reconciles lazily as `photolibraryd`, `bird`, `deleted`, and `tmutil` reclaim blocks in the background. Five minutes later, the same `df` shows 30+ GB more free.

The earlier 21G reading was the "high water mark" pressure; the later 53G was the post-reconciliation baseline. Both are real readings — they just measure different states of the lazy-purge subsystem.

## How the triage report should have been framed

The triage session that ran on the 904G alert first reported 95-98% pressure based on the first reading, then realized the reading was inconsistent and revised to the stable baseline. **The cleaner shape** is to read 3-4 successive `df`s before reporting the baseline, then tag any drift as "mid-reconciliation" in the report:

```bash
for i in 1 2 3 4; do
  df -h /System/Volumes/Data | tail -1 | awk -v i=$i '{print "Read " i ": " $4 " free (" $5 " used)"}'
done
```

If the four reads converge, that number is the real baseline — report it. If they drift, the APFS kernel subsystem is mid-reconciliation; wait 60 s and re-read.

## Confirm purgable-space reality (advanced diagnostic)

```bash
diskutil apfs list 2>&1 | grep -A2 "Volume .* Data"
tmutil listlocalsnapshots / 2>/dev/null | head -10
```

A long `tmutil listlocalsnapshots` output means APFS is holding pre-purge Time Machine snapshots that account for most of the drift. These are SAFE to delete with `tmutil deletelocalsnapshots <date>` IF Time Machine backups have been reconciled, but that's a user-decision call — never auto-delete snapshots.

## What the triage session got right

1. **Cross-referenced worktrees against open PRs** before recommending deletion (`gh pr list --state open --limit 200` returned 0 PRs in this cycle, confirming none of the 102 candidates were PR-backed).
2. **Verified 34 LOCKED worktrees** were not touched (held by live AO/scheduler agents — `git worktree list --porcelain | grep -c locked` returned 34 across the your-project.com repo).
3. **Grouped the 102 eligible worktrees by bucket** so the user could approve a narrowed scope (the `WORKTREE APPROVED lvl-lanes` flag would target just the abandoned `feat/levelup-v2-*` cluster).
4. **Posted the cleanup proposal as a single yes/no gate** rather than asking the user to pick from 4 options, per SOUL.md `no-pick-one-menus`.
5. **Created a one-time 20 min cron** (`fb6959bf3ba5`) to nudge the thread if the gate stayed silent (per SOUL.md `one-time-status-cron-after-every-task`).

## What the triage session got wrong

1. **Reported the 98% number before checking whether `df` was stable.** A second-and-third re-read would have shown the 95% baseline. The first draft of the report said "904G used (97%)"; the final report said "833G (95%)" after the readings stabilized. Earlier reads should have been cross-checked before publishing.
2. **XOX-P Path B first post had `mrkdwn: true`** and lost all but the trailing 714 chars (see `slack-thread-routing-investigation/references/2026-07-15-path-b-mrkdwn-truncation.md`). The trap surfaced only because I verify every posted message via `conversations.replies(ts=<posted_ts>)` and grep for a mid-message marker. Without that verify step, the user would have seen a 3-paragraph-message with only the trailing "Memories used" block.

## Reproduction recipe (cross-check the APFS lazy-purge reading)

```bash
# Run five `df` reads 30 seconds apart
for i in 1 2 3 4 5; do
  ts=$(date -u +%H:%M:%S)
  read=$(df -h /System/Volumes/Data | tail -1 | awk '{print $4 " free / " $5 " used"}')
  echo "[$ts] Read $i: $read"
  sleep 30
done
```

If you see drift > 5 GB between successive reads with no user-initiated cleanup in between, you're in the APFS reconciliation window. Wait 60 seconds and recheck.

## Why this matters for future triage

The `disk_usage_alert.sh` watchdog fires on the same `(path, threshold)` check every time. If the threshold is hit at 21G free because APFS was mid-reconciliation, the next reading at 53G free might not fire — but the underlying disk pressure is still real (53G free is below the 90% threshold of 90.6G free). The watchdog should probably sample 3 readings 60s apart before deciding to alert, but that's an alert-config change the user needs to approve, not an autonomous fix.
