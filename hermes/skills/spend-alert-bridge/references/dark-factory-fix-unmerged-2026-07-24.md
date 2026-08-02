# Dark-factory fix was NOT merged — 2026-07-24 incident verification

## TL;DR

The Spend Alert Bridge skill's `Mode A.2` section describes a fix for the dark-factory daemon's `adoption_branch_collision` comment-spam loop. The fix exists on branch `fix/escalation-dedupe-cooldown` at commit `cb2136ffedb307347175c03107670744ad496b9b` (Author: jleechan2015, 2026-07-23 12:08 PT). That branch was **never merged into `main`** as of 2026-07-24. The daemon running via launchd on the user's mac is on main HEAD `b04df6f449` (the bots branch), which still contains the buggy `tick.rs:1027-1053` block that posts an escalation comment every slow tick to colliding branches.

Result: second spend spike identical to the 2026-07-23 incident. Today (2026-07-24) GH Actions MTD delta jumped from typical $14-19 to **$61.11** (4× baseline), 7-day rolling. `your-project.com` alone: 1,023 dark-factory escalation comments in 4 hours (288/hr peak at 13:00 UTC), then dropped after ~17:00 UTC, then resumed at 1-26/hr overnight and continues today.

## The fix that's NOT on main

```bash
cd ~/projects/dark-factory
git log --all --oneline --grep="adoption_branch_collision"
# cb2136ffedb307347175c03107670744ad496b9b  fix(daemon): dedupe adoption_branch_collision escalation per branch ($USER-rouf)

git merge-base --is-ancestor cb2136ffe HEAD
# echo $?  →  1  (i.e. NOT an ancestor — fix is NOT on main)

git branch --all --contains cb2136ffe
# + fix/escalation-dedupe-cooldown
#   remotes/origin/fix/escalation-dedupe-cooldown
```

## The fix commit's content (per its own message)

> Each slow-tick `normalize_labeled_prs` pass produces a NEW `adopted.bead_id` for the SAME colliding branch (production pattern: 3 factory PRs on $GITHUB_REPOSITORY #8428 / #8420 / #8421). The historical dedup key `escalation_ledger(bead_id, reason)` therefore never matched across ticks and the "🤖 [dark-factory] Escalation required: refusing factory PR adoption" comment + ESCALATION_REQUIRED event spammed every slow tick
> (~174/hour/branch → 5,334 comments in 32h, 73% of all GH Actions workflow_run noise on the repo).
>
> Fix: re-key dedup on the stable `adopted.head_ref_name` so all colliding beads for the same branch collapse to one ledger row, and `cfg.escalation_refire_secs` (default 3600s) gates the noise. Also moves the dedup check BEFORE `comment_external` so the SCM write is suppressed too (previously the dedup check ran but the comment had already been posted).
>
> Tests: 4 new unit tests pin the contract against the real `SqliteStateStore` (not the trait default) covering (a) happy-path first-allowed-second-suppressed, (b) the buggy bead-keyed path is documented as the regression class, (c) branch-keyed dedup suppresses across colliding beads and re-allows after the cooldown, (d) different branches do NOT collide.
>
> All 399 lib tests pass. The 1 daemon-binary systemd_notify failure and 3 tick_integration cross-model-reviewer failures pre-date this change.

## The buggy code on main (tick.rs:1027-1053)

```rust
if let Some(owner) = deps.store.bead_id_for_branch(&adopted.head_ref_name)? {
    if owner != adopted.bead_id {
        let owner_live = deps.store.load(&owner)?.is_some();
        let comment_body = format!(
            "🤖 **[dark-factory]** Escalation required: refusing factory PR adoption for branch `{}` because it is already registered to bead `{}`. Branch-key stealing is not allowed; please use a unique same-repo branch.",
            adopted.head_ref_name, owner
        );
        let _ = deps
            .tracker
            .comment_external(&adopted.external_ref, &comment_body);  // ← posts every tick
        summary.beads_escalated += 1;
        emit(...)?;
        continue;
    }
}
```

No `escalation_dedup_should_emit` guard before `comment_external`. The bead ID is fresh every tick (per the fix commit's own analysis), so even with a dedup check the bead-keyed ledger would never match.

## Evidence the second spike is the same pattern

Last 24h, dark-factory escalation comments on your-project.com:

```
2026-07-23T13   288  ██████████████████████████████████████████████████
2026-07-23T14   285  ██████████████████████████████████████████████████
2026-07-23T15   271  ██████████████████████████████████████████████████
2026-07-23T16   179  ██████████████████████████████████████████████████
2026-07-23T17     2  ██
2026-07-23T19    25  █████████████████████████
2026-07-23T20    26  ██████████████████████████
2026-07-23T21     6  ██████
2026-07-23T22     8  ████████
2026-07-23T23    13  █████████████
2026-07-24T00     3  ███
2026-07-24T01     9  █████████
2026-07-24T02     9  █████████
2026-07-24T03    10  ██████████
2026-07-24T04     6  ██████
2026-07-24T05    14  ██████████████
2026-07-24T06     1  █
2026-07-24T07     0
2026-07-24T08     1  █
2026-07-24T11     0
2026-07-24T12    13  █████████████
2026-07-24T13     0
```

The 13:00-17:00 UTC 2026-07-23 burst matches the documented 2026-07-23 incident timing. The drop at 17:00 is unexplained (probably the daemon restarted with a different slow-tick cadence once the colliding branches closed). The 1-26/hr overnight pattern matches steady-state leak through the still-buggy code.

## What to do — durable fix path

1. **Merge `fix/escalation-dedupe-cooldown` into main.** Branch is clean, has 4 unit tests, all 399 lib tests pass. PR should be reviewable as-is.
2. **Rebuild the daemon binary** (`cargo build --release`).
3. **Restart the launchd job** so the running daemon picks up the new binary:
   ```bash
   launchctl kickstart -k gui/$(id -u)/ai.dark-factory.af-tick
   ```
4. **Verify post-merge.** Run `git merge-base --is-ancestor cb2136ffe HEAD` from `~/projects/dark-factory` — must return "merged". Then check the daemon's stderr for new `escalation_refire_secs` debug lines, and confirm the issue_comment volume on `#8428/#8420/#8421` drops to 0 for an hour.

## Stopgap (NOT recommended)

`launchctl bootout gui/$(id -u)/ai.dark-factory.af-tick` will silence the daemon but the daemon will restart on its next tick interval, and no work gets done in the meantime. This is a 1-hour tarball, not a fix. Document any bootout with a follow-up `launchctl bootstrap` once the fix is merged.

## Lessons for the skill (now encoded)

1. **`git merge-base --is-ancestor <fix-sha> HEAD` is MANDATORY before claiming any bug-fix is shipped.** The 2026-07-23 skill section trusted the PR number `dark-factory#470` to mean "fix is on main" — it didn't. Always verify.
2. **Bug locations drift.** `tick.rs:1377-1424` from the 2026-07-23 skill is now `tick.rs:1027-1053` after refactors. Use `grep -n "adoption_branch_collision"` to find the current location instead of trusting line numbers.
3. **Dedup keys must be stable identifiers.** The recurring root cause is `escalation_ledger(bead_id, reason)` — bead_id is fresh per tick. Branches, PR numbers, commit SHAs are stable. Audit every dedup key in the daemon for this property.
