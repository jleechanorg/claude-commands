---
description: Iterate on a PR until the two current-head green gates pass
type: quality
execution_mode: immediate
---

# /polish

Usage: `/polish [max-iterations] [PR]` (default: 5 iterations and the current
branch's PR).

For each iteration:

1. Resolve the PR URL and current HEAD.
2. Triage actionable code and review findings with `/copilot` and `/fixpr`.
3. Complete applicable draft-quality work: `/es`, `/er`, `/advice`, and
   review-thread cleanup. CodeRabbit and Bugbot feedback is advisory.
4. Commit and push any green unit; wait for current-head CI to settle.
5. Run `/green`. Stop only when required CI is successful and the PR is
   mergeable with no conflicts.

If the two gates still fail after the iteration limit, report each concrete
blocker and the current HEAD SHA.

Never merge, force-push, or describe advisory review as a `/green` gate.
