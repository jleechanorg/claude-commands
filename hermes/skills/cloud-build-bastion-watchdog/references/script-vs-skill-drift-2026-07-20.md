# Watchdog script vs SKILL.md drift — verified 2026-07-20

## The discrepancy

The SKILL.md (`~/.hermes/skills/cloud-build-bastion-watchdog/SKILL.md`) advertises itself as **v1.2.0** and documents:
- A 3rd probe block that iterates the actual handoff users (`git@`, `$USER@`, `cloud-build@` at `cloud.superpowers.build`)
- Exit code 4 = `handoff-fail-with-banner-ok` (= watchdog-lying-about-success)
- The "Tested 2026-07-20" table records the live Mac state as `exit=4` for all three handoff users

But on this Mac, `bash ~/.hermes/scripts/cloud-build-bastion-watchdog.sh --notify` still emits:

```
known_hosts fingerprint OK (sha256:uIogunmqBg/yisJwDP3uHHzJ0ualJ9t2EucfrwjxzaQ)
bastion auth probe OK (banner: cloud-bastion: interactive shell is not permitted)
enroll probe OK (banner: enroll: invalid or expired token — key still trusted on enroll path)
last_enrollment_check age: 4 days (warn at 6)
verdict: exit=0 (0=healthy 1=auth-fail 2=known_hosts-drift 3=age-warn)
EXIT=0
```

That output is the **v1.1.0 surface area** — no handoff-user probe block, no exit-4 verdict. The script on disk is older than the SKILL.md says it is.

## What this means for agents

**Do not trust `exit=0` from the watchdog as proof that `/super` will work.** The watchdog and the SKILL.md can drift independently, and an agent that loads the skill and runs the script will get a green-light that contradicts the skill's own documented truth.

## Defense: the 3-user handoff probe MUST run inline before any /super dispatch

The canonical /super instructions (`~/.claude/commands/super.md`) embed this exact probe as a MANDATORY step-2 preflight. Run it from bash, not zsh, before trusting any "bastion healthy" signal:

```bash
for u in git $USER cloud-build; do
  ssh -i ~/.ssh/cloud-build/id_ed25519 -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
    -o ConnectTimeout=5 -o BatchMode=yes -T "${u}@cloud.superpowers.build" 2>&1 | head -1
done
```

If ANY returns `Permission denied (publickey)`, STOP. Do NOT fall through to local subagents, `claudeg`, OpenRouter, or any other path. The exact canonical /super FAIL message to surface is:

```
/super FAIL: bastion auth is broken on handoff users.
cloud-bastion@ and enroll@ banner probes pass, but the handoff users
(git@/$USER@cloud-build@) return Permission denied (publickey).
Root cause: SSH key is trusted on banner paths but pruned from
authorized_keys for handoff users.
Fix: re-enroll this machine. Paste your fresh enrollment code and run:
  printf %s "$code" | bash ~/superpowers-cloud-build-main/skills/cloud-build/scripts/cb-client-setup.sh
The watchdog at ~/.hermes/scripts/cloud-build-bastion-watchdog.sh now
returns exit=4 for this exact state — if your prior watchdog said
"healthy", it was lying. See feedback_2026-07-20_dual_machine_cloud_build_enrolled_fp_drift.md
in ~/.claude/projects/-Users-$USER/memory/.
```

## Root-cause hypothesis (best guess, 2026-07-20 22:38 PT)

The v1.2.0 SKILL.md was updated in a session that ran the script edit, but either:
- The script edit did not land in this Mac's `~/.hermes/scripts/` (deployment drift between staging and prod trees — see SOUL.md `## COMMIT: hermes-deploy-pipeline`)
- OR the script edit landed but was reverted by a later `git -C ~/.hermes pull --ff-only`
- OR the v1.2.0 reference file shipped first and the script change was supposed to follow but didn't

The contract test `scripts/test_watchdog_exit4_on_handoff_fail.sh` exists and would catch this — Test 6 ("live run correctly exits 4") would FAIL on the current script. Running the test would surface the drift immediately:

```bash
bash ~/.hermes/skills/cloud-build-bastion-watchdog/scripts/test_watchdog_exit4_on_handoff_fail.sh
```

## Fix recipe (for the operator / next deploy)

1. Verify the script on disk matches the v1.2.0 contract:
   ```bash
   grep -nE 'HANDOFF_USERS=\( "git@\$HOST" "$USER@\$HOST" "cloud-build@\$HOST" \)' ~/.hermes/scripts/cloud-build-bastion-watchdog.sh
   grep -nE 'BASTION_OK && ENROLL_OK && !HANDOFF_OK' ~/.hermes/scripts/cloud-build-bastion-watchdog.sh
   ```
   Both should match.
2. If missing, re-apply the v1.2.0 handoff-user probe block from `references/probe-mismatch-bug-2026-07-20.md` ("The fix" section, lines 124-158 of the v1.2.0 script).
3. Run the contract test:
   ```bash
   bash ~/.hermes/skills/cloud-build-bastion-watchdog/scripts/test_watchdog_exit4_on_handoff_fail.sh
   ```
   Expect: PASS=7 FAIL=0 with Test 6 reporting `exit=4` (because the handoff users genuinely fail on this Mac).
4. Confirm the watchdog now reports exit=4 in `--notify` mode, not exit=0.

## Provenance

- Verified live 2026-07-20 22:38 PT on Mac (jeffreys-macbook-pro)
- Session context: Slack thread `C0AH3RY3DK6/1784584425.185909` (Visenya v9 brainstorm)
- Trigger: user asked "drive these PRs through /super"; agent loaded the watchdog, got exit=0, then probed handoff users inline and got `Permission denied` — exactly the bug the SKILL.md claims v1.2.0 catches
- Related session: Slack thread `C09GRLXF9GR/p1784582518.247009` (the v1.2.0 fix's original session)
