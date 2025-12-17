---
description: Authenticate with a secondary Firebase project
type: setup
scope: project
---

# Secondary Firebase Project Authentication

Use this skill when you need an ID token for a **secondary Firebase project**. The auth-cli script supports multiple projects—secondary projects require the `--project <project-id>` flag.

## Commands

```bash
# Login for secondary project
node scripts/auth-cli.mjs login --project <your-secondary-firebase-project-id>

# Get a token (auto-refreshes)
node scripts/auth-cli.mjs token --project <your-secondary-firebase-project-id>

# Check status
node scripts/auth-cli.mjs status --project <your-secondary-firebase-project-id>
```

Tokens are stored at `~/.ai-universe/auth-token-<your-secondary-firebase-project-id>.json` with owner-only permissions. If you see project mismatch errors, re-run login with the correct `--project` flag.
