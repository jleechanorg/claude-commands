---
description: Generate ## What Was Done and ## What to Review as a Human (only items the LLM cannot verify itself, each with "Why the LLM cannot do this:")
argument-hint: "[pr-number-or-scope]"
---

Read and follow `${CLAUDE_HOME:-$HOME/.claude}/skills/human-review-brief/SKILL.md` for `$ARGUMENTS`. Never list LLM-verifiable checks in `## What to Review as a Human`; every human item must state `Why the LLM cannot do this:`.
