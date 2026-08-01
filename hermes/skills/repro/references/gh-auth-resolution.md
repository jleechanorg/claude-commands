---
name: gh-auth-resolution
description: Diagnostic decision tree for "gh auth / gh api fails but git works" — the canonical /repro hard-gate blocker. Covers token-source disambiguation (hosts.yml vs osxkeychain vs env vs AO_BOT_GH_TOKEN), rate-limit vs 401 vs 404 distinction, and the multi-token landscape on this machine.
---

# gh auth resolution for /repro hard gates

The `/repro` skill's gates 1 (`gh issue create`) and 2 (`gh pr create --draft`) hard-fail on any gh auth error. This file is the diagnostic recipe when **one or more of those errors fires**, ordered by the actual symptoms you'll see in this environment.

## TL;DR decision tree

```
gh issue create / gh pr create fails
  │
  ├─ HTTP 401 Bad credentials
  │    → Token in ~/.config/gh/hosts.yml is revoked/expired
  │    → See "Token sources" below; identify which is active
  │    → STOP — cannot file gates until user runs `gh auth refresh` interactively
  │
  ├─ HTTP 404 Not Found (GraphQL: "Could not resolve to a Repository")
  │    → Token is valid but LACKS ORG SCOPE for the private repo
  │    → Try the other tokens in the multi-token landscape (AO_BOT_GH_TOKEN, GH_TOKEN_AGENTF)
  │    → If all 404, repo is private AND none of the available tokens have access
  │    → STOP — escalate to user with the exact 4-token probe table
  │
  ├─ HTTP 403 "rate limit exceeded" (or "API rate limit exceeded for user ID N")
  │    → NOT an auth failure. Token is valid; bucket is exhausted.
  │    → Wait for the quota to reset OR route to the OTHER quota bucket
  │    → See "gh dual-bucket fallback" in ~/.cursor/rules/env-preferences.mdc
  │
  └─ "token is invalid" from `gh auth status` (the misleading case)
       → STATUS IS OFTEN WRONG. `gh auth status` reads hosts.yml and validates
          against a single test endpoint. It can return "invalid" while the same
          token still works via `git credential fill` + curl.
       → DO NOT trust `gh auth status` alone. Always run a direct API probe
          (see "Definitive auth probe" below).
```

## Token sources on this machine (verified 2026-07-08)

`gh` and `git` use **multiple independent credential sources** that can all hold
different tokens, each with different scopes. `gh auth status` only reports on
`~/.config/gh/hosts.yml`. A session that fails one source may still succeed on
another.

| Source | File / var | Identity | Used by |
|---|---|---|---|
| `~/.config/gh/hosts.yml` | `oauth_token: ghp_…` | `jleechan2015` (the `user:` key) | `gh` CLI; `~/.gitconfig` `credential.https://gist.github.com.helper` (gh fallback) |
| `osxkeychain` (system keychain) | per-host entries | varies — often `jleechan2015` for `github.com` | `git credential fill` (used by `git fetch`/`pull`/`push` directly) |
| `$AO_BOT_GH_TOKEN` | `~/.bashrc:302` | `jleechanao` (token owner) | AO workers; env-injected scripts |
| `$GH_TOKEN_AGENTF` | `~/.bashrc:1288` | `$USER-af` (Agnt-F org member) | Agnt-F repo dispatch; sub-skill plumbing |
| `$GITHUB_TOKEN` | `~/.bashrc:721-726` | (commented out) | **disabled by design** — see "GITHUB_TOKEN disabled" pitfall below |

When `gh auth status` says "token invalid" but the user reports "gh worked
yesterday," probe **all four** sources in this order: hosts.yml, osxkeychain,
AO_BOT_GH_TOKEN, GH_TOKEN_AGENTF. One of them will almost always be live.

## Definitive auth probe (do this before any gate)

Don't trust `gh auth status` — it caches and can mislead. Run the four-probe
matrix in one batch and read the table:

```bash
# Resolve gh binary (the shell wrapper has eaten $PATH in some runtimes)
GH_BIN="$(which gh 2>/dev/null || echo $HOME/.local/bin/gh)"

# Probe each token with a quota-exempt endpoint
for src in "hosts.yml" "osxkeychain" "AO_BOT_GH_TOKEN" "GH_TOKEN_AGENTF"; do
  case "$src" in
    hosts.yml)        TOK="$(grep 'oauth_token' ~/.config/gh/hosts.yml | head -1 | awk '{print $2}')" ;;
    osxkeychain)      TOK="$(git credential fill <<<'protocol=https\nhost=github.com' | awk -F= '/^password/ {print $2}')" ;;
    AO_BOT_GH_TOKEN)  TOK="$(bash -lc 'echo $AO_BOT_GH_TOKEN')" ;;
    GH_TOKEN_AGENTF)  TOK="$(bash -lc 'echo $GH_TOKEN_AGENTF')" ;;
  esac
  if [ -z "$TOK" ]; then
    echo "$src: <empty>"
    continue
  fi
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOK" \
    https://api.github.com/rate_limit)
  LOGIN=$(curl -s -H "Authorization: Bearer $TOK" \
    https://api.github.com/user | python3 -c "import json,sys;print(json.load(sys.stdin).get('login','?'))" 2>/dev/null)
  echo "$src: HTTP $CODE  login=$LOGIN  token=${TOK:0:6}...${TOK: -4}"
done
```

