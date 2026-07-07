# AO spawn rejected: 20 active sessions >= cap — kill-zombie + cap-override recipe (added 2026-07-04, PR #8139 dispatch)

## Symptom

`ao spawn -p <project>` rejects with:
```
- Creating session
✖ Failed to create or initialize session
✗ Spawn rejected: 30 active sessions >= cap (30). Set AO_MAX_CONCURRENT_SESSIONS
  env var to increase. Wait for sessions to complete.
```

but `ao session ls` shows the active project has only 1–3 `wa-*`/`jc-*` etc. sessions actually working, with most of the others stuck in `[spawning]` for hours/days (zombies from prior cron runs, abandoned dispatches, killed AO worker panes that did not propagate status to the orchestrator's session table).

## Verify zombies are blocking

```bash
cd ~/.openclaw
env -i HOME="$HOME" PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$HOME/.local/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  bash -c "~/bin/ao session ls 2>&1" | grep -cE '^  [a-z0-9_-]+'
```

If the count is much higher than the number of truly running tmux panes (compare with `tmux ls | grep -E 'wa-|jc-|agento|agy'`), the rest are zombies.

## Two-step resolution

**Step 1 — kill the zombies** (check the session is actually dead before killing, do not blindly batch-kill):
```bash
# Identify orphan sessions (created days ago, still 'spawning')
cd ~/.openclaw
env -i HOME="$HOME" PATH="..." bash -c "~/bin/ao session ls 2>&1" \
  | grep -E '^  wa-[0-9]+|jc-[0-9]+|ao-[0-9]+' | grep '(1d ago|2d ago|\\d+d ago)' | awk '{print $1}' \
  | xargs -I{} env -i HOME="$HOME" PATH="..." bash -c "~/bin/ao session kill {} 2>&1 | tail -1"
```

**Step 2 — raise the cap** (the org-level default is 30):
```bash
AO_MAX_CONCURRENT_SESSIONS=40 \
env -i HOME="$HOME" PATH="..." GH_TOKEN="$(gh auth token)" AO_BOT_GH_TOKEN="$(gh auth token)" \
  bash -c "~/bin/ao spawn -p <project> --agent antigravity '<task>'"
```

Note: the cap is read from environment variable `AO_MAX_CONCURRENT_SESSIONS`, NOT a flag on the spawn CLI.

## Why this happens

The orchestrator's session table is updated when a session reaches a terminal state (`completed`, `failed`, `killed`) via the lifecycle polling worker. Self-hosted runner flakiness, dropped ssh connections, killed tmux panes that weren't properly tombstoned, and abandoned cron dispatches all leave zombie rows in the session table. There is no daemon-side automatic reaper (no cron, no launchd plist prunes stale rows). Until that exists, the work-around is manual.

## Long-term fix (not in scope for a single /green dispatch)

Reaper script + launchd plist that polls `ao session ls` every 30 min and kills sessions older than 4h whose state is still `[spawning]`. Track as a separate bead — don't bundle into PR-driving tasks.

## Reference

Verified 2026-07-04 during PR #8139 dispatch: 24 zombie wa-30xx sessions in the table, ~3 actually alive; killed 3 stale `wa-3076/3077/3079` (1d-old `stuck` state) and spawned with `AO_MAX_CONCURRENT_SESSIONS=40`. Spawn succeeded on first try after zombies were killed (the cap raise was not even needed — but kept for resilience).
