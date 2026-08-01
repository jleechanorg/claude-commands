# AO Spawn: All Providers Simultaneously Exhausted (verified 2026-07-23)

This is the **fifth AO spawn failure mode**, an escalation of failure mode
3 (provider quota block) where a single provider's quota is exhausted. The
distinguishing new symptom is that EVERY available AO harness reports a
quota / rate-limit banner before the first tool call, leaving no worker
slot to dispatch to.

Companion to:
- `references/ao-spawn-provider-quota-block.md` (failure mode 3: single-provider exhaustion)
- SKILL.md "Third failure mode" section (canonical entrypoint)

## Symptom matrix (verified 2026-07-23, AO pool ~12pm PT)

When the user has burnt through every subscription in a single burn-down
window, AO spawns in this order all return a non-actionable banner before
the worker can run the spawn prompt:

| `--harness` | Symptom (verbatim from tmux capture) | Reset / fix |
|---|---|---|
| `claude-code` | "There's an issue with the selected model (MiniMax-M3). It may not exist or you may not have access to it." — *only when the project default `agentConfig.model` is the user's Hermes session model (e.g. `MiniMax-M3`); Claude Code can't use it* | `ao project set-config <id> --model claude-sonnet-4-5` — but that hits the next row |
| `claude-code` (post-model-fix) | "You've hit your weekly limit · resets Jul 27 at 8pm (America/Los_Angeles)" | Wait for Claude Max weekly reset (Sun 8pm PT) |
| `agy` | "⚠ Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 3h38m16s. Error ID: 3af757c3-..." (agy → Claude Sonnet 4.6 by default; **shares Claude Max quota with Claude Code**) | Wait for Claude Max reset |
| `codex` | "■ You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Jul 28th, 2026 10:09 AM." | Wait for Codex reset |
| `opencode` | "⚠ MCP client for `worldai` failed to start: MCP startup failed..." then OK on a fresh build, **but** the only working model is "Nano Banana Pro Google" which requires `GOOGLE_GENERATIVE_AI_API_KEY`; default `GOOGLE_GENERATIVE_AI_API_KEY` is unset, so any prompt sends "Google Generative AI API key is missing. Pass it using the 'apiKey' parameter or the `GOOGLE_GENERATIVE_AI_API_KEY` env..." and the agent stalls | Set `GOOGLE_GENERATIVE_AI_API_KEY` in env (requires Google Cloud project + API key) |
| `qwen` | Spawns the qwen CLI but passes flags qwen doesn't recognize (`Unknown arguments: append-system-prompt, appendSystemPrompt, json-file, jsonFile, input-file, inputFile`) — qwen prints `--help` and exits; agento treats this as spawn failure | **Hard incompatibility, no fix short of patching agento**. qwen CLI v0.x doesn't support agento's prompt-passing contract |

**Important**: `claude-code` and `agy` share the same Claude Max quota pool.
A quota burn on `claude-code` does NOT free up by switching to `agy` — they
hit the same wall.

## Detection recipe (run BEFORE the first spawn attempt)

```bash
# 1. List what actually has an auth token / API key on this Mac
which claude codex agy opencode qwen droid amp grok 2>&1
# 2. Check quota via the cheapest no-IO call per CLI
claude --version        # version !=  quota-ok
timeout 20 claude -p "Reply with just OK" 2>&1 | head -3
timeout 20 codex --version 2>&1 | head -3   # codex CLI doesn't pre-flight quota; will only fail on first prompt
# 3. Check env for the opencode-required keys
env | grep -E 'GOOGLE_GENERATIVE_AI_API_KEY|MINIMAX_API_KEY|MINIMAX_MODEL|ANTHROPIC_BASE_URL' | sort
```

If `claude -p` returns a "weekly limit" banner, **do NOT spawn `agy`** —
they share the quota.

## Recovery: inline implementation in the parent session

When every harness fails, **implement inline in the parent Hermes session**
rather than blocking on the quota reset. The parent session is on Hermes'
session model (e.g. `MiniMax-M3`), which is a separate billing pool from
Claude Max / Codex / agy / opencode. Pattern verified 2026-07-23 on
PR #8551 (rate-limit buckets, 5 files / +599/-14 / 65 unit tests / 10
new tests):

