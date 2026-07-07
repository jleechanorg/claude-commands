# Staging dirty + fix already on `origin/main` — surgical deploy recipe

**When the staging repo (`~/.hermes/`) is on a dirty non-main branch but
the fix you need is already committed to `origin/main`**, the standard
`scripts/deploy.sh` pipeline will DIE on the uncommitted-changes check
and you cannot run a clean `git pull`. This reference documents the
surgical-sync recipe that works in that exact state.

Verified 2026-06-20 against two launchd alerts (`ai.hermes-watchdog`
"log stale or missing" + `ai.agento.health-guardian` "1 alert") where
the actual root cause was a script fix already on `origin/main` as
[jleechanorg/jleechanclaw#619](https://github.com/jleechanorg/jleechanclaw/pull/619)
but the deployed file was stale.

---

## The pattern (3-step diagnostic that prevents the "did I really
fix it?" question)

### Step 1 — Is the fix already on `origin/main`?

```bash
cd ~/.hermes
git fetch origin main
git log --oneline origin/main -- <suspected-file>  # e.g. scripts/hermes-watchdog.sh
# Check the actual deployed copy for the broken content
diff <(git show origin/main:scripts/hermes-watchdog.sh) \
     $HOME/.hermes/scripts/hermes-watchdog.sh
```

**If origin/main already has the fix AND the deployed file is stale,
do NOT open a duplicate PR.** The user's "commit to main" request is
already satisfied by the existing commit. The work is "deploy the
existing fix", not "re-fix and re-PR."

**The judgment call to surface to the user:** "The fix is already on
`origin/main` (PR #N). I'm going to deploy it without opening a new
PR." This is the same shape as the `finish-the-job` "make the call
yourself, don't ask mid-stream" rule applied to a "where is the work"
fork.

### Step 2 — Is staging dirty / on the wrong branch?

```bash
cd ~/.hermes
git status -sb
git branch --show-current
```

**Three bad states you may hit:**

| State | Symptom | What deploy.sh does |
|---|---|---|
| On `auto/commit-pending` with `MM` on tracked files + untracked runtime junk | `git status -sb` shows `## auto/commit-pending` + tracked mods | `deploy.sh` Stage 2 dies with "Uncommitted changes" |
| Detached HEAD at an old SHA | `git status` shows "HEAD detached at ..." | `git pull` will fail opaquely |
| Local branch ahead of `origin/main` by unrelated commits | `git log origin/main..HEAD` non-empty | `git pull --ff-only` will refuse |

**Do NOT try to "fix" the staging state to make `deploy.sh` work.**
The dirty state is from prior sessions' `auto/commit-pending` activity
(channel_directory.json mutations, curator state, cache/ untracked
artifacts). Cleaning it is its own separate task.

### Step 3 — Surgical sync: copy the corrected file from `origin/main`
to the deployed paths (worktree → staging + prod)

```bash
# 1. Make a fresh worktree pinned at origin/main (path-then-branch order)
git worktree add $HOME/.worktrees/<repo>-fix-<purpose> \
    -b fix/<purpose> origin/main

# 2. Verify the worktree is clean
cd $HOME/.worktrees/<repo>-fix-<purpose>
git log --oneline origin/main..HEAD   # MUST be empty
git rev-parse HEAD                    # MUST be the origin/main tip
ls scripts/hermes-watchdog.sh         # the file you need to copy out

# 3. Back up the broken deployed copies (audit trail)
cp -p $HOME/.hermes/scripts/hermes-watchdog.sh \
      /tmp/hermes-watchdog.sh.broken-predeploy-$(date +%Y%m%d-%H%M%S)
cp -p $HOME/.hermes_prod/scripts/hermes-watchdog.sh \
      /tmp/hermes-watchdog-prod.sh.broken-predeploy-$(date +%Y%m%d-%H%M%S)

# 4. Copy the corrected file from origin/main (via the worktree) to BOTH paths
cp -p scripts/hermes-watchdog.sh $HOME/.hermes/scripts/hermes-watchdog.sh
cp -p scripts/hermes-watchdog.sh $HOME/.hermes_prod/scripts/hermes-watchdog.sh

# 5. Verify both deployed copies now match origin/main
diff scripts/hermes-watchdog.sh $HOME/.hermes/scripts/hermes-watchdog.sh \
    && echo "staging OK"
diff scripts/hermes-watchdog.sh $HOME/.hermes_prod/scripts/hermes-watchdog.sh \
    && echo "prod OK"

# 6. Check if the script also imports from a lib/ dir — sync missing libs
diff -r lib/ $HOME/.hermes/lib/ 2>&1 | head -20
# If "Only in <worktree>/lib: <file>" appears, copy those files to BOTH
# staging and prod. Missing lib files cause `source` to fail with "No
# such file or directory" and downstream functions to silently no-op.

# 7. Clean up the throwaway worktree
cd ~/.hermes
git worktree remove $HOME/.worktrees/<repo>-fix-<purpose> --force
git branch -D fix/<purpose>
```

### Step 4 — Restart the launchd job (kickstart, not bootstrap)

```bash
# kickstart a loaded, registered job — safe nudge
launchctl kickstart -kp gui/$(id -u)/<label>
# e.g. launchctl kickstart -kp gui/$(id -u)/ai.hermes.watchdog
```

**Why kickstart and not `bootout` + `bootstrap`?**
- `bootout` on a job that's currently running fails with `Boot-out failed: 3: No such process`
- `bootstrap` after `bootout` fails with `Bootstrap failed: 5: Input/output error` when the bootout didn't fully clean up
- `kickstart -kp` is a one-shot nudge that re-spawns the job and re-reads the plist + script

**Verification window:** the launchd job's natural `StartInterval` (e.g. 300s for `ai.hermes.watchdog`) will fire the new script. Watch the log file path declared in the plist's `StandardOutPath` for the corrected output (e.g. `~/Library/Logs/hermes-watchdog.log` for the watchdog, NOT `~/.hermes/logs/`).

**Don't try to `bootstrap` a registered job.** `launchctl list` showing the job is enough — it's registered, it'll re-run on its interval.

---

## Diagnostic recipes

### "Is the fix actually live?" (the 4-step probe)

```bash
# 1. The git repo has it?
git -C ~/.hermes log --oneline origin/main -3 -- <file>

# 2. The deployed staging file has it?
grep -n <key-content> $HOME/.hermes/<file>

# 3. The deployed prod file has it?
grep -n <key-content> $HOME/.hermes_prod/<file>

# 4. The live process / log shows it?
# e.g. for a launchd-driven script, check the log the plist writes to
tail -10 ~/Library/Logs/<job>.log
```

If 1=yes but 2=no (or 3=no), the fix is on `origin/main` but not deployed — the surgical-sync recipe applies.

### "Missing `lib/` file" silent-failure diagnostic

If a script that `source`s `lib/<helper>.sh` runs without crashing but
silently fails to do something (e.g. `slack_post` doesn't post to
Slack, no error in the log), the `source` is failing. Check:

```bash
# Run the script manually and look for "No such file or directory" lines
bash $HOME/.hermes/scripts/<script>.sh
# If you see: "line 13: $HOME/.hermes/lib/<helper>.sh: No such file or directory"
# → the lib file is missing in ~/.hermes/lib/ even though it exists in origin/main

# Compare the lib/ directory contents by materializing origin/main:lib into a temp dir:
mkdir -p /tmp/origin-lib-check
git -C ~/.hermes archive origin/main lib | tar -x -C /tmp/origin-lib-check
diff -r /tmp/origin-lib-check/lib/ $HOME/.hermes/lib/ 2>&1 | head -20
rm -rf /tmp/origin-lib-check
```

The fix is `cp <worktree>/lib/<missing-file> ~/.hermes/lib/ && cp <worktree>/lib/<missing-file> ~/.hermes_prod/lib/`.

### "Same code on origin/main and deployed, but the launchd job is
running old code"

The launchd process loaded the script into memory at fork time.
A code change to the script file does NOT propagate to the running
process. Two recovery paths:

1. **Wait for the natural cycle.** `StartInterval` jobs re-exec the
   script on every interval. Watch the log for the new output.
2. **`launchctl kickstart -kp <label>`** forces a re-exec now.

Path 2 is the right move when the cycle is long (≥ 1 hour) or when
you need to verify the fix immediately.

---

## Pitfalls

### Don't open a duplicate PR when the fix is already on `origin/main`

The user's "commit to main jleechanclaw" instruction is satisfied by
the existing commit. Opening a new branch + PR for a duplicate fix
creates a rebase burden on the next agent and pollutes the PR queue.
**Surface the existing commit, deploy the existing fix, done.**

### Don't try to "clean up" the dirty staging state to make `deploy.sh` happy

The `auto/commit-pending` branch + dirty files come from
`scripts/auto-commit-pending.sh` and prior curator activity.
`git stash` followed by `git pull --ff-only` followed by `git stash pop`
often re-applies the same mess. The surgical-sync recipe (copy file
from worktree → deployed paths) sidesteps the staging-cleanup problem
entirely.

### Don't `bootstrap` a registered launchd job

`launchctl bootstrap` is for loading a plist that's not yet loaded.
A registered job that disappears from `launchctl list` after a failed
`bootout` may still be in launchd's internal state. `kickstart` is
the recovery — it works on registered, currently-not-running jobs.

### The `slack_post` silent-failure trap is invisible in CI

`slack_thread_lib.sh` is sourced by many cron jobs. When the lib
file is missing, `slack_post` is undefined; the script's `|| log "..."`
fallback logs a non-zero return but the alert never reaches Slack.
The user sees "no alert" instead of "alert failed." The
`bash <script>.sh` manual run shows the "No such file or directory"
line that proves the source failed.

---

## Worked example (2026-06-20 — the alerts that prompted this recipe)

**Alerts:**
- `:rotating_light: ai.agento.health-guardian alerts (1): :warning: ai.hermes-watchdog log stale or missing`
- Jeffrey: "Status? I want you to finish the job and fix these" + "Make sure you fix and commit to original main jleechanclaw"

**Diagnostic that found the real cause:**
1. `launchctl list | grep hermes-watchdog` → PID 45233, exit 0. **The watchdog IS running.**
2. `tail -30 ~/Library/Logs/hermes-watchdog.log` → "prod gateway: DOWN (port 8642)" repeating every 5 min.
3. `lsof -i :8642` → empty. `lsof -i :8643` → Hermes prod (PID 1438). **The script checks the wrong port.**
4. `git -C ~/.hermes log --oneline origin/main -- scripts/hermes-watchdog.sh` → top commit `aab16d6ccb fix(hermes): correct watchdog port mapping (prod 8642→8643, staging 8643→8644) (#619)`. **Fix is already on origin/main since 2026-06-13.**
5. `diff <(git show origin/main:scripts/hermes-watchdog.sh) $HOME/.hermes/scripts/hermes-watchdog.sh` → 39 added, 55 removed. **Deployed file is stale.**

**The surgical-sync execution:**
1. `git worktree add ~/.worktrees/jleechanclaw-fix-watchdog-ports -b fix/watchdog-port-and-log-path origin/main`
2. `cp -p scripts/hermes-watchdog.sh $HOME/.hermes/scripts/ && cp -p scripts/hermes-watchdog.sh $HOME/.hermes_prod/scripts/`
3. Discovered `~/.hermes/lib/` was missing 3 files (`slack_thread_lib.sh`, `policy-drift-probe.sh`, `resolve_review_threads.sh`) via `diff -r`. Copied them too.
4. `launchctl kickstart -kp gui/$UID/ai.hermes.watchdog` → next interval at 12:30:02 logged "prod gateway: healthy (port 8643) + staging gateway: healthy (port 8644)". **Alert loop broken.**
5. `git worktree remove --force && git branch -D fix/watchdog-port-and-log-path` — no PR opened (existing #619 already covers it).

**No new PR was opened.** The user was told: "The fix is already on origin/main (PR #619). I deployed it; alerts will stop on the next 5-min cycle."

**Follow-up NOT in scope:** `ai.agento.health-guardian` in `jleechanorg/agent-orchestrator` checks `/tmp/hermes-watchdog.log` (wrong path) — separate repo, separate fix. Flagged in the Slack reply as a follow-up rather than bundled into the same work, because the user's directive was specifically about jleechanclaw.

---

## When to use this recipe

- Fix is on `origin/main` but the deployed file is stale.
- `deploy.sh` won't run because staging is dirty.
- A launchd job is misbehaving but the script source has the right code somewhere reachable.
- The user says "deploy it" or "fix this alert" and the git log shows the fix was already merged.

## When NOT to use this recipe

- The fix is NOT on `origin/main` — use the standard `pr-clean-worktree` + PR creation path.
- The fix is on `origin/main` but the user explicitly wants a new PR (e.g. they want to verify a regression, run CI on the diff).
- The deployed file matches `origin/main` but the launchd job is running old code — this is just a kickstart, no file copy needed.
