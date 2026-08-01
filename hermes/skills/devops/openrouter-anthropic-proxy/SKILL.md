---
name: openrouter-anthropic-proxy
description: "Local HTTP proxy that lets Claude Code -p mode work with OpenRouter reasoning models (Kimi K3, DeepSeek R1, GLM 5.2, etc.). Strips thinking content blocks and buffers streaming responses so Claude Code's Node SDK doesn't drop stdout. ⚠ DEPRECATED 2026-07-21 — the proxy was deleted on this Mac and /linux because direct OpenRouter works fine for both interactive TUI and `claude -p` mode. Skill retained for users who explicitly want to stand the proxy back up (rare). Prefer the recipes in `openrouter-pilot` for the default no-proxy path."
---

# OpenRouter → Anthropic SDK Proxy

> ⚠ **DEPRECATED 2026-07-21**: The user explicitly asked to delete this proxy after end-to-end testing proved direct OpenRouter works for both interactive TUI and `claude -p` mode on Claude Code v2.1.212. The original 2026-07-17 hypothesis ("Kimi K3 + Claude Code `-p` requires a thinking-stripping proxy") was REFUTED for the model + Claude Code version combination tested. The `~/.local/bin/or-anthropic-proxy.py` binary has been removed on both this Mac and `/linux`. The `~/.claude/CLAUDE.md` "MUST route via proxy" rule has been updated.
>
> **Do NOT auto-spawn this proxy unprompted.** If a future session task says "fix Claude Code `-p` stdout drops with OpenRouter reasoning models", FIRST reproduce the failure against direct OpenRouter on the current Claude Code build before reaching for this proxy. If the reproduction fails to manifest, this skill's premise is stale and should not be re-applied.
>
> The skill is retained because (a) the proxy mechanics are useful if a user explicitly requests the proxy for OTHER reasons (log capture, custom auth intercept, thinking-block logging); (b) the bidirectional gateway-model-discovery patch from `openrouter-pilot` Recipe 3 still references this skill's proxy binary as a base layer; (c) `OR_PROXY_DISABLED=1` back-compat flag in some shells may still reference this code path.

# OpenRouter → Anthropic SDK Proxy

## What it solves

Claude Code 2.1.207's `-p` mode (`claude --print`, `claude -p`) silently drops stdout when used with reasoning models on OpenRouter because:

1. **Thinking blocks poison the parser** — Kimi K3 / DeepSeek R1 / etc. emit `thinking` + `redacted_thinking` content blocks before the visible text. Claude Code's SDK handles these natively for Anthropic-hosted reasoning models but rejects them from OpenRouter-routed models.

2. **Streaming chunked encoding is unreliable through proxies** — Claude Code's Node SDK doesn't reliably consume `Transfer-Encoding: chunked` SSE when the connection comes from a proxy. It needs buffered responses with `Content-Length`.

The proxy solves both: buffers upstream, drops thinking events (and remaps block indices so the visible text starts at index 0), then returns the cleaned stream as a single buffered response.

## Files

- `~/.local/bin/or-anthropic-proxy.py` — the proxy itself (stdlib-only, no deps)
- `~/.local/bin/or-anthropic-proxy.README.md` — user-facing docs
- `~/.bashrc` lines ~1171-1250 — `claudek` / `claudeg` bashrc functions that auto-start the proxy

## Use

```bash
# Auto: bashrc wrappers handle proxy startup
claudek -p "Reply with exactly: pong"   # moonshotai/kimi-k3 via OpenRouter
claudeg -p "Reply with exactly: pong"   # z-ai/glm-5.2 via OpenRouter

# Manual:
python3 ~/.local/bin/or-anthropic-proxy.py &
export ANTHROPIC_BASE_URL="http://127.0.0.1:8765"
claude --print --model moonshotai/kimi-k3 "Reply with exactly: pong"

# Disable for interactive TUI (where seeing thinking is valuable):
OR_PROXY_DISABLED=1 claudek    # routes directly to OpenRouter
```

## How the filter works

For non-streaming responses: strips `thinking` / `redacted_thinking` blocks from the JSON `content` array, adjusts `usage.output_tokens` to reflect only the visible response (preserves `output_tokens_details.thinking_tokens` for cost accounting).

For streaming responses: parses each SSE event, drops events with `type: content_block_start` where the content_block is `thinking` / `redacted_thinking`, drops all `thinking_delta` / `signature_delta` deltas, drops the corresponding `content_block_stop`. Then rewrites the `index` of kept blocks so the visible text starts at index 0.

Path rewriting: Claude Code sends `/v1/messages`; proxy forwards as `/api/v1/messages` to OpenRouter.

## Smoke tests

```bash
# After starting proxy:
curl -sS -X POST http://127.0.0.1:8765/v1/messages \
  -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"moonshotai/kimi-k3","max_tokens":64,"messages":[{"role":"user","content":"Reply with exactly: pong"}]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print([b.get('type') for b in d.get('content',[])])"
# Expected: ['text']

claudek -p "Reply with exactly: pong. Do not call any tools."
claudeg -p "Reply with exactly: pong. Do not call any tools."
```

## Pitfalls

- **Buffering trade-off**: Total response time to first byte ≈ full generation time. Acceptable for `-p` mode; less ideal for long interactive streaming. Use `OR_PROXY_DISABLED=1` for interactive TUI work.
- **HEAD requests return 501**: Claude Code uses HEAD for liveness probes; harmless, but a HEAD-listing tool would see this as a bug.
- **Port collision**: If 8765 is in use, override with `OR_PROTHROPIC_PROXY_PORT` AND `LISTEN_PORT` (must match).
- **Proxy dies silently**: No watchdog. If proxy crashes mid-session, `claudek` falls back to OpenRouter directly (proxy_up=0 path). Bashrc does NOT auto-restart a dead proxy — only auto-starts if no listener exists.
- **OpenRouter model name drift**: `anthropic/claude-sonnet-4.5` was retired 2026-06-15. Run `curl -sS https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq '.data[].id'` to get the current canonical names.

## Diagnostic recipe

```bash
# Check if proxy is running
lsof -nP -iTCP:8765 -sTCP:LISTEN

# Check proxy stderr
tail -30 /tmp/or-proxy.log

# Direct API test (no proxy)
KEY=$(bash -lic 'echo $OPENROUTER_API_KEY')
curl -sS "https://openrouter.ai/api/v1/messages" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"moonshotai/kimi-k3","max_tokens":64,"messages":[{"role":"user","content":"x"}]}' | jq .

# Proxy-only test
curl -sS -X POST "http://127.0.0.1:8765/v1/messages" \
  -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"moonshotai/kimi-k3","max_tokens":64,"messages":[{"role":"user","content":"x"}]}' | jq .
```

## Provenance

Created 2026-07-17. Root-cause session discovered two compounding issues:
- Kimi K3 reasoning model emits `thinking` blocks → Claude Code's `-p` parser drops the output
- Claude Code's Node SDK + chunked SSE through a proxy → response never consumed

Fix verified end-to-end on both Kimi K3 and GLM 5.2 via OpenRouter. Bead `$USER-xk3g` closed with fix documentation.
