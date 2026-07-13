---
name: session-start-protocol
description: "Use at the start of bug-fix/feature sessions. State primary deliverable (file + behavior) before code; time-box CI gate work to 30 min."
---

# Session start — declare primary deliverable first


At the start of any bug-fix or feature session, **state the primary deliverable** (specific file + behavior to change) before writing any code or creating any PR. PR lifecycle work (CI fixes, harness PRs, review responses) is secondary — it must never displace the primary deliverable.

**CI gate time-box**: If fixing gate failures on any PR (including prerequisite/harness PRs) consumes >30 min and the primary deliverable (production code in the target files) has zero commits, surface the gap immediately: "Primary deliverable not yet written — pausing gate work." Do not continue chasing CI on secondary PRs at the expense of the session's core goal.

**Governing doc first**: For multi-PR feature work, read the governing roadmap/design doc before executing. The doc owns the file-exclusive ownership map, prerequisite gates, and concurrency constraints. Improvising without it is a harness violation.
