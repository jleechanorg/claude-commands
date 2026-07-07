# jleechanclaw — Slash Command + Trigger Phrase Rollout Recipe

**Verified 2026-06-20** against PR [`3f5adb80f5`](https://github.com/jleechanorg/jleechanclaw/commit/3f5adb80f5d0ba8738c6b460f6f8295acfaf2a5a) (add `/finish` + `/auto` + literal "finish the job" trigger phrase).

## The Three Wiring Points

A new trigger phrase or slash command on the `jleechanclaw` repo must be wired at THREE separate points to actually auto-fire. Missing any one breaks the path:

| # | File | What it does | If missing |
|---|---|---|---|
| 1 | `~/.hermes/.claude/commands/<name>.md` | Slash-command discovery (per SOUL.md "Slash Command Discovery" rule) | `/name <arg>` returns "command not found" |
| 2 | `~/.hermes_prod/skills/RESOLVER.md` | Natural-language phrase matching | Phrase doesn't load the skill even if user types it |
| 3 | `~/.hermes_prod/SOUL.md` `## COMMIT: <name>` Trigger line | Session-init scan that loads the skill on every conversation | Skill only fires on exact phrase, not on related goal-shaped messages |

**Always write to all three in the same turn.** The deploy script (`scripts/deploy.sh` Stage 4.5) only syncs `POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md)`, so:

- For **(1)** the slash command file: you must `cp -p ~/.hermes/.claude/commands/<name>.md ~/.hermes_prod/.claude/commands/` manually. The `deploy.sh` will NOT do this.
- For **(2)** the RESOLVER.md: edit the staging target first (`~/.hermes/skills/RESOLVER.md`), then sync/deploy to prod (`~/.hermes_prod/skills/RESOLVER.md`). The prod-only path is for emergency recovery only.
- For **(3)** the SOUL.md COMMIT: edit the staging target first (`~/.hermes/workspace/SOUL.md`), then sync/deploy to prod (`~/.hermes_prod/SOUL.md`). The prod-only path is for emergency recovery only.

## jleechanclaw Self-Merge Flow (vs your-project.com AO flow)

jleechanclaw uses a different merge pattern than your-project.com:

- **jleechanclaw** — Jeffrey merges by pushing a fresh `feat/<name>` branch to `main` directly. No human-review PR step. Use `git worktree add ~/.worktrees/<feat> -b feat/<name> origin/main` to keep your main checkout clean.
- **your-project.com** — AO workers open PRs, run `/green` loops, CodeRabbit reviews, evidence/skeptic gates, then merge.

Branch protection on `jleechanclaw` `main`:
- ✅ Force-push is **REJECTED** with `GH013: Cannot force-push to this branch`
- ✅ Non-fast-forward pushes are rejected — you must rebase or use a worktree-from-origin/main
- ❌ Do NOT use `git commit --amend` AFTER the initial push to `main` — you will be stuck with the original commit and unable to update it. Squash into the original commit BEFORE pushing.

## The auto/commit-pending Re-base Trap

The staging branch `auto/commit-pending` is often 1-2 commits behind `origin/main` with **regen-only** changes (timestamps on `docs/context/SYSTEM_SNAPSHOT.md`, `gateway_state.json`, etc.). Trying to rebase onto `origin/main` produces non-trivial merge conflicts on those regen files.

**The right move:** do NOT rebase. Use the worktree recipe:

```bash
cd ~/.hermes
git worktree add ~/.worktrees/<feat-name> -b feat/<name> origin/main
cd ~/.worktrees/<feat-name>
# ... make your changes here on a clean origin/main tip ...
git add <files>
git commit -m "<message>"
git push origin feat/<name>:main
git worktree remove ~/.worktrees/<feat-name>
```

After the push, bring the main checkout in sync:

```bash
cd ~/.hermes
git reset --hard origin/main
```

## Pre-Deploy Audit Checklist (10 items, run BEFORE pushing)

```bash
echo "1. SOUL.md in sync:" && diff -q ~/.hermes_prod/SOUL.md ~/.hermes/workspace/SOUL.md
echo "2. RESOLVER.md in sync:" && diff -q ~/.hermes_prod/skills/RESOLVER.md ~/.hermes/skills/RESOLVER.md
echo "3. slash cmds in prod:" && ls ~/.hermes_prod/.claude/commands/<name>.md
echo "4. slash cmds match staging:" && diff -q ~/.hermes/.claude/commands/<name>.md ~/.hermes_prod/.claude/commands/<name>.md
echo "5. SOUL.md trigger phrase:" && grep -c "<phrase>" ~/.hermes_prod/SOUL.md
echo "6. RESOLVER.md trigger phrase:" && grep -c "<phrase>" ~/.hermes_prod/skills/RESOLVER.md
echo "7. staging SHA == origin/main:" && [ "$(git -C ~/.hermes rev-parse HEAD)" = "$(git -C ~/.hermes rev-parse origin/main)" ] && echo OK
echo "8. gateway up:" && curl -sf http://127.0.0.1:8643/health
echo "9. lib files in prod:" && ls ~/.hermes_prod/lib/*.sh 2>&1 | head -5
echo "10. scripts executable:" && test -x ~/.hermes/scripts/<script>.sh && echo YES
```

## Canaries That Are Pre-existing False Negatives

`scripts/deploy.sh` canary check (`hermes-canary.sh`) sends a Slack message and waits for the bot to ack within 20s. Common reasons it fails UNRELATED to your SOUL.md change:

1. **`scripts/hermes-health.sh` checks port 8642, but the gateway runs on 8643.** This is the documented "deploy-script-port-drift-pitfall" — a known false negative. Pre-flight health-check shows "port:UNBOUND" even when the gateway is healthy.
2. **Slack WS / OpenRouter API key issues** — the canary may timeout waiting for the bot response even though the gateway processed the request. Look at the actual response payload in logs, not the timeout.
3. **High load average** — `loadavg:HIGH(83.52)` warnings are informational; the gateway is still serving.

**The deploy is NOT blocked by these canary failures** if the SOUL.md sync step ran successfully (`[ok] SOUL.md (in sync)`) and `curl http://127.0.0.1:8643/health` returns OK. Document the canary failure in your closure summary as a pre-existing issue, not a regression.

## The Post-Push Local Drift Problem

After pushing to `origin/main`, the staging checkout is now behind. If you `git fetch && git reset --hard origin/main`, you also lose any uncommitted local changes (the `auto/commit-pending` working tree has many untracked cache files and `lib/*.sh` files that the .gitignore doesn't cover).

**The clean sequence:**

1. Move untracked lib files to /tmp: `mkdir -p /tmp/hermes-stash-$$ && mv lib/*.sh /tmp/hermes-stash-$$/`
2. Reset: `git reset --hard origin/main`
3. Restore: `mv /tmp/hermes-stash-*/*.sh lib/`
4. Verify staging is clean: `git status` should show only the expected untracked cache files.

## Why This Is a Reference, Not Just a SKILL.md Bullet

The SKILL.md captures the high-level gotchas (`.claude/commands/` not in POLICY_FILES, `workspace/` gitignore trap, force-push rejection). This reference captures the **end-to-end recipe** with the exact command sequence and the jleechanclaw-specific branch-flow. Future sessions doing a slash-command rollout on jleechanclaw can follow the 10-item audit + the worktree recipe + the post-push drift sequence without rediscovering each step.
