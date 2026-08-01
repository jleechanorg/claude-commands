# OpenRouter endpoint surface (verified 2026-07-13)

Empirical data on how OpenRouter exposes the Anthropic-protocol and OpenAI-protocol endpoints at the same host. Probes run against the live API at `https://openrouter.ai/api`. Save this to `references/` so the next session adding OpenRouter to a new provider wrapper doesn't have to re-probe.

## Path-by-path probe results

| Path | Protocol | Status | Body example | Verdict |
|---|---|---|---|---|
| `/api/v1/auth/key` | N/A (auth probe) | 200 | `{"data":{"label":"sk-or-v1-...","is_management_key":false,"usage":15.04,...}}` | Use this for `openrouter-check` |
| `/api/v1/models` | N/A (catalog) | 200 | 342 model IDs, e.g. `anthropic/claude-sonnet-4.5`, `anthropic/claude-opus-4.7`, `openai/gpt-5` | Use this to verify a model id exists before defaulting to it |
| `/api/v1/messages` | Anthropic-protocol | 200 | `{"type":"message","role":"assistant","content":[{"type":"text","text":"pong"}]}` | USE for `claudeor`/`claudeorop` |
| `/api/v1/chat/completions` | OpenAI-protocol | 200 | `{"id":"gen-...","object":"chat.completion","model":"anthropic/claude-sonnet-4"}` (probe-defaults to cheapest) | USE for `codexor` |
| `/api/v1/responses` | (rejects) | 400 | `{"error":{"code":"invalid_prompt","message":"No input provided"}}` | **Do NOT use** — rejects generic input |

The same auth key works on all three shapes. `Authorization: Bearer $OPENROUTER_API_KEY`.

## Probe recipe (re-runnable)

```bash
curl -sS -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/auth/key | python3 -m json.tool | head -10

# Returns key metadata: label, usage stats, byok subset.
# Usage field is in USD cumulative; ~0.015-0.05 per claudem smoke test.
```

```bash
# Anthropic-protocol model test (claude-style)
curl -sS -X POST -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"anthropic/claude-sonnet-4.5","max_tokens":32,
        "messages":[{"role":"user","content":"Reply with exactly the word pong"}]}' \
  https://openrouter.ai/api/v1/messages | python3 -m json.tool

# OpenAI-protocol model test (codex-style)
curl -sS -X POST -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-5","max_tokens":32,
        "messages":[{"role":"user","content":"Reply with exactly the word pong"}]}' \
  https://openrouter.ai/api/v1/chat/completions | python3 -m json.tool
```

## Confirmed working model IDs (verified live 2026-07-13)

| Model id | Protocol | First-token latency | Notes |
|---|---|---|---|
| `anthropic/claude-sonnet-4` | Anthropic / OpenAI | 11s on Anthropic-protocol | ⚠️ retired 2026-06-15 — Claude Code prints `⚠ Claude Sonnet 4 was retired`. Do not use as default. |
| `anthropic/claude-sonnet-4.5` | Anthropic / OpenAI | 1.8s | ✅ safe default |
| `anthropic/claude-sonnet-4.6` | Anthropic / OpenAI | 1.5s | ✅ brand-new, also stable |
| `anthropic/claude-opus-4.7` | Anthropic / OpenAI | 2.2s | ✅ Opus default |
| `openai/gpt-5` | OpenAI only | (Codex forces this through `--profile codexor`; fails on chatgpt-auth sessions) | see codex auth pitfall |

Provider field in verbose `--output-format=json` returns the underlying backend: `provider: "Amazon Bedrock"` for Anthropic-protocol, `provider: "openai"` for OpenAI-protocol.

## Cost per smoke test (verified 2026-07-13)

| Smoke | Prompt → response | Input tokens | Output tokens | Cost USD |
|---|---|---|---|---|
| `claudeor sonnet-4.5 "Reply with one word: pong"` | pong | 10 | 76–114 | $0.016–0.019 |
| Same prompt one-shot, 1.5–6s round-trip | – | – | – | – |

OpenRouter forwards cache reads/writes to the upstream model, so a second smoke test of the same prompt can hit the cache and cost $0.001 or less.

## Headers to set in probes

- `Authorization: Bearer <OPENROUTER_API_KEY>`
- `Content-Type: application/json`
- (Anthropic-protocol only) `anthropic-version: 2023-06-01` — OpenRouter accepts it and the path still accepts requests without, but adding it future-proofs against any Anthropic-protocol v-strict mode.
- Optional: `HTTP-Referer: https://github.com/jleechanorg/<repo>` and `X-Title: <tool-name>` per OpenRouter attribution policy — these surface on the OpenRouter dashboard.

## Probe scripts

- `scripts/probe_openrouter.sh` — runs the auth-key + catalog + both protocol smoke tests.
- `scripts/parse_claude_verbose.py` — extracts `ASSISTANT_TEXT`, `COST`, `IS_ERROR` from `claude --verbose --output-format=json` output (used to verify `claudeor` actually completes against OpenRouter despite non-TTY stdout swallowing).

## When this surface changes

- A new model id (`anthropic/claude-opus-4.8`, `openai/gpt-5.1`, etc.) appears in the catalog → update the **default model id** in `~/bin/<wrapper>` and the matching `~/.bashrc` function.
- The `/api/v1/messages` path starts rejecting a previously-accepted model id → log to `references/openrouter-surfaces.md`, switch default to the next stable version, file a bug with OpenRouter.
- Anthropic-retirement warnings appear in stderr → switch default model (this happened to `claude-sonnet-4` on 2026-06-15).
