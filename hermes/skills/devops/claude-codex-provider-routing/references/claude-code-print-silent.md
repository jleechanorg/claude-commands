# Claude Code `-p` mode silent across all OpenRouter-backed models (2026-07-17)

Session-specific detail for the **Claude Code non-interactive silent-exit class** of failure when routed through OpenRouter. Distinct from but related to `references/reasoning-models.md`: this issue hits ALL OpenRouter models (Sonnet 4.5, GLM 5.2, Kimi K3 alike), not just reasoning models. Read this before declaring any new `claudeor`-style wrapper broken.

## Symptom

`claude<short> -p "Reply with exactly: pong"` exits 0 in ~60s with NO stdout (only the cosmetic `connectors disabled` warning). The model IS responding — Claude Code is silently dropping the final output.

```text
$ claudek -p "Reply with exactly: pong" 2>&1
⚠ claude.ai connectors are disabled because ANTHROPIC_API_KEY or another auth source is set and takes precedence over your claude.ai login · Unset it to load your organization's connectors

$ echo $?
0
```

## Scope (verified live 2026-07-17)

| Wrapper | Model | `-p` stdout | Raw API (curl) | `--print --verbose` JSONL |
|---|---|---|---|---|
| `claudeor` | `anthropic/claude-sonnet-4.5` | empty | `200` `pong` | works |
| `claudeg` | `z-ai/glm-5.2` | empty | `200` `pong` | works |
| `claudek` | `moonshotai/kimi-k3` | empty | `200` `pong-kimi-k3` | works |
| `claudeorop` | `anthropic/claude-opus-4.7` | empty | `200` `pong` | works |

So: **every OpenRouter-backed wrapper on Claude Code 2.1.207 has this symptom in `-p` mode**, but interactive TUI mode (`claude` with no `-p`) works fine and `--print` works fine too. The `-p` non-interactive finalizer is the breakage.

## Diagnostic ladder (use before declaring the wrapper broken)

1. **Raw API probe** (proves the upstream is alive):
   ```bash
   curl -sS -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
     -d '{"model":"anthropic/claude-sonnet-4.5","max_tokens":32,
          "messages":[{"role":"user","content":"Reply with exactly: pong"}]}' \
     https://openrouter.ai/api/v1/messages | python3 -m json.tool
   ```
   If this returns a real answer, the wrapper is fine.

2. **Verbose JSONL probe** (proves Claude Code SDK completes against OpenRouter):
   ```bash
   bash -lic 'claudeor --print --verbose --output-format=json "Reply with exactly: pong" 2>&1' \
     | python3 ~/.hermes/skills/devops/claude-codex-provider-routing/scripts/parse_claude_verbose.py
   ```
   If `ASSISTANT_TEXT: 'pong'` + `IS_ERROR=False STOP_REASON=end_turn` prints, the wrapper works end-to-end. The `-p` finalizer is the only thing dropping output.

3. **Inspect Claude Code's actual request** (proves the SDK sent what you expect). Add a verbose log to your local proxy (see § "Local proxy recipe" below) and look for the `POST /v1/messages?beta=true` line — the `?beta=true` query param is added by Claude Code 2.1.207, and these critical headers are sent on every request:
   - `anthropic-beta: claude-code-20250219,interleaved-thinking-2025-05-14,thinking-token-count-2026-05-13,context-management-2025-06-27,prompt-caching-scope-2026-01-05,mid-conversation-system-2026-04-07,advanced-tool-use-2025-11-20,effort-2025-11-24`
   - `anthropic-dangerous-direct-browser-access: true`
   - `x-api-key: ***`
   - `User-Agent: claude-cli/2.1.207 (external, sdk-cli)`

## Local proxy recipe (the working fix)

Drop a tiny stdlib HTTP proxy on `127.0.0.1:8765` that:
1. Accepts Claude Code's `/v1/*` paths
2. Rewrites them to OpenRouter's `/api/v1/*`
3. Strips `thinking` + `redacted_thinking` content blocks from non-streaming Anthropic responses (adjusts `usage.output_tokens` to subtract stripped thinking tokens; preserves `output_tokens_details.thinking_tokens` for cost accounting)
4. Passes streaming and `/v1/chat/completions` through unchanged

Then point the wrapper's `ANTHROPIC_BASE_URL` at the proxy instead of `https://openrouter.ai/api` directly.

A generic reference implementation lives at `scripts/or_anthropic_proxy.py`. Key design notes:

- **Path rewrite rule:** Claude Code hits `/v1/messages`; OpenRouter serves `/api/v1/messages`. The proxy translates `/v1/*` → `/api/v1/*` on the way out. Same for `/v1/chat/completions` → `/api/v1/chat/completions`, `/v1/models` → `/api/v1/models`.
- **Stripping only on non-streaming Anthropic-format responses:** detect by `Content-Type: application/json` AND `/v1/messages` path AND no `text/event-stream`. Streaming responses are passed through unchanged so Claude Code's interactive TUI mode (which already renders thinking blocks) keeps working.
- **HEAD requests return 501:** Claude Code 2.1.207 sends `HEAD /` as a liveness probe before the POST. The proxy doesn't implement HEAD; Claude Code ignores the 501 and proceeds with the POST, so this is harmless.
- **Token accounting adjustment:** when a `thinking` block is stripped, the response's `usage.output_tokens` would overcount. Subtract `usage.output_tokens_details.thinking_tokens` from `usage.output_tokens` before forwarding, but keep the `thinking_tokens` detail field intact so cost dashboards still report accurately.

