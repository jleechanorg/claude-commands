# `--claim-pr N` vs opening a new PR — when the issue body does NOT match the existing PR's scope

Verified 2026-07-27, $GITHUB_REPOSITORY dispatch for issue #8623 against in-flight PR #8421.

## The trap

`ao spawn --claim-pr <N>` rebinds the worker to **the existing PR's `headRefName` branch**. Every commit the worker makes in that worktree lands on that branch. If the issue you were dispatched to address is **conceptually a different PR** (different scope, different title, different review surface), the worker will silently push the new work onto the old PR's branch — which:

1. **Pollutes PR #N's diff** with a refactor that reviewers didn't ask for. Greenhouse review surface explodes.
2. **Violates the `## COMMIT: never-push-onto-someone-elses-pr-head` SOUL.md rule** if the old PR's author != the agent's `gh auth status` user (almost always true on a generic dispatch).
3. **Forces auto-merge / merge-train logic to evaluate the wrong unit of work.** Two unrelated fixes get evaluated together; one gets bogged down and blocks the other.

In the verified case: PR #8421 is the auto-factory "silence-watcher false-parks working coders" fix (a small bash-probe + test). Issue #8623 is a refactor extracting that probe into the agent-orchestrator repo + rewriting CI to call an orchestrator API. Different scope, different reviewers, different test plan. Spawning with `--claim-pr 8421` set the worktree to `factory/$USER-coder-silent-false-parks-h92r-r1` — the PR #8421 branch — instead of a fresh `refactor/8623-extract-coder-silent-probe` branch.

## Recipe — pre-flight before `--claim-pr`

Before every `--claim-pr N` dispatch, run this 4-line check:

```bash
# 1. Title + files of the PR you're about to claim
PR_INFO=$(gh pr view <N> --repo <OWNER>/<REPO> --json title,headRefName,files,author)

# 2. Title + body of the issue / request you were dispatched to address
ISSUE_INFO=$(gh issue view <issue-or-zero> --repo <OWNER>/<REPO> --json title,body)

# 3. Fingerprint-similarity: do the PR's files AND title actually align with the issue body?
# If the PR's title talks about a different bug/feature than the issue, do NOT --claim-pr.
if ! echo "$PR_INFO" | jq -r '.title' | grep -qi "<issue-keyword-1>\|<issue-keyword-2>"; then
  echo "MISMATCH: PR <N> title ~~~$(echo "$PR_INFO" | jq -r '.title')~~~ does not match the issue. Open a new PR instead."
  # Fall back to: git worktree add -b refactor/<issue>-<slug> <path> origin/main,
  # then dispatch with --no-claim-pr (default branch derivation from slug).
fi
```

## Decision matrix

| Situation | Action |
|---|---|
| Issue is **clearly the same scope** as PR #N (e.g. CR feedback on PR #N, or a follow-up commit the PR author is reviewing) | `--claim-pr N` is correct. Worker pushes to PR's `headRefName`. |
| Issue is **clearly a different scope** (extraction refactor, parallel feature, unrelated bug) | **Do NOT `--claim-pr`.** Open a fresh branch from `origin/main` and let the worker open a new PR. |
| Issue and PR overlap but the user's intent is ambiguous (e.g. issue mentions PR #N in passing) | **Default to NEW PR.** Worker opens a sibling PR; user can drop one if needed. Dropping a PR is cheap; reclaiming a polluted PR branch is expensive. |
| Issue is already addressed by PR #N (cross-link, "see #N") | **Skip dispatch entirely.** Post a one-line reply in the originating thread: "Issue addressed by [PR #N](URL); closing this bead." |

## Recovery if you already `--claim-pr N` for the wrong PR

The worker is now on PR #N's branch. Do NOT push a mismatched commit there. Instead:

1. **Tell the worker via `ao send` to stop and switch branches.** Include: "Issue <issue> is not the same scope as PR #N. Stop. Create a fresh branch `refactor/<issue>-<slug>` from `origin/main`, cherry-pick or rebuild the work, and open a new PR. Do NOT push to PR #N's branch."
2. **If the worker already pushed at least one commit to PR #N's branch**, do `git revert <sha>` on that branch (PR #N still gets the clean revert), then proceed with the new branch + new PR.
3. **Update the bead notes** with the pivot.

## Anti-pattern

"Don't worry about the existing PR — just push your work somewhere and the user can sort it out." This is the same anti-pattern documented in `references/wrong-target-removal-stop-X-from-Y-2026-07-20.md` (the wrong-target-removal failure mode generalized to PR branch selection). The user's rule: **correct but misinterpret is fine, but stopping halfway is not.** Polluting PR #N with issue #M's scope is **stopping-and-screwing-up**, not correct-but-misinterpret.

## Companion

- **SOUL.md `## COMMIT: never-push-onto-someone-elses-pr-head`** — covers the case where the PR author != `gh auth status` user. This reference covers the *additional* case where the dispatch's intent is mismatched even when the worker COULD technically push.
- **`dispatch-task` SKILL.md Step 0.5 PR-topology pre-flight** — handles the cases where TWO sibling PRs already exist for the same root cause. This reference handles the case where ONE PR exists and the issue is mismatched.
- **Verified on this host:** 2026-07-27, $GITHUB_REPOSITORY issue #8623 dispatch → AO session `wa-3400` claimed PR #8421 via `--claim-pr`. Worker's branch was `factory/$USER-coder-silent-false-parks-h92r-r1` (PR #8421's head ref) instead of the `refactor/8623-extract-...` branch the issue implies. Recovery: steered via `ao send` to switch.
