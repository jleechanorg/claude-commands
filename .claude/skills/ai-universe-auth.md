---
description: Authenticate with AI Universe MCP server for multi-model commands
type: setup
scope: project
---

# AI Universe Authentication Setup

This skill provides authentication setup for the AI Universe MCP server, which powers the `/secondo` command for multi-model AI feedback.

## Prerequisites

- Node.js installed
- Firebase project configured
- Browser for OAuth flow

## Authentication Flow

### 1. Initial Login

```bash
# Start browser-based OAuth authentication
node scripts/auth-cli.mjs login
```

**What happens:**
- Starts local callback server on port 9005
- Opens browser to Firebase Google sign-in
- User signs in with Google account
- Token saved to `~/.ai-universe/auth-token.json`
- Token expires after 1 hour

### 2. Check Authentication Status

```bash
# Verify current authentication status
node scripts/auth-cli.mjs status
```

**Output includes:**
- User information (name, email, UID)
- Token creation time
- Token expiration time
- Current validity status

### 3. Get Token for Scripts

```bash
# Output token for use in other scripts
TOKEN=$(node scripts/auth-cli.mjs token)
echo $TOKEN
```

### 4. Test MCP Connection

```bash
# Verify authenticated connection to MCP server
node scripts/auth-cli.mjs test
```

**Validates:**
- Authentication works
- MCP server is accessible
- Rate limit status
- Current usage and remaining requests

### 5. Logout

```bash
# Remove saved authentication token
node scripts/auth-cli.mjs logout
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
# Simply login again to refresh
node scripts/auth-cli.mjs login
```

### Firebase Config Missing

If you see errors about Firebase configuration:

```bash
# Set environment variables
export FIREBASE_API_KEY="your-api-key"
export FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
export FIREBASE_PROJECT_ID="your-project-id"

# Or run setup script if available
./scripts/setup-firebase-config.sh
```

## Rate Limits

**Authenticated Users:**
- 60 requests per hour
- Multi-model synthesis: 1 per hour
- Token TTL: 1 hour

## Security Notes

- Token stored in `~/.ai-universe/auth-token.json`
- OAuth flow uses localhost callback (127.0.0.1:9005)
- Browser-based authentication (similar to gh CLI, gcloud CLI)
- Never commit authentication tokens
- Tokens auto-expire after 1 hour

## Integration with Commands

Once authenticated, use with:
- `/secondo` - Multi-model second opinion
- Direct HTTPie/curl calls to MCP server

See [ai-universe-httpie.md](ai-universe-httpie.md) for HTTPie usage examples.