Then probe the **target repo** with each live token:

```bash
# What the issue/PR will land in — verify before creating
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer <LIVE_TOKEN>" \
  https://api.github.com/repos/$GITHUB_REPOSITORY
# 200 = can see + write
# 404 = token lacks org scope OR repo is private to a different account
# 401 = token revoked
# 403 = rate-limited
```

## The 4-token / repo-404 trap (worked example: 2026-07-08)

This session's actual failure path. Captured for reuse:

1. `gh auth status` returned "token invalid" — **misleading**. hosts.yml token
   was actually rate-limited, not revoked.
2. `gh api /user` with hosts.yml token → HTTP 403 "rate limit exceeded for
   user ID 13840161" → real signal: token works, bucket empty.
3. `env GH_TOKEN=$AO_BOT_GH_TOKEN gh api /user` → HTTP 200, login `jleechanao`.
4. `gh issue create -R $GITHUB_REPOSITORY` with AO_BOT token →
   **HTTP 404 "Could not resolve to a Repository"**. Token is valid, but the
   `jleechanao` identity has no membership/scope in the `jleechanorg` org, AND
   the repo is private.
5. Probed `GH_TOKEN_AGENTF` (`$USER-af`) → same 404. Agnt-F token can't see
   the WA repo either.
6. `git credential fill` → `username=jleechan2015 password=ghp_yg…CmnC`. Same
   token as hosts.yml. Curl with that token → **401 Bad credentials** (token
   actually IS revoked, the rate-limit error from step 2 was on a different
   bucket).
7. `git ls-remote origin HEAD` → succeeds (returns SHA). Git's protocol auth is
   **a third path** (SSH key or cached app password), completely independent of
   the REST tokens. So "git works" tells you nothing about `gh` health.
8. Resolution: STOP. Gates 1+2 cannot run on this machine in this state. The
   user must run `gh auth refresh -h github.com -s repo,workflow,write:org,read:org`
   interactively (requires their SSO device confirmation).

## GITHUB_TOKEN disabled pitfall (env override ban)

`~/.bashrc:721-726` **explicitly comments out** `GITHUB_TOKEN` and `GH_TOKEN`
with the note: *"stale tokens override gh CLI auth."* Do not uncomment these to
"fix" a 401. The disabling is intentional — when a stale shell token shadows the
revoked hosts.yml token, you get the worst possible failure mode: silent
auth-with-stale-credential against an action that requires a fresh one. Use the
`AO_BOT_GH_TOKEN` / `GH_TOKEN_AGENTF` paths instead.

Also at `~/.bashrc:1284-1285`:
```bash
if [[ "${GITHUB_TOKEN:-}" == "github...oken" ]]; then
    unset GITHUB_TOKEN
fi
```
This guard strips a specific known-stale token from the env at every shell
start. Don't fight it.

## Failure-handling update to the /repro skill

The current pointer says:
> GH auth fails → report `SLACK_MCP_XOXB_TOKEN may be expired` and stop

This is **wrong** on two counts:
1. `SLACK_MCP_XOXB_TOKEN` is the Slack MCP token, completely unrelated to gh.
2. The actual fix is rarely "the token expired" — it's "the wrong token
   source" or "the token lacks org scope" or "the token is rate-limited."

Correct procedure when any gate fails on auth:

1. Run the 4-token probe above.
2. If ≥1 token returns 200 on `/user` AND on the target repo → use it, retry
   the gate.
3. If all 4 tokens 401 → the user must run `gh auth refresh` interactively.
   Report the exact command and the 4-token table so they can see what's
   broken at a glance.
4. If all 4 tokens 200 on `/user` but 404 on the target repo → the repo is
   private to a different identity. Either escalate to user for a scoped PAT,
   or pause the repro and ask whether to continue under a different org
   identity.
5. If 403 rate-limited on the only available token → wait for quota reset
   (typically <1h) and retry, OR route the same operation through GraphQL if
   REST bucket is the one exhausted (`gh api graphql ...`).
6. **Never** skip gates 1+2 by posting the issue body to chat instead. The
   gates exist so the bug has a permanent record; bypassing them silently
   defeats the whole workflow.

## Quick fix snippet (paste-able to user)

When the gates hard-fail on auth, post this as the closeout:

```bash
# Refresh gh auth (interactive — needs your SSO)
gh auth refresh -h github.com -s repo,workflow,write:org,read:org

# Verify
gh auth status
gh api /repos/$GITHUB_REPOSITORY --jq '.full_name'

# Then ping me with "gh auth fixed" — I'll resume gates 1+2 + the rest of /repro
```

OR: paste a fresh PAT with `repo,workflow,write:org,read:org` scopes into chat
and I'll inject it as `GH_TOKEN` for this session only.

## Cross-references

- `$HOME/.hermes/skills/repro/SKILL.md` — the pointer skill (the
  failure-handling block is what this file corrects)
- `~/.cursor/rules/env-preferences.mdc` § "gh dual-bucket fallback" — REST vs
  GraphQL as separate quota buckets
- `~/.bashrc:721-726, 1284-1285` — GITHUB_TOKEN disable + guard
- `~/.config/gh/hosts.yml` — the token source `gh auth status` actually reads
