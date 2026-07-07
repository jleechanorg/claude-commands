---
name: dropped-messages/cron-staging-prod-drift-2026-06-17
description: The staging-vs-prod script drift trap — launchd plist runs ~/.hermes/scripts/, deploy.sh only syncs policy files, prod can be 5+ days stale. How to identify the right file to patch + how to catch up prod.
type: reference
---

# Cron staging-vs-prod script drift (2026-06-17)

> **Cross-reference (added 2026-06-17):** Before applying the shape-mismatch
> patch in `references/cron-gave-up-state-mismatch-2026-06-17.md`, check
> whether `~/.hermes/scripts/dropped-thread-followup.sh` (staging, the file
> launchd actually runs) already has the shape-tolerant `was_nudged_recently`
> + the `gave_up` short-circuit + per-channel cooldown + daily escalation
> thread. If yes, the bug is **staging-vs-prod script drift**, not a missing
> patch. The fix is `cp ~/.hermes/scripts/dropped-thread-followup.sh ~/.hermes_prod/scripts/dropped-thread-followup.sh`,
> NOT editing prod directly. (Verified 2026-06-17: staging was 1688 lines
> with all the fixes from PRs back to 2026-06-12; prod was 980 lines, 5+
> days stale. The agent initially patched prod; the right move was the
> cp-sync.)

## The trap

The agent diagnosed a "gave up loop" bug in the dropped-thread cron, patched
`~/.hermes_prod/scripts/dropped-thread-followup.sh::was_nudged_recently`,
verified `bash -n` clean, ran a dry-run, and... the running cron (launchd
plist `ai.hermes.schedule.dropped-thread-followup`) was still using the
OLD code from `~/.hermes/scripts/dropped-thread-followup.sh` (staging).
The patch was in the wrong file. The cron kept re-pinging.

## The architecture

### launchd plist (the file the running cron actually uses)

```xml
<!-- ~/Library/LaunchAgents/ai.hermes.schedule.dropped-thread-followup.plist -->
<key>ProgramArguments</key>
<array>
  <string>/bin/bash</string>
  <string>$HOME/.hermes/scripts/dropped-thread-followup.sh</string>
</array>
```

Note: STAGING (`~/.hermes/scripts/`), NOT prod (`~/.hermes_prod/scripts/`).

### deploy.sh — what it actually syncs

`~/.hermes/scripts/deploy.sh` Stage 4.5 ("Policy Sync") syncs ONLY policy files:

```bash
# deploy.sh:144-181
POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md)
for f in "${POLICY_FILES[@]}"; do
  src="$REPO_DIR/$f"      # = ~/.hermes/$f
  dst="$PROD_DIR/$f"      # = ~/.hermes_prod/$f
  ...
done
```

It does NOT sync `scripts/`. Prod scripts can be 5+ days stale vs staging.

### The drift is silent

The cron runs without errors, but it's running the older code. The agent
only sees the bug as "I patched it, why is it still broken?"

## The recipe

1. **Find the file the plist actually runs:**
   ```bash
   plutil -p ~/Library/LaunchAgents/ai.hermes.schedule.<label>.plist | grep -A1 ProgramArguments
   ```
   For dropped-thread, it's `~/.hermes/scripts/dropped-thread-followup.sh`.

2. **Compare with prod:**
   ```bash
   diff ~/.hermes/scripts/dropped-thread-followup.sh ~/.hermes_prod/scripts/dropped-thread-followup.sh | head -20
   ```
   If they differ, prod is stale.

3. **Patch the staging file** (the one the cron actually uses), NOT prod.
   Staging is git-tracked; the diff is reviewable.

4. **To catch up prod** (so `DRY_RUN=1 bash ~/.hermes_prod/scripts/...`
   agrees with staging):
   ```bash
   cp ~/.hermes/scripts/dropped-thread-followup.sh ~/.hermes_prod/scripts/dropped-thread-followup.sh
   ```
   This is a one-shot filesystem operation, NOT a `deploy.sh` operation.

5. **Always verify BOTH paths produce the same dry-run output** before
   claiming the fix is live. The cron uses staging, but agent-side
   audits often invoke prod directly:
   ```bash
   DRY_RUN=1 DROP_LOOKBACK_HOURS=72 DROP_CHANNELS="<chan>" \
     bash ~/.hermes/scripts/dropped-thread-followup.sh
   DRY_RUN=1 DROP_LOOKBACK_HOURS=72 DROP_CHANNELS="<chan>" \
     bash ~/.hermes_prod/scripts/dropped-thread-followup.sh
   # Both should print the same SKIP / OK lines for each thread.
   ```

## Verified 2026-06-17

Staging `~/.hermes/scripts/dropped-thread-followup.sh`: 1688 lines, last
modified via PRs back to 2026-06-12 (had `gave_up` short-circuit, per-channel
cooldown, daily escalation thread routing, LLM classification via Hermes
gateway, all `fix(dropped-thread)` improvements).

Prod `~/.hermes_prod/scripts/dropped-thread-followup.sh`: 980 lines, last
modified 2026-06-12 (5+ days stale, missing all of the above improvements).
The agent's earlier "patch" to prod was doubly wrong — it patched the wrong
file, AND it didn't catch up prod with staging's many other improvements.

Fix: `cp ~/.hermes/scripts/dropped-thread-followup.sh ~/.hermes_prod/scripts/dropped-thread-followup.sh` + dry-run verify on both paths.

## Generalization

The `~/.hermes/` → `~/.hermes_prod/` divide is a **policy-file pipeline**,
not a **code-pipeline**. The deploy workflow is for SOUL.md/AGENTS.md/TOOLS.md/
HEARTBEAT.md (rules the gateway reads), not for shell scripts. Scripts in
`~/.hermes/scripts/` are the canonical source for everything launchd runs;
`~/.hermes_prod/scripts/` is just a deployment target that the operator (or
a manual `cp`) is responsible for keeping in sync. Treat any staging-vs-prod
script drift as a maintenance bug, not a deploy bug.

## How to recognize this trap in a new session

Symptom: agent patches a script in `~/.hermes_prod/scripts/...`, the
dry-run shows the fix works, but the cron (or any other launchd-managed
process) is still running the old code.

Quick check: `diff ~/.hermes/scripts/<script> ~/.hermes_prod/scripts/<script>`.
If they differ, the patch is in the wrong file (or prod is stale).
