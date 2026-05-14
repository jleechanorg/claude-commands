---
description: Evidence Standards — alias that reads the evidence-standards skill
type: reference
execution_mode: immediate
---

# /es — Evidence Standards Alias

Thin alias that reads both layers of the evidence-standards skill.

**Usage**: `/es`

## Action

Read and display both layers (agents must consult both):
1. `~/.claude/skills/evidence-standards/SKILL.md` — general cross-project standards
2. `.claude/skills/evidence-standards.md` — WorldArchitect-specific standards

**Caveats**: After reading, you MUST always reconfirm by explicitly stating what the evidence proves vs what it does NOT prove.
