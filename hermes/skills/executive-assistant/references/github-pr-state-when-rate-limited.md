# GitHub PR state when `gh pr view` GraphQL is rate-limited

**Added 2026-07-17 20:08 PT sweep.** Verified on `$GITHUB_REPOSITORY` PRs `#8352`, `#8328`, `#8265`, `#8292` (the "PR fleet" DM picks for operator review).

## Symptom

`gh pr view <N> --repo <OWNER>/<REPO>` returns:

```
GraphQL: API rate limit already exceeded for user ID 13840161.
```

But `gh auth status` reports the keyring account `jleechan2015` as active and healthy. The keyring account's hourly GraphQL budget is exhausted at `0/5000` while any env-sourced token (e.g. `GH_TOKEN_AGENTF`) still has full budget.

## Why the obvious fallbacks don't work

| Approach | Result | Why |
|---|---|---|
| `gh pr view --json state,mergeable,...` | `GraphQL: API rate limit already exceeded` | Same GraphQL endpoint, same exhausted budget |
| `unset GH_TOKEN && gh ...` | Same error | `gh` still uses keyring account |
| `GH_TOKEN=$X gh ...` | Same error | Keyring wins over env |
| `curl -H "Authorization: token $GITHUB_TOKEN"` | 401 Unauthorized | `GITHUB_TOKEN` not sourced in this session's bashrc |
| `curl -H "Authorization: token $GH_TOKEN_AGENTF"` | 401 Unauthorized | `GH_TOKEN_AGENTF` was empty in 2026-07-17 20:08 PT cron session — the agentf PAT exists in the keyring but is not exported to env |
| `curl https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8352` (no auth) | 200 OK with `state=null merged_at=null` | Unauthenticated REST returns no state fields |
| `gh pr view --json state --repo ...` | Same rate-limit error | `--json` uses the same GraphQL endpoint |

## What actually works from cron

When the PR is critical to the brief (e.g. operator is queuing `MERGE APPROVED` decisions), surface the gap and cue the operator to use the web UI:

```markdown
## 🔴 Blocked / gaps
- `gh pr view` GraphQL is rate-limited on keyring user 13840161.
- `GH_TOKEN_AGENTF` (agentf PAT) was empty in this session's bashrc.
- Live PR state for #8352 / #8328 / #8265 / #8292 is **unfetchable from cron** —
  cross-check via the GitHub web UI before issuing `MERGE APPROVED <PR#>`:
  - https://github.com/$GITHUB_REPOSITORY/pull/8352
  - https://github.com/$GITHUB_REPOSITORY/pull/8328
  - https://github.com/$GITHUB_REPOSITORY/pull/8265
  - https://github.com/$GITHUB_REPOSITORY/pull/8292
```

**Do NOT claim "PR state unknown" is acceptable to leave un-fixed for a PR that's blocking the operator's queue.** A blocking decision is a blocking decision — the right artifact is the GitHub URL plus the caveat.

## Token restoration recipe (for the next maintenance window)

When ready to restore cron-readable GitHub access:

1. **For agentf token (Agnt-F repos):**
   ```bash
   # Get the PAT from macOS Keychain — it's there but not exported
   security find-internet-password -s github.com -a $USER-af -w
   export GH_TOKEN_AGENTF="<value>"
   ```
   Verify: `curl -sS -H "Authorization: token $GH_TOKEN_AGENTF" https://api.github.com/user | jq .login` should return `"$USER-af"`. This token sees `Agnt-F/*` repos but NOT `jleechanorg/*`.

2. **For jleechanorg/* repos (cross-org):**
   The agentf token cannot see `jleechanorg/*` (404 on `/repos/jleechanorg/...`). Need a separate token with `repo` scope. Source from the jleechan2015 keyring:
   ```bash
   security find-internet-password -s github.com -a jleechan2015 -w
   ```
   This token also has `admin:enterprise` and `workflow` scopes — verify the operator wants it sourced into cron before exposing it broadly. A narrower fine-grained PAT with `Contents: read` + `Pull requests: read` + `Metadata: read` is safer.

3. **Add to `~/.bashrc` under a clearly-marked export block:**
   ```bash
   # Source for executive-assistant cron sweep (do not rotate without updating cron)
   export GH_TOKEN_JLEECHANORG="<fine-grained-PAT-value>"
   ```

4. **Re-test from cron:**
   ```bash
   curl -sS -H "Authorization: token $GH_TOKEN_JLEECHANORG" \
     https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8352 \
     | jq '{state, merged: .merged_at, mergeable, title}'
   ```

## Related

- SKILL.md **P90** — same pitfall summary in the SKILL body
- P137 (in SOUL.md `grep-before-constant-change`) — covers value-replacement audits
- `references/slack-delivery-dead-recipe.md` — same shape of problem (token source mismatch breaks cron path)