# Claude PR Assistant workflow approvals

When the "Claude PR Assistant" workflow is triggered from a pull request or issue comment that originates from a fork (or from a contributor whose workflows have not yet been approved), GitHub protects the repository by holding the run until someone with write access approves it. In the Actions tab this shows up as the run "needing approval" or "requiring permission to run."

## Why approval is required
- The workflow uses a third-party action (`anthropics/claude-code-action@beta`) and a stored secret (`ANTHROPIC_API_KEY`).
- GitHub automatically pauses any workflow from first-time contributors or forks before the action can access repository secrets or run potentially unsafe code.

## How to approve the run
1. Visit **Actions → Claude PR Assistant** and open the blocked run.
2. Click **Approve and run** (you must have write access to the repo).
3. After approval, GitHub re-queues the job and it executes normally.

For frequent contributors, a maintainer can grant **Workflow** permissions in the repository's settings so future runs from that fork proceed without manual approval. Otherwise, each new contributor's first run will continue to require this manual step by design.
