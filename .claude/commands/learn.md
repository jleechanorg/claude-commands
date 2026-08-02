---
description: /learn Command
type: llm-orchestration
execution_mode: immediate
---

# /learn [optional: specific learning or context]

Capture a durable learning from failures, corrections, repeated mistakes,
successful recovery patterns, or a direct request.

Read `~/.claude/skills/learn/SKILL.md` and execute the full workflow with the
provided context (or, if none was given, the most actionable failure/correction
from the recent conversation).

## Examples

```
/learn
/learn always use source venv/bin/activate
/learn playwright is installed, stop saying it isn't
```
