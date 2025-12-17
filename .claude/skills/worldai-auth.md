---
description: Authenticate with a secondary Firebase project for your application
type: setup
scope: project
---

# Secondary Project Authentication Setup

Use this skill when you need an ID token for a **secondary Firebase project** (e.g., `YOUR_OTHER_FIREBASE_PROJECT_ID`). The same `auth-cli.mjs` script supports multiple projects—the secondary project just requires the `--project YOUR_OTHER_FIREBASE_PROJECT_ID` flag.

## Commands

```bash
# Login for secondary project
node scripts/auth-cli.mjs login --project YOUR_OTHER_FIREBASE_PROJECT_ID

# Get a token (auto-refreshes)
node scripts/auth-cli.mjs token --project YOUR_OTHER_FIREBASE_PROJECT_ID

# Check status
node scripts/auth-cli.mjs status --project YOUR_OTHER_FIREBASE_PROJECT_ID
```

Tokens are stored at `~/.ai-universe/auth-token-YOUR_OTHER_FIREBASE_PROJECT_ID.json` with owner-only permissions. If you see project mismatch errors, re-run login with the `--project YOUR_OTHER_FIREBASE_PROJECT_ID` flag.
