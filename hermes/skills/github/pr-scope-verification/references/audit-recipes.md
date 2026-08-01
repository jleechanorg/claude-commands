# Audit Shell Recipes

Copy-paste shell recipes for the most common PR scope verification
moves. Each recipe is a single shell pipeline; chain them.

## 1. Locate and inspect a shared worktree

```bash
cd /private/tmp/pr-cluster-wt-XXXX
git log -1 --format='HEAD: %H%nBranch: %D%nSubject: %s'
git status -sb
git remote -v
```

If `git status -sb` shows `## HEAD (no branch)`, the worktree is
detached. That's normal for shared PR worktrees.

## 2. Resolve correct refs in a detached worktree

```bash
git rev-parse HEAD                    # PR head
git rev-parse origin/main             # target base (or origin/master)
git log origin/main..HEAD --oneline   # commits added by the PR
git diff --stat origin/main..HEAD     # file-level change set
```

## 3. Read every changed file's diff

```bash
git diff origin/main..HEAD -- <path1>
git diff origin/main..HEAD -- <path2>
```

Loop over the file list from `git diff --stat` to make sure you don't
miss any. PRs that span 10+ files often have coverage spread across
multiple files.

## 4. Search the entire diff for user-stated concepts

```bash
git diff origin/main..HEAD | grep -inE \
  "stress arc|unhealthy|insecurity|personal growth|growth direction|Want|Fear|Boundary|mutate|fulfills|negates"
```

Adjust the regex to the user's exact wording. If you grep with
synonyms you guessed, you may miss the exact terminology.

## 5. Distinguish pre-existing content from new additions

A line that appears as a `-removed line` followed by an identical
`+added line` is pre-existing content. Find these:

```bash
# Show only +/- pairs of identical lines (not really practical with shell;
# use Python or just read each hunk carefully).
```

Practical alternative: for each concept, search the BASE side of the
diff for the same wording:

```bash
git show origin/main:$PROJECT_ROOT/prompts/master_directive.md | grep -n "Character Evolution"
```

If the base already contains the text, it's pre-existing — not added
by the PR.

## 6. Map line numbers from the diff to HEAD-side line numbers

The diff's `@@` headers show `-oldstart,oldcount +newstart,newcount`.
The `+newstart` is the HEAD-side line number to cite in gap reports.

```bash
git diff origin/main..HEAD -- <path> | grep -E '^@@'
```

## 7. Verify a file:line citation is real on the HEAD side

```bash
git show HEAD:<path> | sed -n '<line>p'
```

If this prints the line you expected, the citation is valid.

## 8. Count +/- lines per file

```bash
git diff --shortstat origin/main..HEAD
```

Useful for "how big is this PR?" sanity checks.

## 9. Find which test files cover which concept

```bash
git diff origin/main..HEAD -- '*test*.py' | grep -iE "def test_|class .*Test"
```

PRs often add regression tests for the new coverage. Make sure the
tests actually exercise the user's claimed concepts.

## 10. Check for an "umbrella" wrapping commit (multi-PR rebase)

```bash
git log --format='%H %s' origin/main..HEAD
```

If the commit list includes a merge commit early (e.g.
`merge: resolve conflict with origin/main`), the PR may contain
content from multiple prior PRs being replayed. Read ALL commit
messages, not just the head subject.

## Pitfalls when chaining these

- Always anchor `git diff` on `origin/main` (or whatever base you
  resolved in step 2). Anchoring on the wrong base yields a wrong
  diff.
- `git show HEAD:<path>` requires the file to exist at HEAD. If the
  PR deleted it, you'll get an error.
- `grep -iE` is case-insensitive — fine for concept discovery, but
  case-sensitive matches matter when verifying exact code patterns.
  Switch to `grep -E` (no `-i`) for code verification.

## When NOT to use these

- For code review (security, quality, style), use
  `github-code-review` skill instead. This skill is scope/coverage
  only.
- For PR lifecycle (branch, commit, push, open, merge), use
  `github-pr-workflow` skill instead.
- For triaging which PR to work on next, use
  `pr-triage-and-next-steps` skill instead.