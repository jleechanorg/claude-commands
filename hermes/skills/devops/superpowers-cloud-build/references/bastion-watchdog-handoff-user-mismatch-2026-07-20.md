# bastion-watchdog reports green while /super is broken — verified 2026-07-20

**One-line:** `~/.hermes/scripts/cloud-build-bastion-watchdog.sh` accepts `cloud-bastion@` and `enroll@` banners as auth-OK, but neither of those users gates the real `/super` handoff. The actual handoff uses `$USER@` / `git@` / `cloud-build@` — which the watchdog **never probes**. Result: watchdog exits 0 while `/super` is `Permission denied (publickey)`.

## Reproduction (Mac, 2026-07-20 22:18 PT)

```bash
# Watchdog reports green:
$ bash ~/.hermes/scripts/cloud-build-bastion-watchdog.sh
[2026-07-20T22:17:45Z] === cloud-build bastion watchdog ===
[2026-07-20T22:17:45Z] known_hosts fingerprint OK (sha256:uIogunmqBg/yisJwDP3uHHzJ0ualJ9t2EucfrwjxzaQ)
[2026-07-20T22:17:46Z] bastion auth probe OK (banner: cloud-bastion: interactive shell is not permitted)
[2026-07-20T22:17:46Z] enroll probe OK (banner: enroll: invalid or expired token — key still trusted on enroll path)
[2026-07-20T22:17:46Z] last_enrollment_check age: 4 days (warn at 6)
[2026-07-20T22:17:46Z] verdict: exit=0 (0=healthy 1=auth-fail 2=known_hosts-drift 3=age-warn)
exit=0

# But the actual handoff user returns Permission denied:
$ timeout 8 ssh -i ~/.ssh/cloud-build/id_ed25519 \
    -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
    -o ConnectTimeout=8 -o BatchMode=yes \
    -T '$USER@cloud.superpowers.build'
$USER@cloud.superpowers.build: Permission denied (publickey).

$ timeout 8 ssh -i ~/.ssh/cloud-build/id_ed25519 \
    -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
    -o ConnectTimeout=8 -o BatchMode=yes \
    -T 'git@cloud.superpowers.build'
git@cloud.superpowers.build: Permission denied (publickey).
```

The local key fingerprint `SHA256:8cZsH7MRG...` (later rotated to `f1c66c1fb3...`) did NOT match the enrolled fingerprint in `~/.config/cloud-build/state.json` (`c709569c7b...`). The key was regenerated locally after the last enrollment (4 days old, never re-enrolled). The watchdog's two probe users (`cloud-bastion@` for non-command auth, `enroll@` for the re-enroll path) have different authorization than the actual handoff users — so the watchdogs see green while every real `/super` call fails.

## Why this matters

The watchdog is invoked from TWO places:

1. `~/Library/LaunchAgents/ai.hermes.schedule.cloud-build-bastion-watchdog.plist` — every 12h. If it reports healthy, no Slack alert fires.
2. Manually via `bash ~/.hermes/scripts/cloud-build-bastion-watchdog.sh --notify` before every `/super` dispatch (per SOUL.md `## COMMIT: cloud-build-bastion-watchdog-always-on`).

Both paths return `exit=0` while `/super` is genuinely broken. The dispatch helper then hits `Permission denied (publickey)` mid-handoff with no useful error message, and the operator has to debug from a cryptic SSH stderr instead of seeing the watchdog scream. That's exactly the failure class `## COMMIT: cloud-build-bastion-watchdog-always-on` was created to prevent — but the watchdog doesn't catch it.

## Fix (recipe) — SHIPPED in `cloud-build-bastion-watchdog` v1.2.0 (2026-07-20)

**Status:** This recipe was the proposed fix in v1.4.0 of this umbrella skill. **As of 2026-07-20 22:21 PT, the recipe has been shipped in `cloud-build-bastion-watchdog` v1.2.0.** The script now iterates THREE handoff users (`git@`, `$USER@`, `cloud-build@`) instead of just `$(whoami)@`, returns a new exit code 4 (`handoff-fail-with-banner-ok`), and is verified live on this Mac (7/7 contract tests pass). Future agents can rely on the watchdog's exit code: 0 = all 6 probes pass; 4 = banner-OK but handoff-fail; re-enrollment required. For the full shipped version + transcripts, see:

- `~/.hermes/skills/cloud-build-bastion-watchdog/references/probe-mismatch-bug-2026-07-20.md` — the canonical reference for the shipped fix
- `~/.hermes/skills/cloud-build-bastion-watchdog/scripts/test_watchdog_exit4_on_handoff_fail.sh` — the contract test that verifies exit=4 fires when the bug recurs

The original proposed fix (preserved below for reference — the shipped version is a strict superset):

