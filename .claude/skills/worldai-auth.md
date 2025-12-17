---
description: Authenticate with the PROJECT_B Firebase project for Your Project
type: setup
scope: project
---

# PROJECT_B Authentication Setup

Use this skill when you need an ID token for the **PROJECT_B** Firebase project (`secondary-firebase-project`). The same `auth-cli.mjs` script supports multiple projects—PROJECT_B just requires the `--project secondary-firebase-project` flag.

## Commands

```bash
# Login for PROJECT_B
node scripts/auth-cli.mjs login --project secondary-firebase-project

# Get a token (auto-refreshes)
node scripts/auth-cli.mjs token --project secondary-firebase-project

# Check status
node scripts/auth-cli.mjs status --project secondary-firebase-project
```

Tokens are stored at `~/.ai-universe/auth-token-secondary-firebase-project.json` with owner-only permissions. If you see project mismatch errors, re-run login with the `--project secondary-firebase-project` flag.
