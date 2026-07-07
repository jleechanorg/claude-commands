---
description: Steer work on $USER's MacBook via SSH (mirrors /linux but targets the MacBook). Auto-detects local-vs-remote and chains to jeff-ubuntu when needed.
type: prompt
---

Read ~/.claude/skills/mac-remote/SKILL.md then execute the user's request on the MacBook.

The connection is: `ssh macbook` (passwordless alias, configured in ~/.ssh/config — see SKILL.md setup section if not present).

Auto-detect:
- If running locally on the MacBook (uname == Darwin, hostname == jeffreys-macbook-pro), no SSH needed — execute commands directly.
- If running on jeff-ubuntu or any other machine, SSH into the MacBook first.

For chained ops (e.g. "install this on Mac and then deploy to jeff-ubuntu"), SSH to MacBook then chain `ssh jeff-ubuntu` from inside the Mac.

Execute the task directly — do not hand commands back to the user to run manually.