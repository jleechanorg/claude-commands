---
name: hermes-models
description: Hermes agent model configs — which work, which are broken/quota-limited, and how to switch
type: reference
---

# Hermes Model Reference

**Canonical config on this machine**: `~/.hermes_prod/config.yaml` (prod), `~/.hermes/config.yaml` (staging)

**Auth profiles**: `~/.hermes_prod/.env` (secrets), `~/.hermes_prod/auth-profiles.json` if present

## Current config on this machine (as of 2026-04-13)

```yaml
model:
  default: MiniMax-M2.7
  provider: minimax
```

**Provider**: `minimax` with `MiniMax-M2.7` — API key auth via `MINIMAX_API_KEY` in `~/.hermes_prod/.env`

## Provider status table

| Model | Status | Auth | Notes |
|---|---|---|---|
| `MiniMax-M2.7` | ✅ **CURRENT** | `api_key` → `MINIMAX_API_KEY` | Live in `~/.hermes_prod/config.yaml` |
| `MiniMax-M2.7-highspeed` | ❌ **PLAN NOT SUPPORTED** | `api_key` | HTTP 500 error 2061 — plan does not support this tier |
| `gemini-3-flash-preview` | ✅ Available via AO | API key | Used by AO workers via `modelByCli.gemini` |

## How to switch primary model

### Step 0 — PROBE FIRST (mandatory)

**Verify the model is available on the current plan before adding to config:**

```bash
KEY=$(python3 -c "import os; print(os.environ.get('MINIMAX_API_KEY',''))")
curl -s -o /dev/null -w "%{http_code}" \
  https://api.minimax.io/anthropic/v1/messages \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7-highspeed","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}'
```

- **200** → model available; proceed
- **500 with error 2061** → plan does not support this model; do NOT add to config
- **403/401** → auth issue; check `MINIMAX_API_KEY`

### Step 1 — Update config (surgical)

```bash
HERMES_HOME=/Users/jleechan/.hermes_prod hermes config set model.default <model-name>
```

Or edit `~/.hermes_prod/config.yaml` directly.

### Step 2 — Restart gateway

```bash
launchctl bootout gui/$(id -u)/ai.hermes.prod
sleep 2
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.prod.plist
# or for non-launchd:
HERMES_HOME=/Users/jleechan/.hermes_prod hermes gateway run --replace &
```

### Step 3 — Verify

```bash
HERMES_HOME=/Users/jleechan/.hermes_prod hermes gateway status
HERMES_HOME=/Users/jleechan/.hermes_prod hermes status  # shows model + Slack connectivity
```

## Gateway health check

```bash
curl -fsS -m 8 http://127.0.0.1:18789/health   # only works if Hermes is on 18789
HERMES_HOME=/Users/jleechan/.hermes_prod hermes gateway status
```

**Note**: Hermes prod gateway runs as `ai.hermes.prod` launchd service. Hermes STAGING runs as `ai.hermes-staging`. Only ONE should be active at a time — Slack token conflicts if both claim the same bot.

## Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 400 on Slack mention | Wrong model for context, or MiniMax rejecting the model | Check `config.yaml` model.default matches a plan-supported model |
| Gateway not responding | Wrong HERMES_HOME or port conflict | Verify `HERMES_HOME=/Users/jleechan/.hermes_prod` and only one gateway running |
| Slack bot not replying | Bot token mismatch or gateway not started | Check `hermes gateway status` and `hermes status` |
| HTTP 529 overloaded | MiniMax API overloaded | Retry with backoff; reduce concurrency |
