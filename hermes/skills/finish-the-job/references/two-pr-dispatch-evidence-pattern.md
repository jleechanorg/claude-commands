# Issue-driven two-PR dispatch evidence pattern

Use this reference when one investigation exposes multiple mechanisms and the user asks for draft PRs.

## Decision rule

Split into sibling PRs when the symptoms have different root mechanisms, even if they share a user-facing repro or code area. Create one parent tracking item and one child item per PR. Each brief must state the other PR's scope boundary.

## Required evidence chain

For each child:

1. Start from `origin/main`, not the dirty investigation checkout.
2. Write a focused RED contract and run it before the implementation when practical.
3. Push the branch before claiming a PR exists.
4. Verify the remote ref SHA independently.
5. Create a draft PR, using REST if GraphQL is rate-limited or hangs.
6. Independently read the PR back and verify branch, SHA, draft state, URL, and ancestry.
7. Query check runs directly and distinguish success from skipped. Draft checks being skipped is not green CI.
8. Scan the exact resolved PR body with the outbound-secret gate before sending.

## Root-cause honesty

Use three labels in the final report and PR body:

- **Fix:** changes the behavior causing the defect.
- **Detector:** observes/logs a defect but does not repair it.
- **Guard:** prevents a known regression or proves a structural invariant.

A detector-only PR can be a valid short-term deliverable, but it must not be described as the complete bug fix. Name the missing authoritative writer/backfill and the evidence needed to implement it.

## Dynamic LLM directives versus static system instructions

When BQ shows a mutable campaign directive in `contents[]`, do not move it into a cache-stable `system_instruction` merely because the model later failed to apply a structured state update. First separate:

- directive visibility/delivery and prompt-growth/lost-in-the-middle risk;
- structured response schema, state merge, and authoritative persistence.

Fix each mechanism in its own scope, and require real request/response evidence for claims about what the model saw or followed.

## Known operational recovery

A worker may finish the code and push both branches while hanging at `gh pr create` because the GraphQL path is rate-limited. Do not retry blindly. Verify branches, search PRs with REST, create with `gh api -X POST .../pulls -F draft=true`, and verify via REST `pulls?state=all&head=...`. Full command recipe: `../dispatch-task/references/rest-pr-create-rate-limit-fallback.md`.
