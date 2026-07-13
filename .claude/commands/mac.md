---
description: Steer work on $USER's MacBook via SSH (mirrors /linux but targets the MacBook). Auto-detects local-vs-remote and chains to jeff-ubuntu when needed.
type: skill
execution_mode: immediate
---

# /mac [request]

Steer work on $USER's MacBook via SSH.

Read `~/.claude/skills/mac-remote/SKILL.md` then execute the user's request on the MacBook.

The connection is `ssh macbook` (passwordless alias, configured in `~/.ssh/config` — see SKILL.md setup section if not present).

## Auto-detect

- Running locally on the MacBook (uname == Darwin, hostname == jeffreys-macbook-pro) — no SSH needed, execute commands directly.
- Running on jeff-ubuntu or any other machine — SSH into the MacBook first.
- Chained ops (e.g. "install this on Mac and then deploy to jeff-ubuntu") — SSH to MacBook, then chain `ssh jeff-ubuntu` from inside the Mac.

Execute the task directly — do not hand commands back to the user to run manually.
