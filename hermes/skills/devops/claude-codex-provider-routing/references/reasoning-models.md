# Reasoning models on OpenRouter (Kimi K3, DeepSeek R1, o1-series)

Session-specific detail for the **reasoning-model class** of OpenRouter providers. Captured while wiring `claudek` for `moonshotai/kimi-k3` on 2026-07-16. Read this before defaulting any new wrapper to a reasoning model, and before assuming a smoke-test "silent exit" means the wrapper is broken.

## Kimi K3 verification transcript (2026-07-16)

```text
model: moonshotai/kimi-k3
provider: Moonshot AI
context_length: 1048576              # 1M tokens
input_modalities: ["text", "image"]  # vision support
output_modalities: ["text"]
architecture.modality: "text+image->text"
canonical_slug: moonshotai/kimi-k3-20260715
created: 1784215858                   # 2026-07-15, one day before this session
```

**Direct OpenRouter `/v1/chat/completions` probe** — `{"model":"moonshotai/kimi-k3","messages":[{"role":"user","content":"What is 17 * 23? Just the number."}],"max_tokens":2048,"temperature":0}`:

```json
{
  "model": "moonshotai/kimi-k3",
  "choices": [{"index": 0, "finish_reason": "stop", "message": {
    "role": "assistant",
    "content": "391",
    "reasoning": "The user wants a simple arithmetic answer: 17 * 23.\n\n17 * 23 = 17 * 20 + 17 * 3 = 340 + 51 = 391.\n\nThey asked for just the number, so I should just answer \"391\"."
  }}],
  "usage": {
    "prompt_tokens": 97, "completion_tokens": 72, "total_tokens": 169,
    "cost": 0.001371,
    "completion_tokens_details": {"reasoning_tokens": 56, "image_tokens": 0, "audio_tokens": 0}
  }
}
```

**Anthropic-format `/v1/messages` probe** (what Claude Code uses) — `{"model":"moonshotai/kimi-k3","max_tokens":2048,"messages":[{"role":"user","content":"Reply with exactly: pong-kimi-k3-claudek"}]}`:

```json
{
  "model": "moonshotai/kimi-k3",
  "stop_reason": "end_turn",
  "content": [
    {"type": "thinking", "thinking": "The user wants me to reply with exactly: pong-kimi-k3-claudek ... this is some kind of ping/echo test ..."},
    {"type": "text", "text": "pong-kimi-k3-claudek"},
    {"type": "redacted_thinking", "data": "openrouter.reasoning:eyJ0ZX...cHMg"}
  ],
  "usage": {
    "input_tokens": 97, "output_tokens": 159,
    "output_tokens_details": {"thinking_tokens": 135},
    "cost": 0.002676
  }
}
```

Three content blocks per assistant turn: `thinking` (chain-of-thought), `text` (answer), `redacted_thinking` (OpenRouter's redacted summary blob, encrypted base64).

## Diagnostic ladder — when a reasoning-model wrapper is silent

Use this order before declaring the wrapper broken:

1. **Probe the raw API directly** (curl + `/v1/chat/completions` or `/v1/messages`). If it returns a real answer → wrapper is probably fine, see step 2.
2. **Probe via `--verbose --output-format=json`** through Claude Code:
   ```bash
   bash -lic 'claudek --print --verbose --output-format=json "Reply with exactly: pong" 2>&1' \
     | python3 ~/.hermes/skills/devops/claude-codex-provider-routing/scripts/parse_claude_verbose.py
   ```
   If `ASSISTANT_TEXT: 'pong'` prints → wrapper works, the silent `-p` mode is the issue.
3. **Check for the "connectors disabled" warning** (cosmetic; appears whenever `ANTHROPIC_API_KEY` is set). Not the cause of silence.
4. **Inspect the JSON content block shape** — Claude Code 2.1.207 expects either a flat `text` field or Anthropic-format `content: [{type: text, ...}]`. If the provider emits the chain-of-thought as a separate `type: thinking` block BEFORE the `text` block, Claude Code's display layer may be skipping it. Workaround: use `--verbose --output-format=json` and grep for `assistant_text` or the parsed Python helper.
5. **Verify the model id is current** — reasoning models are often re-released under new slugs (`kimi-k3-20260715`). Stale ids return 200 with empty content or 404.

## Launch-window behavior

New reasoning models almost always rate-limit hard for 1-2 weeks after release. Specifically for Kimi K3 on 2026-07-16:

```json
HTTP 429
{"error":{"code":429,"metadata":{
  "raw":"moonshotai/kimi-k3 is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate your rate limits: https://openrouter.ai/settings/integrations",
  "provider_name":"Moonshot AI",
  "is_byok": false,
  "retry_after_seconds": 1,
  "headers": {"Retry-After": "1"}
}}}
```

**Symptom:** every call returns 429 for the first ~30-60 seconds, then suddenly works. Naive single-shot probes will report success/failure inconsistently.

**Fix for probe scripts:** retry with exponential backoff starting at 3s, capped at 30s, max 6 attempts. See `scripts/probe_openrouter.sh` for the working pattern.

**Fix for client wrappers:** the wrapper itself shouldn't need this — Claude Code's HTTP layer retries 429s. If your wrapper hangs during a fresh-model launch window, wait 60s and retry; if it still fails, escalate to `ao spawn` rather than blocking.

## Upstream-only reasoning-mandatory models

Some reasoning providers reject attempts to disable chain-of-thought at the API layer. Verified with Kimi K3:

```
POST /v1/chat/completions
{"model": "moonshotai/kimi-k3", ..., "reasoning": {"enabled": false}}
→ HTTP 400
{"error":{"message":"Reasoning is mandatory for this endpoint and cannot be disabled.","code":400}}
```

**Implication for wrappers:** don't try to silence reasoning via API params. Set `max_tokens` ≥ 2× the expected answer length to leave room for both thought chain and final answer. If `max_tokens` is too small, the model will hit the budget on thinking and emit `finish_reason: "length"` with `content: null` — same silent-exit symptom on the raw API.

## Naming convention (2026-07-16)

For new reasoning-model wrappers:

| Provider | Family letter | Example wrapper |
|---|---|---|
| Moonshot | `k` (Kimi) | `claudek` (Kimi K3) |
| DeepSeek | `r` (Reasoning) | `clauder` (R1) — pick a letter that doesn't collide |
| OpenAI | `o` (o1/o3) | `claudeo` is taken (legacy GLM alias) → use `claudeoi` or similar |

Don't reuse the provider suffix letter from the non-reasoning model (`g` for GLM, `m` for MiniMax) — pick a letter that maps to the model family. The "family letter" convention is documented in the SKILL.md naming section.

## Bead follow-up

`$USER-3e4o` — Claude Code `-p` silent with reasoning models. Open either: (1) patch Claude Code 2.1.207 to thread `thinking` blocks into stdout, or (2) ship a wrapper that strips `thinking`/`redacted_thinking` blocks before forwarding. As of 2026-07-16 neither is done.

## Cost data (2026-07-16)

- 17 × 23 → 391: 169 tokens (97 prompt + 72 completion, 56 reasoning), $0.001371
- pong reply (Anthropic-format): 256 tokens (97 prompt + 159 completion, 135 thinking), $0.002676

Kimi K3 is **substantially more expensive per inference** than GLM 5.2 or Sonnet 4.5 due to mandatory reasoning tokens. Treat it as a research/quality task wrapper, not a default — set `ANTHROPIC_DEFAULT_HAIKU_MODEL=...` explicitly to avoid burning reasoning-budget on every subagent.
