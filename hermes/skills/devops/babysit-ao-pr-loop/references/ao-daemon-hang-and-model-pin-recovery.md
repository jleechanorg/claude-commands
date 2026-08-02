---
title: AO daemon hang + inherited-model spawn failure — recovery recipe
date: 2026-07-18
bug-ref: agent-orchestrator-ts / `ao-go` daemon hangs after stale PID ownership probe; `ao spawn` rejects inherited gateway session model
---

## Symptom 1: AO daemon appears healthy but every CLI call times out

```
AO daemon: ready
  pid: 96036
  port: 3001
  healthz: ok
  readyz: ready

$ ao project get worldarchitect
[Command timed out after 60s]

$ ao status | head -1
AO daemon: stopped
  run file: missing
```

But `lsof -nP -iTCP:3001 -sTCP:LISTEN` shows `ao-go daemon` STILL listening on port 3001, and `ps` shows the PID running with state `R` (running). Curl to `/healthz` blocks until timeout. The `ao status` output shows `startedAt` as the original process start time — 18 hours ago in the canonical incident (2026-07-18, your-project.com repro).

### Root cause

The `ao-go` daemon's main loop is wedged (likely stuck in a goroutine holding the SQLite write lock, or blocked on a slow `gh api` GraphQL call that never returned). The HTTP accept loop is still up (so `lsof` shows LISTEN) but every request stalls.

The desktop launcher (`ao start` from `$HOME/.local/bin/ao`) refuses to start a new daemon when the old PID file is still present and verifies ownership by hitting `/healthz` — which also hangs. The error path is:

```
daemon pid 96036 is alive but ownership could not be verified: healthz:
  Get "http://127.0.0.1:3001/healthz": context deadline exceeded
Agent Orchestrator is now a desktop app, and the npm `ao` is just its launcher.
The app is distributed from the website and GitHub Releases; it owns the
daemon and updates itself.
```

So `ao stop && ao start` does NOT recover — you have to bypass the launcher's ownership check.

### Recovery recipe

```bash
# 1. Find the wedged ao-go daemon (NOT the launcher)
ps -p <old_pid> -o pid,ppid,state,etime,command
lsof -nP -iTCP -sTCP:LISTEN | grep ao-go

# 2. SIGKILL the wedged daemon (SIGTERM often also hangs)
kill -9 <old_pid>

# 3. Clear the stale runfile (required so the launcher can re-spawn)
rm -f ~/.ao/running.json

# 4. Open the desktop app (it owns the daemon and updates itself)
open -n -a 'Agent Orchestrator'

# 5. Poll until ready
for i in $(seq 1 20); do
  sleep 2
  out=$($HOME/.local/bin/ao status 2>&1)
  echo "[$i] $(echo "$out" | head -1)"
  echo "$out" | grep -q 'AO daemon: ready' && { echo "$out"; break; }
done
```

Once the helper Electron process (`/Applications/Agent Orchestrator.app/Contents/Resources/daemon/ao daemon`) respawns the daemon under the new PID, the launcher path also recovers:

```bash
$HOME/.local/bin/ao status
# AO daemon: ready
#   pid: <new_pid>
#   healthz: ok
```

### Why `open -n` (not `open`)

`open -a` may no-op when the app is already registered with the Dock. `open -n -a` forces a fresh instance and triggers the daemon-spawn path. Use `-n` to avoid silently re-using an already-broken helper Electron process.

## Symptom 2: spawned worker boots but errors "selected model may not exist"

```
▐▛███▜▌   Claude Code v2.1.212
▝▜█████▛▘  MiniMax-M3 with high effort · Claude Max

⏺ There's an issue with the selected model (MiniMax-M3). It may not exist or you
  may not have access to it. Run /model to pick a different model.
```

### Root cause

`ao spawn` resolves the worker model from the registered project's `agentConfig.model` setting. When the per-project config was set via a previous gateway session whose provider has rotated / revoked its model identifier, the freshly spawned worker boots with that model in its `--model` argv and immediately errors before any tool call lands.

The gateway's main model for the current session can resolve to something different than what the worker process gets via `--model` argv. Pin explicitly per-project.

### Recovery recipe

```bash
# Snapshot before override
$HOME/.local/bin/ao project get worldarchitect \
  > /tmp/<project>-ao-project-before.txt

# Pin the worker to a routable model
$HOME/.local/bin/ao project set-config worldarchitect \
  --model claude-sonnet-4-5 --json

# Spawn the worker (uses new model)
$HOME/.local/bin/ao spawn --project worldarchitect \
  --harness claude-code \
  --branch fix/<topic> --name <short-name> \
  --prompt "$(cat /tmp/brief.md)"

# Verify the model banner now reads Sonnet 4.5 (not the broken model)
tmux capture-pane -t <session-id> -p -S -10 | tail -10

# After work completes, restore the original model config
$HOME/.local/bin/ao project set-config worldarchitect \
  --config-json '<original-json-from-snapshot>' \
  --json
```

### When NOT to use this recipe

If the target model is also unavailable (provider outage, rate limit), the next tier is a pure-CLI fallback: spawn without `--model` and rely on the harness's own default, or dispatch manually via `claude -p` from the gateway.

## Lessons for babysit cron prompts

1. **Always pre-flight `ao status` before trusting Phase 0 / Phase 1 observation.** If `ao status` shows `AO daemon: ready` but every follow-up `ao project get` / `ao session ls` / `ao spawn` times out, the daemon is wedged — recovery takes ~30s with the recipe above. Document the recovery in the babysit thread so the operator knows.

2. **Don't trust inherited model identifiers when dispatching across sessions.** The gateway's main model and a worker process's `--model` argv can resolve to different things. Pin explicitly with `ao project set-config --model <routable>` and restore at end of work.

3. **Both recovery paths are first-class babysit infrastructure.** Every AO worker spawn is gated on (a) the daemon being responsive and (b) the worker model being routable. Bake the pre-flight checks into the babysit prompt body so the first tick doesn't waste 5 minutes discovering either failure.
