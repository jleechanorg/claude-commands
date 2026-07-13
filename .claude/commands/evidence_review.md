---
description: Review evidence artifacts for a claim, then check evidence-standards compliance. Dispatches to codex via orchestration library and hard-aborts if required skills fail to load (no inline fallback).
aliases: [er]
type: orchestration
execution_mode: immediate
scope: user
---

# /evidence_review — Evidence Review + Evidence Standards

**Usage**: `/evidence_review [subject or path]`

Run an independent evidence review on the current conversation's claims, a
specific file/directory, or a described subject, then check evidence-standards
compliance, and combine both into a single verdict.

Read `~/.claude/skills/evidence-review/SKILL.md` and execute the full workflow
with the provided subject — it defines the verdict rubric, the 6 mandatory
pre-PASS checks, the 4-phase review procedure, the invocation contract (codex
dispatch → subagent fallback → mandatory evidence-standards pass → two-source
verdict synthesis), and anti-patterns to reject. Also read
`~/.claude/skills/evidence-standards/SKILL.md` (and any repo-scope
`.claude/skills/evidence-standards.md`) for the compliance pass.

## Examples

```
/evidence_review
/evidence_review PR 6198
/er $PROJECT_ROOT/tests/test_rewards_engine.py
```
