---
name: ao-spawn-minimax-worker
description: "Spawn an Agent-Orchestrator (AO) worker that uses the minimax CLI with the M3 model (via the minimax Anthropic-compatible API). Use when: the task should be dispatched to a worker that uses minimax M3 specifically, when the user says 'use minimax', 'use the M3 model', 'use the minimax worker', 'ao spawn minimax', or 'minimax CLI for AO'. This skill verifies the env (MINIMAX_MODEL, MINIMAX_API_KEY, ANTHROPIC_BASE_URL) end-to-end, then runs `ao spawn --agent minimax`. Verified 2026-06-13 against session ao-6355 / PR #678."
when_to_use: "Use when the user asks to spawn an AO worker on minimax M3, or any time `ao spawn` is needed and the model choice is minimax. Do NOT use for: direct `claude` CLI runs (use shell directly), or for AO workers that should use a different model (use the default `ao spawn` with no `--agent` flag). NOT for fixing 401 errors (use `minimax-401-diagnostic` instead)."
allowed-tools: ["Bash", "Read", "Write", "Edit"]
context: "Verified end-to-end on 2026-06-13 with session ao-6355 and PR https://github.com/jleechanorg/agent-orchestrator/pull/678. The agent-minimax plugin (packages/plugins/agent-minimax/src/index.ts) wraps the `claude` CLI with ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic and propagates MINIMAX_MODEL from the tmux env. modelByCli.minimax.model=MiniMax-M3 in ~/agent-orchestrator.yaml makes this the default. The skill is intentionally a thin pointer — the canonical implementation is the AO plugin source + the user's `~/agent-orchestrator.yaml`."
---

# ao-spawn-minimax-worker

## What it does

Spawns an AO worker that uses the **minimax CLI** (an Anthropic-compatible adapter) with the **M3** model. Verifies env, then dispatches.

## When NOT to use this skill

- The user wants a direct `claude` CLI run (use the shell — no AO)
- The user wants a different model (just `ao spawn "<task>"` with no `--agent` flag)
- The user is debugging a 401 from the minimax API → use `minimax-401-diagnostic` instead
- The user wants a non-AO worker (e.g., `claude -p`, `codex`, `opencode`) → use those CLIs directly

## Pre-flight checks (do these BEFORE spawning)

```bash
# 0. CRITICAL — Check that AO will actually source bashrc.
#    An explicit envSource: [] in agent-orchestrator.yaml overrides the default
#    of ["~/.bashrc"] and silently disables bashrc sourcing, which means
#    MINIMAX_API_KEY never reaches the plugin (bd-g884 regression / 2026-06-13).
#    Refuse to spawn if this is wrong; do not work around it.
#    Regex is indented-anchored (`^\s*envSource:`) so it matches whether the
#    key sits at column 0 or nested under `defaults:` / a project block.
if grep -E '^\s*envSource:\s*\[\s*\]\s*$' ~/agent-orchestrator.yaml >/dev/null 2>&1; then
  echo "BLOCKER: ~/agent-orchestrator.yaml has 'envSource: []' — AO will NOT"
  echo "         source bashrc, so MINIMAX_API_KEY will be missing. Fix the"
  echo "         config first (replace with [\"~/.bashrc\"] or delete the line"
  echo "         to restore the default). Aborting spawn."
  exit 1
fi

# 1. Confirm minimax model is set in bashrc
grep "^export MINIMAX_MODEL" ~/.bashrc

# 2. Confirm API key resolves in the current shell (sanity check only — the
#    real check is (0) above, because the spawn happens in a different process)
[ -n "$MINIMAX_API_KEY" ] && echo "OK: MINIMAX_API_KEY set in current shell" || echo "WARN: MINIMAX_API_KEY missing in current shell (bashrc may still provide it)"

# 3. Confirm endpoint reachable
curl -s -o /dev/null -w "minimax endpoint: HTTP %{http_code}\n" -m 5 https://api.minimax.io/anthropic

# 4. Resolve MINIMAX_ANTHROPIC_BASE_URL — fall back to the canonical value if
#    the calling shell didn't inherit it from bashrc. This unblocks shells
#    that source a minimal env (CI runners, fresh tmux, etc.) where the
#    extra var is missing even though the standard MiniMax env is valid.
: "${MINIMAX_ANTHROPIC_BASE_URL:=https://api.minimax.io/anthropic}"
export MINIMAX_ANTHROPIC_BASE_URL
echo "MINIMAX_ANTHROPIC_BASE_URL=$MINIMAX_ANTHROPIC_BASE_URL"

# 5. Quick live test of M3 model — uses $MINIMAX_API_KEY from the calling shell.
#    If (0) is OK but (5) returns 401, the issue is NOT envSource; see
#    minimax-401-diagnostic skill instead.
curl -s -m 30 -X POST "${MINIMAX_ANTHROPIC_BASE_URL}/v1/messages" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MINIMAX_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"MiniMax-M3","max_tokens":20,"messages":[{"role":"user","content":"Reply with: PONG_M3_OK"}]}' \
  | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('model:', d.get('model','?')); print('text:', d.get('content',[{}])[0].get('text','?').strip())"
```

