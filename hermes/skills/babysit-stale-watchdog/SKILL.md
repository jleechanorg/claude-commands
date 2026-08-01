---
name: babysit-stale-watchdog
description: Detect enabled babysit crons whose referenced PR is MERGED or CLOSED and disable them. Companion to the in-script `is_pr_terminal()` check in babysit.py. Without this watchdog, babysit crons can run hundreds of polls for weeks after the PR they were guarding has merged or closed.
trigger: "Run every 30 min via launchd. Also manually via `python3 ~/.hermes/scripts/babysit_stale_watchdog.py`."
---

# 🚨 IF YOU ARE READING THIS BECAUSE THE USER ASKED WHY A THREAD IS FULL OF CRON SPAM, JUMP TO `references/echo-loop-stale-babysit-recovery.md` FIRST 🚨

The recovery recipe there is the single-call cleanup. Do not read the rest of this SKILL.md until the babysit is cancelled and the thread is quiet. Companion skill for the loop half: `gateway-loop-standdown` (read its top-of-file warning before posting any reply in that noisy thread).

---

# babysit-stale-watchdog

## Why

Bug-ref: 2026-07-03 — `babysit-wa-2403-PR7711` fired **251 polls over 11 days** after PR #7711 merged. The original `babysit.py` only recognized "PR created" (a worker output event) as terminal, not "PR MERGED on GitHub" (an external event). The cron kept spamming Slack with "TERMINAL: merged" pings until Jeffrey noticed.

## What

Two-layer fix:

1. **In-script** (`babysit.py` `is_pr_terminal()`): poll() now extracts any PR ref from the task_summary, calls `gh pr view --json state`, and if the PR is MERGED or CLOSED, posts one terminal message and exits the babysit loop. **19/19 tests pass.**

2. **Watchdog** (`babysit_stale_watchdog.py`): belt-and-suspenders. Runs every 30 min via launchd. Even if `babysit.py` is broken or running against an old prompt, the watchdog catches the stale job and disables it within 30 min. **9/9 tests pass.**

## Install

```bash
# 1. Copy template to deployed plist (substitute @HOME@)
cp ~/.hermes/launchd/ai.hermes.schedule.babysit-stale-watchdog.plist.template \
   ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist

# 2. Verify syntax
plutil -lint ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist

# 3. Load + start
launchctl load -w ~/Library/LaunchAgents/ai.hermes.schedule.babysit-stale-watchdog.plist
launchctl kickstart -k gui/$(id -u)/ai.hermes.schedule.babysit-stale-watchdog

# 4. Verify it's running
launchctl list | grep babysit-stale-watchdog
tail -5 ~/.hermes/cron/output/babysit-stale-watchdog.log
```

## Verify

```bash
# Run once manually
python3 ~/.hermes/scripts/babysit_stale_watchdog.py

# Run unit + e2e tests
python3 ~/.hermes/scripts/tests/test_babysit_stale_watchdog.py    # 9 tests
python3 ~/.hermes/skills/ao-babysit/scripts/test_babysit_pr_exit.py  # 19 tests
```

## Files

- `~/.hermes/scripts/babysit_stale_watchdog.py` — the watchdog
- `~/.hermes/scripts/tests/test_babysit_stale_watchdog.py` — 9 tests
- `~/.hermes/skills/ao-babysit/scripts/babysit.py` — restored + patched with `is_pr_terminal()`
- `~/.hermes/skills/ao-babysit/scripts/test_babysit_pr_exit.py` — 19 tests
- `~/.hermes/launchd/ai.hermes.schedule.babysit-stale-watchdog.plist.template` — committed plist template

## Pitfalls

