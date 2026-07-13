---
description: Trigger level-up organic tests against the current PR's preview server
type: tool
scope: project
---

# /levelup — Level-Up Organic Tests Command

## Purpose

Trigger `testing_mcp/core/test_level_up_organic.py` against the PR's deployed preview server
via `.github/workflows/levelup-tests.yml`. Use after `/smoke` passes to verify level-up flows.

## Activation

User types `/levelup` (with optional PR number override).

## Protocol (full skill: `.claude/skills/levelup/SKILL.md`)

### Step 1 — Determine PR number

```bash
# Current branch PR
gh pr view --json number --jq '.number'
```

### Step 2 — Dispatch via workflow_dispatch (reliable, no author_association issue)

```bash
gh workflow run levelup-tests.yml \
  --repo $GITHUB_REPOSITORY \
  --ref main \
  -f pr_number=<PR_NUMBER>
```

> **Note**: PR comments `/levelup` require OWNER/MEMBER/COLLABORATOR. Use `workflow_dispatch`
> for any automated or Claude-triggered runs.

### Step 3 — Monitor and report result

```bash
# Get the dispatched run ID (wait ~5s for registration)
sleep 5 && gh run list --workflow=levelup-tests.yml --repo $GITHUB_REPOSITORY \
  --limit 1 --json databaseId,status --jq '.[0]'

# Watch until complete
gh run watch <RUN_ID> --repo $GITHUB_REPOSITORY
```

### Step 4 — Read PR comment result

```bash
gh pr view <PR_NUMBER> --repo $GITHUB_REPOSITORY \
  --json comments --jq '[.comments[]|select(.body|startswith("## "))][-1].body' | head -20
```

### Step 5 — Iterate on failures

If the test fails:
1. Read the failure comment to identify the failing scenario
2. Check workflow logs: `gh run view <RUN_ID> --repo $GITHUB_REPOSITORY --log | grep -A 30 "FAILED"`
3. Fix the issue on the branch, push, redispatch

## Success Output

```
## ✅ Level-up Organic Tests Passed
All level-up scenarios passed against preview server.
```

## Related Skills

- `.claude/skills/levelup/SKILL.md` — full protocol
- `.claude/skills/level-up-validation/SKILL.md` — validation standards
- `~/.claude/commands/smoke.md` — smoke test command (run first)