Expected:
- Pre-flight (0) must pass — the line must be absent, `["~/.bashrc"]`, or any non-empty array (matches at any indent)
- `MINIMAX_MODEL=MiniMax-M3` (the user's bashrc already has this — see SOUL.md)
- HTTP 301 (the API root redirects; that's normal)
- (4) `MINIMAX_ANTHROPIC_BASE_URL` resolves to `https://api.minimax.io/anthropic` (either from bashrc or the default fallback)
- Direct API call returns `model: MiniMax-M3` and `text: PONG_M3_OK`

## Spawn

```bash
# From a project root that has an agent-orchestrator.yaml with modelByCli.minimax configured
ao spawn --agent minimax "<task description>"

# Example: smoke test the minimax worker
ao spawn --agent minimax "Reply with: PONG_M3_FROM_MINIMAX_WORKER. Do nothing else."

# Example: actual coding task
ao spawn --agent minimax "Fix the bug in src/foo.ts where bar() returns null"
```

AO will:
1. Create a worktree (or use existing project worktree)
2. Launch a tmux session named `953501c04ccc-ao-XXXX`
3. Inject the `agent-minimax` plugin env: `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL=MiniMax-M3`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`
4. Run `claude --dangerously-skip-permissions` in the worktree
5. Auto-create a PR once the worker makes commits

## Verify the worker actually uses M3

```bash
# After ~10s, check the tmux env (proves the plugin injected M3)
tmux show-environment -t 953501c04ccc-ao-XXXX 2>&1 | grep -E "ANTHROPIC_BASE_URL|ANTHROPIC_MODEL|MINIMAX_API_KEY"
# Expected: ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic
#           ANTHROPIC_MODEL=MiniMax-M3
#           (ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN present but redacted)

# Read the worker's screen
tmux capture-pane -t 953501c04ccc-ao-XXXX -p | tail -30
# Expected: a response from MiniMax-M3, with "ctx ##-------- XX%" in the footer
```

## Common pitfalls (caught in production 2026-06-13)

### Drift: `claudem()` shell function is hardcoded to M2.5

`~/.bashrc` has `claudem() { ... ANTHROPIC_MODEL="MiniMax-M2.5" ... claude --model MiniMax-M2.5 ... }`. If you call `claudem` directly (outside of AO), you get M2.5, not M3.

**For AO workers this doesn't matter** — AO uses the plugin, not `claudem`. But if you're verifying with the shell, use raw `claude --model MiniMax-M3 ...` instead of `claudem`.

### Drift: launchd plists hardcode M2.7

`launchd/ai.agento.lifecycle-all.plist.template` and `ai.agento.health.plist.template` both set `<key>MINIMAX_MODEL</key><string>MiniMax-M2.7</string>`. The lifecycle worker spawned from these will use M2.7, NOT M3.

**Workaround:** spawn via `ao spawn --agent minimax` from a shell, which uses `process.env.MINIMAX_MODEL` (= MiniMax-M3 from bashrc).

**Proper fix (not done in this turn):** update the two plist templates to use `MiniMax-M3` or read from a sed-substituted var.

### Drift: autonomous-harness CLI defaults hardcode M2.7

`autonomous-harness/src/{cli,harness-state,orchestrator}.ts` all default `minimax/MiniMax-M2.7`. Anyone running the autonomous-harness without overriding `--generator-model` will get M2.7.

### 401 errors

If the worker shows `/login · API Error: 401` in its tmux pane, the API key is redacted. Use `minimax-401-diagnostic`.

## Verification (proven by this skill)

| Step | Result | Date |
|------|--------|------|
| Direct M3 API call | `model: MiniMax-M3, text: PONG_M3_OK` | 2026-06-13 |
| `ao spawn --agent minimax` | Session `ao-6355` created | 2026-06-13 |
| Plugin env in tmux | `ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic`, `ANTHROPIC_MODEL=MiniMax-M3`, key resolved | 2026-06-13 |
| Worker model identity | `Cogitated for 7s` → `PONG_M3_FROM_MINIMAX_WORKER` | 2026-06-13 |
| PR auto-created | https://github.com/jleechanorg/agent-orchestrator/pull/678 | 2026-06-13 |

## Canonical sources

- **Plugin source:** `~/project_agento/agent-orchestrator/packages/plugins/agent-minimax/src/index.ts`
- **User config:** `~/agent-orchestrator.yaml` (lines ~119-128: `modelByCli.minimax.model: MiniMax-M3`)
- **Companion skill (401):** `~/.claude/skills/minimax-401-diagnostic/SKILL.md`
- **AGENTS.md (fork):** `~/project_agento/agent-orchestrator/AGENTS.md` (Provider Agent Plugins section)
- **This skill (pointer):** `~/.hermes_prod/skills/ao-spawn-minimax-worker/SKILL.md` (and `~/.hermes/skills/...`)

## Pitfalls (anti-pattern guards)

- **Don't** use `claudem` to verify M3 — it has M2.5 hardcoded; use raw `claude --model MiniMax-M3` or just check tmux env
- **Don't** trust the autonomous-harness defaults (M2.7); pass `--generator-model minimax/MiniMax-M3` explicitly
- **Don't** modify `~/Library/LaunchAgents/ai.agento.lifecycle-all.plist` to fix the M2.7 → M3 drift; update the `.template` file and re-run `setup-launchd.sh` instead
- **Don't** spawn without verifying env first — if `MINIMAX_API_KEY` is missing, the worker will hit 401 and the babysit loop will be wasted