**Probe the actual handoff user**, not the auth-banner users. The real handoff user is whatever the dispatch helper resolves via `cloud_build_git_ssh_command` — empirically `$USER@` on this Mac (and likely `git@` on the box side). Two complementary additions to the watchdog:

```bash
# ---- 2.5 real handoff-user probe (the actual /super auth gate) ------------
# cloud-bastion@ and enroll@ are NOT the handoff users — the dispatch helper
# (cloud_build_git_ssh_command) actually pushes to <current_user>@cloud.superpowers.build
# (which on this Mac is $USER@; on a different identity would be different).
# Without probing that user, the watchdog reports green while /super is red.
HANDSHAKE_USER="$(whoami)"
HANDOFF_BANNER="$(ssh -i "$IDENTITY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" -o ConnectTimeout=8 -o BatchMode=yes \
  -T "${HANDSHAKE_USER}@$HOST" 2>&1 || true)"
if [[ "$HANDOFF_BANNER" == *"Permission denied (publickey)"* ]]; then
  log "ERROR: handoff user ${HANDSHAKE_USER}@$HOST got Permission denied — key pruned or never enrolled"
  HANDOFF_OK=0
elif [[ -z "$HANDOFF_BANNER" ]]; then
  log "ERROR: handoff user ${HANDSHAKE_USER}@$HOST unreachable"
  HANDOFF_OK=0
else
  log "handoff probe OK for ${HANDSHAKE_USER}@$HOST (banner: $(echo "$HANDOFF_BANNER" | head -1))"
  HANDOFF_OK=1
fi
```

Then surface the new verdict in the exit logic:

```bash
EXIT=0
if (( !BASTION_OK || !ENROLL_OK || !HANDOFF_OK )); then EXIT=1; fi
(( AGE_WARN == 1 )) && (( EXIT == 0 )) && EXIT=3
```

## Verification — what "fixed" looks like

1. **Local key fingerprint matches `enrolled_fp_hash`** in `~/.config/cloud-build/state.json`:
   ```bash
   LOCAL_FP=$(python3 -c "import hashlib,base64; pub=open('$HOME/.ssh/cloud-build/id_ed25519.pub').read().strip(); print(hashlib.sha256(base64.b64decode(pub.split()[1])).hexdigest())")
   ENROLLED_FP=$(python3 -c "import json; print(json.load(open('$HOME/.config/cloud-build/state.json'))['enrolled_fp_hash'])")
   [[ "$LOCAL_FP" == "$ENROLLED_FP" ]] && echo MATCH || echo MISMATCH
   ```
   If `MISMATCH`, the user must run `bash ~/superpowers-cloud-build-main/skills/cloud-build/scripts/cb-client-setup.sh` with a fresh enrollment code.
2. **The new handoff-user probe line appears** in the watchdog log:
   `handoff probe OK for $USER@cloud.superpowers.build`
3. **`/super` actually dispatches** — full smoke test via the hello-world recipe (`references/hello-world-validation-2026-07-17.md`).

## Why the agent must probe this BEFORE trusting the watchdog

Two failure modes the current watchdog does not catch:
- Local key regenerated after enrollment (`ssh-keygen` produces a new fp; state.json's `enrolled_fp_hash` does not auto-update).
- Bastion pruned `authorized_keys` for the handoff user but kept the auth-banner users.

Both produce "watchdog green, /super red" — the worst kind of silent lie. The probe in `## Fix` above closes both gaps.

## Workaround when the fix isn't applied yet

```bash
# Before any /super dispatch, prove the handoff user works:
timeout 8 ssh -i ~/.ssh/cloud-build/id_ed25519 -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
  -o ConnectTimeout=8 -o BatchMode=yes -T "$(whoami)@cloud.superpowers.build"
# Expect: Permission denied → STOP and surface to user (do not auto-re-enroll).
# Expect: a banner like "cloud-bastion: only git fetch/push/archive is permitted" → safe to dispatch.
```

## Source provenance

Verified failure mode — 2026-07-20, Slack thread `C09GRLXF9GR/p1784582518.247009`. Operator said "/super should work now"; probe proved it didn't. Root cause: the watchdog only verifies the auth-banner paths, not the actual SSH user the dispatch helper uses. Same root cause class as the prior 2026-07-16 host-key rotation failure documented in `## COMMIT: cloud-build-bastion-watchdog-always-on` — but a different bug, in the same script. Filed as a follow-up bead (separate concern from the upstream-port work).

## Cross-references

- `superpowers-cloud-build` SKILL.md (this skill) — Anti-pattern entry covering the watchdog bug
- `references/hello-world-validation-2026-07-17.md` — the canonical /super smoke test (run AFTER applying the watchdog fix to prove it actually catches this)
- `## COMMIT: cloud-build-bastion-watchdog-always-on` in `~/.hermes/workspace/SOUL.md` — the rule that mandates running the watchdog before every /super dispatch; the bug above is in the watchdog itself, not in the rule.