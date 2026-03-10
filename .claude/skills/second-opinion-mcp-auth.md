---
description: How second-opinion MCP authentication works — Firebase JWT lifecycle, auto-refresh, and openclaw-mcp-adapter integration
type: reference
scope: project
---

# Second-Opinion MCP Authentication

## Overview

The second-opinion MCP server (`${SECOND_OPINION_MCP_URL}`) is a Cloud Run service backed by Firebase Auth (project `ai-universe-b3551`). Every request requires `Authorization: Bearer <Firebase ID token>`.

Authentication is handled by `auth-cli.mjs` — a Node.js CLI that manages the full OAuth/refresh lifecycle locally.

## Token Lifecycle

| Token | Expiry | Behaviour |
|-------|--------|-----------|
| **ID token** (`idToken`) | 1 hour (Firebase policy) | Used as the `Bearer` token in HTTP requests |
| **Refresh token** (`refreshToken`) | Months (Google Sign-In; expires only on revocation or ~6-month inactivity) | Used silently to obtain new ID tokens |

Both tokens are stored together in `~/.ai-universe/auth-token-ai-universe-b3551.json`:

```json
{
  "idToken": "<1-hour JWT>",
  "refreshToken": "<months-long token>",
  "user": { "uid": "...", "email": "...", "displayName": "..." },
  "createdAt": "...",
  "expiresAt": "...",
  "firebaseProjectId": "ai-universe-b3551"
}
```

## How Auto-Refresh Works

`auth-cli.mjs token` calls `readTokenData({ autoRefresh: true })`:

1. Reads `~/.ai-universe/auth-token-ai-universe-b3551.json`
2. If `now < expiresAt` → returns `idToken` immediately (no network call)
3. If expired → POSTs `{ grant_type: "refresh_token", refresh_token }` to `https://securetoken.googleapis.com/v1/token`
4. Saves new `idToken` + rotated `refreshToken` back to disk
5. Returns fresh `idToken` to stdout

This means a single login lasts months with zero user interaction.

## Common Commands

```bash
# Initial login (opens browser, one-time per machine)
node ~/.claude/scripts/auth-cli.mjs login

# Get a valid token (auto-refreshes silently if expired)
TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)

# Check status / expiry
node ~/.claude/scripts/auth-cli.mjs status

# Force manual refresh
node ~/.claude/scripts/auth-cli.mjs refresh

# Test connectivity to MCP server
node ~/.claude/scripts/auth-cli.mjs test
```

## Using the Token in HTTP Requests

```bash
TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)
http POST "${SECOND_OPINION_MCP_URL}" \
  "Accept:application/json, text/event-stream" \
  "Authorization:Bearer $TOKEN" \
  < /tmp/mcp_request.json \
  --timeout=180 \
  --print=b
```

## openclaw-mcp-adapter Integration (ORCH-d5b)

The `openclaw-mcp-adapter` config currently only sets an `Accept` header:

```json
"headers": {
  "Accept": "application/json, text/event-stream"
}
```

A static `${SECOND_OPINION_MCP_TOKEN}` env var would expire after 1 hour.

**Preferred fix**: if `openclaw-mcp-adapter` supports a `tokenCommand` field, set:

```json
"tokenCommand": "node ~/.claude/scripts/auth-cli.mjs token"
```

This calls `auth-cli.mjs token` before each request — returns instantly from cache if valid, silently refreshes via the months-long refresh token if expired.

Until `tokenCommand` support is confirmed, the workaround is to start the gateway with a fresh token injected:

```bash
export SECOND_OPINION_MCP_TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)
openclaw gateway run
```

…and re-export hourly (e.g. via a cron job calling `auth-cli.mjs token`).

## Script Location

| Location | Notes |
|----------|-------|
| `~/.claude/scripts/auth-cli.mjs` | User-global, used by Claude Code sessions |
| `~/projects/ai_universe/scripts/auth-cli.mjs` | Source of truth upstream |

Keep in sync: `cp ~/projects/ai_universe/scripts/auth-cli.mjs ~/.claude/scripts/`

## Environment Variables Required

| Variable | Purpose |
|----------|---------|
| `VITE_AI_UNIVERSE_FIREBASE_API_KEY` | Firebase web API key for `ai-universe-b3551` |
| `SECOND_OPINION_MCP_URL` | MCP server URL (injected into openclaw-mcp-adapter config) |

## Related

- `~/.claude/skills/ai-universe-auth.md` — login walkthrough
- `~/.claude/skills/ai-universe-second-opinion-workflow.md` — full `/secondo` workflow
- ORCH-d5b — tracking the openclaw-mcp-adapter tokenCommand investigation