1. **Worktree** — `git worktree add -b feat/wa-<topic> <path> origin/main`
   in `~/.worktrees/wa-<topic>/`. Confirmed no sibling PR per the
   `pr-clean-branch-from-main-no-history-bloat` discipline.
2. **Pre-flight greps** — `rg -n 'CONST_NAME|<OLD_BEHAVIOR>' $PROJECT_ROOT/`
   per `grep-before-constant-change` rule; fix all duplicates in the same
   commit.
3. **Implement, test, lint** — `python3 -m pytest <file>`, `ruff check`,
   `./run_tests.sh <file>` (CI sim).
4. **Commit + push + `gh pr create`** — the durable state is the remote
   branch, not the local commit (per `push-pr-donot-stop-halfway`).
5. **Slack ack in originating thread** with PR URL + per-file diff stat +
   test/lint summary + the inline-fallback note ("AO pool exhausted, did
   it inline rather than blocking on quota reset"). Include the
   one-time 20m status cron job ID per
   `one-time-status-cron-after-every-task`.
6. **Do NOT drive the PR to N-green inline** — multi-cycle `/green`
   iteration needs an AO worker with a quota slot. Tell the user: "If
   Green Gate stays red after my cron checks in 20m, ping me to spawn
   a worker once Codex / Claude Max has a slot."

## Why the inline fallback works

- Hermes parent session model (e.g. `MiniMax-M3`) has its own quota
  pool that is NOT shared with Claude Code / agy / Codex. The user
  only hits the inline-fallback path when they have specifically
  exhausted Claude Max AND Codex AND opencode API key — the Hermes
  pool is still open.
- Inline tasks under ~600 lines of well-scoped diff complete in
  one parent-session turn (verified 2026-07-23: rate-limit buckets,
  5 files, +599/-14).
- The cost is the parent session's quota (small per turn), not the
  user's Claude Max / Codex budget.

## What the user sees

When this fires, post a single Slack reply that says:

1. PR URL (so the work is visible)
2. "implemented inline because every AO harness was quota-blocked"
3. Quota reset times per harness (so they can decide whether to wait
   or buy more credits)
4. The status-cron ID per `one-time-status-cron-after-every-task`
5. "I am NOT driving this to merge in this session — you review +
   merge, and if Green Gate needs babysitting, ping me to spawn a
   worker once Codex / Claude Max has a slot"

## Anti-pattern: the spawn-and-pray loop

Do NOT spin through `claude-code` / `agy` / `codex` / `opencode` /
`qwen` / `droid` blindly. Each failed spawn:
- Wastes a tmux session (clogs `tmux ls` until `ao session cleanup`)
- Consumes agento daemon state (requires `kill -9 <old_pid>` if
  two daemons bind the same port — verified 2026-07-23)
- Burns audit-detector budget without producing work

**Stop after 2-3 harness failures if the symptoms are clearly quota /
auth-related (weekly limit, individual quota, missing API key, CLI
arg-incompatible). Pivot to inline immediately.** The user's time is
worth more than the next retry.

## Pitfall — agento daemon port collision

When an `ao spawn` fails with "Internal server error (INTERNAL_ERROR)",
check `lsof -nP -iTCP:63609 -sTCP:LISTEN`. Two `ao-go` daemons
binding the same port (an old CLI daemon and the new desktop-app
daemon) is a known failure mode. Recovery:

```bash
# Identify the older PID
cat $HOME/.ao/running.json
# Kill the old one (don't kill the desktop app's daemon)
kill -9 <old_pid>
rm $HOME/.ao/running.json
# Restart via the desktop-app CLI
env -i HOME="$HOME" PATH="..." GH_TOKEN="$(gh auth token)" \
  $HOME/.local/bin/ao-go daemon &
# Verify
sleep 3 && $HOME/.local/bin/ao status
```

## Related references

- `references/ao-spawn-provider-quota-block.md` — single-provider
  exhaustion (failure mode 3)
- SKILL.md "Second failure mode" — pool exhaustion / zombie recovery
- SKILL.md "Fourth failure mode" — GHA self-hosted runner saturation
- SKILL.md "Step 0.5 — PR-topology pre-flight" — always run before
  any `/green` dispatch