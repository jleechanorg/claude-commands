---
description: Evidence standards slash command — run /evidence_review on a file or directory
aliases: [es]
type: slash
execution_mode: immediate
---

# /es — Evidence Standards

Run `/evidence_review` on a file, directory, or subject to verify claims have real evidence
(not just assertions).

**Usage**: `/es <path-or-description>`

Read `~/.claude/skills/evidence-standards/SKILL.md` and execute the full workflow — evidence
class table, unit-only disallow rule (3 exceptions), gist-first publication, and the mandatory
reconfirm-what-evidence-proves rule all live there.

**Examples**:
- `/es src/rewards/box.py` — review evidence standards compliance
- `/es "the LLM sprite system works"` — verify claim about a feature
- `/es .` — review current directory
