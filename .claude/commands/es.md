---
description: Evidence standards slash command — run /evidence_review on a file or directory
aliases: [es]
type: slash
execution_mode: immediate
---

# /es — Evidence Standards

Run `/evidence_review` on a file, directory, or subject to verify claims have real evidence (not just assertions).

**Usage**: `/es <path-or-description>`

**Examples**:
- `/es src/rewards/box.py` — review evidence standards compliance
- `/es "the LLM sprite system works"` — verify claim about a feature
- `/es .` — review current directory

**Why**: Before claiming a PR is "working" or "fixed," evidence must prove production behavior — not just test assertions or code presence. See `~/.claude/skills/evidence-standards.md` for the full standard.
