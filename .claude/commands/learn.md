---
description: /learn Command
type: llm-orchestration
execution_mode: immediate
---

# /learn

Execute the `learn` skill immediately.

Resolution order:

1. User skill: `~/.claude/skills/learn/SKILL.md`
2. Repo skill: `.claude/skills/learn/SKILL.md`
3. Codex mirror: `.codex/skills/learn/SKILL.md`

The skill is the source of truth. It must capture the learning and persist it to
Claude auto-memory, optional mem0, `~/roadmap`, beads, and wiki ingest.

Do not treat wiki ingest as optional. If `~/llm_wiki` is unavailable, report the
blocker explicitly after completing the other persistence steps.
