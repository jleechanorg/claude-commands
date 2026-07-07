# ER - Evidence Review

Run an independent evidence review of files matching `evidence*` or `testing_*` in the current PR.

## When to use

Use this skill when you need to verify that evidence or test files in a PR are correct. This is required as condition 6 of the merge gate — the PR must have a PASS comment from evidence review before it can be merged.

## Steps

1. **Identify evidence/test files** in the current PR:
   ```bash
   gh pr view $PR_NUMBER --repo $REPO --json files | jq '.files[].path' | grep -E "^evidence|testing_"
   ```

2. **Read the content** of each evidence/test file:
   ```bash
   gh pr diff $PR_NUMBER --repo $REPO -- -- evidence* testing_*
   ```

3. **Run codex review** on those files:
   ```bash
   codex review --files "<file1,file2,...>"
   ```

4. **Post the result** as a PR comment in the format:
   ```
   **PASS** — evidence review: agent self-reviewed ✅, CR reviewed ✅, codex passed ✅
   ```
   OR
   ```
   **FAIL** — evidence review: <specific reasons>
   ```

## Example

```bash
# Find evidence files
EVIDENCE_FILES=$(gh pr view 123 --repo jleechanorg/jleechanclaw --json files | jq -r '.files[].path' | grep -E "^evidence|testing_" | tr '\n' ',')

# Review with codex
codex review --files "$EVIDENCE_FILES"

# Post result
gh pr comment 123 --repo jleechanorg/jleechanclaw --body "**PASS** — evidence review: agent self-reviewed ✅, CR reviewed ✅, codex passed ✅"
```

## Requirements

- CodeRabbit must have already reviewed the PR (check via `gh pr reviews`)
- Agent must have self-reviewed the diff
- This skill provides the independent verification step

## Output format

Always post the result as a PR comment. The format must be exactly:
- `**PASS** — evidence review: agent self-reviewed ✅, CR reviewed ✅, codex passed ✅`
- or `**FAIL** — evidence review: <reason>`
