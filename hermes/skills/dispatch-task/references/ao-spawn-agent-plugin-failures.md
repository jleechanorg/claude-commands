# AO spawn — agent plugin failure modes (Linux v0.1.3 + cross-version)

**Bug-ref: 2026-07-24, noop-smoke test on `jeff-ubuntu` + `macbook`.**
Two unrelated agent-plugin failures surfaced during a "noop PR on each machine"
smoke test. Both are silent to `ao spawn` (the daemon returns success, creates a
session row + tmux pane, and only the worker's first prompt reveals the bug).

---

## 1. `--agent claude-code` boots into a rate-limited Claude Max

**Symptom:** `ao spawn -p <project> --agent claude-code "<task>"` succeeds —
session row `cc-N` appears in `ao session ls --project <project>`, tmux pane
(e.g. `ed3dd2670551-cc-2`) is created at `~/.worktrees/<project>/cc-N`, and the
pane captures the Claude Code first-run trust prompt. After the user/agent
confirms trust, the worker prints:

```
✻ Sautéed for 0s
─────────────────────────────────────
❯ /home/$USER/.claude/mcp-strict.json
  ⎿  You've hit your weekly limit · resets Jul 27, 8pm (America/Los_Angeles)
     /usage-credits to finish what you're working on.
```

Then the pane idles indefinitely, no work happens.

**Root cause:** Claude Code Max has a weekly usage window (resets every
~7 days at the calendar boundary). The agent has no preflight that reads
`~/.claude.json`/`~/.config/claude-code/usage` before spawning. The worker boots
into a fully rate-limited account and never produces output.

**Diagnostic (after spawn, when worker is idle):**

```bash
# Capture the pane and search for the limit message
tmux capture-pane -t <tmux-name> -p -S -40 | grep -E "weekly limit|resets|usage"
# If it prints, the worker is rate-limited — no amount of waiting will fix it.
```

**Recovery:**

```bash
# 1. Kill the stuck session
ao session kill <session-id>

# 2. Pivot to inline implementation in a manually-created worktree
#    (the same workflow an AO worker would have used)
git worktree add -b <branch> ~/.worktrees/<project>/<short-slug> origin/main
# ... edit, commit, push, gh pr create ...
```

**Defensive preflight (to ADD to agento-friendly scripts):**

```bash
# Before spawning with --agent claude-code, check the cached usage window if
# you have one. As of 2026-07-24, AO has no built-in preflight — this is a
# manual probe. Future: add this as a hook in agent-orchestrator or a
# pre-spawn script in `~/.hermes/scripts/`.
~/.local/bin/claude --version  # does NOT reveal the limit
# The only reliable signal is the spawned worker's first output. If the user
# reports "I keep seeing noop PRs take 4+ min then die", check the tmux pane
# for this limit message.
```

---

## 2. `--agent codex` rejects `--full-auto` (codex CLI ≥ 0.144.x)

**Symptom:** `ao spawn -p <project> --agent codex "<task>"` succeeds — session
row `cc-N` appears, tmux pane is created. The pane exits immediately with:

```
error: unexpected argument '--full-auto' found

  tip: to pass '--full-auto' as a value, use '-- --full-auto'

Usage: codex [OPTIONS] [PROMPT]
       codex [OPTIONS] <COMMAND> [ARGS]

For more information, try '--help'.
$USER@Jeff-Ubuntu:~/.worktrees/<project>/cc-N$
```

Worker exits, prompt returned to shell, no work happens.

**Root cause:** AO 0.1.3's codex agent plugin passes `--full-auto` to the
codex CLI. `codex-cli 0.144.1` (verified on jeff-ubuntu, 2026-07-24) removed
top-level `--full-auto` support — the flag now requires `-- --full-auto` or
a different spelling. Newer codex versions changed the CLI surface; the AO
plugin was not updated.

**Diagnostic (after spawn, ~2s):**

```bash
tmux capture-pane -t <tmux-name> -p -S -20 | grep -E "unexpected argument|--full-auto"
```

**Recovery:**

```bash
# 1. Kill the dead session
ao session kill <session-id>

# 2. Patch the AO codex plugin (out of scope for noop smoke tests). Fix:
#    in the codex agent plugin source, remove `--full-auto` from the argv
#    list, or replace with `-- -q --full-auto` (the workaround hint codex
#    prints). Patch pending in agent-orchestrator-ts.

# 3. Until patched, pivot to inline implementation per the same workflow
#    as the Claude-Max failure mode above.
```

**Down-stream compatibility check (before spawning `--agent codex`):**

```bash
~/.local/bin/codex --version
# If >= 0.144.0, expect this failure on AO 0.1.3.
# If <= 0.143.x, --full-auto may still work.
```

---

## 3. Cross-cutting pattern: both failures are silent to `ao spawn`

Neither failure surfaces in `ao spawn` exit code, `ao status`, or `ao session ls`
state columns — only by reading the tmux pane. The standard diagnostic ladder
for any "the worker isn't doing anything" symptom is:

```bash
# 1. Confirm session exists
ao session ls --project <project> | grep -E "<session-id>"

# 2. Confirm tmux pane exists
tmux ls | grep -E "<session-id>"

# 3. Read the pane — this is the source of truth
tmux capture-pane -t <tmux-name> -p -S -50 | tail -50

# 4. If pane shows a Claude/Codex error message — kill and pivot inline.
#    If pane shows a working prompt waiting for input — send steer via
#    `ao send <session-id> "<message>"`.
```

**Inline-pivot is faster than debugging plugin args mid-dispatch** (verified
2026-07-24 — both Linux noop PRs landed via inline worktree + `gh pr create`
in <90s each, after the AO spawn attempts failed). When the task is small
(<=10 lines, no PR-required CI sweep), skipping the dispatcher and producing
the artifact directly is the right call.

---

## 4. Failure mode cross-reference

| Failure | Symptom | Time-to-detect | Recovery |
|---|---|---|---|
| Mac `ao` daemon INTERNAL_ERROR | orphan session row, no worktree, no pane | ~10s (verify `tmux ls`) | `ao session kill <id>` + inline worktree |
| Linux `ao` v0.1.3 + `claude-code` Max limit | pane idles at "weekly limit" message | ~30s (after trust confirm) | `ao session kill <id>` + inline worktree |
| Linux `ao` v0.1.3 + `codex --full-auto` | pane exits with "unexpected argument" | ~2s | `ao session kill <id>` + inline worktree |
| Token / auth failure | pane shows "401 / not authenticated" | ~5s | re-auth, respawn |

The recovery recipe is the same in all four cases: kill the dead session,
make a worktree off `origin/main`, do the work inline, push, `gh pr create`.
The inline fallback is the durable escape hatch — invest in it, not in
debugging every plugin wrinkle.
