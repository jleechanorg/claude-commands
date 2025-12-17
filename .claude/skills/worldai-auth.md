---
description: Authenticate with the Secondary Firebase project for Project B
type: setup
scope: project
---

# Secondary Project Authentication Setup

Use this skill when you need an ID token for your **Secondary Project** Firebase project (`your-secondary-project-id`). The same `auth-cli.mjs` script supports multiple projects—the secondary project just requires the `--project your-secondary-project-id` flag.

## Commands

```bash
# Login for Secondary Project
node scripts/auth-cli.mjs login --project your-secondary-project-id

# Get a token (auto-refreshes)
node scripts/auth-cli.mjs token --project your-secondary-project-id

# Check status
node scripts/auth-cli.mjs status --project your-secondary-project-id
```

Tokens are stored at `~/.ai-universe/auth-token-your-secondary-project-id.json` with owner-only permissions. If you see project mismatch errors, re-run login with the `--project your-secondary-project-id` flag.
