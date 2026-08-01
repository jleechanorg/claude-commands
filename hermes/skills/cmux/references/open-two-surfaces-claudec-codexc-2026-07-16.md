# Open two new surfaces in an existing workspace (claudec + codexc)

Verified recipe for the user request: *"use the cmux skills to reopen the fable iOS app workspaces/surfaces and make one surface run claudec and one run codexc"*.

**Session:** 2026-07-16 07:07 PT — workspace:12 "fable: ios app" (workspace id `D114DA05-7755-4899-8A83-41AAA6EF296E`), pane:15, worktree `$HOME/project_worldaiclaw/worldai_claw`, branch `feat/mobile-architecture-cleanup`, PR [#256](https://github.com/jleechanorg/worldai_claw/pull/256).

## Socket + aliases (canonical, verified)

- Live socket: `/tmp/cmux-debug-dev-fork.sock` (only live session on 2026-07-16 — multi-socket probe confirmed; pointer file `$HOME/.local/state/cmux/dev-dev-fork-last-socket-path`).
- `claudec` = `claude --continue` (`~/.bashrc:700`)
- `codexc` = `codex resume --last` (`~/.bashrc:564`)

## Discovery transcript (commands actually run)

```bash
# Multi-socket probe → only /tmp/cmux-debug-dev-fork.sock is live
for s in /tmp/cmux*.sock /private/tmp/cmux*.sock ~/.local/state/cmux/cmux.sock; do
  [ -S "$s" ] && printf '{"id":"q","method":"ping","params":{}}\n' | nc -U -w 2 "$s" 2>&1 | head -c 200
done
# → LIVE: /tmp/cmux-debug-dev-fork.sock + /private/tmp/cmux-debug-dev-fork.sock (same, symlinked)

cmux --socket /tmp/cmux-debug-dev-fork.sock list-workspaces --id-format both
# → workspace:12 D114DA05-7755-4899-8A83-41AAA6EF296E  fable: ios app
# → workspace:12 has pane:15 with one surface (surface:15, the rate-limited Claude session)

cmux --socket /tmp/cmux-debug-dev-fork.sock tree --all --workspace workspace:12
# → workspace workspace:12 "fable: ios app"
#     └── pane pane:15 [focused]
#         └── surface surface:15 [terminal] "$USER@...: ~/project_worldaiclaw/worldai_claw"
```

## Surface creation + brief

```bash
WS=workspace:12; CWD=$HOME/project_worldaiclaw/worldai_claw; PANE=pane:15
SOCK=/tmp/cmux-debug-dev-fork.sock

# 1. Create surface 55 (focus on it for claudec)
cmux --socket "$SOCK" new-surface --type terminal --pane "$PANE" --workspace "$WS" \
     --working-directory "$CWD" --focus true
# → OK surface:55 pane:15 workspace:12

# 2. Write brief to worktree (worktree-pointer strategy)
cat > "$CWD/.cmux-ios-pivot-brief.md" <<'BRIEF'
# iOS-App Pivot Brief (from operator, 2026-07-16 07:07 PT)

User explicitly asks: drop worldai_claw / openclaw connection logic from the iOS app;
focus on mirroring your-project.com's $PROJECT_ROOT/.

Live preview to mirror: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/

Worktree: $HOME/project_worldaiclaw/worldai_claw
Branch: feat/mobile-architecture-cleanup (synced +uncommitted, PR #256)

Required actions:
1. Drop everything else (the sidekick-janitor investigation is interesting but off-task).
2. Confirm current branch + working tree status.
3. Outline a 3-bullet next-steps plan for the iOS-app pivot:
   a. Build target (react-native? expo? what ships today?)
   b. What to mirror from $PROJECT_ROOT/ (start with $PROJECT_ROOT/templates/settings.html factionMinigameSwitch
      and $PROJECT_ROOT/main.py:4348 GET /api/campaigns/<id>/export — see docs/us_audit_rnw_vs_website_2026-07-07.md).
   c. How to make OpenClaw/worldai_claw connection optional via SettingsScreen.tsx toggle (off by default).
4. HOLD — do not write code. Wait for user's go-ahead.
BRIEF

# 3. Get UUID for s55 via raw RPC
S55_ID=$(printf '{"id":"sl","method":"surface.list","params":{}}\n' | nc -U -w 3 "$SOCK" | \
  python3 -c "import json,sys;d=json.load(sys.stdin);print(next(s['id'] for s in d['result']['surfaces'] if s['ref']=='surface:55'))")

# 4. Focus s55 + send claudec (short pointer to brief)
printf '{"id":"sf","method":"surface.focus","params":{"surface_id":"%s"}}\n' "$S55_ID" | nc -U -w 3 "$SOCK" >/dev/null
sleep 1
cmux --socket "$SOCK" send --workspace "$WS" --surface surface:55 "Read .cmux-ios-pivot-brief.md and follow it. Reply with the 3-bullet plan and HOLD."
cmux --socket "$SOCK" send-key --workspace "$WS" --surface surface:55 enter

# 5. Wait for absorption, then create surface 56 (codexc)
sleep 8
cmux --socket "$SOCK" new-surface --type terminal --pane "$PANE" --workspace "$WS" \
     --working-directory "$CWD" --focus false

# 6. Focus s56 + send codexc
S56_ID=$(printf '{"id":"sl","method":"surface.list","params":{}}\n' | nc -U -w 3 "$SOCK" | \
  python3 -c "import json,sys;d=json.load(sys.stdin);print(next(s['id'] for s in d['result']['surfaces'] if s['ref']=='surface:56'))")
printf '{"id":"sf","method":"surface.focus","params":{"surface_id":"%s"}}\n' "$S56_ID" | nc -U -w 3 "$SOCK" >/dev/null
sleep 1
cmux --socket "$SOCK" send --workspace "$WS" --surface surface:56 "Read .cmux-ios-pivot-brief.md and follow it. Reply with the 3-bullet plan and HOLD."
cmux --socket "$SOCK" send-key --workspace "$WS" --surface surface:56 enter
```

## Verified outcome (10s + 30s post-launch)

| Surface | Initial state | 10s after launch | Final (30s) |
|---|---|---|---|
| s55 (claudec) | resumed prior session, ctx 47% | `Galloping… 1m 25s · ↓ 3.9k tokens` (still on prior /goal sidekick investigation) | After Escape + re-send: `Simmering… 9s · ↓ 391 tokens`, ctx 50%, on iOS-app pivot |
| s56 (codexc) | resumed gpt-5.6-sol (warning: was gpt-5.5) | `• Working (5s • esc to interrupt)` | `Context compacted`, `Working (1m 17s • esc to interrupt)`, already created 5 beads |

## Pitfalls hit (each a real bug, not speculation)

1. **`surface.read_text` ignores ref params even with surface_id=UUID.** Called `surface.read_text {surface_id: B615B11C...}` (s55's UUID from `surface.list`) and got back the focused surface's (s15) text. Same with `cmux capture-pane --surface surface:55` — returns s15's content. **Workaround:** trust absorption (churning label / `Working (Ns)`) without read-screen verification, OR focus-then-read if the target IS the focused surface.

2. **`cmux --workspace 12` (bare integer) is parsed as index, not ref.** Always use `--workspace workspace:12` (ref form) — same trap as `select-workspace`. Already in main SKILL.md but worth repeating.

3. **`--focus true` on `new-surface` switches focus each call.** When creating multiple surfaces in sequence with `--focus true`, only the LAST surface stays focused. Use raw-RPC `surface.focus` for explicit control between creates.

4. **`claudec` resumes prior session, inherits quota state.** If the prior session was rate-limited, the resumed session may also be blocked. Verified: s55 resumed fine but s15 (also Claude Code) was rate-limited; they're separate sessions.

5. **Slack MCP bot `not_in_channel` on C0AJQ5M0A0Y.** The MCP bot identity isn't invited to the user's home channel. xoxp user-token fallback via curl works — message posts as `U09GH5BR3QU` ($USER), not the bot.

## Status follow-up cron (per SOUL.md `one-time-status-cron-after-every-task`)

```python
cronjob_create(
  action="create",
  schedule="20m",
  name="fable ios app status (20m)",
  deliver="slack:C0AJQ5M0A0Y:1784185650.528089",
  prompt="Post a brief status update to Slack thread ... [see main SKILL.md for full prompt template]",
  model={"model": "MiniMax-M3", "provider": "minimax"},
)
# → job_id="483aea7b7d92", fires at +20m, one-time
```

## Things to do differently next time

- **Skip the first send of a long bootstrap to a worker with an active `/goal` (1d timer running).** The worker will prioritize the 1d goal over a fresh message. Better: first send a short "interrupt + new task" pointer, then verify absorption, then send the long brief via file pointer.
- **Don't try to read-screen between sends in the same surface during multi-surface creation.** The capture-pane routing bug makes verification via read unreliable. Trust the churning label and move on.
- **For parallel claudec+codexc on the same brief, write the brief FIRST before any new-surface calls.** Avoids the "s55 pivoted to a side-task while s56 still spinning up" race.
