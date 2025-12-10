---
description: Authenticate with AI Universe MCP server for multi-model commands
type: setup
scope: project
---

# AI Universe Authentication Setup

This skill provides authentication setup for the AI Universe MCP server, which powers the `/secondo` command for multi-model AI feedback.

## Prerequisites

- Node.js (>=20.0.0) installed
- Express dependency installed (`npm install`)
- Browser for OAuth flow
- Run `/localexportcommands` to install auth-cli.mjs to ~/.claude/scripts/

## Authentication Flow

> **Shared development credentials:** All `/secondo` users share the same AI Universe Firebase project for the MCP server. Do **not** modify these values unless you are provisioning a private instance; if you need a private deployment, create your own Firebase project and update the single credential block documented below.

```bash
# Canonical AI Universe credentials (obtain from secure vault/secret manager)
: "${AI_UNIVERSE_FIREBASE_PROJECT_ID:?Set AI_UNIVERSE_FIREBASE_PROJECT_ID from the shared secret vault}"
: "${AI_UNIVERSE_FIREBASE_AUTH_DOMAIN:?Set AI_UNIVERSE_FIREBASE_AUTH_DOMAIN from the shared secret vault}"
: "${AI_UNIVERSE_FIREBASE_API_KEY:?Set AI_UNIVERSE_FIREBASE_API_KEY from the shared secret vault}"
```

### 1. Initial Login

```bash
# CRITICAL: Use AI Universe Firebase credentials (not worldarchitecture-ai)
# Start browser-based OAuth authentication
# Note: Run this outside Claude Code in a regular terminal
FIREBASE_PROJECT_ID="$AI_UNIVERSE_FIREBASE_PROJECT_ID" \
FIREBASE_AUTH_DOMAIN="$AI_UNIVERSE_FIREBASE_AUTH_DOMAIN" \
FIREBASE_API_KEY="$AI_UNIVERSE_FIREBASE_API_KEY" \
node ~/.claude/scripts/auth-cli.mjs login
```

**What happens:**
- Starts local callback server on port 9005
- Opens browser to Firebase Google sign-in
- User signs in with Google account
- ID token and refresh token saved to `~/.ai-universe/auth-token.json`
- ID token expires after 1 hour (Firebase security policy)
- Refresh token enables automatic token renewal

### 2. Check Authentication Status

```bash
# Verify current authentication status
node ~/.claude/scripts/auth-cli.mjs status
```

**Output includes:**
- User information (name, email, UID)
- Token creation time
- Token expiration time
- Current validity status

### 3. Get Token for Scripts

```bash
# CRITICAL: Set AI Universe Firebase credentials
export FIREBASE_PROJECT_ID="$AI_UNIVERSE_FIREBASE_PROJECT_ID"
export FIREBASE_AUTH_DOMAIN="$AI_UNIVERSE_FIREBASE_AUTH_DOMAIN"
export FIREBASE_API_KEY="$AI_UNIVERSE_FIREBASE_API_KEY"

# Get token (auto-refreshes if expired, does nothing if valid)
TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)
echo $TOKEN
```

**Token Behavior (Exact AI Universe Repo Logic):**
- **Token Valid**: Does nothing, just returns it ✅
- **Token Expired**: Auto-refreshes using refresh token (silent, no browser popup) ✅
- **Refresh Token Expired**: Prompts for login (browser OAuth) ⚠️

This enables seamless 30+ day sessions - exact same behavior as AI Universe repo.

### 4. Manual Token Refresh

```bash
# Manually refresh token before expiration
node ~/.claude/scripts/auth-cli.mjs refresh
```

### 5. Test MCP Connection

```bash
# Verify authenticated connection to MCP server
node ~/.claude/scripts/auth-cli.mjs test
```

**Validates:**
- Authentication works
- MCP server is accessible
- Rate limit status
- Current usage and remaining requests

### 6. Logout

```bash
# Remove saved authentication token
node ~/.claude/scripts/auth-cli.mjs logout
```

## Troubleshooting

### Port 9005 Already in Use

```bash
# Find process using port 9005
lsof -ti:9005 | xargs kill -9

# Or use different port (requires code modification)
```

### Token Expired

```bash
# Get token (automatically refreshes using refresh token)
TOKEN=$(node ~/.claude/scripts/auth-cli.mjs token)

# Or manually refresh
node ~/.claude/scripts/auth-cli.mjs refresh

# If refresh token is also expired, re-login
node ~/.claude/scripts/auth-cli.mjs login
```

### Firebase Config Missing or PROJECT_NUMBER_MISMATCH

If you see errors about Firebase configuration or `PROJECT_NUMBER_MISMATCH`:

```bash
# Use AI Universe Firebase credentials (REQUIRED for /secondo)
export FIREBASE_PROJECT_ID="$AI_UNIVERSE_FIREBASE_PROJECT_ID"
export FIREBASE_AUTH_DOMAIN="$AI_UNIVERSE_FIREBASE_AUTH_DOMAIN"
export FIREBASE_API_KEY="$AI_UNIVERSE_FIREBASE_API_KEY"

# Then run login or token command
node ~/.claude/scripts/auth-cli.mjs login

# Or if you have env vars in ~/.bashrc:
source ~/.bashrc
```

**Note:** The MCP server (`ai-universe-backend-dev`) requires authentication with the `ai-universe-b3551` Firebase project, NOT `worldarchitecture-ai`.

## Rate Limits

**Authenticated Users:**
- Rate limits applied per Firebase account
- Multi-model synthesis available
- ID Token TTL: 1 hour (Firebase security policy)
- Refresh token enables automatic renewal

## Security Notes

- Token stored in `~/.ai-universe/auth-token.json`
  - ID token: 1-hour expiration
  - Refresh token: enables automatic renewal without re-authentication
- OAuth flow uses localhost callback (127.0.0.1:9005)
- Browser-based authentication (similar to gh CLI, gcloud CLI)
- Never commit authentication tokens
- Firebase security best practices enforced
- Credential ownership: the canonical credential values live in this file; if rotation is required, update this section **once** and ensure dependent scripts source the new values from here.
- Private deployments: for your own MCP server, create a separate Firebase project and replace the credential block above instead of reusing the shared development keys.

## Integration with Commands

Once authenticated, use with:
- `/secondo` - Multi-model second opinion (uses exact AI Universe auth-cli.mjs with auto-refresh)
- Direct HTTPie/curl calls to MCP server (use `node ~/.claude/scripts/auth-cli.mjs token`)

See [ai-universe-httpie.md](ai-universe-httpie.md) for HTTPie usage examples.