- **`babysit.py` was deleted** in commit `4a7befcfa4` (squash-merge of feat/hermes-agent-default into main) — only the .pyc survived. Every cron prompt that referenced `python3 ~/.hermes/skills/ao-babysit/scripts/babysit.py poll ...` was failing silently. **Restored from `git show 4a7befcfa4^:skills/ao-babysit/scripts/babysit.py`** plus the new merged-PR check.
- **Default repo for bare `PR #NNNN` refs**: defaults to `$GITHUB_REPOSITORY` since that's the most common babysit target (5 of 5 in the 2026-07-03 sweep). If babysits for other repos get created, the URL form `https://github.com/o/r/pull/N` is exact — prefer that.
- **Parked-handoff end-state (worker never spawned)** — see `references/worker-not-spawned-parked-handoff.md` for the three-way check (session + PR + operator reply) and the verbatim cancel recipe. Verified 2026-07-22 on cron `5a771c731157` (thread `C0AH3RY3DK6/p1784721612.183329`); this is the third end-state the watchdog catches, alongside PR-MERGED and PR-CLOSED.
- **gh failures fall through to "not terminal"** — if `gh` is down or rate-limited, the watchdog leaves the job enabled rather than disabling it. The in-script `is_pr_terminal()` has the same fallback.
- **`cronjob` CLI may not exist on PATH** (verified 2026-07-31, thread C09GRLXF9GR/p1784235989.925899): the recovery recipe in `references/echo-loop-stale-babysit-recovery.md` assumes `cronjob action=remove job_id=<id>` works, but `cronjob` returned `command not found` from the gateway session. `~/.hermes/scripts/cronjob*` files absent, `hermes_tools` Python module not importable. When the recovery recipe's `cronjob` invocation fails, fall back in this order: (a) `launchctl bootout gui/$(id -u)/ai.hermes.schedule.cronjob-<name>` if the babysit runs under a named launchd plist; (b) look for a cronjob dispatcher under `~/.local/bin/`, `~/.hermes/bin/`, or `~/bin/` — many Hermes installs put it there rather than on PATH; (c) ask the user to type `stop reminder <babysit-name>` in-thread (the babysit prints this hint itself); (d) treat the babysit as an external system you cannot cancel and focus on the closeout post instead. Do NOT loop on "tool not found" — pick one fallback, post the closeout, and stop.
- **Watchdog is silent by design**: only writes a log line when a job gets disabled. No daily digest.
- **Watchdog requires the launchd plist to be installed AND loaded.** If the plist is missing from `~/Library/LaunchAgents/`, every check is a no-op — babysit crons will spam forever after their PR terminal-states. Verified 2026-07-31: cron `wa-pr-8466-babysit` (job `124ad03896f5`) was still firing ~40 rate-limit-error polls/day into the user's real Slack thread 7+ days after [PR #8466](https://github.com/$GITHUB_REPOSITORY/pull/8466) merged on 2026-07-24. The skill's "Install" section above is required, not optional. Verification recipe: `launchctl list | grep babysit-stale-watchdog` MUST return a row; `tail -5 ~/.hermes/cron/output/babysit-stale-watchdog.log` MUST show a recent heartbeat. If either check fails, the watchdog is silently broken and stale babysits will run indefinitely. This is the canonical failure mode for the cron spam pattern; do not assume the watchdog is active just because the skill file exists.
- **Babysit `gh pr view` failures are NOT terminal-state signals.** When the babysit's own `gh pr view` call returns "rate limited" / "could not fetch", the in-script `is_pr_terminal()` falls through to "not terminal, keep polling." This is correct for the babysit (don't spuriously exit on a transient gh failure) but combined with a missing watchdog it produces an unbounded poll storm. The fix for that storm is installing the watchdog (previous pitfall) — not patching `babysit.py` to treat gh failures as terminal, which would cause false-exits on legit transient blips. Verified 2026-07-31: cron `124ad03896f5` fired every ~1h with "could not fetch PR 8466 state gh may be rate-limited" for 7 days straight.
- **Auto-merge cron while PR is alive but user has explicitly required human `MERGE APPROVED`** (added 2026-07-21, PR #8462 thread C0BCVG4F560/1784219487): The watchdog currently watches only terminal-state transitions (MERGED / CLOSED). A different alive-but-deferred failure mode exists: you arm a one-shot "merge the PR once green" babysit cron, then the user posts an update containing an explicit human-approval gate (`"NOT auto-merging. Waiting for \`MERGE APPROVED\`"`, `"need your signoff before merge"`, `"don't merge until I review"`). The PR is still OPEN and mergeable, but the original auto-merge intent is now superseded. Symptom pattern: the cron will run its full polling cycle (e.g. +30m) and execute the merge step on its own, which is exactly what the user just told you NOT to do. **Recipe:** every babysit prompt that the operator armed with auto-merge intent MUST re-check the originating thread for a "waiting for <token> APPROVED" / "no auto-merge" / "manual approval required" phrase BEFORE executing the merge step. If found, post a single-line acknowledgment in thread and `hermes cron remove <id>` immediately (same self-cancel discipline as terminal-state). Do NOT wait for the watchdog — the PR is alive, the merge is the disputed action, and the cron has minutes not days. Bug-ref thread C0BCVG4F560/1784580796.416199 — agent armed `babysit-pr-8462-green` cron `a679edc9079d` with auto-merge intent on green, then user (Jeffrey) posted "NOT auto-merging. Waiting for `MERGE APPROVED`" 7 minutes later. Cron was deleted manually before it fired; the live `verify-pr-8462-rollout` +24h cron was correctly left armed because it only fires post-merge.

- **Echo-loop + stale babysit recovery (added 2026-07-31, thread C09GRLXF9GR/p1784235989.925899, cron `124ad03896f5`)**: When a stale babysit cron is actively polluting the user's Slack thread AND the user's recent messages are gateway echoes of prior assistant turns with no new imperative content, **cancel the babysit IMMEDIATELY** via `cronjob action=remove job_id=<id>`. Do not wait for "go." The user's silence IS the answer because they cannot see new messages while the babysit is spamming. Then post ONE short closeout reply and stop replying. Full recipe + verification: see `references/echo-loop-stale-babysit-recovery.md`. Companion skill: `slack-thread-echo-loop-recognition` Tier 2 covers the echo-loop detection half.

- **Worker never spawned — three-way end-state check (added 2026-07-22, thread C0AH3RY3DK6/p1784721612.183329, cron `5a771c731157`)**: A babysit cron can fire while the worker it was supposed to be polling was never actually created. This is the third end-state the watchdog cares about — neither "PR MERGED" nor "PR CLOSED" but `worker_not_spawned_parked_handoff`. Symptom pattern: previous session left re-spawn attempts in `/tmp/wa-failures/2026-07-22/ao-spawn.log` showing `INTERNAL_ERROR` / `PROMPT_TOO_LONG` / daemon executor pool hard-fault, with a stale `/tmp/wa-failures/2026-07-22/ao-spawn-cmd.sh` re-spawn script on disk; the worker was supposed to be named `fix-daily-0722` but `ao session ls | grep fix-daily-0722` returned zero rows; the matching PR with head `fix-daily-0722` did not exist (`gh pr list --head <branch>` empty); and the originating thread had no `U09GH5BR3QU` reply to the previous session's "your call" A/B/C question. **Recipe — three-way end-state check before posting the babysit status reply:**
  1. `ao session ls 2>&1 | grep <expected-session-name>` — zero hits means worker never spawned.
  2. `gh pr list --repo <repo> --head <expected-branch> --json url,state,headRefName,additions,changedFiles` — empty means no PR exists.
  3. If both 1 and 2 hit AND the originating thread has zero user replies since the A/B/C hand-off was posted, the previous session's caller went silent → state is `worker_not_spawned_parked_handoff`.
  4. Post the standard 1-line status to the originating thread (`Worker still iterating; no PR yet. (Cron <id> — no <expected-session-name> AO session exists; <root-cause-from-prior-session>; user A/B/C decision never received. Self-cancelling this cron.)`) and `hermes cron rm <id>` immediately. Do NOT loop. Do NOT re-spawn. Do NOT post a separate "investigation" message. The cron firing IS the investigation; the parked-handoff is the end-state.
  5. The PR-watching baby still has value if the operator manually re-spawns — but that is a fresh `ao spawn` invocation, not a babysit continuation. New work = new cron, not the old one reanimated.
  This is distinct from the "auto-merge superseded by human-approval gate" pitfall: there the PR is alive and mergeable. Here the worker and PR both never existed. The silent-operator signal is the same — both recipes pivot on zero user replies since the last hand-off question — but the cancel reason and the in-thread message text differ. Bug-ref: cron `5a771c731157` self-cancelled cleanly after posting ts `1784763797.688999` with the parked-handoff text; AO daemon pool had later recovered (no ghost sessions in DB; 12 sessions created since restart but none matching `fix-daily-0722`), but the originating hand-off question was already 26h old with zero replies.

## Companion pattern — no-agent hermes cron PR watchdog

For PRs that don't need an AO worker babysit, use `hermes cron create --no-agent --script <watch-script>.sh` to run a bash polling script on a fixed cadence. The script exits silently except on state transitions (OPEN with failures / OPEN with all-green / MERGED / CLOSED). Zero LLM tokens burned, instant state-transition pings to a Slack thread. See `references/no-agent-hermes-cron-pr-watchdog.md` for the full recipe plus the verified worked example (PR 8466 cron 124ad03896f5, 2026-07-20).

The script writes MERGED/CLOSED to its state file and exits 0; the launchd babysit-stale-watchdog cron disables the stale cron within 30 min via this skill.

## First-time investigation recipe (when you arrive at a thread that's already full of babysit noise)

If a user surfaces a thread where a babysit cron has been spamming rate-limit errors for days/weeks (the cron is stale, the PR is already MERGED/CLOSED, but nobody canceled the cron), use `references/stale-babysit-investigation-recipe.md` for the 5-step investigate → cancel → verify recipe. Verified 2026-07-31 (cron `124ad03896f5`, ~40 noise posts/day for 7 days).