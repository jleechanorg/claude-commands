---
name: launchd-plist-template
description: "Use when installing/modifying any ~/Library/LaunchAgents plist. Requires template in repo that owns the job; @HOME@ placeholders; install-launchagents.sh cleanup."
---

# launchd jobs — plist templates must live in a repo


Every plist installed to `~/Library/LaunchAgents/` must have a **template** (using `@HOME@` placeholders) committed to the repo that owns the job:
- Hermes gateway / scripts → `~/.hermes/launchd/<label>.plist`
- MCP daemons → `~/.config/mcp-daemon/` (tracked repo or script)
- Any new job → identify the owning repo and commit the template there before installing

**Why**: Missing repo template breaks `install-launchagents.sh` cleanup (2026-06-09 incident — `launchd/ai.hermes.prod.plist` absent let orphan `ai.hermes.gateway` plist survive every deploy). The `/launchd` skill enforces this: Step 4 is "commit plist template to repo."
