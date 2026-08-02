---
name: pr-scope-verification
description: |
  Use when a user asks "verify PR #X covers Y; report gaps", "does PR #X implement
  feature Y?", or any scope/coverage verification request. Performs a read-only
  diff audit against the PR head and merge base, then emits a structured JSON gap
  report with explicit file:line citations for every gap. Trigger patterns include
  "verify PR covers X", "does PR cover Y", "audit PR against these requirements",
  "scope check for PR #X", and "does this PR actually fix X". This skill covers the
  audit pattern; it does NOT cover code quality review (use github-code-review)
  or PR lifecycle management (use github-pr-workflow).
category: github
---

# PR Scope Verification

Read-only audit workflow for answering "does PR #X cover Y?" with citations.
Never infer coverage from PR title, description, or branch name alone — always
verify against the actual diff between the PR head and the merge base.

## When to use

- "Verify PR #X covers Y; report gaps"
- "Does PR #X implement feature Y?"
- "Audit PR #X against this checklist"
- "Is claim Y covered by PR #X?"
- "Scope check for PR #X — does it actually address Z?"
- Any time the user wants explicit, citation-backed coverage flags

## Workflow

1. **Locate the worktree.** Find the shared worktree (often
   `/private/tmp/pr-cluster-wt-XXXX` or similar). `cd` into it. Run
   `git log -1 --format='%H%n%D%n%s'` and `git status -sb` to confirm
   the worktree state. Note: the worktree may be detached
   (`## HEAD (no branch)`).

2. **Resolve correct refs.** Detached HEADs are common in shared
   worktrees. Use `git rev-parse HEAD` and `git rev-parse origin/main`
   (or whatever the actual target branch is) to get explicit SHA refs.
   Then `git log origin/main..HEAD --oneline` enumerates commits, and
   `git diff --stat origin/main..HEAD` gives the file-level change set.

3. **Read every changed file's diff.** Use
   `git diff origin/main..HEAD -- <path>` for each file in the stat
   output. Don't stop at the first file — coverage claims often span
   prompt files, schemas, and tests.

4. **Search for specific terms across the entire diff.** When the
   user's claim involves a specific concept (e.g. "stress arcs",
   "Want/Fear/Boundary", "insecurity-driven"), run:
   `git diff origin/main..HEAD | grep -inE "<term1>|<term2>|..."`
   to find every line touching the concept. This catches indirect
   coverage that you'd miss reading files linearly.

5. **Distinguish pre-existing content from new additions.** This is
   the most critical pitfall. A line that appears as a `-removed line`
   followed by an identical `+added line` is PRE-EXISTING content that
   was touched but not added by the PR. Don't count it as new coverage.
   The `-` and `+` lines for the same content reveal the original line
   number on the base side.

6. **Map each user claim to an explicit coverage flag.** Build a list
   of the user's specific concepts. For each one, set
   `covers_<claim>: true|false`:
   - `true` → cite the file:line where the new coverage appears.
   - `false` → state which diff hunks were checked and that none
     mention the concept.

7. **Emit structured JSON.** Use the schema in
   `references/output-template.md`. Required fields: `pr_url`,
   `head_sha`, `base_sha`, `covers_<claim>` flags, `gaps` array,
   `recommendation`, `blockers`.

8. **Cite every gap.** No gap claim without a file:line citation.
   Vague "PR doesn't cover X" reports are useless for deciding whether
   to push a follow-up or close the PR.

## Pitfalls

- **Don't infer coverage from PR title.** PR titles are short
  summaries. "fix(deps): pin mcp<2.0.0" might include unrelated prompt
  refactors. Always read the diff.
- **Don't count pre-existing content as new coverage.** Pre-existing
  text that was rewritten verbatim (same words, same line number) is
  not a feature this PR added. Look for `-` followed by identical `+`.
- **Don't fabricate coverage to be helpful.** If the PR doesn't cover
  a claim, say so with citations. Inventing coverage is worse than
  reporting a gap honestly — it leads the user to merge a PR that
  doesn't actually solve their problem.
- **Don't stop after the first file.** Multi-file PRs often partially
  cover a claim in one file and miss it in another. Read the full
  stat output and all its files.
- **Worktree may be detached.** Use `git rev-parse HEAD` instead of
  `git symbolic-ref HEAD` when the worktree has no branch checked
  out. `git status -sb` will show `## HEAD (no branch)` if detached.
- **Read-only audit.** Never `git checkout`, `git commit`, `git push`,
  or write to the worktree. The audit must be reproducible from the
  same refs the next session sees.
- **Reference files at HEAD, not at merge base.** When citing
  file:line locations, give the line number on the HEAD side (the
  PR's version), not the base side. Otherwise the citation is
  invalid for the version the user is about to merge.
- **Don't conflate "touched" with "added".** A file appearing in
  `git diff --stat` means it was changed, not necessarily that the
  PR added the concepts in that file. Many prompt files have
  pre-existing rule lines that get rewritten in place.

## Verification

Before emitting the JSON, sanity-check:
- Did I read every file in `git diff --stat`?
- Did I grep for the user's specific concepts (not just synonyms I
  guessed)?
- Are all gap citations pointing at real file:line locations in HEAD?
- Are `head_sha` / `base_sha` / `pr_url` actually populated from the
  worktree (not hallucinated)?
- Did I distinguish pre-existing content from new additions for
  every claim?

## Output

- `references/output-template.md` — JSON schema for the gap report,
  with a worked example from PR #8539 in `$GITHUB_REPOSITORY`.
- `references/audit-recipes.md` — Copy-paste shell recipes for the
  common audit moves (worktree inspection, ref resolution in detached
  HEADs, full-diff concept search, pre-existing-vs-new detection,
  HEAD-side citation verification).