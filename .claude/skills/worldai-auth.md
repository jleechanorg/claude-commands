---
description: Authenticate with the WorldAI Firebase project
type: setup
scope: project
---

# WorldAI Authentication Setup

Use this skill when you need an ID token for the **WorldAI** Firebase project (`worldarchitecture-ai`). The same `auth-cli.mjs` script supports multiple projects—WorldAI just requires the `--project worldarchitecture-ai` flag.

## Commands

```bash
# Login for WorldAI
node scripts/auth-cli.mjs login --project worldarchitecture-ai

# Get a token (auto-refreshes)
node scripts/auth-cli.mjs token --project worldarchitecture-ai

# Check status
node scripts/auth-cli.mjs status --project worldarchitecture-ai
```

Tokens are stored at `~/.ai-universe/auth-token-worldarchitecture-ai.json` with owner-only permissions. If you see project mismatch errors, re-run login with the `--project worldarchitecture-ai` flag.
