---
description: Verify the two current-head PR green gates
type: verification
execution_mode: immediate
---

# /green

Read and execute
`~/.claude/skills/pr-green-definition/SKILL.md`.

`/green` has exactly two gates, both evaluated at the same current PR HEAD:

1. every required CI check is terminal and successful;
2. GitHub reports `mergeable == MERGEABLE`.

CodeRabbit, Bugbot, evidence, `/advice`, and review-thread state are not
additional `/green` gates. Treat review bots as advisory and handle evidence,
advice, and thread cleanup during the draft-quality phase.

If no PR number is supplied, resolve the PR from the current branch. Report the
full PR URL, HEAD SHA, each gate, and an overall `GREEN` or `NOT GREEN`
verdict. Never merge as part of `/green`.
