---
description: Launch a real Sonnet-only Claude Code team in tmux
type: orchestration
execution_mode: immediate
---

# /team-claude — real Claude Code tmux team

`/team-claude <prompt>` decomposes `<prompt>` into independent lanes and starts
REAL Claude Code teammates in `tmux`. Do not use pseudo agent APIs for this
command.

## Hard contract

- **Primitive:** every teammate is a real Claude Code process launched by
  `tmux new-session`.
- **Model:** every teammate uses `claude --model sonnet --teammate-mode tmux`.
- **Sonnet-only:** do not start other model lanes, scout lanes, or fallback lanes.
- **Proof:** after launch, verify with `tmux ls`, `tmux capture-pane`, and process
  inspection before claiming the team started.
- **Isolation:** each lane gets a clear lane name and either a dedicated worktree
  or an explicit read-only role. Do not let lanes contend on the same files.
- **Crash recovery:** write lane prompts under `/tmp/team-claude-<slug>/` so a
  later session can inspect or restart them.
- **5-minute checkpoint cadence (mandatory, every lane owner):** every lane owner
  must heartbeat within ≤5 min — append a timestamped progress line to the lane
  state file, `br update <P1-bead-id> --append ...` then `br sync` (one bead
  writer per mission, see /sidekick contract item 6), and commit state safely
  (isolated state repo or WIP branch with path-scoped add; never `git add -A`
  in a worktree with unrelated staged/modified work — gitignored `.tmp/` state
  needs the isolated-repo or `git add -f` path). The 5-min target is
  best-effort and only holds while the orchestrator + watcher are alive; for
  non-repo missions, fall back to plain `/tmp/team-claude-<slug>/` files.

## Execution steps

1. **Decompose** the user's prompt into 2–6 independent lanes. For each lane,
   decide whether it is implementation, verification, investigation, or synthesis.
   If two lanes would edit the same files, merge them or sequence them.

2. **Create lane prompt files**:

   ```bash
   SLUG="$(date +%Y%m%d-%H%M%S)-team-claude"
   BASE="/tmp/team-claude-${SLUG}"
   mkdir -p "$BASE"
   cat > "$BASE/lane-1.prompt.md" <<'PROMPT'
   You are lane 1 of a real Claude Code tmux team.
   Model contract: you are running under `claude --model sonnet --teammate-mode tmux`.
   Follow strict TDD/red-green when changing code.
   COMMIT OFTEN: commit + push after EVERY green unit of work. Never hold more
   than ~30 minutes of uncommitted changes. Include this instruction verbatim in
   every sub-agent prompt you write.

   Lane mission:
   <lane-specific mission here>
   PROMPT
   ```

3. **Launch one tmux session per lane**. Use a shell wrapper so the pane stays
   open for proof capture after Claude exits:

   ```bash
   SESSION="team-${SLUG}-lane-1"
   PROMPT_FILE="$BASE/lane-1.prompt.md"
   tmux kill-session -t "$SESSION" 2>/dev/null || true
   tmux new-session -d -s "$SESSION" -x 160 -y 48 \
     "cd '$PWD' && claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions -p \"\$(cat '$PROMPT_FILE')\"; rc=\$?; printf '\n[team-claude lane done exit=%s]\n' \"\$rc\"; exec bash"
   ```

   Repeat for every lane. The required command prefix is always:

   ```bash
   claude --model sonnet --teammate-mode tmux
   ```

4. **Verify the real team started** before proceeding:

   ```bash
   tmux ls | grep "team-${SLUG}"
   tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' \
     | grep "team-${SLUG}"
   tmux capture-pane -t "$SESSION" -p -S -80 | tail -80
   ps -ef | grep "claude --model sonnet --teammate-mode tmux" | grep -v grep
   ```

   If these checks do not show real tmux sessions and real Claude Code commands,
   the team did **not** start. Fix the launch before doing any work.

5. **Poll and aggregate**:

   ```bash
   for s in $(tmux ls -F '#S' | grep "team-${SLUG}"); do
     echo "===== $s ====="
     tmux capture-pane -t "$s" -p -S -120 | tail -120
   done
   ```

6. **Verification lanes** are also real Sonnet Claude Code tmux sessions. A
   verifier lane checks out the coder's branch or reads the diff, runs tests, and
   tries to refute readiness. Do not mark work ready without verifier output.

7. **Final response** includes: lane names, prompt-file paths, branch/PR URLs if
   created, test output, and the tmux/process proof above.

## Failure modes

- **No tmux session:** launch failed; rerun the `tmux new-session` command and
  inspect stderr.
- **Pane is only a shell:** Claude exited immediately; capture the pane and fix the
  prompt/auth/permission issue before claiming a teammate is active.
- **Process inspection lacks `--model sonnet`:** wrong launch command; kill and
  relaunch with the required prefix.
- **Two lanes edit the same files:** stop one lane and serialize the work.

## Usage

```text
/team-claude <prompt>
```

The current Claude session is the orchestrator. The teammates are real Claude
Code processes in tmux, not in-memory pseudo agents.
