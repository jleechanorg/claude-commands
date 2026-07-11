---
description: Launch a real Sonnet Claude Code team — official in-session Agent Teams by default, tmux lanes as fallback
type: orchestration
execution_mode: immediate
---

# /team-claude — real Claude Code team (in-session Agent Teams DEFAULT)

`/team-claude <prompt>` decomposes `<prompt>` into independent lanes and starts
REAL Claude Code teammates. **DEFAULT (user directive 2026-07-11): use the
official Agent Teams feature IN THE CURRENT SESSION** — teammates spawned via
the Agent tool with `name:` are real Claude Code agents, visible in the user's
team panel, SendMessage-addressable, and registered on disk in
`~/.claude/teams/session-<id>/config.json` with per-teammate inboxes. A team
the user cannot see in their own panel does not satisfy this command.

## Hard contract — DEFAULT mode (in-session Agent Teams)

- **Primitive:** every teammate is spawned via the Agent tool with an explicit
  `name: lane-<n>-<topic>` and `model: sonnet`. These are NOT pseudo agents —
  they register in the session team config with inboxes and colors.
- **Sonnet-only:** every lane uses `model: sonnet`; the orchestrating session
  is the team lead.
- **Proof:** after launch, verify the registry on disk —
  `ls ~/.claude*/teams/session-*/inboxes/` shows one inbox per named lane, and
  the config.json `members[]` lists them. The user additionally SEES the
  teammates in the session panel; teammate messages render with team colors.
- **Isolation:** each lane gets a clear lane name and either a dedicated
  worktree or an explicit read-only role. Two lanes never write the same file.
- **Collection:** lanes go `idle_notification` WITHOUT auto-delivering — the
  lead must SendMessage-nudge each idle lane for its report.
- **Crash recovery:** write lane prompts + a mission STATE.md under
  `/tmp/team-claude-<slug>/` so a later session can inspect or respawn. Lanes
  die with the parent CLI — durable state lives on disk, per the sidekick
  skill's STATE.md pattern.
- **Verification lanes** are teammates too (refute-by-default prompts). Do not
  mark work ready without verifier output.

## FALLBACK mode — external tmux lanes

Use ONLY when the mission must survive this session exiting, or Agent Teams is
unavailable. Disclose to the user up front: "these lanes will NOT appear in
your panel; watch with `tmux attach -t team-<slug>-lane-<n>` (detach:
ctrl+b d)."

```bash
SESSION="team-${SLUG}-lane-1"
PROMPT_FILE="$BASE/lane-1.prompt.md"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux capture-pane -t "$SESSION" -p -S -20 | tail -20   # never kill a live lane blind
fi
tmux new-session -d -s "$SESSION" -x 160 -y 48 \
  "cd '$PWD' && CLAUDE_CONFIG_DIR='${CLAUDE_CONFIG_DIR:-$HOME/.claude}' claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$PROMPT_FILE')\"; rc=\$?; printf '\n[team-claude lane done exit=%s]\n' \"\$rc\"; exec bash"
```

Verify with `tmux ls | grep "team-${SLUG}"`, `pgrep -fl -- "--teammate-mode tmux"`
(match the flag — ps may show a full binary path), and capture-pane. Blank pane
in `-p` mode is normal while working. Poll/aggregate with capture-pane loops.
Inline `CLAUDE_CONFIG_DIR` always — the tmux server strips it (wrong-account
session-limit failures otherwise).

## Failure modes

- **User says "I don't see the team":** you used tmux mode without disclosure,
  or spawned unnamed agents. Switch to DEFAULT mode — named in-session
  teammates — immediately; this exact complaint recurred 5× across 3 sessions
  on 2026-07-10/11 before the default was flipped.
- **No inbox file for a lane:** the spawn was not a named teammate; respawn
  with `name:`.
- **Idle lanes, no reports:** you forgot the SendMessage nudge.
- **Two lanes edit the same files:** stop one lane and serialize the work.
- **(fallback) Pane is only a shell:** Claude exited immediately; capture the
  pane and fix prompt/auth before claiming the lane is active.

## Usage

```text
/team-claude <prompt>
```

The current Claude session is the orchestrator/team lead. Related: the sidekick
skill (durability layer, STATE.md pattern) and /swarm (which composes this
team primitive with adversarial verification).
