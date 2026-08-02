# Watchdog probe-mismatch bug — verified + fixed 2026-07-20

## The bug (one line)

`cloud-build-bastion-watchdog.sh` v1.1.0 and earlier probed only `cloud-bastion@` and `enroll@` users at the bastion — both of which print success banners ("interactive shell is not permitted" / "invalid or expired token") regardless of whether the local SSH key is actually trusted for the handoff users (`git@`, `$USER@`, `cloud-build@`) that `/super` and `cloud_build_handoff` use. Result: watchdog exits 0 while every real `/super` dispatch fails with `Permission denied (publickey)`.

## Live repro on this Mac (2026-07-20 22:18 PT)

```
$ ssh -T cloud-bastion@cloud.superpowers.build
cloud-bastion: interactive shell is not permitted   ← key trusted (banner path)

$ ssh -T enroll@cloud.superpowers.build
enroll: invalid or expired token                     ← key trusted (enroll path)

$ ssh -T git@cloud.superpowers.build
git@cloud.superpowers.build: Permission denied (publickey).    ← key NOT trusted (handoff path)

$ ssh -T $USER@cloud.superpowers.build
$USER@cloud.superpowers.build: Permission denied (publickey). ← key NOT trusted

$ ssh -T cloud-build@cloud.superpowers.build
cloud-build@cloud.superpowers.build: Permission denied (publickey). ← key NOT trusted
```

Root cause: the local key fingerprint `SHA256:f1c66c1fb3…` had been rotated by `ssh-keygen` after the last `cb-client-setup.sh` run, but `~/.config/cloud-build/state.json` still contained the OLD enrolled fingerprint `c709569c7b…`. The bastion trusts the key that was enrolled, not whatever the local key happens to be now — and trust on the banner users (`cloud-bastion@`, `enroll@`) is decoupled from trust on the handoff users. So banners pass while handoff fails.

## The fix (shipped in watchdog v1.2.0)

Added a third probe block at `~/.hermes/scripts/cloud-build-bastion-watchdog.sh` (lines 124-158 in v1.2.0) that iterates the three actual handoff users and surfaces a new exit code:

| Code | Meaning |
|------|---------|
| 0 | All 6 probes pass (banner users + handoff users + known_hosts + age) |
| 4 | Banner users OK + handoff users fail — watchdog-lying-about-success |

Verified: `bash ~/.hermes/scripts/cloud-build-bastion-watchdog.sh` now exits **4** on this Mac (was 0 before the fix). The exit-4 contract is verified by the support script `scripts/test_watchdog_exit4_on_handoff_fail.sh` (7/7 tests pass).

## Why the recipe uses three handoff users (not `whoami`)

An earlier draft of this fix used `$(whoami)@cloud.superpowers.build` as the single probe user. That works on the Mac (where `whoami=$USER`) but doesn't generalize — the box-side `git@` user is also a handoff user for git-fetch operations, and `cloud-build@` is the user for handoff ack. The three-user probe covers all of them without needing per-machine configuration. Tradeoff: three SSH round-trips per watchdog run (~3s), still well within the 12h cadence budget.

## Defense in depth — pre-dispatch probe

Even with the watchdog fix, agents about to call `/super` should run the three-user probe inline as a final sanity check. The watchdog is 12h-cadence, not per-dispatch — there's a window where the watchdog was healthy at the last tick but a key rotation since then has broken the handoff path. Recipe:

```bash
for u in git $USER cloud-build; do
  ssh -i ~/.ssh/cloud-build/id_ed25519 -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
    -o ConnectTimeout=5 -o BatchMode=yes -T "${u}@cloud.superpowers.build" 2>&1 | head -1
done
```

If ANY returns `Permission denied (publickey)`, STOP and surface to the user — do not auto-re-enroll (the user must paste a fresh enrollment code from the maintainer) and do not silently route around `/super`.

## Companion changes shipped in this session

- `~/.claude/commands/super.md` (MD5 `29d49bcff870b2a804d46f215834ae1a`) — new MANDATORY handoff-user auth probe at step 2 with the exact FAIL message + fix recipe
- `~/.claude/projects/-Users-$USER/memory/feedback_2026-07-20_dual_machine_cloud_build_enrolled_fp_drift.md` — durable memory of the dual-machine enrolled_fp_hash drift pattern
- jeff-ubuntu's `~/.ssh/cloud-build/known_hosts` re-pinned from `assets/cloud-build-client-config-v0.json` (was already correct, but re-synced for safety)
- New contract test at `scripts/test_watchdog_exit4_on_handoff_fail.sh` (7/7 pass)

## Out of scope / what this fix does NOT do

- **Does not auto-re-enroll on exit=4.** That requires a fresh enrollment code from the maintainer (out-of-band, invite-only — see `references/bastion-watchdog-handoff-user-mismatch-2026-07-20.md` in the umbrella skill for the full discussion). The autoheal path that consumes `~/.config/cloud-build/enrollment-code` only fires when the operator has manually placed a fresh code there.
- **Does not reconcile jeff-ubuntu's state.json with the Mac's.** Both machines can drift independently if their local keys rotate at different times (see Pitfall P6 in the watchdog SKILL.md). The fix here detects the symptom on each machine independently; cross-machine reconciliation requires a separate `cb-client-setup.sh` run on jeff-ubuntu.
- **Does not fix the underlying question of why the local key was rotated.** That was a separate decision by the user (likely during a `ssh-keygen` rotation or a fresh dev environment setup), and is not the watchdog's job to prevent.

## Source provenance

Verified failure mode — 2026-07-20, Slack thread `C09GRLXF9GR/p1784582518.247009`. Operator said "/super should work now"; probe proved it didn't. The watchdog itself shipped the v1.1.0 banner-string fix on 2026-07-20 but never probed the handoff users. v1.2.0 closes that structural gap. Bead `cloud-build-bastion-watchdog-can-lie-about-pty-handoff-fail` tracks the umbrella-level follow-up.
