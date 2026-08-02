---
name: skillify
description: /skillify — Turn any feature, script, or workflow into a properly-skilled, tested, auditable Hermes skill
type: llm-orchestration
execution_mode: immediate
---

# /skillify [target_path] [description]

Runs the 10-item skill completeness checklist against a target feature/script/workflow and creates all missing artifacts (SKILL.md, tests, evals, resolver triggers).

Read `~/.claude/skills/skillify/SKILL.md` and execute the full workflow with the provided target.

## Quick reference

| Flag | Effect |
|------|--------|
| (none) | Target `~/.claude/skills/` (Claude canonical) |
| `--hermes` | Target `~/.hermes_prod/skills/` |
| `--claude` | Explicitly target Claude skills dir |

## Example

```
/skillify ~/.hermes/scripts/deploy.sh "deploy automation for prod pushes"
```

See the skill file for the full 10-item contract, phases, quality gates, and known test-suite bugs.
