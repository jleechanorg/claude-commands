# Codex v0.144.5 quirks when routed through OpenRouter

## Hard wall: built-in `/model` picker is ChatGPT-only

The Codex TUI picker (`/model` command) lists ONLY ChatGPT-side models — `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.5`, `gpt-5.5-codex`, etc. No env var, no config knob, no `/v1/models` discovery can add Kimi/GLM to this picker.

To use Kimi/GLM with Codex, you must either:
1. **Use `--model <slug>` at invocation** — works but bypasses the picker
2. **Use `--profile <name>` pointing to a config with `model_provider = "openrouter"`** — the profile activates BYOK routing via `env_key`
3. **Pre-set the model in the config** — same as #2 but the profile `model = "..."` is the default

## Auth preference: ChatGPT token > OPENAI_API_KEY env

Codex v0.144.5 (and earlier) prefers the saved ChatGPT token in `~/.codex/auth.json` over the `OPENAI_API_KEY` env var. This causes:

```
The 'openai/gpt-5.5' model is not supported when using Codex with a ChatGPT account.
```

**Workaround: use a profile file** (`~/.codex/<name>.config.toml`) with:
```toml
model_provider = "openrouter"

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"
```

The `model_provider` field tells Codex to use the `openrouter` provider config (which resolves the auth via `env_key`), bypassing the saved ChatGPT token.

**Alternative workaround:** `codex logout` removes the ChatGPT token so `OPENAI_API_KEY` env takes over. But this also breaks any other codex workflow that relies on the ChatGPT login.

## Responses API vs Chat Completions

OpenRouter supports both `POST /v1/responses` (OpenAI Responses API, recommended) and `POST /v1/chat/completions` (legacy). The `wire_api` config field picks:
- `wire_api = "responses"` — Responses API (default in `or-pick`, `codexo`, `codexor`, `codexk`)
- `wire_api = "chat"` — Chat Completions (fallback if Responses errors)

If a model errors on Responses (rare for OpenRouter — most providers' Responses support is "limited"), edit the profile and switch to `"chat"`. Document this in the test notes.

## Profile file discovery

Codex loads profile files from `~/.codex/<name>.config.toml` and project `.codex/<name>.config.toml`. Invoke with `codex --profile <name>`. The `--profile` flag activates that layer on top of `~/.codex/config.toml`.

Common profile names in use:
- `codexo` — GLM 5.2 via OpenRouter (pre-existing)
- `codexor` — GPT-5 via OpenRouter (pre-existing)
- `codexk` — Kimi K3 via OpenRouter (added in this session)
- `orpick` — auto-created by `or-pick` on first codex run

## Working directory and `--skip-git-repo-check`

Codex refuses to start outside a git repo unless `--skip-git-repo-check` is passed. Common workaround: `cd ~/projects/<repo> && codex --profile <name>` or use `codex --profile <name> --skip-git-repo-check`.

## Codex startup banner

```
> _ OpenAI Codex (v0.144.5)
model:       openai/gpt-5.5 high   /model to change
directory:   /private/tmp
permissions: YOLO mode
```

The `model:` line shows the active model. `high` is the reasoning effort (configured via `--config model_reasoning_effort=high` or in the profile).

## End-to-end proof pattern

```bash
# 1. Direct via or-pick (or-claude / or-codex via --profile orpick)
or-pick codex                     # pick GPT-5.5
# 2. In the codex TUI, prompt with a known string
codex> reply with exactly three words: codex or pick works
# 3. Verify the response
> codex pick works
```

The banner's `model:` line + a clean prompt/response cycle = end-to-end proof.
