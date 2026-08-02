# OpenRouter → Claude Code picker: research findings (2026-07-21)

Condensed from Anthropic's official docs (researched via `aside browser` headless,
canonical URL `code.claude.com/docs/en/llm-gateway-protocol` § Model discovery and
`code.claude.com/docs/en/model-config` § Add a custom model option).

## What the picker actually is (Claude Code v2.1.212)

The `/model` picker is a fixed-slot TUI overlay, not a free-form model list:

| Slot | Row | Source env var |
|------|-----|-----------------|
| 1 | Default (recommended) | account default / `model` in settings |
| 2 | Opus alias | `ANTHROPIC_DEFAULT_OPUS_MODEL` |
| 3 | Fable | built-in (Fable 5) |
| 4 | Sonnet alias | `ANTHROPIC_DEFAULT_SONNET_MODEL` |
| 5 | Haiku alias | `ANTHROPIC_DEFAULT_HAIKU_MODEL` |

The picker shows ~5 visible rows; scrolling doesn't reveal more. To get a non-Claude
model into a slot, bind it via the alias env var. To show TWO non-Claude models
simultaneously, bind them to different slots:

```bash
export ANTHROPIC_DEFAULT_OPUS_MODEL=moonshotai/kimi-k3     # → slot 2 = Kimi
export ANTHROPIC_DEFAULT_SONNET_MODEL=z-ai/glm-5.2         # → slot 4 = GLM
# Picker now shows both visible at once.
```

## `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` — what it actually does

When set, Claude Code calls `GET /v1/models?limit=1000` on the gateway at startup,
caches to `~/.claude/cache/gateway-models.json`, and adds returned entries to the picker
as "From gateway" rows. BUT the picker hard-caps at ~5 visible rows, so the
discovery cache feeds the picker uniformly — the alias slots still take precedence
in display.

### Filter rule (the wall Claude Code enforces)

> Claude Code reads `id` and the optional `display_name` from each entry in the
> response's `data` array, **and ignores entries whose `id` doesn't begin with
> `claude` or `anthropic`**.

This is the reason OpenRouter's `z-ai/glm-5.2` and `moonshotai/kimi-k3` are
silently dropped. Direct workaround: the **gateway** must rewrite IDs before
returning them to Claude Code. Verified working approach:

```python
# In the gateway proxy, on /v1/models response:
for entry in data["data"]:
    mid = entry.get("id", "")
    if not (mid.startswith("claude") or mid.startswith("anthropic")):
        entry["id"] = "anthropic-" + mid            # synthetic Claude Code-compatible ID
        entry["display_name"] = mid                 # picker shows the original slug
# Then on /v1/messages request body, strip "anthropic-" before forwarding upstream.
```

The `anthropic-` (hyphen) prefix is deliberate: Claude Code's filter accepts it
(`startswith("anthropic")`), but the original OpenRouter slug is what gets
forwarded to upstream. The hyphen distinguishes the synthetic picker-id from
real `anthropic/claude-*` IDs.

### When discovery does NOT fire

Per Anthropic docs, discovery is skipped when ANY of:
- A `CLAUDE_CODE_USE_*` provider variable is set (even if `ANTHROPIC_BASE_URL` is too)
- `ANTHROPIC_BASE_URL` is unset OR points at `api.anthropic.com` (first-party)
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` is set
- An organization policy disables it

### Caching

Discovery cache: `~/.claude/cache/gateway-models.json` (or
`%USERPROFILE%\.claude\cache\gateway-models.json` on Windows). Refreshed on
each startup. Delete the file to force fresh discovery after changing the
gateway's model list.

## `ANTHROPIC_CUSTOM_MODEL_OPTION` — singular only

Setting `ANTHROPIC_CUSTOM_MODEL_OPTION=<id>` adds ONE additional entry to the
picker. There is no plural form, no comma-separated syntax. Verified in
`code.claude.com/docs/en/env-vars`:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_CUSTOM_MODEL_OPTION` | Single model ID to add |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` | Display name (defaults to model ID) |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION` | Description text |
| `ANTHROPIC_CUSTOM_MODEL_OPTION_SUPPORTED_CAPABILITIES` | Feature gate override |

The docs note: "Use this to make a non-standard or gateway-specific model
selectable **without replacing built-in aliases**." Singular — use the
alias env vars for multiple models.

## `availableModels` is a RESTRICTION, not an extension (for non-Mantle models)

The `availableModels` setting bounds which model IDs the user can select,
but for non-Mantle Anthropic-Anthropic-Claude deployments it's a
restrict-only list. The Mantle ID exception (where `anthropic.*` entries
in `availableModels` ADD picker rows) is specific to Amazon Bedrock
Mantle endpoint and doesn't generalize to OpenRouter.

## Verified dual-model picker result (round 3, 2026-07-21)

After applying the discovery-rewrite patch to `or-anthropic-proxy.py` and
launching Claude Code with the alias env vars, the picker shows:

```
1. Default (recommended)  Use the default model (currently moonshotai/kimi-k3[1m])
❯ 2. moonshotai/kimi-k3 ✔   Custom Opus model
   3. Fable                  Fable 5 · Most capable for your hardest and longest-running tasks
   4. z-ai/glm-5.2           Custom Sonnet model
   5. z-ai/glm-4.5-air       Custom Haiku model
```

Both Kimi K3 and GLM 5.2 visible simultaneously. The `anthropic-` prefix
on IDs (set by the proxy) satisfies Claude Code's filter; the `display_name`
field (also set by the proxy) keeps the picker text human-readable.

## Codex equivalent — does NOT exist (verified 2026-07-21)

`learn.chatgpt.com/codex/config-reference` was searched for any
`model_picker` / `custom_providers` / `model_presets` / `extra_model`
config — none exist. Codex v0.144.5's `/model` picker is hard-coded to
ChatGPT-side models only. Kimi/GLM access is via wrapper scripts
(`codexk`, `codexo`) only. A codex-rs source patch would be required to
add non-ChatGPT entries to the picker; out of scope for the pilot.

## Source URLs (verified 2026-07-21)

- `https://code.claude.com/docs/en/model-config` (canonical Anthropic docs)
- `https://code.claude.com/docs/en/llm-gateway-protocol` (gateway protocol)
- `https://code.claude.com/docs/en/env-vars` (env var reference)
- `https://learn.chatgpt.com/codex/config-reference` (Codex config — verified
  no picker extension knobs exist)
