# Claude Code /model picker mechanism (verified 2026-07-21)

Sources:
- `https://code.claude.com/docs/en/model-config` (gateway model discovery section, "Add a custom model option", "Mantle model IDs")
- `https://code.claude.com/docs/en/llm-gateway-protocol` (Model discovery)
- `https://code.claude.com/docs/en/env-vars` (env var reference)
- Live test: Claude Code v2.1.212 + OpenRouter (342 models)

## Picker structure (5 visible slots)

| Slot | Source | Binds via |
|---|---|---|
| 1. Default | account-type default | `ANTHROPIC_MODEL` env / `--model` flag / `model` setting |
| 2. Opus | `ANTHROPIC_DEFAULT_OPUS_MODEL` | any model id |
| 3. Fable | built-in (`anthropic/claude-fable-5` etc.) | n/a |
| 4. Sonnet | `ANTHROPIC_DEFAULT_SONNET_MODEL` | any model id |
| 5. Haiku | `ANTHROPIC_DEFAULT_HAIKU_MODEL` | any model id |

The picker is a fixed 5-row TUI overlay. No scroll, no search box. Press `Enter` to set as default, `s` for session only, `Esc` to cancel. Up/Down arrows move between rows.

## Discovery protocol (`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`)

When set, Claude Code calls `GET /v1/models?limit=1000` on the gateway base URL at startup (3-second timeout, no redirect-following).

Response schema (Claude Code reads `id` + optional `display_name`):
```json
{
  "data": [
    {"id": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6"},
    {"id": "anthropic/claude-opus-4.8"}
  ]
}
```

**Hard filter (dropped entries):**
```python
if not (id.startswith("claude") or id.startswith("anthropic")):
    skip
```

OpenRouter returns `z-ai/glm-5.2`, `moonshotai/kimi-k3`, `openai/gpt-5.5` — all DROPPED. To pass, the proxy must add `claude-` or `anthropic-` prefix on `/v1/models` responses, then strip the prefix on `/v1/messages` request bodies.

## When discovery runs (and when it doesn't)

**Runs only when:**
- `ANTHROPIC_BASE_URL` is set to a non-Anthropic host (e.g., a gateway)
- No `CLAUDE_CODE_USE_*` provider variable is set
- `ANTHROPIC_BASE_URL` is NOT `api.anthropic.com`
- Nonessential traffic is enabled (`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is unset, no org policy blocks it)

**Cached at** `~/.claude/cache/gateway-models.json` (or `%USERPROFILE%\.claude\cache\gateway-models.json` on Windows). Refreshed each startup; falls back to cached list if `/v1/models` fails.

## Mantle exception (Bedrock only)

For Amazon Bedrock Mantle endpoint, entries in `availableModels` that start with `anthropic.` are added to the picker and routed to Mantle. This is the ONLY case where `availableModels` adds (rather than restricts) picker entries.

For non-Bedrock gateways, `availableModels` is purely a restriction: an explicit ID in the list disables its family wildcard; missing entries get filtered out.

## `ANTHROPIC_CUSTOM_MODEL_OPTION` (singular)

Adds ONE custom entry to the picker. No plural/array form exists. Companion env vars:
- `ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` — display name (defaults to model id)
- `ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION` — description (defaults to "Custom model (<model-id>)")
- `ANTHROPIC_CUSTOM_MODEL_OPTION_SUPPORTED_CAPABILITIES` — see Model configuration doc

## Picker-related known issues

1. **README checklist items 2/7 are stale for v2.1.212.** Item 2 (`/status` shows auth + base URL) — `/status` is a custom user-installed slash command for PR status, NOT the built-in model-status command. Item 7 (prompt-cache check via `claude --verbose` JSON usage output) — `--verbose` no longer emits JSON in v2.1.212; cache evidence requires OpenRouter Activity dashboard (Clerk-authed, human-only).
2. **`--effort` UI on Opus rows.** The picker shows `○ Effort not supported for anthropic/claude-opus-4.8` (no-effort mode) for some Anthropic-side models. Switching effort via picker arrow keys may not work for all models.
3. **Startup banner always says "Claude Opus 4 was retired on June 15, 2026"** when using OpenRouter Anthropic-skin models. Cosmetic; doesn't affect functionality.

## End-to-end picker recipe (proxy patch + alias env vars)

```bash
# .bashrc / .zshrc
ANTHROPIC_BASE_URL="http://127.0.0.1:8767"   # patched proxy
ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
ANTHROPIC_API_KEY="$OPENROUTER_API_KEY"
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
ANTHROPIC_DEFAULT_OPUS_MODEL="moonshotai/kimi-k3"   # picker row 2
ANTHROPIC_DEFAULT_SONNET_MODEL="z-ai/glm-5.2"       # picker row 4
ANTHROPIC_DEFAULT_HAIKU_MODEL="z-ai/glm-4.5-air"
claude
# /model → shows BOTH Kimi K3 and GLM 5.2 simultaneously
```

Without the proxy patch, only ONE of these models appears in the picker (the one bound to the first alias slot the user picks).
