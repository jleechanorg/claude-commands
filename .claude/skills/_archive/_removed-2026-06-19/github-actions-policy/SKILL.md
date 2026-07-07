---
name: github-actions-policy
description: "Use when editing GitHub Actions in private repos. Requires self-hosted runners; flags ubuntu-latest as policy drift unless explicitly approved."
---

# Private repo Actions policy


For private repositories, GitHub Actions jobs must run on self-hosted runners by default to minimize runner costs (save money).

- Use the repo/org shared selector, for example: `${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted","self-hosted-mikey"]') }}`
- Do not use `ubuntu-latest` or other GitHub-hosted runners in a private repo unless the user explicitly approves a specific exception
- Treat any mixed routing pattern like "PRs on GitHub-hosted, pushes on self-hosted" as a routing decision that requires explicit user approval
- When reviewing or editing private-repo workflows, flag GitHub-hosted runner usage as policy drift unless there is documented approval
