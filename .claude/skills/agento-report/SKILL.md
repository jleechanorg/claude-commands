---
name: agento-report
description: Use when reporting live Agent Orchestrator pull-request status and zero-touch-by-operator metrics.
type: skill
---

# Agento Status Report

Report live state for open PRs in `jleechanorg/agent-orchestrator` and merged
zero-touch metrics for the requested window.

## Per-PR Status

Resolve the current HEAD, required CI checks, and mergeability. A PR is green
only when:

1. every required non-advisory check at HEAD is terminal and successful;
2. GitHub reports the PR mergeable with no conflicts.

Report CodeRabbit, Bugbot, `/er`, `/advice`, and unresolved threads in a
separate **Draft quality / advisory** column. They do not redefine `/green`.

Use REST when GraphQL quota is exhausted:

```bash
gh api "repos/jleechanorg/agent-orchestrator/pulls?state=open&per_page=30"
gh api "repos/jleechanorg/agent-orchestrator/pulls/NUM"
gh api "repos/jleechanorg/agent-orchestrator/commits/SHA/check-runs"
```

Classify each open PR as `GREEN`, `CI_PENDING`, `CI_FAILED`, or `CONFLICT`.
Bind the row to its exact HEAD SHA and full PR URL.

## Zero-Touch

Use the canonical `zero-touch/SKILL.md` actor audit. Report:

- merged PRs in the requested window;
- zero-touch versus operator-assisted counts;
- the resulting percentage;
- concrete operator actions that changed classification.

Display the report inline. Post externally only when the user explicitly asks
for that destination.
