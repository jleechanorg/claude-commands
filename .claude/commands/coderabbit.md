---
description: Post "@coderabbitai all good?" on the current branch's PR only after pushing fixes for CodeRabbit comments
type: git
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately.**

## 🚨 GUARDRAIL — When to run
- **Only** run after you have **pushed at least one commit** that addresses CodeRabbit review comments. Do **not** run on a timer or before pushing.
- If you have not yet pushed fixes for CodeRabbit feedback, tell the user to push first, then run this command.

## Step 1: Get current branch and PR
```bash
gh pr view --json number,url,title
```
If no PR is found, tell the user: "No open PR found for the current branch."

## Step 2: Post CodeRabbit re-review ping
Post exactly this (correct GitHub handle is `coderabbitai`, no hyphen):
```bash
gh pr comment <PR_NUMBER> --body "@coderabbitai all good?"
```

## Step 3: Confirm
Report to the user: PR number, URL, and that the comment `@coderabbitai all good?` was posted. Remind that this should be done only after a fix push, not repeatedly.

## Reference
- CodeRabbit Review Protocol: post only after a fresh commit that addresses coderabbitai comments; avoids spam/duplicates.
