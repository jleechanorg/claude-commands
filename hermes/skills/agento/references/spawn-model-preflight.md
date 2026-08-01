# AO spawn model preflight — avoid model-availability dead-ends

## Failure class
An `ao spawn` worker boots, the harness prints the chosen model on the
TUI banner, and **only after the prompt is sent** does the worker hit a
provider-side rate/usage limit. The session is left in `idle`/`working`
with `lastActivityAt` ticking, but no real work happens. The parent
process wastes a spawn slot, the task clock starts over, and the user
sees a worker that appears healthy but produces nothing.

Verified 2026-07-20 in Slack thread
`C0AH3RY3DK6/1782336926.897789` (auto-level-up redesign). First Codex
worker + a parallel Codex brainstorm `codex exec` both died with:
`You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
to purchase more credits or try again at Jul 24th 2026 8:25 PM.`

## Pre-flight recipe (run BEFORE `ao spawn`)

1. **Probe the chosen model tier explicitly** — cheap reads, no spend:
   ```bash
   agy models                # confirms Gemini availability per tier
   codex --version           # confirms codex CLI presence
   python3 - <<'PY'
   from pathlib import Path
   p = Path.home() / ".codex/config.toml"
   print(p.read_text() if p.exists() else "no config")
   PY
   ```
2. **Send a throwaway heartbeat** to the chosen CLI harness on a
   trivial input that is known to respond, but with `--print-timeout`
   capped low (30-60s) so a hung auth/usage probe does not block
   dispatch:
   ```bash
   codex exec -m gpt-5.4-mini -s read-only --ephemeral \
     --output-last-message /tmp/heartbeat.txt - <<< 'Reply with the single word: pong'
   agy --print --new-project --dangerously-skip-permissions \
     --model 'Gemini 3.5 Flash (High)' --print-timeout 1m \
     --prompt 'Reply with exactly: pong'
   ```
   Both must end with the literal `pong` (or your agreed sentinel).
   Anything else — including the OpenAI usage-limit banner — is a hard
   stop: pick a different tier / harness BEFORE spawning the real worker.
3. **Match the spawn tier to the budget** — the SOUL.md subagent model
   routing policy mandates explicit tier (mini/haiku for pollers, mid
   for standard fix/review, top only for adversarial design judgment).
   If a tier is rate-limited, downgrade to the next cheaper available
   tier; never re-attempt the same tier and hope.
4. **Keep an alternative harness in your back pocket** — both `codex`
   and `agy` are registered in `~/.ao`. If `codex` is unusable, retry
   with `agy` and an explicit `--model` per the agy model list.
5. **Verify the spawn actually entered `working`** — after `ao spawn`,
   poll `ao session get <id>` for `status: working` AND `lastActivityAt`
   advancing within ~60s. If status stays `idle` for >90s with no
   tool calls in the tmux pane, kill the session and respawn on a
   different harness:
   ```bash
   ao session kill <id>
   ao session get <id>   # confirm isTerminated=true
   ao spawn --project <project> --harness <alt> --name <name> --prompt '...'
   ```

## Kill signals (don't wait them out)

- Pane shows `⚠ --dangerously-bypass-hook-trust is enabled` **and** the
  next line is a `usage limit` / `rate limit` / `429` / `payment
  required` notice. Kill and switch harness immediately.
- Pane shows `You've hit your usage limit` verbatim. Kill and switch.
- Pane shows repeated `ERROR:` lines from the harness's SessionStart
  hook with the same error. Kill and switch.

## After-action lessons

- The preflight is cheap (≤2 min). Skipping it burns the spawn slot and
  the user's trust.
- The `--ephemeral` flag on `codex exec` is fine for one-shot probes —
  it does not consume a real session quota, but the usage-limit banner
  still appears, which is exactly the signal you want to catch
  early.
- `agy --print` writes a real project file under
  `~/.agy/projects/...` even in probe mode. If you want zero
  residue, prefer `codex exec --ephemeral` for the cheap probe and
  reserve `agy --print` for the actual spawn.