---
description: Evidence Review — alias that invokes the evidence-review skill (with codex/claude fallback)
type: orchestration
execution_mode: immediate
---

# /er — Evidence Review Alias

Thin alias. The canonical enforcement rules live in the `evidence-review` skill.

**Usage**: `/er [subject or path]`

## Action

Execute these steps in order:

1. Resolve the skill path:
   - Use `~/.claude/skills/evidence-review/SKILL.md` when it exists.
   - Otherwise use `.claude/skills/evidence-review.md`.
   - If neither path exists, stop and report that the evidence-review skill is missing.
2. Load the selected `SKILL.md` content into this command context as the active evidence-review rules.
3. Invoke the evidence-review dispatcher against `$ARGUMENTS` using those loaded rules. Follow `.claude/commands/evidence_review.md` dispatch behavior: codex first, claude fallback.