### Smoke test recipe (proxy + wrapper)

```bash
# 1. Start proxy (background, tracked by the runtime)
python3 ~/.hermes/skills/devops/claude-codex-provider-routing/scripts/or_anthropic_proxy.py &
PROXY_PID=$!

# 2. Wait for listener
for i in 1 2 3 4 5; do
  lsof -nP -iTCP:8765 -sTCP:LISTEN >/dev/null 2>&1 && break
  sleep 0.3
done

# 3. Hit Anthropic-format through proxy
curl -sS -X POST http://127.0.0.1:8765/v1/messages \
  -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"moonshotai/kimi-k3","max_tokens":128,
       "messages":[{"role":"user","content":"Reply with exactly: pong"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
      print('blocks:', [b.get('type') for b in d.get('content',[])]); \
      print('text:', repr([b['text'] for b in d['content'] if b['type']=='text']))"

# Expected: blocks: ['text']  text: ['pong']

# 4. Hit OpenAI-format through proxy (passthrough, no strip)
curl -sS -X POST http://127.0.0.1:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"anthropic/claude-sonnet-4.5","max_tokens":64,
       "messages":[{"role":"user","content":"Reply with exactly: pong"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); \
      print('content:', d['choices'][0]['message']['content'])"

kill $PROXY_PID
```

### Wiring the wrapper to use the proxy

```bash
# Point Claude Code at the local proxy; claudek/claudeor etc. only need to add the URL.
export ANTHROPIC_BASE_URL="http://127.0.0.1:8765"
# The proxy reads $OPENROUTER_API_KEY itself; pass it through if it's not already set.
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
export ANTHROPIC_API_KEY="$OPENROUTER_API_KEY"

claude --dangerously-skip-permissions --effort high \
  --print --model anthropic/claude-sonnet-4.5 \
  "Reply with exactly: pong"
```

For interactive TUI mode (no `-p`), the proxy is NOT needed — Claude Code handles thinking blocks itself.

## Runtime pitfalls when shipping the proxy

**Hermes runtime `terminal()` foreground rejects `nohup ... &` / `setsid ... &` subshells.** Symptom: `Foreground command uses shell-level background wrappers (nohup/disown/setsid). Use terminal(background=true) so Hermes can track the process, then run readiness checks and tests in separate commands.` Fix:

- Don't try to daemonize from inside a `terminal()` foreground command — even via `setsid` or `nohup` subshells, the runtime's pre-flight check rejects `&` characters and shell-detected background patterns.
- Use `terminal(background=true, notify_on_complete=false)` to spawn the daemon — Hermes tracks the process lifetime and gives you a `session_id` for `process(action=kill)` later.
- A common port-in-use cycle: previous `terminal(background=true)` Python listener is still bound to `:8765` even after you `process(action=kill)`. `kill` may SIGTERM the launcher shim while the actual python child (whose PPID was detached by `setsid`) stays alive. Recover by `lsof -nP -iTCP:<port> -sTCP:LISTEN -t | xargs -r kill -9; sleep 1` between restarts, OR keep one stable proxy process and don't restart it.

**Idempotent launcher pattern (when bash can run naked, e.g. from `~/.local/bin/` scripts):**

```bash
#!/usr/bin/env bash
# or-proxy-up — start the OR proxy if no listener is bound to :8765
PORT="${1:-${OR_ANTHROPIC_PROXY_PORT:-8765}}"
LOG="${OR_ANTHROPIC_PROXY_LOG:-/tmp/or-anthropic-proxy.log}"
PIDFILE="${OR_ANTHROPIC_PROXY_PIDFILE:-/tmp/or-anthropic-proxy.pid}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "or-proxy-up: :$PORT already listening"
  exit 0
fi
# Setsid + nohup is fine here because we're outside a terminal() foreground command.
nohup setsid python3 "$HOME/.local/bin/or-anthropic-proxy.py" >"$LOG" 2>&1 < /dev/null &
PROXY_PID=$!
echo "$PROXY_PID" > "$PIDFILE"
for _i in 1 2 3 4 5 6 7 8 9 10; do
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "or-proxy-up: listening on :$PORT (pid $PROXY_PID)"
    exit 0
  fi
  sleep 0.3
done
echo "or-proxy-up: proxy did not start within 3s" >&2
exit 1
```

## Beads

- `$USER-3e4o` — Claude Code `-p` silent with reasoning models (Kimi K3 specifically). Original scope.
- `$USER-xk3g` — Claude Code `-p` silent on OpenRouter (broader scope; ALL OpenRouter models, not just reasoning ones). Created 2026-07-17. The local proxy (`scripts/or_anthropic_proxy.py`) is the working workaround.

## When the upstream SDK fixes this

If/when Claude Code's `-p` mode starts threading thinking blocks into stdout correctly, the proxy becomes optional. The test is:

```bash
# Without the proxy, against OpenRouter directly:
unset ANTHROPIC_BASE_URL
bash -lic 'claudeor -p "Reply with exactly: pong"' 2>&1 | tail -3
# Expected: prints "pong" and exits 0. If yes, drop the proxy.
```

Until then, all OpenRouter-backed `-p` invocations should go through the proxy.
